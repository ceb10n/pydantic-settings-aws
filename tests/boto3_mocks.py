import datetime


class SessionMock:
    def __init__(self, *args, **kwargs) -> None:
        pass

    def client(self, name: str):
        return self


class ClientMock:
    def __init__(
        self,
        secret_string: str = None,
        secret_bytes: bytes = None
    ) -> None:
        self.secret_string = secret_string
        self.secret_bytes = secret_bytes

    def get_secret_value(
        self, SecretId=None, VersionId=None, VersionStage=None
    ):
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
