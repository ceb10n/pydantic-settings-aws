import time
from typing import Annotated

import pytest

from pydantic_settings_aws import (
    AWSSettingsConfigDict,
    ParameterStoreBaseSettings,
    SecretsManagerBaseSettings,
)
from pydantic_settings_aws.reload import ChangeEvent, SettingsReloader

# ---------------------------------------------------------------------------
# Mutable mocks — return different values on successive instantiations

class MutableSSMClientMock:
    def __init__(self, ssm_value: str = "initial") -> None:
        self.ssm_value = ssm_value
        self.should_fail = False

    def get_parameter(self, Name=None, WithDecryption=None):
        if self.should_fail:
            raise Exception("simulated SSM failure")
        return {"Parameter": {"Value": self.ssm_value}}


class MutableSecretsClientMock:
    def __init__(self, secret_string: str = '{"username": "user1"}') -> None:
        self.secret_string = secret_string

    def get_secret_value(self, SecretId=None, VersionId=None, VersionStage=None):
        return {
            "ARN": "arn:aws:...",
            "Name": "myapp/db",
            "VersionId": "v1",
            "SecretBinary": None,
            "SecretString": self.secret_string,
            "VersionStages": ["AWSCURRENT"],
        }


# ---------------------------------------------------------------------------
# Helpers to build settings classes around mutable mocks

def make_ssm_settings(client: MutableSSMClientMock):
    class SSMSettings(ParameterStoreBaseSettings):
        my_param: Annotated[
            str, {"ssm": "my/param", "ssm_client": client}
        ]
    return SSMSettings


def make_secrets_settings(client: MutableSecretsClientMock):
    class SecretSettings(SecretsManagerBaseSettings):
        model_config = AWSSettingsConfigDict(
            secrets_name="myapp/db",
            secrets_client=client,
        )
        username: str

    return SecretSettings


# ---------------------------------------------------------------------------
# Proxy

def test_proxy_forwards_attribute() -> None:
    client = MutableSSMClientMock("hello")
    reloader = SettingsReloader(make_ssm_settings(client))
    assert reloader.my_param == "hello"


def test_proxy_forwards_model_dump() -> None:
    client = MutableSSMClientMock("hello")
    reloader = SettingsReloader(make_ssm_settings(client))
    data = reloader.model_dump()
    assert data == {"my_param": "hello"}


# ---------------------------------------------------------------------------
# Manual reload

def test_reload_picks_up_new_value() -> None:
    client = MutableSSMClientMock("v1")
    reloader = SettingsReloader(make_ssm_settings(client))

    assert reloader.my_param == "v1"
    client.ssm_value = "v2"
    reloader.reload()
    assert reloader.my_param == "v2"


def test_reload_keeps_value_when_unchanged() -> None:
    client = MutableSSMClientMock("v1")
    reloader = SettingsReloader(make_ssm_settings(client))

    reloader.reload()
    assert reloader.my_param == "v1"


def test_reload_keeps_current_on_failure() -> None:
    client = MutableSSMClientMock("v1")
    reloader = SettingsReloader(make_ssm_settings(client))

    assert reloader.my_param == "v1"
    client.should_fail = True
    reloader.reload()  # must not raise
    assert reloader.my_param == "v1"


# ---------------------------------------------------------------------------
# Change events — per-field listeners

def test_on_change_fires_for_changed_field() -> None:
    client = MutableSSMClientMock("v1")
    reloader = SettingsReloader(make_ssm_settings(client))
    received: list[dict[str, ChangeEvent]] = []

    @reloader.on_change("my_param")
    def handler(changed: dict[str, ChangeEvent]) -> None:
        received.append(changed)

    client.ssm_value = "v2"
    reloader.reload()

    assert len(received) == 1
    assert received[0]["my_param"].old == "v1"
    assert received[0]["my_param"].new == "v2"


def test_on_change_not_fired_when_value_unchanged() -> None:
    client = MutableSSMClientMock("v1")
    reloader = SettingsReloader(make_ssm_settings(client))
    fired: list = []

    @reloader.on_change("my_param")
    def handler(changed: dict[str, ChangeEvent]) -> None:
        fired.append(changed)

    reloader.reload()  # same value → no event

    assert not fired


def test_on_change_not_fired_for_unregistered_field() -> None:
    client = MutableSSMClientMock("v1")
    reloader = SettingsReloader(make_ssm_settings(client))
    fired: list = []

    @reloader.on_change("other_field")
    def handler(changed: dict[str, ChangeEvent]) -> None:
        fired.append(changed)

    client.ssm_value = "v2"
    reloader.reload()

    assert not fired


def test_multi_field_listener_called_once() -> None:
    """A callback registered for multiple fields is called once per reload, not once per field."""
    import json

    client = MutableSecretsClientMock('{"username": "u1", "password": "p1"}')

    class TwoFieldSettings(SecretsManagerBaseSettings):
        model_config = AWSSettingsConfigDict(
            secrets_name="myapp/db",
            secrets_client=client,
        )
        username: str
        password: str

    reloader = SettingsReloader(TwoFieldSettings)
    call_count = 0
    received: list[dict[str, ChangeEvent]] = []

    @reloader.on_change("username", "password")
    def handler(changed: dict[str, ChangeEvent]) -> None:
        nonlocal call_count
        call_count += 1
        received.append(changed)

    client.secret_string = json.dumps({"username": "u2", "password": "p2"})
    reloader.reload()

    assert call_count == 1
    assert "username" in received[0]
    assert "password" in received[0]


# ---------------------------------------------------------------------------
# Change events — global listeners

def test_global_on_change_fires_for_any_change() -> None:
    client = MutableSSMClientMock("v1")
    reloader = SettingsReloader(make_ssm_settings(client))
    received: list[dict[str, ChangeEvent]] = []

    @reloader.on_change()
    def handler(changed: dict[str, ChangeEvent]) -> None:
        received.append(changed)

    client.ssm_value = "v2"
    reloader.reload()

    assert len(received) == 1
    assert "my_param" in received[0]


def test_global_on_change_not_fired_when_unchanged() -> None:
    client = MutableSSMClientMock("v1")
    reloader = SettingsReloader(make_ssm_settings(client))
    fired: list = []

    @reloader.on_change()
    def handler(changed: dict[str, ChangeEvent]) -> None:
        fired.append(changed)

    reloader.reload()

    assert not fired


def test_listener_exception_does_not_abort_reload() -> None:
    client = MutableSSMClientMock("v1")
    reloader = SettingsReloader(make_ssm_settings(client))
    second_fired = False

    @reloader.on_change("my_param")
    def bad_handler(changed: dict[str, ChangeEvent]) -> None:
        raise RuntimeError("oops")

    @reloader.on_change()
    def good_handler(changed: dict[str, ChangeEvent]) -> None:
        nonlocal second_fired
        second_fired = True

    client.ssm_value = "v2"
    reloader.reload()  # must not raise despite bad_handler

    assert second_fired


# ---------------------------------------------------------------------------
# Lazy TTL mode

def test_ttl_triggers_reload_on_stale_access() -> None:
    client = MutableSSMClientMock("v1")
    reloader = SettingsReloader(make_ssm_settings(client), ttl=0.01)

    assert reloader.my_param == "v1"
    client.ssm_value = "v2"
    time.sleep(0.02)
    assert reloader.my_param == "v2"


def test_ttl_does_not_reload_before_expiry() -> None:
    client = MutableSSMClientMock("v1")
    reloader = SettingsReloader(make_ssm_settings(client), ttl=60)

    assert reloader.my_param == "v1"
    client.ssm_value = "v2"
    # TTL not expired — should still see the old value
    assert reloader.my_param == "v1"


def test_ttl_fires_change_event_on_reload() -> None:
    client = MutableSSMClientMock("v1")
    reloader = SettingsReloader(make_ssm_settings(client), ttl=0.01)
    received: list[dict[str, ChangeEvent]] = []

    @reloader.on_change("my_param")
    def handler(changed: dict[str, ChangeEvent]) -> None:
        received.append(changed)

    client.ssm_value = "v2"
    time.sleep(0.02)
    _ = reloader.my_param  # triggers the lazy reload

    assert len(received) == 1
    assert received[0]["my_param"].new == "v2"


# ---------------------------------------------------------------------------
# Background thread (interval mode)

def test_background_thread_reloads_on_interval() -> None:
    client = MutableSSMClientMock("v1")
    reloader = SettingsReloader(make_ssm_settings(client), interval=0.05)

    with reloader:
        client.ssm_value = "v2"
        time.sleep(0.15)
        assert reloader.my_param == "v2"


def test_background_thread_fires_change_event() -> None:
    client = MutableSSMClientMock("v1")
    reloader = SettingsReloader(make_ssm_settings(client), interval=0.05)
    received: list[dict[str, ChangeEvent]] = []

    @reloader.on_change("my_param")
    def handler(changed: dict[str, ChangeEvent]) -> None:
        received.append(changed)

    with reloader:
        client.ssm_value = "v2"
        time.sleep(0.15)

    assert len(received) >= 1
    assert received[0]["my_param"].old == "v1"
    assert received[0]["my_param"].new == "v2"


def test_context_manager_stops_thread() -> None:
    client = MutableSSMClientMock("v1")
    reloader = SettingsReloader(make_ssm_settings(client), interval=0.05)

    with reloader as r:
        thread = object.__getattribute__(r, "_thread")
        assert thread.is_alive()

    assert not thread.is_alive()


def test_stop_without_start_is_safe() -> None:
    client = MutableSSMClientMock("v1")
    reloader = SettingsReloader(make_ssm_settings(client), interval=0.05)
    reloader.stop()  # must not raise


# ---------------------------------------------------------------------------
# Validation

def test_cannot_specify_both_interval_and_ttl() -> None:
    client = MutableSSMClientMock()
    with pytest.raises(ValueError, match="interval or ttl"):
        SettingsReloader(make_ssm_settings(client), interval=60, ttl=300)


def test_start_raises_without_interval() -> None:
    client = MutableSSMClientMock()
    reloader = SettingsReloader(make_ssm_settings(client), ttl=60)
    with pytest.raises(RuntimeError, match="interval mode"):
        reloader.start()


def test_start_raises_in_manual_mode() -> None:
    client = MutableSSMClientMock()
    reloader = SettingsReloader(make_ssm_settings(client))
    with pytest.raises(RuntimeError, match="interval mode"):
        reloader.start()
