# :fontawesome-brands-aws:{ .aws } Secrets Manager

You can use `pydantic-settings-aws` to create your settings with data located in AWS Secrets Manager.

!!! info "Secrets Manager content"
    The content of the Secrets Manager **must** be a valid JSON.

## :fontawesome-solid-screwdriver-wrench: SettingsConfigDict options

There is only one required setting that you must especify: `secrets_name`.

### :fontawesome-solid-toolbox: Settings for boto3 client usage

| Option                  | Required?                                         | Description                                                                   |
| :---------------------- | :------------------------------------------------ | :---------------------------------------------------------------------------- |
| `secrets_client`        | :fontawesome-solid-xmark: optional                | An existing boto3 client for Secrets Manager if you already have one          |
| `aws_region`            | :fontawesome-solid-xmark: optional                | The region your Secrets Manager lives. Used only if you don't inform a client |
| `aws_profile`           | :fontawesome-solid-xmark: optional                | An existing aws configured profile. Used only if you don't inform a client    |
| `aws_access_key_id`     | :fontawesome-solid-xmark: optional                | A valid Access Key Id. Used only if you don't inform a client                 |
| `aws_secret_access_key` | :fontawesome-solid-xmark: optional                | A valid Secret Access Key Id. Used only if you don't inform a client          |
| `aws_session_token`     | :fontawesome-solid-xmark: optional                | A valid Session Token. Used only if you don't inform a client                 |

### :fontawesome-solid-user-secret: Settings for Secrets Manager

| Option            | Required?                                         | Description                      |
| :---------------- | :------------------------------------------------ | :------------------------------- |
| `secrets_name`    | :fontawesome-solid-triangle-exclamation: required | The name of your Secrets Manager |
| `secrets_version` | :fontawesome-solid-xmark: optional                | The version of your secret       |
| `secrets_stage`   | :fontawesome-solid-xmark: optional                | The stage of your secret         |
