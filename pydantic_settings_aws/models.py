from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class AwsSecretsArgs(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    secrets_name: str = Field(..., alias="SecretId")
    secrets_version: Optional[str] = Field(None, alias="VersionId")
    secrets_stage: Optional[str] = Field(None, alias="VersionStage")


class AwsSession(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    aws_region: Optional[str] = Field(None, alias="region_name")
    aws_profile: Optional[str] = Field(None, alias="profile_name")
    aws_access_key_id: Optional[str] = None
    aws_secret_access_key: Optional[str] = None
    aws_session_token: Optional[str] = None

    def session_key(self) -> str:
        key = ""
        for k in self.model_fields.keys():
            # session token is too long
            if k != "aws_session_token":
                v = getattr(self, k)
                if v:
                    key += f"{v}_"
                    print(key)

        if not key:
            key = "default"

        return key.rstrip("_")
