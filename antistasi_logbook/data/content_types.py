from mimetypes import types_map, init, knownfiles, encodings_map, suffix_map, guess_type, MimeTypes
from enum import Enum, Flag
from typing import Any
from rich.panel import Panel


class ContentType(Flag):
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
