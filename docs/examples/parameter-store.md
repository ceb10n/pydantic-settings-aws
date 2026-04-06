# :fontawesome-brands-aws:{ .aws } Parameter Store

When working with `ParameterStoreBaseSettings`, you can work with parameters living in the same account and region, or with multiple accounts / regions.


## :fontawesome-solid-chart-simple: Simplest way

The simplest way you can work with `ParameterStoreBaseSettings` is to leaving it all to boto3 and create your fields with the same name as your parameters:

```py linenums="1"
from pydantic_settings_aws import ParameterStoreBaseSettings


class ParameterStoreSettings(ParameterStoreBaseSettings):
    # no AWSSettingsConfigDict

    mongodb_host: str
    mongodb_db_name: str
```

In this case, `pydantic-settings-aws` will leave to boto3 to try to identify how he can connect to AWS, and then will look for the parameters with name `mongodb_host` and `mongodb_db_name`.

!!! info "Structured exceptions"
    `pydantic-settings-aws` wraps errors into its own exception hierarchy so you can catch them precisely:

    - `ParameterNotFoundError` — the parameter does not exist in Parameter Store
    - `AWSClientError` — a boto3 session or client could not be created
    - `AWSSettingsConfigError` — the settings configuration is invalid or missing required fields

    All of these inherit from `PydanticSettingsAWSError`, so you can catch them at any level.
    Unrecognised boto3 / botocore errors are re-raised as-is.


## :fontawesome-solid-quote-right: Specifying the name of the parameter

For almost all cases, your parameter's name will be different from your field name.

=== "SSM descriptor"

    ```py linenums="1"
    from typing import Annotated
    from pydantic_settings_aws import AWSSettingsConfigDict, ParameterStoreBaseSettings, SSM


    class DynamoDBSettings(ParameterStoreBaseSettings):
        model_config = AWSSettingsConfigDict(
            ssm_client=my_ssm_client
        )

        db_name: Annotated[str, SSM(name="/databases/dynamodb/payments/dbname")]
    ```

=== "string (legacy)"

    ```py linenums="1"
    from typing import Annotated
    from pydantic_settings_aws import AWSSettingsConfigDict, ParameterStoreBaseSettings


    class DynamoDBSettings(ParameterStoreBaseSettings):
        model_config = AWSSettingsConfigDict(
            ssm_client=my_ssm_client
        )

        db_name: Annotated[str, "/databases/dynamodb/payments/dbname"]
    ```

## :fontawesome-solid-viruses: Multiple accounts and regions

If you need to work with multiple accounts or regions, you can use `Annotated` and specify a per-field client:

=== "SSM descriptor"

    ```py linenums="1"
    from typing import Annotated
    from pydantic_settings_aws import ParameterStoreBaseSettings, SSM


    class MongoDBSettings(ParameterStoreBaseSettings):

        prod_host: Annotated[str, SSM(name="/prod/databases/mongodb/host", client=prod_client)]
        release_host: Annotated[str, SSM(name="/release/databases/mongodb/host", client=release_client)]
        development_host: Annotated[str, SSM(name="/development/databases/mongodb/host", client=development_client)]
    ```

=== "dict (legacy)"

    ```py linenums="1"
    from typing import Annotated
    from pydantic_settings_aws import ParameterStoreBaseSettings


    class MongoDBSettings(ParameterStoreBaseSettings):

        prod_host: Annotated[str, {"ssm": "/prod/databases/mongodb/host", "ssm_client": prod_client}]
        release_host: Annotated[str, {"ssm": "/release/databases/mongodb/host", "ssm_client": release_client}]
        development_host: Annotated[str, {"ssm": "/development/databases/mongodb/host", "ssm_client": development_client}]
    ```
