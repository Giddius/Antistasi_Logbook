"""
WiP.

Soon.
"""

# region [Imports]

# * Standard Library Imports ---------------------------------------------------------------------------->
from typing import TYPE_CHECKING, Any, Iterable, Optional, ClassVar
from pathlib import Path
from datetime import datetime
import re
# * Gid Imports ----------------------------------------------------------------------------------------->
from gidapptools import get_logger
from gidapptools.general_helper.timing import get_dummy_profile_decorator_in_globals
# * Local Imports --------------------------------------------------------------------------------------->
from antistasi_logbook.storage.models.models import LogFile, LogRecord, RecordOrigin, BaseModel
import attr
from gidapptools.general_helper.string_helper import string_strip

# * Type-Checking Imports --------------------------------------------------------------------------------->
if TYPE_CHECKING:
    from antistasi_logbook.parsing.parser import RecordLine, RecordClass

# endregion[Imports]

# region [TODO]


# endregion [TODO]

# region [Logging]


# endregion[Logging]

# region [Constants]

get_dummy_profile_decorator_in_globals()
THIS_FILE_DIR = Path(__file__).parent.absolute()
log = get_logger(__name__)
# endregion[Constants]


@attr.s(frozen=True, kw_only=True, slots=True, weakref_slot=True, auto_attribs=True, auto_detect=True)
class RawSQLPhrase:
    phrase: str = attr.ib(converter=string_strip)
    value_names: tuple[str] = attr.ib()
    value_names_regex: ClassVar = re.compile(r"\((?P<value_names>[\"\w\,\s]+)\)\s*VALUES")

    @value_names.default
    def _parse_value_names(self) -> tuple[str]:
        raw_value_names = self.value_names_regex.search(self.phrase).group("value_names")
        value_names = [name.strip().strip('"') for name in raw_value_names.split(",")]
        return tuple(value_names)

    @property
    def batch_size(self) -> int:
        return 327670 // len(self.value_names)


class RawRecord:
    insert_sql_phrase = RawSQLPhrase(phrase="""INSERT OR IGNORE INTO "LogRecord" ("start", "end", "message", "recorded_at", "called_by", "origin", "logged_from", "log_file", "log_level", "marked") VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""")
    __slots__ = ("lines", "_is_antistasi_record", "start", "end", "_content", "parsed_data", "record_class", "record_origin")

    def __init__(self, lines: Iterable["RecordLine"]) -> None:
        self.lines = tuple(lines)
        self._content: str = None
        self._is_antistasi_record: bool = None
        self.start: int = self.lines[0].start
        self.end: int = self.lines[-1].start
        self.parsed_data: dict[str, Any] = None
        self.record_class: "RecordClass" = None
        self.record_origin: "RecordOrigin" = None

    @property
    def content(self) -> str:
        if self._content is None:
            self._content = ' '.join(line.content.lstrip(" >>>").rstrip() for line in self.lines if line.content)
        return self._content

    @property
    def recorded_at(self) -> Optional[datetime]:
        return self.parsed_data.get("recorded_at")

    def remove_content(self, content_to_remove: str) -> "RawRecord":
        remove_lines = content_to_remove.splitlines()
        new_lines = [l for l in self.lines if l.content not in remove_lines]
        return self.__class__(lines=new_lines)

    @property
    def unformatted_content(self) -> str:
        return '\n'.join(line.content for line in self.lines)

    def to_log_record_dict(self, log_file: "LogFile") -> dict[str, Any]:
        return {"start": self.start, "end": self.end, 'message': self.parsed_data.get("message"), 'recorded_at': self.parsed_data.get("recorded_at"),
                'called_by': self.parsed_data.get("called_by"), "record_origin": self.record_origin, 'logged_from': self.parsed_data.get("logged_from"),
                "log_file": log_file.id, 'log_level': self.parsed_data.get("log_level"), "record_class": self.record_class.id, "marked": False}

    def to_sql_params(self, log_file: "LogFile") -> tuple:
        called_by = self.parsed_data.get("called_by")
        if called_by is not None:
            called_by = called_by.id
        logged_from = self.parsed_data.get("logged_from")
        if logged_from is not None:
            logged_from = logged_from.id

        return (self.start, self.end, self.parsed_data.get("message"), LogRecord.recorded_at.db_value(self.parsed_data.get("recorded_at")), called_by, self.record_origin.id, logged_from, log_file.id, self.parsed_data.get("log_level").id, 0)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(start={self.start!r}, end={self.end!r}, content={self.content!r}, origin={self.record_origin!r}, lines={self.lines!r})"

    def __eq__(self, o: object) -> bool:
        if isinstance(o, self.__class__):
            return self.lines == o.lines and self.content == o.content and self.record_origin == o.record_origin and self.start == o.start and self.end == o.end


# region[Main_Exec]
if __name__ == '__main__':
    pass

# endregion[Main_Exec]
