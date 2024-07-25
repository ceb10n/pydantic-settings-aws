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
        secret_bytes: bytes = None,
        ssm_value: str = None
    ) -> None:
        self.secret_string = secret_string
        self.secret_bytes = secret_bytes
        self.ssm_value = ssm_value

    def client(self, *args):
        return self

    def get_parameter(self, Name=None, WithDecryption=None):
        return {
            "Parameter": {
                "Value": self.ssm_value
            }
        }

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
