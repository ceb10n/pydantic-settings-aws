# pydantic-settings-aws skill

## Overview

`pydantic-settings-aws` extends [Pydantic Settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/) to load settings from AWS Secrets Manager and AWS Systems Manager Parameter Store.

- Version: 1.0.0b1
- Requires: Python >= 3.10, pydantic >= 2.0.1, pydantic-settings >= 2.0.2, boto3 >= 1.27.0

## Critical rules

- Always use `AWSSettingsConfigDict` (from `pydantic_settings_aws`) instead of pydantic-settings' `SettingsConfigDict`. `AWSSettingsConfigDict` extends it and adds autocomplete and type safety for all AWS-specific keys.
- Never import `SettingsConfigDict` from `pydantic_settings` when using this library.
- The boto3 client cache is thread-safe and safe for free-threaded Python (no-GIL) builds.

## Base classes

Choose the base class that matches your use case:

| Class | Use when |
| :---- | :------- |
| `SecretsManagerBaseSettings` | All settings come from a single Secrets Manager secret (JSON) |
| `ParameterStoreBaseSettings` | All settings come from SSM Parameter Store parameters |
| `AWSBaseSettings` | Settings come from both Secrets Manager and Parameter Store |

## AWSSettingsConfigDict keys

### boto3 session (all optional)

```python
aws_region: str | None          # e.g. "us-east-1"
aws_profile: str | None         # e.g. "dev"
aws_access_key_id: str | None
aws_secret_access_key: str | None
aws_session_token: str | None
```

### Secrets Manager (secrets_name is required when using SecretsManagerBaseSettings or AWSBaseSettings with secrets)

```python
secrets_name: str               # required — name or ARN of the secret
secrets_version: str | None     # optional — version ID
secrets_stage: str | None       # optional — version stage (e.g. "AWSCURRENT")
secrets_client: Any             # optional — pre-built boto3 secretsmanager client
```

### Parameter Store (all optional)

```python
ssm_client: Any                 # optional — pre-built boto3 SSM client
```

## Usage examples

### Secrets Manager — simplest

```python
from pydantic_settings_aws import AWSSettingsConfigDict, SecretsManagerBaseSettings


class MySettings(SecretsManagerBaseSettings):
    model_config = AWSSettingsConfigDict(
        secrets_name="myapp/prod/db"
    )

    username: str
    password: str
```

The secret content must be valid JSON with keys matching the field names:

```json
{"username": "admin", "password": "s3cr3t"}
```

### Secrets Manager — with explicit boto3 client

```python
import boto3
from pydantic_settings_aws import AWSSettingsConfigDict, SecretsManagerBaseSettings

client = boto3.client("secretsmanager", region_name="us-east-1")


class MySettings(SecretsManagerBaseSettings):
    model_config = AWSSettingsConfigDict(
        secrets_name="myapp/prod/db",
        secrets_client=client
    )

    username: str
    password: str
```

### Parameter Store — field name as parameter name

```python
from pydantic_settings_aws import ParameterStoreBaseSettings


class MySettings(ParameterStoreBaseSettings):
    # pydantic-settings-aws looks for a parameter named "db_host"
    db_host: str
    db_port: str
```

### Parameter Store — explicit parameter name via Annotated

```python
from typing import Annotated
from pydantic_settings_aws import AWSSettingsConfigDict, ParameterStoreBaseSettings


class MySettings(ParameterStoreBaseSettings):
    model_config = AWSSettingsConfigDict(ssm_client=my_client)

    db_host: Annotated[str, "/myapp/prod/db/host"]
```

### Parameter Store — multiple accounts or regions

Use a dict in `Annotated` with `ssm` (parameter name) and `ssm_client` (per-field client):

```python
from typing import Annotated
from pydantic_settings_aws import ParameterStoreBaseSettings


class MySettings(ParameterStoreBaseSettings):
    us_host: Annotated[str, {"ssm": "/prod/us/db/host", "ssm_client": us_client}]
    eu_host: Annotated[str, {"ssm": "/prod/eu/db/host", "ssm_client": eu_client}]
```

### AWSBaseSettings — mixed sources

Use `{"service": "secrets"}` or `{"service": "ssm"}` in `Annotated` to route each field:

```python
from typing import Annotated
from pydantic_settings_aws import AWSBaseSettings, AWSSettingsConfigDict


class MySettings(AWSBaseSettings):
    model_config = AWSSettingsConfigDict(
        secrets_name="myapp/prod/credentials",
        secrets_client=secrets_client,
        ssm_client=ssm_client
    )

    # loaded from Secrets Manager
    username: Annotated[str, {"service": "secrets"}]
    password: Annotated[str, {"service": "secrets"}]

    # loaded from Parameter Store
    db_host: Annotated[str, {"service": "ssm", "ssm": "/myapp/prod/db/host"}]

    # loaded from environment variable (standard pydantic-settings fallback)
    log_level: str
```

## Live Reloading

`SettingsReloader` is a transparent proxy that reloads settings from AWS on a schedule or TTL and fires change events when field values change.

### Import

```python
from pydantic_settings_aws import (
    ChangeEvent,
    SecretsManagerVersionChecker,
    SettingsReloader,
    SSMVersionChecker,
    VersionChecker,
)
```

### SettingsReloader

```python
SettingsReloader(
    settings_cls,        # any settings class
    *,
    interval=None,       # float — background thread polls every N seconds
    ttl=None,            # float — lazy reload after N seconds of staleness
    version_checker=None # VersionChecker | None
)
```

- `interval` and `ttl` are mutually exclusive. Omit both for manual-only reloading.
- Acts as a transparent proxy: `reloader.my_field` forwards to the current inner instance.
- `reload()` — re-fetch immediately.
- `start()` / `stop()` — start/stop background thread (interval mode only).
- Context manager (`with reloader`) — calls `start()` on enter, `stop()` on exit.

### Change events

```python
@reloader.on_change("field1", "field2")
def handle(changed: dict[str, ChangeEvent]) -> None:
    # called once per reload with all registered fields that changed
    old = changed["field1"].old
    new = changed["field1"].new

@reloader.on_change()  # no args = global listener, fires for any change
def handle_all(changed: dict[str, ChangeEvent]) -> None:
    ...
```

`ChangeEvent` has three attributes: `field: str`, `old: Any`, `new: Any`.

### Version checkers

Version checkers skip the full `settings_cls()` call when nothing changed in AWS. Pass one via `version_checker=`.

**`SecretsManagerVersionChecker`** — calls `describe_secret` (no secret payload). Real API savings when polling frequently.

```python
checker = SecretsManagerVersionChecker(
    client=boto3.client("secretsmanager"),
    secret_name="myapp/db",
)
```

**`SSMVersionChecker`** — calls `get_parameters` (batch, up to 10 per call) and compares `Parameter.Version` integers. Still makes an API call but skips instantiation and diffing.

```python
checker = SSMVersionChecker(
    client=boto3.client("ssm"),
    parameter_names=["/myapp/db/host", "/myapp/db/port"],
)
```

**`VersionChecker`** — `runtime_checkable` Protocol. Any object with `has_changed() -> bool` satisfies it. First call should return `False`; return `True` on errors (conservative fallback).

### Critical rules for live reloading

- Never pass both `interval` and `ttl` — raises `ValueError`.
- `start()` raises `RuntimeError` if not in interval mode.
- If `settings_cls()` raises during reload, current values are kept and the exception is logged — the reloader never propagates reload errors to callers.
- Callbacks that raise are caught and logged; remaining callbacks still run.

## Settings priority

1. `__init__` arguments
2. AWS sources (Secrets Manager / Parameter Store)
3. Environment variables
4. dotenv files
5. Secret files

## Known pitfalls

- Secrets Manager content **must** be valid JSON. A plain string secret will raise `json.JSONDecodeError`.
- Only **one** Secrets Manager secret per settings class. Use multiple `ssm_client` values in `Annotated` for multi-region Parameter Store.
- If no client is provided and no AWS credentials are configured, boto3 will raise an exception. pydantic-settings-aws does not suppress boto3 or pydantic errors.
- `AWSBaseSettings` fields without `{"service": ...}` metadata are silently skipped for AWS lookups and fall through to the standard pydantic-settings source chain.
