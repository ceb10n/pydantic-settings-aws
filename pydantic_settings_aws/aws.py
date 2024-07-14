import json
from typing import Any

import boto3
from mypy_boto3_secretsmanager import SecretsManagerClient
from mypy_boto3_secretsmanager.type_defs import GetSecretValueResponseTypeDef
from pydantic import ValidationError
from pydantic_settings import BaseSettings

from .logger import logger
from .models import AwsSecretsArgs, AwsSession


def create_secrets_client(settings: type[BaseSettings]) -> SecretsManagerClient:
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


def get_secrets_content(settings: type[BaseSettings]) -> dict[str, Any]:
    logger.debug("Getting secrets manager content.")
    client: SecretsManagerClient | None = settings.model_config.get(  # type: ignore
        "secrets_client", None
    )

    if not client:
        logger.debug(
            "No boto3 client was informed. Will try to create a new one"
        )
        client = create_secrets_client(settings)

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
        secrets_args = AwsSecretsArgs(**args)

    except ValidationError as err:
        logger.error(
            f"A validation error was caugth. Please, check all required fields: {err}"
        )
        raise err

    try:
        logger.debug("Getting secrets manager value with boto3 client")
        secret_value_response: GetSecretValueResponseTypeDef = (
            client.get_secret_value(
                **secrets_args.model_dump(by_alias=True, exclude_none=True)
            )
        )
    except client.exceptions.ResourceNotFoundException as resource_nf_err:
        logger.error(
            f"The secrets manager with name {secrets_args.secrets_name} does not exist: {resource_nf_err}"
        )

        raise resource_nf_err

    secrets_content: str | None = None

    if "SecretString" in secret_value_response and secret_value_response.get(
        "SecretString"
    ):
        logger.debug("Extracting content from SecretString.")
        secrets_content = secret_value_response.get("SecretString")

    elif "SecretBinary" in secret_value_response:
        logger.debug(
            "SecretString was not present. Getting content from SecretBinary."
        )
        secret_binary: bytes | None = secret_value_response.get("SecretBinary")

        if secret_binary:
            try:
                secrets_content = secret_binary.decode("utf-8")
            except ValueError as val_err:
                logger.error(f"Error decoding secrets content: {val_err}")

                raise val_err

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
