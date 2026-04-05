class PydanticSettingsAWSError(Exception):
    """Base exception for all pydantic-settings-aws errors."""


class AWSClientError(PydanticSettingsAWSError):
    """Raised when a boto3 client cannot be created."""


class AWSSettingsConfigError(PydanticSettingsAWSError):
    """Raised when the settings configuration is invalid or missing required fields."""


class SecretsManagerError(PydanticSettingsAWSError):
    """Base exception for AWS Secrets Manager errors."""


class SecretNotFoundError(SecretsManagerError):
    """Raised when the requested secret does not exist in Secrets Manager."""


class SecretContentError(SecretsManagerError):
    """Raised when a secret exists but its content is empty or missing."""


class SecretDecodeError(SecretsManagerError):
    """Raised when the secret content cannot be decoded as valid JSON."""


class SSMError(PydanticSettingsAWSError):
    """Base exception for AWS SSM Parameter Store errors."""


class ParameterNotFoundError(SSMError):
    """Raised when the requested parameter does not exist in Parameter Store."""
