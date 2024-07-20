# :fontawesome-brands-aws:{ .aws } Parameter Store

When working with `ParameterStoreBaseSettings`, you can work with parameters living in the same account and region, or with multiple accounts / regions.


## :fontawesome-solid-chart-simple: Simplest way

The simplest way you can work with `ParameterStoreBaseSettings` is to leaving it all to boto3 and create your fields with the same name as your parameters:

```py linenums="1"
class ParameterStoreSettings(ParameterStoreBaseSettings):
    # no SettingsConfigDict

    mongodb_host: str
    mongodb_db_name: str
```

In this case, `pydantic-settings-aws` will leave to boto3 to try to identify how he can connect to AWS, and then will look for the parameters with name `mongodb_host` and `mongodb_db_name`.

!!! warning "We don't shadow pydantic and boto3 errors"
    In the above case, if for some reason mongodb_host is `None`, it will raise a pydantic's `ValidationError`.


## :fontawesome-solid-quote-right: Specifying the name of the parameter

For almost all cases, your parameter's name will be different from your field name.

To deal with these cases, you must use `Annotated` and add the name of your parameter:

```py linenums="1"
class DynamoDBSettings(ParameterStoreBaseSettings):
    model_config = SettingsConfigDict(
        ssm_client=my_ssm_client
    )

    db_name: Annotated[str, "/databases/dynamodb/payments/dbname"]
```

## :fontawesome-solid-viruses: Multiple accounts and regions

If you need to work with multiple accounts or regions, you can use `Annotated` and specify a `dict`:

```py
{
    "ssm": "parameter name",
    "ssm_client": my_boto3_client
}
```

```py linenums="1"
class MongoDBSettings(ParameterStoreBaseSettings):

    prod_host: Annotated[str, {"ssm": "/prod/databases/mongodb/host", "ssm_client": prod_client}]
    release_host: Annotated[str, {"ssm": "/release/databases/mongodb/host", "ssm_client": release_client}]
    development_host: Annotated[str, {"ssm": "/development/databases/mongodb/host", "ssm_client": development_client}]
```
