from typing import Any


def get_annotated_service_metadata(
    metadata: list[Any],
) -> dict[str, Any] | None:
    service_metadata = list(filter(_get_service_metadata, metadata))

    return service_metadata[0] if service_metadata else None


def get_ssm_name_from_annotated_field(metadata: list[Any]) -> str | None:
    ssm_metadata = list(filter(_get_ssm_info_from_metadata, metadata))

    if ssm_metadata:
        return ssm_metadata[0]

    return None


def _get_ssm_info_from_metadata(metadata: Any) -> Any | None:
    if isinstance(metadata, str):
        return metadata

    if isinstance(metadata, dict) and "ssm" in metadata:
        return metadata

    return None


def _get_service_metadata(metadata: Any) -> dict[str, Any] | None:
    if isinstance(metadata, dict) and "service" in metadata:
        return metadata

    return None
