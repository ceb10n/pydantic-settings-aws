from typing import Any

from pydantic_settings_aws import AWSSettingsConfigDict

from .boto3_mocks import ClientErrorMock, ClientMock

TARGET_SESSION = "pydantic_settings_aws.aws.boto3.Session"

TARGET_CREATE_CLIENT_FROM_SETTINGS = (
    "pydantic_settings_aws.aws._create_client_from_settings"
)

TARGET_SECRET_CONTENT = "pydantic_settings_aws.aws._get_secrets_content"


def mock_secrets_content_invalid_json(*args: Any) -> ClientMock:
    return ClientMock(secret_string="invalid-json")


def mock_secrets_content_empty(*args: Any) -> ClientMock:
    return ClientMock(secret_string=None)


def mock_ssm(
    region_name: str | None = None,
    profile_name: str | None = None,
    aws_access_key_id: str | None = None,
    aws_secret_access_key: str | None = None,
    aws_session_token: str | None = None,
    *args: Any,
) -> ClientMock:
    return ClientMock(ssm_value="value")


def mock_create_client(*args: Any) -> object:
    return object()


def mock_secret_not_found(*args: Any) -> ClientErrorMock:
    return ClientErrorMock("ResourceNotFoundException")


def mock_parameter_not_found(*args: Any) -> ClientErrorMock:
    return ClientErrorMock("ParameterNotFound")


class BaseSettingsMock:
    model_config: AWSSettingsConfigDict = AWSSettingsConfigDict()
