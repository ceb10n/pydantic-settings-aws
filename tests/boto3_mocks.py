import datetime


class SessionMock:

    def __init__(self, *args, **kwargs) -> None:
        pass

    def client(self, name: str):
        return self



class ClientMock:

    def __init__(self, secret_string: str = None, raise_client_err: bool = False) -> None:
        self.secret_string = secret_string
        self.raise_client_err = raise_client_err

    def get_secret_value(self, SecretId=None, VersionId=None, VersionStage=None):
        if self.raise_client_err:
            raise 

        return {
            "ARN": "string",
            "Name": "string",
            "VersionId": "string",
            "SecretBinary": b"bytes",
            "SecretString": str(self.secret_string),
            "VersionStages": [
                "string",
            ],
            "CreatedDate": datetime.datetime.utcnow()
        }
