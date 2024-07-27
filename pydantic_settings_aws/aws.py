import json
from typing import Any, AnyStr, Dict, Literal, Optional, Type, Union

import boto3  # type: ignore[import-untyped]
from pydantic import ValidationError
from pydantic_settings import BaseSettings

from .logger import logger
from .models import AwsSecretsArgs, AwsSession

AWSService = Literal["ssm", "secretsmanager"]

ClientParam = Literal["secrets_client", "ssm_client"]

_client_cache: Dict[str, Any] = {}


def get_ssm_content(
    settings: Type[BaseSettings],
    field_name: str,
    ssm_info: Optional[Union[Dict[Any, AnyStr], AnyStr]] = None,
) -> Optional[str]:
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

    else:
        logger.debug("Will try to find a parameter with the parameter name")

    if not client:
        logger.debug("Boto3 client not specified in metadata")
        client = _create_client_from_settings(settings, "ssm", "ssm_client")

    logger.debug(f"Getting parameter {ssm_name} value with boto3 client")
    ssm_response: Dict[str, Any] = client.get_parameter(  # type: ignore
        Name=ssm_name, WithDecryption=True
    )

    return ssm_response.get("Parameter", {}).get("Value", None)


def get_secrets_content(settings: Type[BaseSettings]) -> Dict[str, Any]:
    client = _create_client_from_settings(
        settings, "secretsmanager", "secrets_client"
    )
    secrets_args: AwsSecretsArgs = _get_secrets_args(settings)

    logger.debug("Getting secrets manager value with boto3 client")
    secret_response = client.get_secret_value(
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


def _get_secrets_args(settings: Type[BaseSettings]) -> AwsSecretsArgs:
    logger.debug(
        "Extracting settings prefixed with secrets_, except _client and _dir"
    )
    args: Dict[str, Any] = {
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


def _get_secrets_content(
    secret: Dict[str, Any],
) -> Optional[str]:
    secrets_content: Optional[str] = None

    if "SecretString" in secret and secret.get("SecretString"):
        logger.debug("Extracting content from SecretString.")
        secrets_content = secret.get("SecretString")

    elif "SecretBinary" in secret:
        logger.debug(
            "SecretString was not present. Getting content from SecretBinary."
        )
        secret_binary: Optional[bytes] = secret.get("SecretBinary")

        if secret_binary:
            try:
                secrets_content = secret_binary.decode("utf-8")
            except (AttributeError, ValueError) as err:
                logger.error(f"Error decoding secrets content: {err}")

                raise err

    return secrets_content


def _create_client_from_settings(  # type: ignore[no-untyped-def]
    settings: Type[BaseSettings], service: AWSService, client_param: ClientParam
):
    client = settings.model_config.get(client_param)

    if client:
        logger.debug(f"Will use client from model config {client_param}")
        return client

    logger.debug("Extracting settings prefixed with aws_")
    args: Dict[str, Any] = {
        k: v for k, v in settings.model_config.items() if k.startswith("aws_")
    }

    session_args = AwsSession(**args)

    return _create_boto3_client(session_args, service)


def _create_boto3_client(session_args: AwsSession, service: AWSService):  # type: ignore[no-untyped-def]
    """Create a boto3 client for the service informed.

    Neither `boto3` nor `pydantic` exceptions will be handled.

    Args:
        session_args (AwsSession): Settings informed in `SettingsConfigDict` to create
            the boto3 session.
        service (str): The service client that will be created.

    Returns:
        boto3.client: An aws service boto3 client.
    """
    cache_key = service + "_" + session_args.session_key()

    if cache_key in _client_cache:
        return _client_cache[cache_key]

    session: boto3.Session = boto3.Session(
        **session_args.model_dump(by_alias=True, exclude_none=True)
    )

    client = session.client(service)
    _client_cache[cache_key] = client

    return client
