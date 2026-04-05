from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
)

from .sources import (
    AWSSettingsSource,
    ParameterStoreSettingsSource,
    SecretsManagerSettingsSource,
)


class AWSBaseSettings(BaseSettings):
    """Base settings class that loads values from both AWS Secrets Manager and SSM Parameter Store.

    Fields are routed to the appropriate AWS source via ``Annotated`` metadata:
    use ``{"service": "secrets"}`` for Secrets Manager and ``{"service": "ssm"}``
    for Parameter Store. Fields without AWS metadata fall through to the standard
    pydantic-settings sources (environment variables, dotenv, etc.).

    Source priority order: init > AWS > env > dotenv > file secrets.
    """

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
            AWSSettingsSource(settings_cls),
            env_settings,
            dotenv_settings,
            file_secret_settings,
        )


class ParameterStoreBaseSettings(BaseSettings):
    """Base settings class that loads values from AWS SSM Parameter Store.

    By default each field name is used as the parameter name. Use ``Annotated``
    to override the parameter name with a string or a dict (the latter also
    allows supplying a per-field ``ssm_client``).

    Fields whose parameter is not found in Parameter Store are silently skipped
    and resolved by the remaining pydantic-settings sources (environment
    variables, dotenv, etc.).

    Source priority order: init > Parameter Store > env > dotenv > file secrets.
    """

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
            ParameterStoreSettingsSource(settings_cls),
            env_settings,
            dotenv_settings,
            file_secret_settings,
        )


class SecretsManagerBaseSettings(BaseSettings):
    """Base settings class that loads values from a single AWS Secrets Manager secret.

    The secret must contain a JSON object whose keys map to the model's field
    names. The secret is fetched once at instantiation time and cached for the
    lifetime of the source.

    Requires ``secrets_name`` to be set in :class:`AWSSettingsConfigDict`.

    Source priority order: init > Secrets Manager > env > dotenv > file secrets.
    """

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
