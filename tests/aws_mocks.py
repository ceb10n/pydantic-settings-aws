from typing import TypedDict

TARGET_SESSION = "pydantic_settings_aws.aws.boto3.Session"

TARGET_SECRETS_CLIENT = "pydantic_settings_aws.aws._create_secrets_client"


def mock_create_client(*args):
    return object()


class BaseSettingsMock:
    model_config = TypedDict("SettingsConfigDict")  # noqa: UP013
