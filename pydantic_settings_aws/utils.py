from typing import Any, Dict, List, Optional


def get_annotated_service_metadata(
    metadata: List[Any],
) -> Optional[Dict[str, Any]]:
    service_metadata = list(filter(_get_service_metadata, metadata))

    return service_metadata[0] if service_metadata else None


def get_ssm_name_from_annotated_field(metadata: List[Any]) -> Optional[str]:
    ssm_metadata = list(filter(_get_ssm_info_from_metadata, metadata))

    if ssm_metadata:
        return ssm_metadata[0]

    return None


def _get_ssm_info_from_metadata(metadata: Any) -> Optional[Any]:
    if isinstance(metadata, str):
        return metadata

    if isinstance(metadata, dict) and "ssm" in metadata:
        return metadata

    return None


def _get_service_metadata(metadata: Any) -> Optional[Dict[str, Any]]:
    if isinstance(metadata, dict) and "service" in metadata:
        return metadata

    return None
