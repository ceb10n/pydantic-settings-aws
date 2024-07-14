import json
from typing import Any, Optional

import boto3
from mypy_boto3_secretsmanager import SecretsManagerClient
from mypy_boto3_secretsmanager.type_defs import GetSecretValueResponseTypeDef
from pydantic import ValidationError
from pydantic_settings import BaseSettings

from .logger import logger
from .models import AwsSecretsArgs, AwsSession


def get_secrets_content(settings: type[BaseSettings]) -> dict[str, Any]:
    client: SecretsManagerClient | None = _get_boto3_client(settings)
    secrets_args: AwsSecretsArgs = _get_secrets_args(settings)

    logger.debug("Getting secrets manager value with boto3 client")
    secret_response: GetSecretValueResponseTypeDef = client.get_secret_value(
        **secrets_args.model_dump(by_alias=True, exclude_none=True)
    )

    secrets_content = _get_secrets_content(secret_response)

    if not secrets_content:
        logger.warning(
            "Secrets content was not present neither in SecretString nor SecretBinary"
        )
        raise ValueError("Could not get secrets content")

    try:
        return json.loads(secrets_content)
    except json.decoder.JSONDecodeError as json_err:
        logger.error(
            f"The content of the secrets manager must be a valid json: {json_err}"
        )
        raise json_err


def _get_boto3_client(settings: type[BaseSettings]) -> SecretsManagerClient:
    logger.debug("Getting secrets manager content.")
    client: SecretsManagerClient | None = settings.model_config.get(  # type: ignore
        "secrets_client", None
    )

    if client:
        return client

    logger.debug("No boto3 client was informed. Will try to create a new one")
    return _create_secrets_client(settings)


def _create_secrets_client(
    settings: type[BaseSettings],
) -> SecretsManagerClient:
    """Create a boto3 client for secrets manager.

    Neither `boto3` nor `pydantic` exceptions will be handled.

    Args:
        settings (BaseSettings): Settings from `pydantic_settings`

    Returns:
        SecretsManagerClient: A secrets manager boto3 client.
    """
    logger.debug("Extracting settings prefixed with aws_")
    args: dict[str, Any] = {
        k: v for k, v in settings.model_config.items() if k.startswith("aws_")
    }

    session_args = AwsSession(**args)

    session: boto3.Session = boto3.Session(
        **session_args.model_dump(by_alias=True, exclude_none=True)
    )

    return session.client("secretsmanager")


def _get_secrets_args(settings: type[BaseSettings]) -> AwsSecretsArgs:
    logger.debug(
        "Extracting settings prefixed with secrets_, except _client and _dir"
    )
    args: dict[str, Any] = {
        k: v
        for k, v in settings.model_config.items()
        if k.startswith("secrets_")
        and k not in ("secrets_client", "secrets_dir")
    }

    try:
        return AwsSecretsArgs(**args)

    except ValidationError as err:
        logger.error(
            f"A validation error was caugth. Please, check all required fields: {err}"
        )
        raise err


def _get_secrets_content(secret: dict[str, Any]) -> Optional[str]:
    secrets_content: Optional[str] = None

    if "SecretString" in secret and secret.get("SecretString"):
        logger.debug("Extracting content from SecretString.")
        secrets_content = secret.get("SecretString")

    elif "SecretBinary" in secret:
        logger.debug(
            "SecretString was not present. Getting content from SecretBinary."
        )
        secret_binary: bytes | None = secret.get("SecretBinary")

        if secret_binary:
            try:
                secrets_content = secret_binary.decode("utf-8")
            except (AttributeError, ValueError) as err:
                logger.error(f"Error decoding secrets content: {err}")

                raise err

    return secrets_content
