from pydantic_settings_aws import utils


def test_get_annotated_ssm(*args):
    metadata = [{"ssm": "my/ssm"}]
    a = utils.get_ssm_name_from_annotated_field(metadata)

    assert a is not None
    assert a["ssm"] == "my/ssm"

    metadata = ["my/ssm"]
    a = utils.get_ssm_name_from_annotated_field(metadata)

    assert a is not None
    assert a == "my/ssm"

    metadata = [str]
    a = utils.get_ssm_name_from_annotated_field(metadata)

    assert a is None
