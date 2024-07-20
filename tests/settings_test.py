from .settings_mocks import (
    MySecretsWithClientConfig,
    ParameterSettings,
    ParameterWithOptionalValueSettings,
    ParameterWithTwoSSMClientSettings,
    SecretsWithNestedContent,
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
