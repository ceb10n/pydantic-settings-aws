from typing import Annotated, Any

from pydantic_settings_aws import (
    AWSSettingsConfigDict,
    ParameterStoreBaseSettings,
    SecretsManagerBaseSettings,
)
from pydantic_settings_aws.reload import (
    ChangeEvent,
    SecretsManagerVersionChecker,
    SettingsReloader,
    SSMVersionChecker,
    VersionChecker,
)

# ---------------------------------------------------------------------------
# Mocks

class SecretsVersionMock:
    """Minimal Secrets Manager client mock for version checker tests."""

    def __init__(self, version_id: str = "v1") -> None:
        self.version_id = version_id
        self.describe_call_count = 0
        self.get_value_call_count = 0
        self.should_fail = False

    def describe_secret(self, SecretId: str) -> dict[str, Any]:
        self.describe_call_count += 1
        if self.should_fail:
            raise Exception("simulated describe_secret failure")
        return {
            "ARN": "arn:aws:...",
            "Name": SecretId,
            "VersionIdsToStages": {
                self.version_id: ["AWSCURRENT"],
                "old-version": ["AWSPREVIOUS"],
            },
        }

    def get_secret_value(self, SecretId=None, VersionId=None, VersionStage=None) -> dict[str, Any]:
        self.get_value_call_count += 1
        return {
            "ARN": "arn:aws:...",
            "Name": SecretId,
            "VersionId": self.version_id,
            "SecretBinary": None,
            "SecretString": '{"username": "user1"}',
            "VersionStages": ["AWSCURRENT"],
        }


class SSMVersionMock:
    """Minimal SSM client mock for version checker tests."""

    def __init__(self, params: dict[str, tuple[str, int]] | None = None) -> None:
        # params: {name: (value, version)}
        self.params = params or {"/my/param": ("value1", 1)}
        self.get_parameters_call_count = 0
        self.should_fail = False

    def get_parameters(self, Names: list[str], WithDecryption: bool = True) -> dict[str, Any]:
        self.get_parameters_call_count += 1
        if self.should_fail:
            raise Exception("simulated get_parameters failure")
        parameters = [
            {"Name": name, "Value": val, "Version": ver}
            for name, (val, ver) in self.params.items()
            if name in Names
        ]
        return {"Parameters": parameters, "InvalidParameters": []}


# ---------------------------------------------------------------------------
# VersionChecker protocol

def test_version_checker_protocol_is_satisfied_by_secrets_checker() -> None:
    client = SecretsVersionMock()
    checker = SecretsManagerVersionChecker(client, "myapp/db")
    assert isinstance(checker, VersionChecker)


def test_version_checker_protocol_is_satisfied_by_ssm_checker() -> None:
    client = SSMVersionMock()
    checker = SSMVersionChecker(client, ["/my/param"])
    assert isinstance(checker, VersionChecker)


# ---------------------------------------------------------------------------
# SecretsManagerVersionChecker

def test_secrets_checker_first_call_returns_false() -> None:
    client = SecretsVersionMock("v1")
    checker = SecretsManagerVersionChecker(client, "myapp/db")
    assert checker.has_changed() is False


def test_secrets_checker_records_version_on_first_call() -> None:
    client = SecretsVersionMock("v1")
    checker = SecretsManagerVersionChecker(client, "myapp/db")
    checker.has_changed()
    assert checker._last_version_id == "v1"


def test_secrets_checker_returns_false_when_version_unchanged() -> None:
    client = SecretsVersionMock("v1")
    checker = SecretsManagerVersionChecker(client, "myapp/db")
    checker.has_changed()  # first call, records version
    assert checker.has_changed() is False


def test_secrets_checker_returns_true_when_version_changes() -> None:
    client = SecretsVersionMock("v1")
    checker = SecretsManagerVersionChecker(client, "myapp/db")
    checker.has_changed()  # first call
    client.version_id = "v2"
    assert checker.has_changed() is True


def test_secrets_checker_updates_stored_version_after_change() -> None:
    client = SecretsVersionMock("v1")
    checker = SecretsManagerVersionChecker(client, "myapp/db")
    checker.has_changed()
    client.version_id = "v2"
    checker.has_changed()
    assert checker._last_version_id == "v2"


def test_secrets_checker_returns_false_after_version_stabilises() -> None:
    client = SecretsVersionMock("v1")
    checker = SecretsManagerVersionChecker(client, "myapp/db")
    checker.has_changed()
    client.version_id = "v2"
    checker.has_changed()  # detects change, stores v2
    assert checker.has_changed() is False  # v2 unchanged


def test_secrets_checker_returns_true_on_describe_failure() -> None:
    client = SecretsVersionMock("v1")
    checker = SecretsManagerVersionChecker(client, "myapp/db")
    checker.has_changed()  # init
    client.should_fail = True
    assert checker.has_changed() is True


def test_secrets_checker_calls_describe_not_get_value() -> None:
    client = SecretsVersionMock("v1")
    checker = SecretsManagerVersionChecker(client, "myapp/db")
    checker.has_changed()
    checker.has_changed()
    assert client.describe_call_count == 2
    assert client.get_value_call_count == 0


# ---------------------------------------------------------------------------
# SSMVersionChecker

def test_ssm_checker_first_call_returns_false() -> None:
    client = SSMVersionMock({"/my/param": ("val", 1)})
    checker = SSMVersionChecker(client, ["/my/param"])
    assert checker.has_changed() is False


def test_ssm_checker_records_versions_on_first_call() -> None:
    client = SSMVersionMock({"/my/param": ("val", 1)})
    checker = SSMVersionChecker(client, ["/my/param"])
    checker.has_changed()
    assert checker._last_versions == {"/my/param": 1}


def test_ssm_checker_returns_false_when_version_unchanged() -> None:
    client = SSMVersionMock({"/my/param": ("val", 1)})
    checker = SSMVersionChecker(client, ["/my/param"])
    checker.has_changed()
    assert checker.has_changed() is False


def test_ssm_checker_returns_true_when_version_increments() -> None:
    client = SSMVersionMock({"/my/param": ("val", 1)})
    checker = SSMVersionChecker(client, ["/my/param"])
    checker.has_changed()
    client.params["/my/param"] = ("val2", 2)
    assert checker.has_changed() is True


def test_ssm_checker_tracks_multiple_parameters() -> None:
    client = SSMVersionMock({"/a": ("v1", 1), "/b": ("v2", 1)})
    checker = SSMVersionChecker(client, ["/a", "/b"])
    checker.has_changed()
    client.params["/b"] = ("v3", 2)  # only /b changed
    assert checker.has_changed() is True


def test_ssm_checker_returns_true_on_get_parameters_failure() -> None:
    client = SSMVersionMock({"/my/param": ("val", 1)})
    checker = SSMVersionChecker(client, ["/my/param"])
    checker.has_changed()
    client.should_fail = True
    assert checker.has_changed() is True


def test_ssm_checker_batches_more_than_10_parameters() -> None:
    params = {f"/param/{i}": (f"v{i}", 1) for i in range(25)}
    client = SSMVersionMock(params)
    checker = SSMVersionChecker(client, list(params.keys()))
    checker.has_changed()
    # 25 params → 3 batches of 10, 10, 5
    assert client.get_parameters_call_count == 3


# ---------------------------------------------------------------------------
# SettingsReloader integration

class MutableSSMClientMock:
    def __init__(self, ssm_value: str = "initial") -> None:
        self.ssm_value = ssm_value
        self.get_parameter_call_count = 0

    def get_parameter(self, Name=None, WithDecryption=None):
        self.get_parameter_call_count += 1
        return {"Parameter": {"Value": self.ssm_value}}


def make_ssm_settings(client):
    class SSMSettings(ParameterStoreBaseSettings):
        my_param: Annotated[str, {"ssm": "my/param", "ssm_client": client}]
    return SSMSettings


class AlwaysFalseChecker:
    """Version checker that always says nothing changed."""
    def has_changed(self) -> bool:
        return False


class AlwaysTrueChecker:
    """Version checker that always says something changed."""
    def has_changed(self) -> bool:
        return True


def test_reloader_skips_fetch_when_version_checker_returns_false() -> None:
    client = MutableSSMClientMock("v1")
    Settings = make_ssm_settings(client)
    reloader = SettingsReloader(Settings, version_checker=AlwaysFalseChecker())

    initial_call_count = client.get_parameter_call_count
    client.ssm_value = "v2"
    reloader.reload()

    # No new get_parameter call — fetch was skipped
    assert client.get_parameter_call_count == initial_call_count
    assert reloader.my_param == "v1"


def test_reloader_fetches_when_version_checker_returns_true() -> None:
    client = MutableSSMClientMock("v1")
    Settings = make_ssm_settings(client)
    reloader = SettingsReloader(Settings, version_checker=AlwaysTrueChecker())

    client.ssm_value = "v2"
    reloader.reload()

    assert reloader.my_param == "v2"


def test_reloader_without_version_checker_always_fetches() -> None:
    client = MutableSSMClientMock("v1")
    Settings = make_ssm_settings(client)
    reloader = SettingsReloader(Settings)

    initial_call_count = client.get_parameter_call_count
    reloader.reload()

    assert client.get_parameter_call_count > initial_call_count


def test_version_checker_prevents_spurious_change_events() -> None:
    client = MutableSSMClientMock("v1")
    Settings = make_ssm_settings(client)
    reloader = SettingsReloader(Settings, version_checker=AlwaysFalseChecker())
    fired: list = []

    @reloader.on_change("my_param")
    def handler(changed: dict[str, ChangeEvent]) -> None:
        fired.append(changed)

    client.ssm_value = "v2"
    reloader.reload()

    assert not fired


def test_secrets_manager_checker_with_reloader_skips_on_no_change() -> None:
    version_client = SecretsVersionMock("v1")
    checker = SecretsManagerVersionChecker(version_client, "myapp/db")

    class MySettings(SecretsManagerBaseSettings):
        model_config = AWSSettingsConfigDict(
            secrets_name="myapp/db",
            secrets_client=version_client,
        )
        username: str

    reloader = SettingsReloader(MySettings, version_checker=checker)
    checker.has_changed()  # initialise checker state

    get_value_calls_before = version_client.get_value_call_count
    reloader.reload()  # version unchanged → skipped

    assert version_client.get_value_call_count == get_value_calls_before


def test_secrets_manager_checker_with_reloader_fetches_on_change() -> None:
    version_client = SecretsVersionMock("v1")
    checker = SecretsManagerVersionChecker(version_client, "myapp/db")

    class MySettings(SecretsManagerBaseSettings):
        model_config = AWSSettingsConfigDict(
            secrets_name="myapp/db",
            secrets_client=version_client,
        )
        username: str

    reloader = SettingsReloader(MySettings, version_checker=checker)
    checker.has_changed()  # initialise checker state

    version_client.version_id = "v2"
    get_value_calls_before = version_client.get_value_call_count
    reloader.reload()

    assert version_client.get_value_call_count > get_value_calls_before
