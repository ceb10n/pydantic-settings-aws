from dataclasses import dataclass
from dataclasses import field as dc_field
from typing import Any


@dataclass
class Secrets:
    """Typed descriptor for mapping a model field to a key in an AWS Secrets Manager secret.

    Use this as ``Annotated`` metadata instead of a raw ``{"service": "secrets"}`` dict.
    All arguments are optional — omitting them falls back to the behaviour of the
    plain dict annotation.

    Examples:
        Map a field to a differently-named key in the secret::

            class MySettings(SecretsManagerBaseSettings):
                model_config = AWSSettingsConfigDict(secrets_name="myapp/prod")

                db_password: Annotated[str, Secrets(field="password")]

        Use the model field name as the key (equivalent to the raw dict annotation)::

            db_host: Annotated[str, Secrets()]
    """

    field: str | None = None
    """The key to look up inside the secret's JSON object. When ``None``, the model field name is used as the key."""

    client: Any = dc_field(default=None, repr=False)
    """A pre-constructed ``boto3`` Secrets Manager client to use for this field. When ``None``, the client is resolved from :class:`AWSSettingsConfigDict` or created automatically."""


@dataclass
class SSM:
    """Typed descriptor for mapping a model field to an AWS SSM Parameter Store parameter.

    Use this as ``Annotated`` metadata instead of a raw string or
    ``{"ssm": "...", "ssm_client": ...}`` dict. All arguments are optional —
    omitting them falls back to the behaviour of the plain string/dict annotation.

    Examples:
        Map a field to a specific parameter name::

            class MySettings(ParameterStoreBaseSettings):
                db_host: Annotated[str, SSM(name="/prod/db/host")]

        Use a per-field client for a multi-account setup::

            class MySettings(ParameterStoreBaseSettings):
                prod_host: Annotated[str, SSM(name="/prod/db/host", client=prod_client)]
                staging_host: Annotated[str, SSM(name="/staging/db/host", client=staging_client)]

        Use the model field name as the parameter name::

            mongodb_host: Annotated[str, SSM()]
    """

    name: str | None = None
    """The SSM parameter name or ARN to retrieve. When ``None``, the model field name is used as the parameter name."""

    client: Any = dc_field(default=None, repr=False)
    """A pre-constructed ``boto3`` SSM client to use for this field. When ``None``, the client is resolved from :class:`AWSSettingsConfigDict` or created automatically. Useful for per-field multi-account or multi-region setups."""
