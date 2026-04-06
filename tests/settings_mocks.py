import json
from typing import Annotated

from pydantic import BaseModel

from pydantic_settings_aws import (
    AWSBaseSettings,
    AWSSettingsConfigDict,
    ParameterStoreBaseSettings,
    SSM,
    Secrets,
    SecretsManagerBaseSettings,
)

from .boto3_mocks import ClientMock

dict_secrets_with_username_and_password = {
    "username": "myusername",
    "password": "password1234",
    "name": None,
}

secrets_with_username_and_password = json.dumps(
    dict_secrets_with_username_and_password
)

mock_secrets_with_username_and_pwd = ClientMock(
    secret_string=secrets_with_username_and_password
)


class MySecretsWithClientConfig(SecretsManagerBaseSettings):
    model_config = AWSSettingsConfigDict(
        secrets_name="my/secret",
        secrets_client=mock_secrets_with_username_and_pwd,
    )

    username: str
    password: str
    name: str | None = None


secrets_with_nested_content = json.dumps(
    {
        "username": "myusername",
        "password": "password1234",
        "nested": {"roles": ["user", "admin"]},
    }
)

mock_secrets_with_nested_content = ClientMock(
    secret_string=secrets_with_nested_content
)


class NestedContent(BaseModel):
    roles: list[str]


class SecretsWithNestedContent(SecretsManagerBaseSettings):
    model_config = AWSSettingsConfigDict(
        secrets_name="my/secret",
        secrets_client=mock_secrets_with_nested_content,
    )

    username: str
    password: str
    nested: NestedContent


class ParameterSettings(ParameterStoreBaseSettings):
    my_ssm: Annotated[
        str,
        {"ssm": "my/parameter", "ssm_client": ClientMock(ssm_value="value")},
    ]


class ParameterWithTwoSSMClientSettings(ParameterStoreBaseSettings):
    model_config = AWSSettingsConfigDict(ssm_client=ClientMock(ssm_value="value"))

    my_ssm: Annotated[
        str,
        {"ssm": "my/parameter", "ssm_client": ClientMock(ssm_value="value")},
    ]
    my_ssm_1: Annotated[
        str,
        {"ssm": "my/parameter", "ssm_client": ClientMock(ssm_value="value1")},
    ]
    my_ssm_2: Annotated[str, "my/ssm/2/parameter"]


class ParameterWithOptionalValueSettings(ParameterStoreBaseSettings):
    model_config = AWSSettingsConfigDict(ssm_client=ClientMock())

    my_ssm: Annotated[str | None, "my/ssm/2/parameter"] = None


class AWSWithParameterAndSecretsWithDefaultBoto3Client(AWSBaseSettings):
    model_config = AWSSettingsConfigDict(
        ssm_client=ClientMock(ssm_value="value"),
        secrets_client=mock_secrets_with_username_and_pwd,
        secrets_name="my/secret",
    )

    username: Annotated[str, {"service": "secrets"}]
    password: Annotated[str, {"service": "secrets"}]
    host: Annotated[str, {"service": "ssm"}]


class AWSWithParameterSecretsAndEnvironmentWithDefaultBoto3Client(AWSBaseSettings):
    model_config = AWSSettingsConfigDict(
        ssm_client=ClientMock(ssm_value="value"),
        secrets_client=mock_secrets_with_username_and_pwd,
        secrets_name="my/secret",
    )

    username: Annotated[str, {"service": "secrets"}]
    password: Annotated[str, {"service": "secrets"}]
    host: Annotated[str, {"service": "ssm"}]
    server_name: str


class AWSWithUnknownService(AWSBaseSettings):
    my_name: Annotated[str | None, {"service": "s3"}] = None


class AWSWithNonDictMetadata(AWSBaseSettings):
    my_name: Annotated[str | None, "my irrelevant metadata"] = None


# --- SSM descriptor mocks ---

class ParameterWithSSMDescriptor(ParameterStoreBaseSettings):
    my_ssm: Annotated[
        str,
        SSM(name="my/parameter", client=ClientMock(ssm_value="value")),
    ]


class ParameterWithSSMDescriptorNoName(ParameterStoreBaseSettings):
    model_config = AWSSettingsConfigDict(ssm_client=ClientMock(ssm_value="value"))

    my_ssm: Annotated[str, SSM()]


# --- Secrets descriptor mocks ---

secrets_with_db_password = json.dumps({"db_password": "supersecret"})
mock_secrets_with_db_password = ClientMock(secret_string=secrets_with_db_password)


class SecretsWithFieldDescriptor(SecretsManagerBaseSettings):
    model_config = AWSSettingsConfigDict(
        secrets_name="myapp/prod",
        secrets_client=mock_secrets_with_db_password,
    )

    password: Annotated[str, Secrets(field="db_password")]


# --- AWSBaseSettings with typed descriptors ---

class AWSWithTypedDescriptors(AWSBaseSettings):
    model_config = AWSSettingsConfigDict(
        ssm_client=ClientMock(ssm_value="value"),
        secrets_client=mock_secrets_with_username_and_pwd,
        secrets_name="my/secret",
    )

    username: Annotated[str, Secrets(field="username")]
    host: Annotated[str, SSM(name="my/host/parameter")]
