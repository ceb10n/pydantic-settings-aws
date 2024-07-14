from .settings_mocks import (
    MySecretsWithClientConfig,
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
