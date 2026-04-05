import json
from unittest import mock

import pytest

from pydantic_settings_aws import aws
from pydantic_settings_aws.errors import (
    AWSClientError,
    AWSSettingsConfigError,
    ParameterNotFoundError,
    SecretContentError,
    SecretDecodeError,
    SecretNotFoundError,
)

from .aws_mocks import (
    TARGET_CREATE_CLIENT_FROM_SETTINGS,
    TARGET_SECRET_CONTENT,
    TARGET_SESSION,
    BaseSettingsMock,
    mock_create_client,
    mock_parameter_not_found,
    mock_secret_not_found,
    mock_secrets_content_empty,
    mock_secrets_content_invalid_json,
    mock_ssm,
)
from .boto3_mocks import BrokenSessionMock, SessionMock


@mock.patch(TARGET_CREATE_CLIENT_FROM_SETTINGS, mock_ssm)
def test_get_ssm_content_must_return_parameter_content_if_annotated_with_parameter_name(*args: object) -> None:
    aws._client_cache = {}
    settings = BaseSettingsMock()
    settings.model_config = {"aws_region": "region", "aws_profile": "profile"}
    parameter_value = aws.get_ssm_content(settings, "field", "my/parameter/name")  # type: ignore[arg-type]

    assert parameter_value is not None
    assert isinstance(parameter_value, str)


@mock.patch(TARGET_CREATE_CLIENT_FROM_SETTINGS, mock_ssm)
def test_get_ssm_content_must_return_parameter_content_if_annotated_with_dict_args(*args: object) -> None:
    aws._client_cache = {}
    settings = BaseSettingsMock()
    settings.model_config = {"aws_region": "region", "aws_profile": "profile"}
    parameter_value = aws.get_ssm_content(settings, "field", {"ssm": "my/parameter/name"})  # type: ignore[arg-type]

    assert parameter_value is not None
    assert isinstance(parameter_value, str)


@mock.patch(TARGET_CREATE_CLIENT_FROM_SETTINGS, mock_ssm)
def test_get_ssm_content_must_use_client_if_present_in_metadata(*args: object) -> None:
    aws._client_cache = {}
    settings = BaseSettingsMock()
    settings.model_config = {"aws_region": "region", "aws_profile": "profile"}
    ssm_info: dict[str, object] = {"ssm": "my/parameter/name", "ssm_client": mock_ssm()}
    parameter_value = aws.get_ssm_content(settings, "field", ssm_info)  # type: ignore[arg-type]

    assert parameter_value is not None
    assert isinstance(parameter_value, str)


@mock.patch(TARGET_CREATE_CLIENT_FROM_SETTINGS, mock_ssm)
def test_get_ssm_content_must_use_field_name_if_ssm_name_not_in_metadata(*args: object) -> None:
    aws._client_cache = {}
    settings = BaseSettingsMock()
    settings.model_config = {"aws_region": "region", "aws_profile": "profile"}
    parameter_value = aws.get_ssm_content(settings, "field", None)  # type: ignore[arg-type]

    assert parameter_value is not None
    assert isinstance(parameter_value, str)


@mock.patch(TARGET_SESSION, SessionMock)
def test_create_ssm_client(*args: object) -> None:
    aws._client_cache = {}
    settings = BaseSettingsMock()
    settings.model_config = {"aws_region": "region", "aws_profile": "profile"}
    client = aws._create_client_from_settings(settings, "ssm", "ssm_client")  # type: ignore[arg-type]

    assert client is not None


@mock.patch(TARGET_CREATE_CLIENT_FROM_SETTINGS, mock_create_client)
def test_get_ssm_boto3_client_must_create_a_client_if_its_not_given(*args: object) -> None:
    aws._client_cache = {}
    settings = BaseSettingsMock()
    settings.model_config = {}
    client = aws._create_client_from_settings(settings, "ssm", "ssm_client")  # type: ignore[arg-type]

    assert client is not None


@mock.patch(TARGET_SESSION, SessionMock)
def test_create_secrets_client(*args: object) -> None:
    aws._client_cache = {}
    settings = BaseSettingsMock()
    settings.model_config = {"aws_region": "region", "aws_profile": "profile"}
    client = aws._create_client_from_settings(settings, "secretsmanager", "secrets_client")  # type: ignore[arg-type]

    assert client is not None


@mock.patch(TARGET_CREATE_CLIENT_FROM_SETTINGS, mock_create_client)
def test_get_secrets_boto3_client_must_create_a_client_if_its_not_given(*args: object) -> None:
    aws._client_cache = {}
    settings = BaseSettingsMock()
    settings.model_config = {}
    client = aws._create_client_from_settings(settings, "secretsmanager", "secrets_client")  # type: ignore[arg-type]

    assert client is not None


@mock.patch(TARGET_SECRET_CONTENT, lambda *args: None)
@mock.patch(TARGET_CREATE_CLIENT_FROM_SETTINGS, mock_secrets_content_empty)
def test_get_secrets_content_must_raise_value_error_if_secrets_content_is_none(
    *args: object,
) -> None:
    aws._client_cache = {}
    settings = BaseSettingsMock()
    settings.model_config = {
        "secrets_name": "secrets/name",
        "aws_region": "region",
        "aws_profile": "profile",
    }

    with pytest.raises(SecretContentError):
        aws.get_secrets_content(settings)  # type: ignore[arg-type]


@mock.patch(TARGET_CREATE_CLIENT_FROM_SETTINGS, mock_secrets_content_invalid_json)
def test_should_not_obfuscate_json_error_in_case_of_invalid_secrets(*args: object) -> None:
    aws._client_cache = {}
    settings = BaseSettingsMock()
    settings.model_config = {
        "secrets_name": "secrets/name",
        "aws_region": "region",
        "aws_profile": "profile",
    }

    with pytest.raises(SecretDecodeError):
        aws.get_secrets_content(settings)  # type: ignore[arg-type]


def test_get_secrets_content_must_get_binary_content_if_string_is_not_set(*args: object) -> None:
    aws._client_cache = {}
    content = {
        "SecretBinary": json.dumps({"username": "admin"}).encode("utf-8")
    }
    secret_content = aws._get_secrets_content(content)

    assert isinstance(secret_content, str)


def test_get_secrets_content_must_not_hide_decode_error_if_not_binary_in_secret_binary(*args: object) -> None:
    aws._client_cache = {}
    content = {
        "SecretBinary": json.dumps({"username": "admin"})
    }

    with pytest.raises(SecretContentError):
        aws._get_secrets_content(content)


def test_get_secrets_content_must_return_none_if_neither_string_nor_binary_are_present(*args: object) -> None:
    aws._client_cache = {}
    secret_content = aws._get_secrets_content({})

    assert secret_content is None


def test_get_secrets_content_must_return_none_if_binary_is_present_but_none(*args: object) -> None:
    aws._client_cache = {}
    content = {
        "SecretBinary": None
    }
    secret_content = aws._get_secrets_content(content)

    assert secret_content is None


def test_get_secrets_args_must_not_shadow_pydantic_validation_if_required_args_are_not_present(*args: object) -> None:
    aws._client_cache = {}
    settings = BaseSettingsMock()
    settings.model_config = {}

    with pytest.raises(AWSSettingsConfigError):
        aws._get_secrets_args(settings)  # type: ignore[arg-type]


@mock.patch(TARGET_CREATE_CLIENT_FROM_SETTINGS, mock_secret_not_found)
def test_get_secrets_content_must_raise_secret_not_found_error(*args: object) -> None:
    aws._client_cache = {}
    settings = BaseSettingsMock()
    settings.model_config = {
        "secrets_name": "secrets/name",
        "aws_region": "region",
    }

    with pytest.raises(SecretNotFoundError):
        aws.get_secrets_content(settings)  # type: ignore[arg-type]


@mock.patch(TARGET_CREATE_CLIENT_FROM_SETTINGS, mock_parameter_not_found)
def test_get_ssm_content_must_raise_parameter_not_found_error(*args: object) -> None:
    aws._client_cache = {}
    settings = BaseSettingsMock()
    settings.model_config = {"aws_region": "region"}

    with pytest.raises(ParameterNotFoundError):
        aws.get_ssm_content(settings, "field", "my/parameter/name")  # type: ignore[arg-type]


@mock.patch(TARGET_SESSION, BrokenSessionMock)
def test_create_boto3_client_must_raise_aws_client_error_on_failure(*args: object) -> None:
    aws._client_cache = {}
    settings = BaseSettingsMock()
    settings.model_config = {"aws_region": "region"}

    with pytest.raises(AWSClientError):
        aws._create_client_from_settings(settings, "ssm", "ssm_client")  # type: ignore[arg-type]


@mock.patch(TARGET_SESSION, mock_ssm)
def test_must_cache_boto3_clients_for_the_same_service_region_and_account(*args: object) -> None:
    aws._client_cache = {}

    settings = BaseSettingsMock()
    settings.model_config = {"aws_region": "region", "aws_profile": "profile"}
    aws._create_client_from_settings(settings, "secretsmanager", "secrets_client")  # type: ignore[arg-type]
    aws._create_client_from_settings(settings, "secretsmanager", "secrets_client")  # type: ignore[arg-type]
    aws._create_client_from_settings(settings, "ssm", "ssm_client")  # type: ignore[arg-type]

    assert len(aws._client_cache) == 2
