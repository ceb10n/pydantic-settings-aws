from typing import Any

from pydantic_settings import SettingsConfigDict


class AWSSettingsConfigDict(SettingsConfigDict, total=False):
    """Configuration dictionary for AWS-backed pydantic-settings sources.

    Extends :class:`pydantic_settings.SettingsConfigDict` with options specific to
    AWS Secrets Manager and AWS Systems Manager (SSM) Parameter Store sources.

    Example::

        class MySettings(SecretsManagerBaseSettings):
            model_config = AWSSettingsConfigDict(
                secrets_name="myapp/prod/db",
                aws_region="us-east-1",
            )

            db_host: str
            db_password: str
    """

    # boto3 session args
    aws_region: str | None
    """AWS region name (e.g. ``"us-east-1"``). When ``None``, boto3 falls back to the standard credential chain."""

    aws_profile: str | None
    """Named AWS CLI / boto3 profile to use. When ``None``, the default profile is used."""

    aws_access_key_id: str | None
    """Explicit AWS access key ID. Should be paired with ``aws_secret_access_key``. When ``None``, boto3 resolves credentials through the standard chain."""

    aws_secret_access_key: str | None
    """Explicit AWS secret access key. Should be paired with ``aws_access_key_id``. When ``None``, boto3 resolves credentials through the standard chain."""

    aws_session_token: str | None
    """Temporary session token, required when using short-lived STS credentials. When ``None``, boto3 resolves credentials through the standard chain."""

    # Secrets Manager args
    secrets_name: str
    """Name or full ARN of the Secrets Manager secret to retrieve. Required when using ``SecretsManagerSettingsSource``."""

    secrets_version: str | None
    """Version ID (UUID) of the secret. When ``None``, the latest version labelled ``AWSCURRENT`` is returned."""

    secrets_stage: str | None
    """Version stage label of the secret (e.g. ``"AWSCURRENT"`` or ``"AWSPREVIOUS"``). When ``None``, defaults to ``AWSCURRENT``."""

    secrets_client: Any
    """Pre-constructed ``boto3`` Secrets Manager client. Useful for injecting custom clients in tests. When not provided, a client is created automatically."""

    # SSM Parameter Store args
    ssm_client: Any
    """Pre-constructed ``boto3`` SSM client. Useful for injecting custom clients in tests. When not provided, a client is created automatically."""
