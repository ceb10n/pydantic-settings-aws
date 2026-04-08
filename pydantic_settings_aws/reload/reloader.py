import threading
import time
from collections.abc import Callable
from typing import Any, Generic, TypeVar

from pydantic_settings_aws.logger import logger
from pydantic_settings_aws.reload.events import ChangeEvent
from pydantic_settings_aws.reload.version_checkers import VersionChecker

T = TypeVar("T")


class SettingsReloader(Generic[T]):
    """Transparent proxy that reloads settings from AWS on a schedule or TTL.

    Forwards all attribute access to the current inner settings instance, so
    existing code that reads ``settings.my_field`` works unchanged.

    Three reload modes:

    - **interval**: background daemon thread polls AWS every *interval* seconds.
      Use ``start()`` / ``stop()`` or the context manager to control the thread.
    - **ttl**: lazy reload — on the first attribute access after *ttl* seconds
      have elapsed, settings are re-fetched before returning the value.
    - **manual**: no automatic reloading; call ``reload()`` explicitly.

    Change events are fired only for fields whose values actually differ between
    reloads. Callbacks registered via :meth:`on_change` receive a
    ``dict[str, ChangeEvent]`` containing only the fields they were registered
    for (or all changed fields for global listeners).

    Example — background mode::

        class MySettings(SecretsManagerBaseSettings):
            db_user: str
            db_password: str
            model_config = AWSSettingsConfigDict(secrets_name="myapp/db")

        reloader = SettingsReloader(MySettings, interval=60)

        @reloader.on_change("db_user", "db_password")
        def reconnect(changed: dict[str, ChangeEvent]) -> None:
            recreate_db_connection(changed["db_user"].new)

        with reloader:
            print(reloader.db_user)  # reads from current inner instance

    Example — lazy TTL mode::

        reloader = SettingsReloader(MySettings, ttl=300)
        print(reloader.db_user)  # re-fetches from AWS if TTL expired

    Example — with a version checker to skip full fetches when nothing changed::

        checker = SecretsManagerVersionChecker(
            client=boto3.client("secretsmanager"),
            secret_name="myapp/db",
        )
        reloader = SettingsReloader(MySettings, interval=60, version_checker=checker)
    """

    def __init__(
        self,
        settings_cls: type[T],
        *,
        interval: float | None = None,
        ttl: float | None = None,
        version_checker: VersionChecker | None = None,
    ) -> None:
        if interval is not None and ttl is not None:
            raise ValueError("Specify either interval or ttl, not both")

        object.__setattr__(self, "_settings_cls", settings_cls)
        object.__setattr__(self, "_interval", interval)
        object.__setattr__(self, "_ttl", ttl)
        object.__setattr__(self, "_version_checker", version_checker)
        object.__setattr__(self, "_lock", threading.RLock())
        object.__setattr__(self, "_current", settings_cls())
        object.__setattr__(self, "_last_load", time.monotonic())
        # dict[str | None, list[Callable]] — None key = global listeners
        object.__setattr__(self, "_listeners", {})
        object.__setattr__(self, "_stop_event", threading.Event())
        object.__setattr__(self, "_thread", None)

    # ------------------------------------------------------------------
    # Proxy

    def __getattr__(self, name: str) -> Any:
        ttl = object.__getattribute__(self, "_ttl")
        if ttl is not None:
            lock = object.__getattribute__(self, "_lock")
            last_load = object.__getattribute__(self, "_last_load")
            if time.monotonic() - last_load > ttl:
                with lock:
                    # double-checked locking: re-read last_load inside the lock
                    if time.monotonic() - object.__getattribute__(self, "_last_load") > ttl:
                        self.reload()
        current = object.__getattribute__(self, "_current")
        return getattr(current, name)

    # ------------------------------------------------------------------
    # Events

    def on_change(self, *fields: str) -> Callable[[Callable[[dict[str, ChangeEvent]], None]], Callable[[dict[str, ChangeEvent]], None]]:
        """Register a callback that fires when any of *fields* change.

        The callback signature is ``(changed: dict[str, ChangeEvent]) -> None``.
        When registered for multiple fields, it is called **once** per reload
        with all the fields that changed (filtered to the registered ones).

        If no fields are given, the callback fires for **any** change and
        receives the complete ``dict[str, ChangeEvent]``.

        Can be used as a decorator::

            @reloader.on_change("db_user", "db_password")
            def handle(changed: dict[str, ChangeEvent]) -> None:
                reconnect(changed["db_user"].new)
        """
        def decorator(fn: Callable[[dict[str, ChangeEvent]], None]) -> Callable[[dict[str, ChangeEvent]], None]:
            listeners: dict[str | None, list[Callable[[dict[str, ChangeEvent]], None]]] = object.__getattribute__(self, "_listeners")
            if fields:
                for field in fields:
                    listeners.setdefault(field, []).append(fn)
            else:
                listeners.setdefault(None, []).append(fn)
            return fn
        return decorator

    # ------------------------------------------------------------------
    # Reload

    def reload(self) -> None:
        """Re-fetch settings from AWS and fire change events for modified fields.

        If a *version_checker* is configured and reports no change, the full
        re-fetch is skipped entirely. If re-fetching fails, the current settings
        are kept unchanged and the exception is logged.
        """
        version_checker: VersionChecker | None = object.__getattribute__(self, "_version_checker")
        if version_checker is not None and not version_checker.has_changed():
            return

        settings_cls = object.__getattribute__(self, "_settings_cls")
        lock = object.__getattribute__(self, "_lock")
        listeners: dict[str | None, list[Callable[[dict[str, ChangeEvent]], None]]] = object.__getattribute__(self, "_listeners")

        try:
            new_instance = settings_cls()
        except Exception:
            logger.exception("Failed to reload settings, keeping current values")
            return

        changed: dict[str, ChangeEvent] = {}

        with lock:
            current = object.__getattribute__(self, "_current")
            for field in settings_cls.model_fields:
                old_val = getattr(current, field)
                new_val = getattr(new_instance, field)
                if old_val != new_val:
                    changed[field] = ChangeEvent(field=field, old=old_val, new=new_val)
            object.__setattr__(self, "_current", new_instance)
            object.__setattr__(self, "_last_load", time.monotonic())

        if not changed:
            return

        # Build per-callback payload: deduplicate so multi-field listeners
        # are called once with all their relevant changes.
        callbacks_to_fire: dict[int, tuple[Callable[[dict[str, ChangeEvent]], None], dict[str, ChangeEvent]]] = {}
        for field, event in changed.items():
            for cb in listeners.get(field, []):
                cb_id = id(cb)
                if cb_id not in callbacks_to_fire:
                    callbacks_to_fire[cb_id] = (cb, {})
                callbacks_to_fire[cb_id][1][field] = event

        for _, (cb, events) in callbacks_to_fire.items():
            try:
                cb(events)
            except Exception:
                logger.exception("Error in change listener")

        for cb in listeners.get(None, []):
            try:
                cb(changed)
            except Exception:
                logger.exception("Error in global change listener")

    # ------------------------------------------------------------------
    # Background thread (interval mode)

    def start(self) -> "SettingsReloader[T]":
        """Start the background polling thread. Returns *self* for chaining.

        Only valid in interval mode.
        """
        interval = object.__getattribute__(self, "_interval")
        if interval is None:
            raise RuntimeError(
                "start() requires interval mode; pass interval= to SettingsReloader"
            )
        stop_event = object.__getattribute__(self, "_stop_event")
        stop_event.clear()
        thread = threading.Thread(
            target=self._run,
            daemon=True,
            name="pydantic-settings-aws-reloader",
        )
        object.__setattr__(self, "_thread", thread)
        thread.start()
        return self

    def stop(self) -> None:
        """Signal the background thread to stop and wait for it to exit."""
        stop_event = object.__getattribute__(self, "_stop_event")
        stop_event.set()
        thread = object.__getattribute__(self, "_thread")
        if thread is not None:
            thread.join()

    def _run(self) -> None:
        interval = object.__getattribute__(self, "_interval")
        stop_event = object.__getattribute__(self, "_stop_event")
        while not stop_event.wait(timeout=interval):
            self.reload()

    def __enter__(self) -> "SettingsReloader[T]":
        return self.start()

    def __exit__(self, *args: Any) -> None:
        self.stop()
