# :fontawesome-brands-aws:{ .aws } Secrets Manager

For more information about all the options and settings, refer to [Configuring Secrets Manager](../configuration/secrets-manager.md)

## :fontawesome-solid-toolbox: Using your boto3 client

You can use an already created `boto3 client`.

All you need to do is to add `secrets_client` to your `SettingsConfigDict`.

```py linenums="1"
import boto3
from pydantic_settings_aws import SecretsManagerBaseSettings

client = boto3.client("secretsmanager")


class AWSSecretsSettings(SecretsManagerBaseSettings):
    model_config = SettingsConfigDict(
        secrets_name="my/secret",
        secrets_client=client
    )

    username: str
    password: str
```

And now, **if** your secrets has the format:

```json
{
    "username": "my-awesome-user-name",
    "password": "really-strong-password"
}
```

You can just create your settings, and everything will be allright:

```python
settings = AWSSecretsSettings()
```

## :fontawesome-solid-toolbox: Getting specific version and stage of the secret

```py linenums="1"
from pydantic_settings_aws import SecretsManagerBaseSettings

class AWSSecretsSettings(SecretsManagerBaseSettings):
    model_config = SettingsConfigDict(
        secrets_name="my/secret",
        secrets_version="2",
        secrets_stage="AWSCURRENT"
    )

    username: str
    password: str
```

## :fontawesome-solid-id-card: With AWS profile name

```py linenums="1"
from pydantic_settings_aws import SecretsManagerBaseSettings

class AWSSecretsSettings(SecretsManagerBaseSettings):
    model_config = SettingsConfigDict(
        secrets_name="my/secret",
        aws_profile="DEV",
        aws_region="sa-east-1"
    )

    username: str
    password: str
```

## :fontawesome-solid-gears: With access key

```py linenums="1"
from pydantic_settings_aws import SecretsManagerBaseSettings

class AWSSecretsSettings(SecretsManagerBaseSettings):
    model_config = SettingsConfigDict(
        secrets_name="my/secret",
        aws_region="us-east-1",
        aws_access_key_id="my_aws_access_key_id",
        aws_secret_access_key="my_aws_secret_access_key",
        aws_session_token="my_aws_session_token"
    )

    username: str
    password: str
```


## :fontawesome-solid-gears: With IAM Identity Center (SSO)

Just login with sso:

```shell
aws sso login --profile DEV
```

And then you can leave all empty:

```py linenums="1"
from pydantic_settings_aws import SecretsManagerBaseSettings

class AWSSecretsSettings(SecretsManagerBaseSettings):
    model_config = SettingsConfigDict(
        secrets_name="my/secret"
    )

    username: str
    password: str
```
