import json
import os
from typing import Annotated

from pydantic_settings_aws import (
    AWSBaseSettings,
    AWSSettingsConfigDict,
    ParameterStoreBaseSettings,
    SSM,
    Secrets,
    SecretsManagerBaseSettings,
)

from .boto3_mocks import ClientMock
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


def test_parameter_store_skips_field_already_in_current_state() -> None:
    client = ClientMock(ssm_value="from-aws")

    class S(ParameterStoreBaseSettings):
        model_config = AWSSettingsConfigDict(ssm_client=client)
        my_value: Annotated[str, SSM(name="my/parameter")] = "default"

    cfg = S(my_value="from-init")
    assert cfg.my_value == "from-init"
    assert client.get_parameter_calls == 0


def test_parameter_store_fetches_when_field_not_in_current_state() -> None:
    client = ClientMock(ssm_value="from-aws")

    class S(ParameterStoreBaseSettings):
        model_config = AWSSettingsConfigDict(ssm_client=client)
        my_value: Annotated[str, SSM(name="my/parameter")] = "default"

    cfg = S()
    assert cfg.my_value == "from-aws"
    assert client.get_parameter_calls == 1


def test_secrets_manager_skips_eager_fetch_when_all_fields_in_current_state() -> None:
    client = ClientMock(
        secret_string=json.dumps({"username": "from-aws", "password": "from-aws"})
    )

    class S(SecretsManagerBaseSettings):
        model_config = AWSSettingsConfigDict(
            secrets_name="my/secret", secrets_client=client
        )
        username: str
        password: str

    cfg = S(username="from-init", password="from-init")
    assert cfg.username == "from-init"
    assert cfg.password == "from-init"
    assert client.get_secret_value_calls == 0


def test_secrets_manager_fetches_once_when_any_field_missing() -> None:
    client = ClientMock(
        secret_string=json.dumps({"username": "from-aws", "password": "from-aws"})
    )

    class S(SecretsManagerBaseSettings):
        model_config = AWSSettingsConfigDict(
            secrets_name="my/secret", secrets_client=client
        )
        username: str
        password: str

    cfg = S(username="from-init")  # type: ignore[call-arg]
    assert cfg.username == "from-init"
    assert cfg.password == "from-aws"
    assert client.get_secret_value_calls == 1


def test_aws_source_skips_field_already_in_current_state() -> None:
    ssm_client = ClientMock(ssm_value="from-aws")
    secrets_client = ClientMock(
        secret_string=json.dumps({"username": "from-aws"})
    )

    class S(AWSBaseSettings):
        model_config = AWSSettingsConfigDict(
            ssm_client=ssm_client,
            secrets_client=secrets_client,
            secrets_name="my/secret",
        )
        username: Annotated[str, Secrets(field="username")]
        host: Annotated[str, SSM(name="my/host")]

    cfg = S(username="from-init", host="from-init")
    assert cfg.username == "from-init"
    assert cfg.host == "from-init"
    assert ssm_client.get_parameter_calls == 0
    assert secrets_client.get_secret_value_calls == 0
