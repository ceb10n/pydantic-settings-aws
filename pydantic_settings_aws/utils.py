from typing import Any

from .fields import SSM, Secrets


def get_annotated_service_metadata(
    metadata: list[Any],
) -> dict[str, Any] | None:
    for m in metadata:
        result = _get_service_metadata(m)
        if result is not None:
            return result
    return None


def get_ssm_name_from_annotated_field(metadata: list[Any]) -> str | dict[str, Any] | SSM | None:
    ssm_metadata = list(filter(_get_ssm_info_from_metadata, metadata))

    if ssm_metadata:
        return ssm_metadata[0]

    return None


def get_secrets_field_name(metadata: list[Any], default: str) -> str:
    """Return the secret JSON key to use for a field.

    When a :class:`Secrets` descriptor with a ``field`` override is found in
    ``metadata``, that value is returned. Otherwise ``default`` (the model
    field name) is returned unchanged, preserving backwards compatibility with
    the raw ``{"service": "secrets"}`` dict annotation.
    """
    for m in metadata:
        if isinstance(m, Secrets) and m.field is not None:
            return m.field

    return default


def _get_ssm_info_from_metadata(metadata: Any) -> Any | None:
    if isinstance(metadata, str):
        return metadata

    if isinstance(metadata, dict) and "ssm" in metadata:
        return metadata

    if isinstance(metadata, SSM):
        return metadata

    return None


def _get_service_metadata(metadata: Any) -> dict[str, Any] | None:
    if isinstance(metadata, dict) and "service" in metadata:
        return metadata

    if isinstance(metadata, Secrets):
        return {"service": "secrets"}

    if isinstance(metadata, SSM):
        return {"service": "ssm"}

    return None
