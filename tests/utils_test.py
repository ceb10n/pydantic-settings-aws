from pydantic_settings_aws import SSM, Secrets, utils


def test_get_annotated_ssm() -> None:
    metadata = [{"ssm": "my/ssm"}]
    a = utils.get_ssm_name_from_annotated_field(metadata)

    assert a is not None
    assert isinstance(a, dict)
    assert a["ssm"] == "my/ssm"

    metadata = ["my/ssm"]
    a = utils.get_ssm_name_from_annotated_field(metadata)

    assert a is not None
    assert a == "my/ssm"

    metadata = [str]
    a = utils.get_ssm_name_from_annotated_field(metadata)

    assert a is None


def test_get_ssm_name_from_annotated_field_with_ssm_descriptor() -> None:
    metadata = [SSM(name="/my/param")]
    a = utils.get_ssm_name_from_annotated_field(metadata)

    assert isinstance(a, SSM)
    assert a.name == "/my/param"


def test_get_ssm_name_from_annotated_field_with_ssm_descriptor_no_name() -> None:
    metadata = [SSM()]
    a = utils.get_ssm_name_from_annotated_field(metadata)

    assert isinstance(a, SSM)
    assert a.name is None


def test_get_annotated_service_metadata_with_ssm_descriptor() -> None:
    metadata = [SSM(name="/my/param")]
    service = utils.get_annotated_service_metadata(metadata)

    assert service is not None
    assert service["service"] == "ssm"


def test_get_annotated_service_metadata_with_secrets_descriptor() -> None:
    metadata = [Secrets(field="db_password")]
    service = utils.get_annotated_service_metadata(metadata)

    assert service is not None
    assert service["service"] == "secrets"


def test_get_secrets_field_name_with_field_override() -> None:
    metadata = [Secrets(field="db_password")]
    name = utils.get_secrets_field_name(metadata, "password")

    assert name == "db_password"


def test_get_secrets_field_name_falls_back_to_default() -> None:
    assert utils.get_secrets_field_name([], "password") == "password"
    assert utils.get_secrets_field_name([Secrets()], "password") == "password"
    assert utils.get_secrets_field_name([{"service": "secrets"}], "password") == "password"
