from typing import TypedDict

from .boto3_mocks import ClientMock

TARGET_SESSION = "pydantic_settings_aws.aws.boto3.Session"

TARGET_SECRETS_BOTO3_CLIENT = "pydantic_settings_aws.aws._get_secrets_boto3_client"

TARGET_SSM_BOTO3_CLIENT = "pydantic_settings_aws.aws._get_ssm_boto3_client"

TARGET_SECRETS_CLIENT = "pydantic_settings_aws.aws._create_secrets_client"

TARGET_SSM_CLIENT = "pydantic_settings_aws.aws._create_ssm_client"

TARGET_SECRET_CONTENT = "pydantic_settings_aws.aws._get_secrets_content"


def mock_secrets_content_invalid_json(*args):
    return ClientMock(secret_string="invalid-json")


def mock_secrets_content_empty(*args):
    return ClientMock(secret_string=None)


def mock_ssm(*args):
    return ClientMock(ssm_value="value")


def mock_create_client(*args):
    return object()


class BaseSettingsMock:
    model_config = TypedDict("SettingsConfigDict")  # noqa: UP013
