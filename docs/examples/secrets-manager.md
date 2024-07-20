# :fontawesome-brands-aws:{ .aws } Secrets Manager

You can use `pydantic-settings-aws` to create your settings with data located in AWS Secrets Manager.

!!! info "Secrets Manager content"
    The content of the Secrets Manager **must** be a valid JSON.

## :fontawesome-brands-aws:{ .aws } Secrets Manager options

There is only one required setting that you must especify: `secrets_name`.

### SettingsConfigDict options

| Option         | Required?                                      |
| :------------- | :--------------------------------------------- |
| `secrets_name` | :fontawesome-solid-triangle-exclamation: required    |
| `PUT`          | :material-check-all: Update resource           |
| `DELETE`       | :material-close:     Delete resource           |

## Using your boto3 client

You can use an already created `boto3 client`.

All you need to do is to add `secrets_client` to your `SettingsConfigDict`.

```py title="user_settings.py" linenums="1"
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
