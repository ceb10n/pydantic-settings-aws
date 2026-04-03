from pydantic_settings_aws.models import AwsSession


def test_aws_session_key_must_be_default_if_all_values_are_none() -> None:
    session = AwsSession()  # type: ignore[call-arg]
    assert session.session_key() == "default"
