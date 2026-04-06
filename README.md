# Pydantic Settings AWS

<p align="center">
  <img src="docs/assets/logo.png" alt="pydantic-settings-aws logo" width="400"/>
</p>

<br/>

[![CI](https://github.com/ceb10n/pydantic-settings-aws/actions/workflows/ci.yml/badge.svg)](https://github.com/ceb10n/pydantic-settings-aws/actions)
[![codecov](https://codecov.io/github/ceb10n/pydantic-settings-aws/graph/badge.svg?token=K77HYDZR3P)](https://codecov.io/github/ceb10n/pydantic-settings-aws)
[![PyPI - Implementation](https://img.shields.io/pypi/implementation/pydantic-settings-aws)](https://pypi.org/project/pydantic-settings-aws)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/pydantic-settings-aws)](https://pypi.org/project/pydantic-settings-aws)
[![Pydantic v2 only](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/pydantic/pydantic/main/docs/badge/v2.json)](https://docs.pydantic.dev/latest/contributing/#badges)
[![PyPI - License](https://img.shields.io/pypi/l/pydantic-settings-aws)](https://pypi.org/project/pydantic-settings-aws)
[![Downloads](https://static.pepy.tech/badge/pydantic-settings-aws/month)](https://pepy.tech/project/pydantic-settings-aws)

`pydantic-settings-aws` extends Pydantic Settings to load configuration from AWS Secrets Manager and SSM Parameter Store directly into type-safe Pydantic models, eliminating the need for manual boto3 parsing or environment variable mapping.

📖 **[Full documentation](https://ceb10n.github.io/pydantic-settings-aws)**

## ✨ Why pydantic-settings-aws?

- Define your configuration once using Pydantic models
- Load secrets and parameters from AWS without manual boto3 code
- Built-in validation, parsing, and type safety
- Works with any AWS authentication method — profiles, SSO, IAM roles, access keys
- Thread-safe and compatible with free-threaded Python

## ⚡ Quick Start

Add your secret to AWS Secrets Manager as a JSON object:

```json
{
    "username": "admin",
    "password": "s3cr3t"
}
```

Then create your settings class:

```python
from pydantic_settings_aws import AWSSettingsConfigDict, SecretsManagerBaseSettings


class MySettings(SecretsManagerBaseSettings):
    model_config = AWSSettingsConfigDict(
        secrets_name="my/secret"
    )

    username: str
    password: str


settings = MySettings()
print(settings.username)  # "admin"
```

That’s it, `boto3` will resolve your AWS credentials automatically using its standard configuration chain.

## ✅ Features

- Load settings from **AWS Secrets Manager**, **SSM Parameter Store**, or both simultaneously
- Type-safe configuration with full IDE autocomplete via `AWSSettingsConfigDict`
- Typed field descriptors `Secrets` and `SSM` as ergonomic alternatives to raw dict metadata
- Structured exception hierarchy (`SecretNotFoundError`, `ParameterNotFoundError`, etc.) for precise error handling
- Multi-region and multi-account support via per-field boto3 clients
- Thread-safe client cache, compatible with free-threaded Python (3.13t, 3.14t)
- Falls back to environment variables, dotenv, and secret files automatically

## 🔧 Requirements

| Python | Pydantic | boto3 |
| :----- | :------- | :---- |
| 3.10+  | v2       | v1    |

## 💽 Installation

```bash
pip install pydantic-settings-aws
```

Or with [uv](https://docs.astral.sh/uv/):

```bash
uv add pydantic-settings-aws
```

## 📦 Usage

You can provide your own boto3 client or let pydantic-settings-aws create one for you. To learn how boto3 resolves credentials, see [Configuring credentials](https://boto3.amazonaws.com/v1/documentation/api/latest/guide/credentials.html#configuring-credentials).

### 🔐 Secrets Manager — with boto3 client

```python
import boto3
from pydantic_settings_aws import AWSSettingsConfigDict, SecretsManagerBaseSettings


client = boto3.client("secretsmanager")


class MySettings(SecretsManagerBaseSettings):
    model_config = AWSSettingsConfigDict(
        secrets_name="my/secret",
        secrets_client=client
    )

    username: str
    password: str
    name: str | None = None


settings = MySettings()
```

Your secret content must be valid JSON with keys matching the field names:

```json
{
    "username": "admin",
    "password": "admin",
    "name": "John"
}
```

### 📦 SSM Parameter Store

```python
from typing import Annotated
from pydantic_settings_aws import AWSSettingsConfigDict, ParameterStoreBaseSettings, SSM


class MySettings(ParameterStoreBaseSettings):
    model_config = AWSSettingsConfigDict(aws_region="us-east-1")

    # pydantic-settings-aws looks for a parameter named "db_host"
    db_host: str

    # explicit parameter name via SSM descriptor
    db_port: Annotated[str, SSM(name="/myapp/prod/db/port")]
```

### 🙋🏾‍♂️ Secrets Manager — with AWS profile

```python
from pydantic_settings_aws import AWSSettingsConfigDict, SecretsManagerBaseSettings


class MySettings(SecretsManagerBaseSettings):
    model_config = AWSSettingsConfigDict(
        secrets_name="my/secret",
        aws_region="us-east-1",
        aws_profile="dev"
    )

    username: str
    password: str
```

### 🔑 Secrets Manager — with access key

```python
from pydantic_settings_aws import AWSSettingsConfigDict, SecretsManagerBaseSettings


class MySettings(SecretsManagerBaseSettings):
    model_config = AWSSettingsConfigDict(
        secrets_name="my/secret",
        aws_region="us-east-1",
        aws_access_key_id="aws_access_key_id",
        aws_secret_access_key="aws_secret_access_key",
        aws_session_token="aws_session_token"
    )

    username: str
    password: str
```

### 🔒 Secrets Manager — with AWS IAM Identity Center (SSO)

```shell
aws sso login --profile my-profile
```

```python
from pydantic_settings_aws import AWSSettingsConfigDict, SecretsManagerBaseSettings


class MySettings(SecretsManagerBaseSettings):
    model_config = AWSSettingsConfigDict(
        secrets_name="my/secret"
    )

    username: str
    password: str
```

## 👩🏼‍⚖️ License

This project is licensed under the terms of the [MIT license.](LICENSE)
