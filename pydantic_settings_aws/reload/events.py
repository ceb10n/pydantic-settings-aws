from dataclasses import dataclass
from typing import Any


@dataclass
class ChangeEvent:
    """Represents a single field value change detected during a settings reload."""

    field: str
    old: Any
    new: Any
