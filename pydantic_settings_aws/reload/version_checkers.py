from typing import Any, Protocol, runtime_checkable

from pydantic_settings_aws.logger import logger


@runtime_checkable
class VersionChecker(Protocol):
    """Protocol for lightweight AWS change detection.

    Implementations check whether remote settings have changed using
    cheap metadata calls, so :class:`~pydantic_settings_aws.reload.SettingsReloader`
    can skip a full re-fetch when nothing changed.
    """

    def has_changed(self) -> bool:
        """Return ``True`` if the remote value has changed since the last check.

        On the very first call the implementation should record the current
        version and return ``False`` (the value was just loaded by the reloader).
        On subsequent calls it compares the stored version with the live one.

        If the metadata call itself fails, implementations should return ``True``
        so the reloader falls back to a full re-fetch rather than silently
        skipping a potential change.
        """
        ...


class SecretsManagerVersionChecker:
    """Detects Secrets Manager changes via ``describe_secret`` — no secret value is fetched.

    ``describe_secret`` returns the current ``VersionId`` (the UUID tagged with
    ``AWSCURRENT``) without transferring the secret payload. The full
    ``get_secret_value`` call is only made when the ``VersionId`` differs from
    the one seen on the previous check.

    Args:
        client: A boto3 Secrets Manager client (or any object with a
            ``describe_secret(SecretId=...)`` method).
        secret_name: The secret name or ARN passed as ``SecretId``.

    Example::

        checker = SecretsManagerVersionChecker(
            client=boto3.client("secretsmanager"),
            secret_name="myapp/db",
        )
        reloader = SettingsReloader(MySettings, interval=60, version_checker=checker)
    """

    def __init__(self, client: Any, secret_name: str) -> None:
        self._client = client
        self._secret_name = secret_name
        self._last_version_id: str | None = None

    def has_changed(self) -> bool:
        try:
            response = self._client.describe_secret(SecretId=self._secret_name)
        except Exception:
            logger.exception(
                "SecretsManagerVersionChecker: describe_secret failed, "
                "assuming changed to trigger a full reload"
            )
            return True

        versions: dict[str, list[str]] = response.get("VersionIdsToStages", {})
        current_version_id = next(
            (vid for vid, stages in versions.items() if "AWSCURRENT" in stages),
            None,
        )

        if self._last_version_id is None:
            # First call — record version, assume in sync with the initial load.
            self._last_version_id = current_version_id
            return False

        if current_version_id != self._last_version_id:
            self._last_version_id = current_version_id
            return True

        return False


class SSMVersionChecker:
    """Detects SSM Parameter Store changes by comparing ``Parameter.Version``.

    Unlike :class:`SecretsManagerVersionChecker`, SSM has no lightweight
    "describe" API for standard parameters — ``get_parameters`` (batch) is
    called every check. The benefit over a plain reload is that settings
    instantiation, change diffing, and event dispatch are all skipped when
    the versions are unchanged.

    Args:
        client: A boto3 SSM client (or any object with a
            ``get_parameters(Names=..., WithDecryption=...)`` method).
        parameter_names: The SSM parameter names to watch. These must match
            the names resolved by your settings class.

    Note:
        If your settings use per-field clients (``ssm_client`` in ``Annotated``
        metadata), make sure the client passed here has access to the same
        parameters.

    Example::

        checker = SSMVersionChecker(
            client=boto3.client("ssm"),
            parameter_names=["/myapp/db/host", "/myapp/db/port"],
        )
        reloader = SettingsReloader(MySettings, interval=60, version_checker=checker)
    """

    def __init__(self, client: Any, parameter_names: list[str]) -> None:
        self._client = client
        self._parameter_names = parameter_names
        self._last_versions: dict[str, int] = {}

    def has_changed(self) -> bool:
        try:
            current_versions = self._fetch_versions()
        except Exception:
            logger.exception(
                "SSMVersionChecker: get_parameters failed, "
                "assuming changed to trigger a full reload"
            )
            return True

        if not self._last_versions:
            # First call — record versions, assume in sync with the initial load.
            self._last_versions = current_versions
            return False

        changed = current_versions != self._last_versions
        if changed:
            self._last_versions = current_versions
        return changed

    def _fetch_versions(self) -> dict[str, int]:
        versions: dict[str, int] = {}
        # get_parameters accepts up to 10 names per call.
        for i in range(0, len(self._parameter_names), 10):
            batch = self._parameter_names[i : i + 10]
            response = self._client.get_parameters(Names=batch, WithDecryption=True)
            for param in response.get("Parameters", []):
                versions[param["Name"]] = param["Version"]
        return versions
