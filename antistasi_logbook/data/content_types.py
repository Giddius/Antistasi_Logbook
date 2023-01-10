# * Standard Library Imports ---------------------------------------------------------------------------->
from enum import Flag, Enum
from typing import Any


class ContentType(Enum):
    TEXT = "text/plain"
    ZIP = "application/zip"
    OTHER = "other"
    NONE = None

    @classmethod
    def _missing_(cls, value: Any) -> "ContentType":
        if isinstance(value, str) and value == '':
            return cls.NONE
        return cls.OTHER

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.value!r})"

    def __str__(self) -> str:
        return self.name
