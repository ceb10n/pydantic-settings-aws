import json
from typing import Any

import boto3
from mypy_boto3_secretsmanager import SecretsManagerClient
from mypy_boto3_secretsmanager.type_defs import GetSecretValueResponseTypeDef
from pydantic import ValidationError
from pydantic_settings import BaseSettings

from .logger import logger
from .models import AwsSecretsArgs, AwsSession


def create_secrets_client(settings: BaseSettings) -> SecretsManagerClient:
    """Create a boto3 client for secrets manager.

    Neither `boto3` nor `pydantic` exceptions will be handled.

    Args:
        settings (BaseSettings): Settings from `pydantic_settings`

    Returns:
        SecretsManagerClient: A secrets manager boto3 client.
    """
    logger.debug("Extracting settings prefixed with aws_")
    args = {k: v for k, v in settings.model_config.items() if k.startswith("aws_") }
    
    session_args = AwsSession(**args)
    
    session: boto3.Session = boto3.Session(
        **session_args.model_dump(by_alias=True, exclude_none=True)
    )

    return session.client("secretsmanager")


def get_secrets_content(settings: BaseSettings) -> dict[str, Any]:
    client: SecretsManagerClient | None = settings.model_config.get(
        "secrets_client",
        None
    )

    if not client:
        logger.debug("No boto3 client was informed. Creating a new one")
        client = create_secrets_client(settings)

    logger.debug("Extracting settings prefixed with secrets_, except _client and _dir")
    args = {k: v for k, v in settings.model_config.items() if k.startswith("secrets_") and k not in ("secrets_client", "secrets_dir")}

    try:
        secrets_args = AwsSecretsArgs(**args)

    except ValidationError as err:
        logger.error(f"A validation error was caugth. Please, check all required fields: {err}")
        raise err

    try:
        secret_value_response: GetSecretValueResponseTypeDef = client.get_secret_value(
            **secrets_args.model_dump(by_alias=True, exclude_none=True)
        )
    except client.exceptions.ResourceNotFoundException as resource_nf_err:
        logger.error(f"The secrets manager with name {secrets_args.secrets_name} does not exist: {resource_nf_err}")

        raise resource_nf_err

    secrets_content: str | None = None

    if "SecretString" in secret_value_response and secret_value_response.get("SecretString"):
        secrets_content = secret_value_response.get("SecretString")

    elif "SecretBinary" in secret_value_response:
        secrets_content = secret_value_response.get("SecretBinary").decode("utf-8")

    try:
        return json.loads(secrets_content)
    except json.decoder.JSONDecodeError as json_err:
        logger.error(f"The content of the secrets manager must be a valid json: {json_err}")
        raise json_err
