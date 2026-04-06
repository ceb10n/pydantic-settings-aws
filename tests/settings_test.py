import os

from .settings_mocks import (
    AWSWithNonDictMetadata,
    AWSWithParameterAndSecretsWithDefaultBoto3Client,
    AWSWithParameterSecretsAndEnvironmentWithDefaultBoto3Client,
    AWSWithTypedDescriptors,
    AWSWithUnknownService,
    MySecretsWithClientConfig,
    ParameterSettings,
    ParameterWithOptionalValueSettings,
    ParameterWithSSMDescriptor,
    ParameterWithSSMDescriptorNoName,
    ParameterWithTwoSSMClientSettings,
    SecretsWithFieldDescriptor,
    SecretsWithNestedContent,
    dict_secrets_with_username_and_password,
)


def test_secrets_settings_with_basic_secrets_content() -> None:
    my_config = MySecretsWithClientConfig()  # type: ignore[call-arg]

    assert my_config is not None
    assert my_config.username == "myusername"


def test_secrets_settings_with_nested_secrets_content() -> None:
    my_config = SecretsWithNestedContent()  # type: ignore[call-arg]

    assert my_config is not None
    assert my_config.username == "myusername"
    assert my_config.nested is not None
    assert len(my_config.nested.roles) > 0


def test_ssm_with_annotated_str() -> None:
    my_config = ParameterSettings()  # type: ignore[call-arg]

    assert my_config is not None
    assert my_config.my_ssm is not None
    assert isinstance(my_config.my_ssm, str)


def test_ssm_with_and_without_ssm_client() -> None:
    my_config = ParameterWithTwoSSMClientSettings()  # type: ignore[call-arg]

    assert my_config is not None
    assert my_config.my_ssm is not None
    assert isinstance(my_config.my_ssm, str)

    assert my_config.my_ssm_2 is not None
    assert isinstance(my_config.my_ssm_2, str)


def test_ssm_with_none_in_optional_values() -> None:
    my_config = ParameterWithOptionalValueSettings()

    assert my_config is not None
    assert my_config.my_ssm is None


def test_aws_with_secrets_and_parameters() -> None:
    my_config = AWSWithParameterAndSecretsWithDefaultBoto3Client()  # type: ignore[call-arg]

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


def test_aws_settings_should_get_value_from_environment_if_not_found_in_ssm_or_secrets() -> None:
    os.environ["server_name"] = "test-server"

    my_config = AWSWithParameterSecretsAndEnvironmentWithDefaultBoto3Client()  # type: ignore[call-arg]
    assert my_config is not None
    assert my_config.username is not None
    assert my_config.password is not None
    assert my_config.host is not None
    assert my_config.server_name == "test-server"


def test_aws_settings_should_ignore_value_if_service_is_unknown() -> None:
    my_config = AWSWithUnknownService()
    assert my_config is not None
    assert my_config.my_name is None


def test_aws_settings_should_ignore_value_if_metadata_is_not_a_dict() -> None:
    my_config = AWSWithNonDictMetadata()
    assert my_config is not None
    assert my_config.my_name is None


def test_ssm_descriptor_with_name_and_client() -> None:
    my_config = ParameterWithSSMDescriptor()  # type: ignore[call-arg]
    assert my_config is not None
    assert my_config.my_ssm is not None
    assert isinstance(my_config.my_ssm, str)


def test_ssm_descriptor_with_no_name_uses_field_name() -> None:
    my_config = ParameterWithSSMDescriptorNoName()  # type: ignore[call-arg]
    assert my_config is not None
    assert my_config.my_ssm is not None
    assert isinstance(my_config.my_ssm, str)


def test_secrets_descriptor_with_field_override() -> None:
    my_config = SecretsWithFieldDescriptor()  # type: ignore[call-arg]
    assert my_config is not None
    assert my_config.password == "supersecret"


def test_aws_settings_with_typed_descriptors() -> None:
    my_config = AWSWithTypedDescriptors()  # type: ignore[call-arg]
    assert my_config is not None
    assert my_config.username == dict_secrets_with_username_and_password["username"]
    assert my_config.host is not None
