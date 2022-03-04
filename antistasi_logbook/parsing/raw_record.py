"""
WiP.

Soon.
"""

# region [Imports]

# * Standard Library Imports ---------------------------------------------------------------------------->
from typing import TYPE_CHECKING, Any, Iterable, Optional
from pathlib import Path
from datetime import datetime

# * Gid Imports ----------------------------------------------------------------------------------------->
from gidapptools import get_logger

# * Local Imports --------------------------------------------------------------------------------------->
from antistasi_logbook.storage.models.models import LogFile, LogRecord, RecordOrigin

# * Type-Checking Imports --------------------------------------------------------------------------------->
if TYPE_CHECKING:
    from antistasi_logbook.parsing.parser import RecordLine, RecordClass

# endregion[Imports]

# region [TODO]


# endregion [TODO]

# region [Logging]


# endregion[Logging]

# region [Constants]
from gidapptools.general_helper.timing import get_dummy_profile_decorator_in_globals

THIS_FILE_DIR = Path(__file__).parent.absolute()
log = get_logger(__name__)
# endregion[Constants]


class RawRecord:

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
