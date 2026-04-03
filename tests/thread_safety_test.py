import sys
import threading
from unittest import mock

import pytest

from pydantic_settings_aws import aws

from .aws_mocks import TARGET_SESSION, BaseSettingsMock
from .boto3_mocks import SessionMock


def test_is_free_threaded() -> None:
    if sys.version_info < (3, 13):
        pytest.skip("Free-threaded builds only available in 3.13+")
    if sys._is_gil_enabled():
        pytest.skip("Not running in a free-threaded Python build")


@mock.patch(TARGET_SESSION, SessionMock)
def test_client_cache_concurrent_access() -> None:
    aws._client_cache = {}
    errors: list[Exception] = []

    def create_client() -> None:
        try:
            settings = BaseSettingsMock()
            settings.model_config = {"aws_region": "us-east-1"}
            aws._create_client_from_settings(settings, "ssm", "ssm_client")  # type: ignore[arg-type]
        except Exception as e:
            errors.append(e)

    threads = [threading.Thread(target=create_client) for _ in range(50)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert not errors
    assert len(aws._client_cache) == 1


@mock.patch(TARGET_SESSION, SessionMock)
def test_client_cache_concurrent_access_multiple_services() -> None:
    aws._client_cache = {}
    errors: list[Exception] = []

    def create_ssm_client() -> None:
        try:
            settings = BaseSettingsMock()
            settings.model_config = {"aws_region": "us-east-1"}
            aws._create_client_from_settings(settings, "ssm", "ssm_client")  # type: ignore[arg-type]
        except Exception as e:
            errors.append(e)

    def create_secrets_client() -> None:
        try:
            settings = BaseSettingsMock()
            settings.model_config = {"aws_region": "us-east-1"}
            aws._create_client_from_settings(settings, "secretsmanager", "secrets_client")  # type: ignore[arg-type]
        except Exception as e:
            errors.append(e)

    threads = [
        threading.Thread(target=create_ssm_client if i % 2 == 0 else create_secrets_client)
        for i in range(50)
    ]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert not errors
    assert len(aws._client_cache) == 2
