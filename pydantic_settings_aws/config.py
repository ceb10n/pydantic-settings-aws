from typing import Any

from pydantic_settings import SettingsConfigDict


class AWSSettingsConfigDict(SettingsConfigDict, total=False):
    # boto3 session args
    aws_region: str | None
    aws_profile: str | None
    aws_access_key_id: str | None
    aws_secret_access_key: str | None
    aws_session_token: str | None

    # Secrets Manager args
    secrets_name: str
    secrets_version: str | None
    secrets_stage: str | None
    secrets_client: Any

    # SSM Parameter Store args
    ssm_client: Any
