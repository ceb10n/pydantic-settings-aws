# :fontawesome-solid-magnifying-glass: Version Checkers

Version checkers let `SettingsReloader` skip a full AWS re-fetch when nothing has changed. Instead of calling `settings_cls()` on every poll, the reloader first calls a lightweight metadata API and only proceeds if the version has changed.

## SecretsManagerVersionChecker

Calls `describe_secret` — which returns secret metadata **without transferring the secret payload** — and compares the `AWSCURRENT` `VersionId` (a UUID that changes on every rotation).

This is the primary win: for high-frequency polling with infrequent rotations, you avoid the `GetSecretValue` call on every poll cycle.

```python
import boto3
from pydantic_settings_aws import (
    AWSSettingsConfigDict,
    SecretsManagerBaseSettings,
    SecretsManagerVersionChecker,
    SettingsReloader,
)

class MySettings(SecretsManagerBaseSettings):
    model_config = AWSSettingsConfigDict(secrets_name="myapp/db")
    db_user: str
    db_password: str

checker = SecretsManagerVersionChecker(
    client=boto3.client("secretsmanager"),
    secret_name="myapp/db",
)
reloader = SettingsReloader(MySettings, interval=60, version_checker=checker)
```

!!! tip "Separate clients are fine"
    The client passed to `SecretsManagerVersionChecker` does not have to be the same object as `secrets_client` in `model_config`. Both just need access to the same secret.

### Behaviour

| Call | What happens |
| :--- | :----------- |
| First `has_changed()` | Fetches the current `VersionId`, stores it, returns `False` (assumes in sync with the initial load) |
| Subsequent calls — version unchanged | Returns `False` |
| Subsequent calls — version changed | Updates the stored `VersionId`, returns `True` |
| `describe_secret` raises | Returns `True` — triggers a full reload rather than silently missing a change |

## SSMVersionChecker

Calls `get_parameters` (batch, up to 10 per request) and compares the `Version` integer for each parameter. SSM has no lightweight "describe" equivalent for standard parameters, so this always makes an API call — but it still avoids settings instantiation, change diffing, and event dispatch when nothing changed.

```python
import boto3
from pydantic_settings_aws import (
    AWSSettingsConfigDict,
    ParameterStoreBaseSettings,
    SSMVersionChecker,
    SettingsReloader,
)

class MySettings(ParameterStoreBaseSettings):
    model_config = AWSSettingsConfigDict(aws_region="us-east-1")
    db_host: str
    db_port: str

checker = SSMVersionChecker(
    client=boto3.client("ssm"),
    parameter_names=["/myapp/prod/db/host", "/myapp/prod/db/port"],
)
reloader = SettingsReloader(MySettings, interval=60, version_checker=checker)
```

!!! warning "Parameter names must match"
    The names passed to `SSMVersionChecker` must match the names actually resolved by your settings class. If your fields use per-field `ssm_client` values pointing to different accounts or regions, a single `SSMVersionChecker` client may not be able to reach all of them.

### Behaviour

| Call | What happens |
| :--- | :----------- |
| First `has_changed()` | Fetches `Version` for all parameters, stores them, returns `False` |
| Subsequent calls — all versions unchanged | Returns `False` |
| Subsequent calls — any version incremented | Updates stored versions, returns `True` |
| `get_parameters` raises | Returns `True` — triggers a full reload |

## Writing a custom version checker

`VersionChecker` is a `runtime_checkable` `Protocol`. Any class with a `has_changed() -> bool` method satisfies it.

```python
from pydantic_settings_aws import VersionChecker, SettingsReloader

class MyChecker:
    def has_changed(self) -> bool:
        # your logic — e.g. poll a DynamoDB table, read an S3 object ETag, etc.
        ...

reloader = SettingsReloader(MySettings, interval=60, version_checker=MyChecker())
```

### Guidelines for custom implementations

- **First call should return `False`** — the reloader already loaded initial values in `__init__`; returning `True` on the first check would trigger an immediate redundant reload.
- **Return `True` on errors** — if your metadata call fails, assume a change may have occurred so the full reload runs as a fallback.
- **Store state between calls** — the checker instance is long-lived; keep the last-seen version in an instance attribute.
