from pydantic import BaseModel, ConfigDict, Field


class AwsSecretsArgs(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    secrets_name: str = Field(..., alias="SecretId")
    secrets_version: str | None = Field(None, alias="VersionId")
    secrets_stage: str | None = Field(None, alias="VersionStage")


class AwsSession(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    aws_region: str | None = Field(None, alias="region_name")
    aws_profile: str | None = Field(None, alias="profile_name")
    aws_access_key_id: str | None = None
    aws_secret_access_key: str | None = None
    aws_session_token: str | None = None

    def session_key(self) -> str:
        key = ""
        for k in self.model_fields.keys():
            # session token is too long
            if k != "aws_session_token":
                v = getattr(self, k)
                if v:
                    key += f"{v}_"

        if not key:
            key = "default"

        return key.rstrip("_")
