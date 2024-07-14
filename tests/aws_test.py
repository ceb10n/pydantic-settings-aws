from unittest import mock

from pydantic_settings_aws import aws

from .aws_mocks import (
    TARGET_SECRETS_CLIENT,
    TARGET_SESSION,
    BaseSettingsMock,
    mock_create_client,
)
from .boto3_mocks import SessionMock


@mock.patch(TARGET_SESSION, SessionMock)
def test_create_secrets_client(*args):
    settings = BaseSettingsMock()
    settings.model_config = {"aws_region": "region", "aws_profile": "profile"}
    client = aws._create_secrets_client(settings)

    assert client is not None


@mock.patch(TARGET_SECRETS_CLIENT, mock_create_client)
def test_get_boto3_client_must_create_a_client_if_its_not_given(*args):
    settings = BaseSettingsMock()
    settings.model_config = {}
    client = aws._get_boto3_client(settings)

    assert client is not None
