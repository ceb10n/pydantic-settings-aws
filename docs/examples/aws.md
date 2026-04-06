# :fontawesome-brands-aws:{ .aws } Parameter Store

When working with `AWSBaseSettings`, you can work with multiple parameters living in the same account and region, or with multiple accounts / regions.

The only restriction if for Secrets Manager. You can only use one *secret / client / account / region* at a time.


## :fontawesome-solid-chart-simple: Simplest way

The only required setting is your secret's name. All other configurations you can leave to boto3 to deal.

=== "typed descriptors"

    ```py linenums="1"
    from typing import Annotated
    from pydantic_settings_aws import AWSBaseSettings, AWSSettingsConfigDict, SSM, Secrets


    class ParameterStoreSettings(AWSBaseSettings):
        model_config = AWSSettingsConfigDict(
            secrets_name="my/secret"
        )

        username: Annotated[str, Secrets()]
        password: Annotated[str, Secrets()]
        mongodb_host: Annotated[str, SSM(name="/mysystem/mongodb/host")]
        mongodb_db_name: Annotated[str, SSM()]  # will look for a parameter named mongodb_db_name
        environment: str  # not related to aws. If you have an environment named ENVIRONMENT, it will work as if you were using BaseSettings
    ```

=== "dict (legacy)"

    ```py linenums="1"
    from typing import Annotated
    from pydantic_settings_aws import AWSBaseSettings, AWSSettingsConfigDict


    class ParameterStoreSettings(AWSBaseSettings):
        model_config = AWSSettingsConfigDict(
            secrets_name="my/secret"
        )

        username: Annotated[str, {"service": "secrets"}]
        password: Annotated[str, {"service": "secrets"}]
        mongodb_host: Annotated[str, {"service": "ssm", "ssm": "/mysystem/mongodb/host"}]
        mongodb_db_name: Annotated[str, {"service": "ssm"}]  # will look for a parameter named mongodb_db_name
        environment: str  # not related to aws. If you have an environment named ENVIRONMENT, it will work as if you were using BaseSettings
    ```

In this case, `pydantic-settings-aws` will leave to boto3 to try to identify how he can connect to AWS.

!!! info "Structured exceptions"
    `pydantic-settings-aws` wraps errors into its own exception hierarchy so you can catch them precisely:

    - `SecretNotFoundError` — the secret does not exist in Secrets Manager
    - `SecretContentError` — the secret exists but its content is empty or cannot be decoded
    - `SecretDecodeError` — the secret content is not valid JSON
    - `ParameterNotFoundError` — the parameter does not exist in Parameter Store
    - `AWSClientError` — a boto3 session or client could not be created
    - `AWSSettingsConfigError` — the settings configuration is invalid or missing required fields

    All of these inherit from `PydanticSettingsAWSError`, so you can catch them at any level.
    Unrecognised boto3 / botocore errors are re-raised as-is.
