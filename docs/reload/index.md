# :fontawesome-solid-arrows-rotate: Live Reloading

`pydantic-settings-aws` includes a built-in live reloading mechanism that keeps your settings in sync with AWS as secrets rotate or parameters change — without restarting your application.

## How it works

`SettingsReloader` is a **transparent proxy** that wraps any settings class. It forwards all attribute access to the current inner settings instance, so existing code that reads `settings.db_user` works unchanged.

When a reload happens (on a schedule, after a TTL, or explicitly), the reloader creates a new settings instance, diffs it field-by-field against the old one, and fires change events only for fields that actually changed. Your application can react — for example, recreating a database connection when the password rotates.

```python
from pydantic_settings_aws import (
    AWSSettingsConfigDict,
    SecretsManagerBaseSettings,
    SettingsReloader,
)

class MySettings(SecretsManagerBaseSettings):
    model_config = AWSSettingsConfigDict(secrets_name="myapp/db")
    db_user: str
    db_password: str

reloader = SettingsReloader(MySettings, interval=60)

@reloader.on_change("db_user", "db_password")
def reconnect(changed):
    recreate_db_connection(
        user=changed["db_user"].new,
        password=changed["db_password"].new,
    )

with reloader:
    print(reloader.db_user)  # reads from the live inner instance
```

## Reload modes

### Background thread — `interval`

A daemon thread polls AWS every *interval* seconds. Use `start()` / `stop()` or the context manager to control the thread.

```python
# context manager (recommended)
with SettingsReloader(MySettings, interval=60) as reloader:
    ...

# or manually
reloader = SettingsReloader(MySettings, interval=60)
reloader.start()
# ... app runs ...
reloader.stop()
```

### Lazy TTL — `ttl`

No background thread. On the first attribute access after *ttl* seconds, the reloader re-fetches from AWS before returning the value. Good for Lambda and other serverless runtimes.

```python
reloader = SettingsReloader(MySettings, ttl=300)
print(reloader.db_password)  # re-fetches from AWS if 5 minutes have elapsed
```

### Manual — no mode

Call `reload()` explicitly — for example, on a POSIX signal or a health-check endpoint.

```python
import signal

reloader = SettingsReloader(MySettings)

signal.signal(signal.SIGHUP, lambda *_: reloader.reload())
```

## Change events

Register callbacks with `on_change()`. Each callback receives `dict[str, ChangeEvent]` where `ChangeEvent` has `field`, `old`, and `new` attributes.

```python
from pydantic_settings_aws import ChangeEvent

# per-field: only fires when db_user or db_password changed
@reloader.on_change("db_user", "db_password")
def reconnect(changed: dict[str, ChangeEvent]) -> None:
    new_password = changed["db_password"].new
    ...

# global: fires for any field change
@reloader.on_change()
def log_all(changed: dict[str, ChangeEvent]) -> None:
    for field, event in changed.items():
        print(f"{field}: {event.old!r} → {event.new!r}")
```

A callback registered for multiple fields is called **once per reload** with all its relevant changes — not once per field.

Callback exceptions are caught and logged; one failing callback does not prevent others from running.

## Reducing unnecessary fetches

By default the reloader calls `settings_cls()` on every poll, which hits AWS regardless of whether anything changed. You can attach a [Version Checker](version-checkers.md) to skip the full re-fetch when nothing has changed.

```python
from pydantic_settings_aws import SecretsManagerVersionChecker, SettingsReloader

checker = SecretsManagerVersionChecker(
    client=boto3.client("secretsmanager"),
    secret_name="myapp/db",
)
reloader = SettingsReloader(MySettings, interval=60, version_checker=checker)
```

See [Version Checkers](version-checkers.md) for details.

## Error handling

- If `settings_cls()` raises during a reload, the current settings are kept unchanged and the exception is logged. The reloader never surfaces a reload error to the caller.
- If a version checker's metadata call fails, it conservatively returns `True` so a full reload is attempted rather than silently missing a change.
