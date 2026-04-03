from .config import AWSSettingsConfigDict
from .settings import (
    AWSBaseSettings,
    ParameterStoreBaseSettings,
    SecretsManagerBaseSettings,
)
from .version import VERSION

__all__ = [
    "AWSBaseSettings",
    "AWSSettingsConfigDict",
    "ParameterStoreBaseSettings",
    "SecretsManagerBaseSettings",
]

__version__ = VERSION
