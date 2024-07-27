# :fontawesome-brands-aws:{ .aws } AWSBaseSettings

You can use `pydantic-settings-aws` to create your settings with data located both in [Parameter Store](https://docs.aws.amazon.com/systems-manager/latest/userguide/systems-manager-parameter-store.html) and [Secrets Manager](https://aws.amazon.com/secrets-manager/).

## :fontawesome-solid-screwdriver-wrench: SettingsConfigDict options

You need to inform at least the Secrets Manager name, if you are using it as a data source.

!!! tip "Parameter Store Settings"
    If you are not using secrets manager as a data source, check [ParameterStoreBaseSettings](parameter-store.md).

### :fontawesome-solid-toolbox: Settings for boto3 client usage

| Option                  | Required?                          | Description                                                                   |
| :---------------------- | :--------------------------------- | :---------------------------------------------------------------------------- |
| `ssm_client`            | :fontawesome-solid-xmark: optional | An existing boto3 client for Parameter Store if you already have one          |
| `secrets_client`        | :fontawesome-solid-xmark: optional | An existing boto3 client for Secrets Manager if you already have one          |
| `aws_region`            | :fontawesome-solid-xmark: optional | The region your Parameter Store lives. Used only if you don't inform a client |
| `aws_profile`           | :fontawesome-solid-xmark: optional | An existing aws configured profile. Used only if you don't inform a client    |
| `aws_access_key_id`     | :fontawesome-solid-xmark: optional | A valid Access Key Id. Used only if you don't inform a client                 |
| `aws_secret_access_key` | :fontawesome-solid-xmark: optional | A valid Secret Access Key Id. Used only if you don't inform a client          |
| `aws_session_token`     | :fontawesome-solid-xmark: optional | A valid Session Token. Used only if you don't inform a client                 |

## :fontawesome-solid-tags: Define which service you field is using with Annotated

When you are using `AWSBaseSettings` you need to add at least a `dict` with the AWS service you are using.

```py linenums="1"
class MongoDBSettings(AWSBaseSettings):
    model_config = SettingsConfigDict(
        secrets_client=my_secrets_client,
        secrets_name="myservice/mongodb",
        ssm_client=my_ssm_client
    )

    username: Annotated[str, {"service": "secrets"}]
    password: Annotated[str, {"service": "secrets"}]
    server_host: Annotated[str, {"service": "ssm", "ssm": "/databases/mongodb/host"}]
    server_port: Annotated[str, {"service": "ssm", "ssm": "/databases/mongodb/port"}]
```

### :fontawesome-solid-list: Single Secrets, multiple parameter store

At the moment you can only have one Secrets Manager source, but multiple parameter store.

```py linenums="1"
class MongoDBSettings(AWSBaseSettings):
    model_config = SettingsConfigDict(
        secrets_client=my_secrets_client,
        secrets_name="myservice/mongodb"
    )

    username: Annotated[str, {"service": "secrets"}] # will use SettingsConfigDict
    password: Annotated[str, {"service": "secrets"}] # will use SettingsConfigDict
    host: Annotated[str, {"ssm": "/dev/virginia/databases/mongodb/host", "ssm_client": dev_virginia_client}] # will use dev_virginia_client
    port: Annotated[str, {"ssm": "/dev/saopaulo/databases/mongodb/host", "ssm_client": dev_saopaulo_client}] # will use dev_saopaulo_client
```

## :fontawesome-solid-quote-right: Settings Order

First, `AWSBaseSettings` will try to load your data from either Parameter Store or Secrets Manager.

If it can't find a value, `AWSBaseSettings` will still try to get your information from Environment, dotenv files and secret files.

* AWS SSM and Secrets Manager
* Environment variables
* dotenv files
* secret files
