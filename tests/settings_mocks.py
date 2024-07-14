import json
from typing import Optional

from pydantic import BaseModel
from pydantic_settings import SettingsConfigDict

from pydantic_settings_aws import SecretsManagerBaseSettings

from .boto3_mocks import ClientMock

secrets_with_username_and_password = json.dumps(
    {"username": "myusername", "password": "password1234", "name": None}
)

mock_secrets_with_username_and_pwd = ClientMock(
    secret_string=secrets_with_username_and_password
)


class MySecretsWithClientConfig(SecretsManagerBaseSettings):
    model_config = SettingsConfigDict(
        secrets_name="my/secret",
        secrets_client=mock_secrets_with_username_and_pwd,
    )

    username: str
    password: str
    name: Optional[str] = None


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
    model_config = SettingsConfigDict(
        secrets_name="my/secret",
        secrets_client=mock_secrets_with_nested_content,
    )

    username: str
    password: str
    nested: NestedContent
