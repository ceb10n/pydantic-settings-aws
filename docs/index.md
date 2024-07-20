# Pydantic Settings AWS

[![CI](https://github.com/ceb10n/pydantic-settings-aws/actions/workflows/ci.yml/badge.svg)](https://github.com/ceb10n/pydantic-settings-aws/actions)
[![codecov](https://codecov.io/github/ceb10n/pydantic-settings-aws/graph/badge.svg?token=K77HYDZR3P)](https://codecov.io/github/ceb10n/pydantic-settings-aws)
[![PyPI - Implementation](https://img.shields.io/pypi/implementation/pydantic-settings-aws)](https://pypi.org/project/pydantic-settings-aws)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/pydantic-settings-aws)](https://pypi.org/project/pydantic-settings-aws)
[![Pydantic v2 only](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/pydantic/pydantic/main/docs/badge/v2.json)](https://docs.pydantic.dev/latest/contributing/#badges)
[![PyPI - License](https://img.shields.io/pypi/l/pydantic-settings-aws)](https://pypi.org/project/pydantic-settings-aws)
[![Downloads](https://static.pepy.tech/badge/pydantic-settings-aws/month)](https://pepy.tech/project/pydantic-settings-aws)

Pydantic Settings AWS is an extension of the great 🚀 [Pydantic Settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/) library.

It offers an easy way to load your settings hosted in ☁️ AWS [Secrets Manager](https://aws.amazon.com/secrets-manager/) and [Parameter Store](https://docs.aws.amazon.com/systems-manager/latest/userguide/systems-manager-parameter-store.html).

## Installation

You can install pydantic-settings-aws with [pip](https://pypi.org/project/pip/):

```bash
pip install pydantic-settings-aws
```

`pydantic-settings-aws` will install some dependencies for you:

- pydantic >= 2.0.1
- pydantic-settings >= 2.0.2
- boto3 >= 1.27.0
- boto3-stubs[secretsmanager] >= 1.27.0

## Usage

Using pydantic-settings-aws can be as easy as:

=== "no boto3"

    ```py title="settings.py" linenums="1"
    # import pydantic_settings_aws
    from pydantic_settings_aws import SecretsManagerBaseSettings


    class AWSSecretsSettings(SecretsManagerBaseSettings):
        model_config = SettingsConfigDict(
            secrets_name="my/secret" # just put your secrets manager name
        )

        username: str
        password: str


    settings = AWSSecretsSettings()
    ```

=== "with boto3 client"

    ```py title="settings.py" linenums="1"
    import boto3
    from pydantic_settings_aws import SecretsManagerBaseSettings

    client = boto3.client("secretsmanager")


    class AWSSecretsSettings(SecretsManagerBaseSettings):
        model_config = SettingsConfigDict(
            secrets_name="my/secret", # just put your secrets manager name
            secrets_client=client # pass your already created boto3 client
        )

        username: str
        password: str


    settings = AWSSecretsSettings()
    ```


=== "with profile"

    ```py title="settings.py" linenums="1"
    from pydantic_settings_aws import SecretsManagerBaseSettings


    class AWSSecretsSettings(SecretsManagerBaseSettings):
        model_config = SettingsConfigDict(
            aws_region="us-east-1",
            aws_profile="dev"
        )

        username: str
        password: str


    settings = AWSSecretsSettings()
    ```
