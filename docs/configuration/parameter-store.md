# :fontawesome-brands-aws:{ .aws } Parameter Store

You can use `pydantic-settings-aws` to create your settings with data located in [Systems Manager: Parameter Store](https://docs.aws.amazon.com/systems-manager/latest/userguide/systems-manager-parameter-store.html).

!!! info "Parameter Store content"
    The content of the the parameter store **must** be a `string`.

## :fontawesome-solid-screwdriver-wrench: SettingsConfigDict options

There is no required setting that you must especify.

### :fontawesome-solid-toolbox: Settings for boto3 client usage

| Option                  | Required?                          | Description                                                                   |
| :---------------------- | :--------------------------------- | :---------------------------------------------------------------------------- |
| `ssm_client`            | :fontawesome-solid-xmark: optional | An existing boto3 client for Parameter Store if you already have one          |
| `aws_region`            | :fontawesome-solid-xmark: optional | The region your Parameter Store lives. Used only if you don't inform a client |
| `aws_profile`           | :fontawesome-solid-xmark: optional | An existing aws configured profile. Used only if you don't inform a client    |
| `aws_access_key_id`     | :fontawesome-solid-xmark: optional | A valid Access Key Id. Used only if you don't inform a client                 |
| `aws_secret_access_key` | :fontawesome-solid-xmark: optional | A valid Secret Access Key Id. Used only if you don't inform a client          |
| `aws_session_token`     | :fontawesome-solid-xmark: optional | A valid Session Token. Used only if you don't inform a client                 |

## :fontawesome-solid-tags: Configure your Parameter Store with Annotated

You can declare your settings without any annotated field. In case you this, `pydantic-settings-aws` will look for a parater store with the same name as your field.

### :fontawesome-solid-quote-right: Specify the name of the parameter

In case all your parameters are in the same AWS account and region, you can just annotate you field with a string:

```py linenums="1"
class MongoDBSettings(ParameterStoreBaseSettings):
    model_config = SettingsConfigDict(
        ssm_client=my_ssm_client
    )

    server_host: Annotated[str, "/databases/mongodb/host"]
```

### :fontawesome-regular-comments: Multiple regions and accounts

If you need to work with multiple accounts and/or regions, you can create a client for each account:

```py linenums="1"
class MongoDBSettings(ParameterStoreBaseSettings):

    prod_host: Annotated[str, {"ssm": "/prod/databases/mongodb/host", "ssm_client": prod_client}]
    release_host: Annotated[str, {"ssm": "/release/databases/mongodb/host", "ssm_client": release_client}]
    development_host: Annotated[str, {"ssm": "/development/databases/mongodb/host", "ssm_client": development_client}]
```
