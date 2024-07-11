from pydantic_settings import SettingsConfigDict
from pydantic_settings_aws.main import SecretsManagerBaseSettings

from .boto3_mocks import ClientMock

secrets_with_username_and_password = '{ "username": "myusername", "password": "password1234" }'

mock_secrets_with_username_and_pwd = ClientMock(secret_string=secrets_with_username_and_password)


class MySecretsWithClientConfig(SecretsManagerBaseSettings):
    model_config = SettingsConfigDict(
        secrets_name="my/secret",
        secrets_client=mock_secrets_with_username_and_pwd
    )

    username: str
    password: str



def test():
    my_config = MySecretsWithClientConfig()
    assert my_config is not None
    assert my_config.username == "myusername"
