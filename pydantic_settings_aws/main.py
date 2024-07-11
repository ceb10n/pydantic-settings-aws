import logging
import json
from typing import Any
from typing import Type

import boto3

from pydantic_settings_yaml import YamlBaseSettings
from pydantic.fields import FieldInfo
from pydantic_settings import BaseSettings
from pydantic_settings import SettingsConfigDict
from pydantic_settings import PydanticBaseSettingsSource
from pydantic_settings import JsonConfigSettingsSource
from mypy_boto3_secretsmanager import SecretsManagerClient
from mypy_boto3_secretsmanager.type_defs import GetSecretValueResponseTypeDef

from .models import AwsSecretsArgs
from .models import AwsSession


def get_secrets_value(client: SecretsManagerClient, settings: BaseSettings):
    client_args = {
        "SecretId": settings.model_config.get("secrets_name")
    }
    
    if "secrets_version_id" in settings.model_config:
        client_args["VersionId"] = settings.model_config.get("secrets_version_id")

    if "secrets_version_stage" in settings.model_config:
        client_args["VersionStage"] = settings.model_config.get("secrets_version_stage")

    try:
        return client.get_secret_value(**client_args)
    except:
        pass


def create_secrets_client(settings: BaseSettings) -> SecretsManagerClient:
    args = {k: v for k, v in settings.model_config.items() if k.startswith("aws_") }
    logging.info(f"args -> {args}")
    session_args = AwsSession(**args)
    
    session: boto3.Session = boto3.Session(**session_args.model_dump(by_alias=True, exclude_none=True))

    return session.client("secretsmanager")


def get_secrets_content(settings: BaseSettings) -> dict[str, Any]:
    client: SecretsManagerClient | None = settings.model_config.get(
        "secrets_client",
        None
    )

    if not client:
        client = create_secrets_client(settings)

    args = {k: v for k, v in settings.model_config.items() if k.startswith("secrets_") and k not in ("secrets_client", "secrets_dir")}
    secrets_args = AwsSecretsArgs(**args)

    secret_value_response: GetSecretValueResponseTypeDef = client.get_secret_value(
        **secrets_args.model_dump(by_alias=True, exclude_none=True)
    )

    if "SecretString" in secret_value_response and secret_value_response.get("SecretString"):
        return json.loads(secret_value_response.get("SecretString"))
    elif "SecretBinary" in secret_value_response:
        return json.loads(secret_value_response.get("SecretBinary").decode('utf-8'))


class SecretsManagerSettingsSource(PydanticBaseSettingsSource):

    def __init__(self, settings_cls: BaseSettings):
        super().__init__(settings_cls)
        self._json_content = get_secrets_content(settings_cls)

    def get_field_value(
        self, field: FieldInfo, field_name: str
    ) -> tuple[Any, str, bool]:
        field_value = self._json_content.get(field_name)
        return field_value, field_name, False

    def __call__(self) -> dict[str, Any]:
        d: dict[str, Any] = {}

        for field_name, field in self.settings_cls.model_fields.items():
            field_value, field_key, value_is_complex = self.get_field_value(
                field, field_name
            )
            field_value = self.prepare_field_value(
                field_name, field, field_value, value_is_complex
            )
            if field_value is not None:
                d[field_key] = field_value

        return d


class SecretsManagerBaseSettings(BaseSettings):

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: Type[BaseSettings],
        init_settings,
        env_settings,
        dotenv_settings,
        file_secret_settings,
    ):
        """
        Define the sources and their order for loading the settings values.

        Args:
            settings_cls: The Settings class.
            init_settings: The `InitSettingsSource` instance.
            env_settings: The `EnvSettingsSource` instance.
            dotenv_settings: The `DotEnvSettingsSource` instance.
            file_secret_settings: The `SecretsSettingsSource` instance.

        Returns:
            A tuple containing the sources and their order for
            loading the settings values.
        """
        return (
            init_settings,
            SecretsManagerSettingsSource(settings_cls),
            env_settings,
            dotenv_settings,
            file_secret_settings,
        )
