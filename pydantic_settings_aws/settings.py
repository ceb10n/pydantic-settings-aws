from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
)

from .sources import SecretsManagerSettingsSource


class SecretsManagerBaseSettings(BaseSettings):

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        return (
            init_settings,
            SecretsManagerSettingsSource(settings_cls),
            env_settings,
            dotenv_settings,
            file_secret_settings,
        )
