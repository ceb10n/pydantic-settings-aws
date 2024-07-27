import os

from .settings_mocks import (
    AWSWithNonDictMetadata,
    AWSWithParameterAndSecretsWithDefaultBoto3Client,
    AWSWithParameterSecretsAndEnvironmentWithDefaultBoto3Client,
    AWSWithUnknownService,
    MySecretsWithClientConfig,
    ParameterSettings,
    ParameterWithOptionalValueSettings,
    ParameterWithTwoSSMClientSettings,
    SecretsWithNestedContent,
    dict_secrets_with_username_and_password,
)


def test_secrets_settings_with_basic_secrets_content():
    my_config = MySecretsWithClientConfig()

    assert my_config is not None
    assert my_config.username == "myusername"


def test_secrets_settings_with_nested_secrets_content():
    my_config = SecretsWithNestedContent()

    assert my_config is not None
    assert my_config.username == "myusername"
    assert my_config.nested is not None
    assert len(my_config.nested.roles) > 0


def test_ssm_with_annotated_str():
    my_config = ParameterSettings()

    assert my_config is not None
    assert my_config.my_ssm is not None
    assert isinstance(my_config.my_ssm, str)


def test_ssm_with_and_without_ssm_client():
    my_config = ParameterWithTwoSSMClientSettings()

    assert my_config is not None
    assert my_config.my_ssm is not None
    assert isinstance(my_config.my_ssm, str)

    assert my_config.my_ssm_2 is not None
    assert isinstance(my_config.my_ssm_2, str)


def test_ssm_with_none_in_optional_values():
    my_config = ParameterWithOptionalValueSettings()

    assert my_config is not None
    assert my_config.my_ssm is None


def test_aws_with_secrets_and_parameters():
    my_config = AWSWithParameterAndSecretsWithDefaultBoto3Client()

    assert my_config is not None
    assert (
        my_config.username
        == dict_secrets_with_username_and_password["username"]
    )
    assert (
        my_config.password
        == dict_secrets_with_username_and_password["password"]
    )
    assert my_config.host is not None


def test_aws_settings_should_get_value_from_environment_if_not_found_in_ssm_or_secrets():
    os.environ["server_name"] = "test-server"

    my_config = AWSWithParameterSecretsAndEnvironmentWithDefaultBoto3Client()
    assert my_config is not None
    assert my_config.username is not None
    assert my_config.password is not None
    assert my_config.host is not None
    assert my_config.server_name == "test-server"


def test_aws_settings_should_ignore_value_if_service_is_unknown():
    my_config = AWSWithUnknownService()
    assert my_config is not None
    assert my_config.my_name is None


def test_aws_settings_should_ignore_value_if_metadata_is_not_a_dict():
    my_config = AWSWithNonDictMetadata()
    assert my_config is not None
    assert my_config.my_name is None
