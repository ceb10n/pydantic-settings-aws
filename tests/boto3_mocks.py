import datetime


class ClientMock:

    def __init__(self, secret_string: str = None) -> None:
        self.secret_string = secret_string

    def get_secret_value(self, SecretId=None, VersionId=None, VersionStage=None):
        import json
        a = json.loads(self.secret_string)
        print(f"str -> {a}")
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
