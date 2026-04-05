import datetime
from typing import Any

from botocore.exceptions import ClientError  # type: ignore[import-untyped]


class SessionMock:
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        pass

    def client(self, name: str) -> "SessionMock":
        return self


class ClientMock:
    def __init__(
        self,
        secret_string: str | None = None,
        secret_bytes: bytes | None = None,
        ssm_value: str | None = None,
    ) -> None:
        self.secret_string = secret_string
        self.secret_bytes = secret_bytes
        self.ssm_value = ssm_value

    def client(self, *args: Any) -> "ClientMock":
        return self

    def get_parameter(
        self, Name: str | None = None, WithDecryption: bool | None = None
    ) -> dict[str, Any]:
        return {"Parameter": {"Value": self.ssm_value}}

    def get_secret_value(
        self,
        SecretId: str | None = None,
        VersionId: str | None = None,
        VersionStage: str | None = None,
    ) -> dict[str, Any]:
        return {
            "ARN": "string",
            "Name": "string",
            "VersionId": "string",
            "SecretBinary": self.secret_bytes,
            "SecretString": self.secret_string,
            "VersionStages": [
                "string",
            ],
            "CreatedDate": datetime.datetime.utcnow(),
        }


class ClientErrorMock:
    """Mock boto3 client that raises a ClientError with the given error code."""

    def __init__(self, error_code: str) -> None:
        self.error_code = error_code

    def client(self, *args: Any) -> "ClientErrorMock":
        return self

    def get_parameter(self, **kwargs: Any) -> None:
        raise ClientError(
            {"Error": {"Code": self.error_code, "Message": "mocked error"}},
            "GetParameter",
        )

    def get_secret_value(self, **kwargs: Any) -> None:
        raise ClientError(
            {"Error": {"Code": self.error_code, "Message": "mocked error"}},
            "GetSecretValue",
        )


class BrokenSessionMock:
    """Mock boto3 Session that raises on client creation."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        pass

    def client(self, name: str) -> None:
        raise Exception("cannot create client")
