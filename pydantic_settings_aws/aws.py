import json
import threading
from typing import Any, Literal

import boto3  # type: ignore[import-untyped]
from botocore.exceptions import ClientError  # type: ignore[import-untyped]
from pydantic import ValidationError
from pydantic_settings import BaseSettings

from .errors import (
    AWSClientError,
    AWSSettingsConfigError,
    ParameterNotFoundError,
    SecretContentError,
    SecretDecodeError,
    SecretNotFoundError,
)
from .fields import SSM
from .logger import logger
from .models import AwsSecretsArgs, AwsSession

AWSService = Literal["ssm", "secretsmanager"]

ClientParam = Literal["secrets_client", "ssm_client"]

_client_cache: dict[str, Any] = {}
_client_cache_lock = threading.Lock()


def get_ssm_content(
    settings: type[BaseSettings],
    field_name: str,
    ssm_info: dict[str, Any] | str | SSM | None = None,
) -> str | None:
    client = None
    ssm_name = field_name

    if isinstance(ssm_info, str):
        logger.debug("Parameter name specified as a str")
        ssm_name = ssm_info

    elif isinstance(ssm_info, dict):
        logger.debug("Parameter specified as a dict")
        ssm_name = str(ssm_info["ssm"])

        logger.debug("Checking for a especific boto3 client for the Parameter")
        client = ssm_info.get("ssm_client", None)

    elif isinstance(ssm_info, SSM):
        logger.debug("Parameter specified as an SSM descriptor")
        if ssm_info.name:
            ssm_name = ssm_info.name
        client = ssm_info.client

    else:
        logger.debug("Will try to find a parameter with the parameter name")

    if not client:
        logger.debug("Boto3 client not specified in metadata")
        client = _create_client_from_settings(settings, "ssm", "ssm_client")

    logger.debug(f"Getting parameter {ssm_name} value with boto3 client")
    try:
        ssm_response: dict[str, Any] = client.get_parameter(
            Name=ssm_name, WithDecryption=True
        )
    except ClientError as e:
        if e.response["Error"]["Code"] == "ParameterNotFound":
            raise ParameterNotFoundError(
                f"Parameter '{ssm_name}' not found in SSM Parameter Store"
            ) from e
        raise

    return ssm_response.get("Parameter", {}).get("Value", None)


def get_secrets_content(settings: type[BaseSettings]) -> dict[str, Any]:
    client = _create_client_from_settings(
        settings, "secretsmanager", "secrets_client"
    )
    secrets_args: AwsSecretsArgs = _get_secrets_args(settings)

    logger.debug("Getting secrets manager value with boto3 client")
    try:
        secret_response = client.get_secret_value(
            **secrets_args.model_dump(by_alias=True, exclude_none=True)
        )
    except ClientError as e:
        if e.response["Error"]["Code"] == "ResourceNotFoundException":
            raise SecretNotFoundError(
                f"Secret '{secrets_args.secrets_name}' not found in Secrets Manager"
            ) from e
        raise

    secrets_content = _get_secrets_content(secret_response)

    if not secrets_content:
        logger.warning(
            "Secrets content was not present neither in SecretString nor SecretBinary"
        )
        raise SecretContentError(
            f"Secret '{secrets_args.secrets_name}' exists but its content is empty"
        )

    try:
        return json.loads(secrets_content)
    except json.decoder.JSONDecodeError as json_err:
        logger.error(
            f"The content of the secrets manager must be a valid json: {json_err}"
        )
        raise SecretDecodeError(
            f"Secret '{secrets_args.secrets_name}' content is not valid JSON"
        ) from json_err


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
            f"A validation error was caught. Please check all required fields: {err}"
        )
        raise AWSSettingsConfigError(
            f"Invalid or missing Secrets Manager configuration: {err}"
        ) from err


def _get_secrets_content(
    secret: dict[str, Any],
) -> str | None:
    secrets_content: str | None = None

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
                raise SecretContentError(
                    "Failed to decode SecretBinary content as UTF-8"
                ) from err

    return secrets_content


def _create_client_from_settings(  # type: ignore[no-untyped-def]
    settings: type[BaseSettings], service: AWSService, client_param: ClientParam
):
    client = settings.model_config.get(client_param)

    if client:
        logger.debug(f"Will use client from model config {client_param}")
        return client

    logger.debug("Extracting settings prefixed with aws_")
    args: dict[str, Any] = {
        k: v for k, v in settings.model_config.items() if k.startswith("aws_")
    }

    session_args = AwsSession(**args)

    return _create_boto3_client(session_args, service)


def _create_boto3_client(session_args: AwsSession, service: AWSService):  # type: ignore[no-untyped-def]
    """Create a boto3 client for the service informed.

    Args:
        session_args (AwsSession): Settings informed in `SettingsConfigDict` to create
            the boto3 session.
        service (str): The service client that will be created.

    Returns:
        boto3.client: An aws service boto3 client.

    Raises:
        AWSClientError: If the boto3 session or client cannot be created.
    """
    cache_key = service + "_" + session_args.session_key()

    with _client_cache_lock:
        if cache_key in _client_cache:
            return _client_cache[cache_key]

        try:
            session: boto3.Session = boto3.Session(
                **session_args.model_dump(by_alias=True, exclude_none=True)
            )
            client = session.client(service)
        except Exception as e:
            raise AWSClientError(
                f"Failed to create boto3 client for '{service}': {e}"
            ) from e

        _client_cache[cache_key] = client

    return client
