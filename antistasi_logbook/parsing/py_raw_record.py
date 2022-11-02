"""
WiP.

Soon.
"""

# region [Imports]

# * Standard Library Imports ---------------------------------------------------------------------------->
from typing import Optional
from pathlib import Path
from datetime import datetime
from concurrent.futures import Future

# * Gid Imports ----------------------------------------------------------------------------------------->
from gidapptools import get_logger
from gidapptools.general_helper.timing import get_dummy_profile_decorator_in_globals

# * Local Imports --------------------------------------------------------------------------------------->
from antistasi_logbook.storage.models.models import LogFile, Message, LogRecord
from antistasi_logbook.parsing.raw_sql_phrase import RawSQLPhrase

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


class RawRecord:
    insert_sql_phrase = RawSQLPhrase(phrase="""INSERT OR IGNORE INTO "LogRecord" ("start", "end", "message_item", "recorded_at", "called_by", "origin", "logged_from", "log_file", "log_level", "record_class", "marked") VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""")
    __slots__ = ("lines", "_is_antistasi_record", "start", "end", "parsed_data", "record_class", "record_origin", "_message_item_id", "_message_hash")

    def __init__(self, lines) -> None:
        self.lines = lines
        self._is_antistasi_record = None
        self.start = self.lines[0].start
        self.end = self.lines[-1].start
        self.parsed_data = None
        self.record_class = None
        self.record_origin = None
        self._message_item_id = None
        self._message_hash = None

    @property
    def message_item_id(self) -> int:
        if isinstance(self._message_item_id, Future):
            self._message_item_id = self._message_item_id.result()
        return self._message_item_id

    @property
    def content(self) -> str:
        return ' '.join(line.content.lstrip(" >>>").rstrip() for line in self.lines if line.content)

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

    def to_log_record_dict(self, log_file: LogFile):
        called_by = self.parsed_data.get("called_by")
        if called_by is not None:
            called_by = called_by.id
        logged_from = self.parsed_data.get("logged_from")
        if logged_from is not None:
            logged_from = logged_from.id

        return {"start": self.start,
                "end": self.end,
                "message_item": self.message_item_id,
                "recorded_at": self.parsed_data["recorded_at"],
                "called_by": called_by,
                "origin": self.record_origin.id,
                "logged_from": logged_from,
                "log_file": log_file.id,
                "log_level": self.parsed_data["log_level"].id,
                "record_class": self.record_class.id,
                "marked": False}

    def to_sql_params(self, log_file: LogFile):

        called_by = self.parsed_data.get("called_by")
        if called_by is not None:
            called_by = called_by.id
        logged_from = self.parsed_data.get("logged_from")
        if logged_from is not None:
            logged_from = logged_from.id

        # if self.record_class is None:
        #     raise RuntimeError("no record_class: " + repr(self.record_class) + '  --  ' + repr(self))

        return (self.start,
                self.end,
                self.message_hash,
                LogRecord.recorded_at.db_value(self.parsed_data["recorded_at"]),
                called_by,
                self.record_origin.id,
                logged_from,
                log_file.id,
                self.parsed_data["log_level"].id,
                self.record_class.id,
                0)

    @property
    def message(self) -> str:
        return self.parsed_data["message"]

    @property
    def message_hash(self) -> str:
        if self._message_hash is None:
            self._message_hash = Message.hash_text(self.message)
        return self._message_hash

    def __repr__(self) -> str:
        content = self.content
        if len(content) > 300:
            content = content[:297] + '...'
        return "%s(start=%r, end=%r, content=%r, origin=%r)" % (self.__class__.__name__, self.start, self.end, content, self.record_origin)

    def __eq__(self, o: object) -> bool:
        if isinstance(o, self.__class__):
            return self.lines == o.lines and self.content == o.content and self.record_origin == o.record_origin and self.start == o.start and self.end == o.end


# region[Main_Exec]
if __name__ == '__main__':
    pass

# endregion[Main_Exec]
