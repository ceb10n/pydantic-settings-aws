from typing import Any, List, Optional


def get_ssm_name_from_annotated_field(metadata: List[Any]) -> Optional[str]:
    ssm_metadata = list(
        filter(_get_ssm_info_from_metadata, metadata)
    )

    if ssm_metadata:
        return ssm_metadata[0]

    return None


def _get_ssm_info_from_metadata(metadata: Any) -> Optional[Any]:
    if isinstance(metadata, str):
        return metadata

    if isinstance(metadata, dict) and "ssm" in metadata.keys():
        return metadata

    return None
