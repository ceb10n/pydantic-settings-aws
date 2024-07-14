from unittest import mock

import pytest

from pydantic_settings_aws import aws

from .aws_mocks import (
    TARGET_BOTO3_CLIENT,
    TARGET_SECRET_CONTENT,
    TARGET_SECRETS_CLIENT,
    TARGET_SESSION,
    BaseSettingsMock,
    mock_create_client,
    mock_secrets_content_empty,
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


@mock.patch(TARGET_BOTO3_CLIENT, mock_secrets_content_empty)
@mock.patch(TARGET_SECRET_CONTENT, lambda *args: None)
def test_get_secrets_content_must_raise_value_error_if_secrets_content_is_none(
    *args,
):
    settings = BaseSettingsMock()
    settings.model_config = {
        "secrets_name": "secrets/name",
        "aws_region": "region",
        "aws_profile": "profile",
    }

    with pytest.raises(ValueError):
        aws.get_secrets_content(settings)
