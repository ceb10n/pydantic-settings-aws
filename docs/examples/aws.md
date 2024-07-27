# :fontawesome-brands-aws:{ .aws } Parameter Store

When working with `AWSBaseSettings`, you can work with multiple parameters living in the same account and region, or with multiple accounts / regions.

The only restriction if for Secrets Manager. You can only use one *secret / client / account / region* at a time.


## :fontawesome-solid-chart-simple: Simplest way

The only required setting is your secret's name. All other configurations you can leave to boto3 to deal.

```py linenums="1"
class ParameterStoreSettings(AWSBaseSettings):
    model_config = SettingsConfigDict(
        secrets_name="my/secret"
    )

    username: Annotated[str, {"service": "secrets"}]
    password: Annotated[str, {"service": "secrets"}]
    mongodb_host: Annotated[str, {"service": "ssm", "ssm": "/mysystem/mongodb/host"}]
    mongodb_db_name: Annotated[str, {"service": "ssm"}] # will look for a parameter named mongodb_db_name
    environment: str # not related to aws. If you have an environment named ENVIRONMENT, it will work as if you were using BaseSettings
```

In this case, `pydantic-settings-aws` will leave to boto3 to try to identify how he can connect to AWS.

!!! warning "We don't shadow pydantic and boto3 errors"
    In the above case, if for some reason any field is `None`, it will raise a pydantic's `ValidationError`.
