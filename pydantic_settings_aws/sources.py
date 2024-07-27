from typing import Any, Dict, Tuple, Type

from pydantic.fields import FieldInfo
from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
)

from pydantic_settings_aws import aws, utils
from pydantic_settings_aws.logger import logger


class AWSSettingsSource(PydanticBaseSettingsSource):
    def __init__(self, settings_cls: Type[BaseSettings]):
        super().__init__(settings_cls)

    def get_field_value(
        self, field: FieldInfo, field_name: str
    ) -> Tuple[Any, str, bool]:
        logger.debug(f"Getting {field_name} value from AWS service")
        field_value = None

        service_metadata = utils.get_annotated_service_metadata(field.metadata)

        if not service_metadata:
            logger.info("No information about AWS service was found")
            return None, field_name, False

        service = service_metadata.get("service")

        if service == "ssm":
            ssm_info = utils.get_ssm_name_from_annotated_field(field.metadata)
            field_value = aws.get_ssm_content(
                self.settings_cls, field_name, ssm_info
            )

        elif service == "secrets":
            logger.debug(
                f"Getting value from secrets manager for filed {field_name}"
            )
            json_content = aws.get_secrets_content(self.settings_cls)
            field_value = json_content.get(field_name)

        logger.info(f"field value={field_value}")

        return field_value, field_name, False

    def prepare_field_value(
        self,
        field_name: str,
        field: FieldInfo,
        value: Any,
        value_is_complex: bool,
    ) -> Any:
        return value

    def __call__(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {}

        for field_name, field in self.settings_cls.model_fields.items():
            field_value, field_key, value_is_complex = self.get_field_value(
                field, field_name
            )
            field_value = self.prepare_field_value(
                field_name, field, field_value, value_is_complex
            )
            if field_value is not None:
                d[field_key] = field_value

        return d


class ParameterStoreSettingsSource(PydanticBaseSettingsSource):
    """Source class for loading settings from AWS Parameter Store."""

    def __init__(self, settings_cls: Type[BaseSettings]):
        super().__init__(settings_cls)

    def get_field_value(
        self, field: FieldInfo, field_name: str
    ) -> Tuple[Any, str, bool]:
        ssm_info = utils.get_ssm_name_from_annotated_field(field.metadata)
        field_value = aws.get_ssm_content(
            self.settings_cls, field_name, ssm_info
        )

        return field_value, field_name, False

    def prepare_field_value(
        self,
        field_name: str,
        field: FieldInfo,
        value: Any,
        value_is_complex: bool,
    ) -> Any:
        return value

    def __call__(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {}

        for field_name, field in self.settings_cls.model_fields.items():
            field_value, field_key, value_is_complex = self.get_field_value(
                field, field_name
            )
            field_value = self.prepare_field_value(
                field_name, field, field_value, value_is_complex
            )
            if field_value is not None:
                d[field_key] = field_value

        return d


class SecretsManagerSettingsSource(PydanticBaseSettingsSource):
    def __init__(self, settings_cls: Type[BaseSettings]):
        super().__init__(settings_cls)
        self._json_content = aws.get_secrets_content(settings_cls)

    def get_field_value(
        self, field: FieldInfo, field_name: str
    ) -> Tuple[Any, str, bool]:
        field_value = self._json_content.get(field_name)
        return field_value, field_name, False

    def prepare_field_value(
        self,
        field_name: str,
        field: FieldInfo,
        value: Any,
        value_is_complex: bool,
    ) -> Any:
        return value

    def __call__(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {}

        for field_name, field in self.settings_cls.model_fields.items():
            field_value, field_key, value_is_complex = self.get_field_value(
                field, field_name
            )
            field_value = self.prepare_field_value(
                field_name, field, field_value, value_is_complex
            )
            if field_value is not None:
                d[field_key] = field_value

        return d
