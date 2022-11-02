"""
WiP.

Soon.
"""

# region [Imports]

# * Standard Library Imports ---------------------------------------------------------------------------->
from typing import TYPE_CHECKING, Any, Union, Optional, Generator, Iterable, List, Set, Dict
from pathlib import Path
from datetime import datetime
from threading import Lock, RLock, Condition, Event, Semaphore, Thread
import sys
# * Third Party Imports --------------------------------------------------------------------------------->
import attr

# * Gid Imports ----------------------------------------------------------------------------------------->
from gidapptools import get_logger
from gidapptools.general_helper.color.color_item import Color
from gidapptools.gid_config.interface import get_config, GidIniConfig
# * Local Imports --------------------------------------------------------------------------------------->
from antistasi_logbook.records.enums import RecordFamily, MessageFormat

try:
    from PySide6.QtWidgets import QApplication
    from PySide6.QtGui import QColor
    from PySide6.QtCore import QSize
    PYSIDE6_AVAILABLE = True
except ImportError:
    PYSIDE6_AVAILABLE = False
# * Gid Imports ----------------------------------------------------------------------------------------->
from gidapptools.general_helper.enums import MiscEnum
from gidapptools.general_helper.string_helper import shorten_string
from antistasi_logbook.records.special_message_formats import discord_format

from frozendict import frozendict
from antistasi_logbook.storage.models.models import LogFile, LogLevel, LogRecord, ArmaFunction, RecordOrigin, Server

# * Type-Checking Imports --------------------------------------------------------------------------------->
if TYPE_CHECKING:
    from antistasi_logbook.storage.database import GidSqliteApswDatabase
    from antistasi_logbook.parsing.foreign_key_cache import ForeignKeyCache
    from PySide6.QtGui import QColor

# endregion[Imports]

# region [TODO]


# endregion [TODO]

# region [Logging]


# endregion[Logging]

# region [Constants]

THIS_FILE_DIR = Path(__file__).parent.absolute()
log = get_logger(__name__)
# endregion[Constants]


# class PrettyAttributeCache:
#     __slots__ = ("pretty_recorded_at", "pretty_log_level", "pretty_message", "pretty_log_file")

#     def __init__(self, pretty_recorded_at: str = None, pretty_log_level: str = None, pretty_message: str = None, pretty_log_file: str = None) -> None:
#         self.pretty_recorded_at: str = pretty_recorded_at or MiscEnum.NOTHING
#         self.pretty_log_level: str = pretty_log_level or MiscEnum.NOTHING
#         self.pretty_message: str = pretty_message or MiscEnum.NOTHING
#         self.pretty_log_file: str = pretty_log_file or MiscEnum.NOTHING


class RecordColorCache:
    __slots__ = ("_config", "_cache", "_access_lock")
    default_color_values = frozendict(**{"r": 255, "g": 255, "b": 255, "a": 150})

    def __init__(self, config: GidIniConfig = None) -> None:
        self._config = config or QApplication.instance().color_config
        self._cache: dict[str, "QColor"] = {}
        self._access_lock = Lock()

    @property
    def default_color(self) -> QColor:
        return QColor(*[self.default_color_values[k] for k in "rgba"])

    def _retrieve_color_from_config(self, name: str) -> "QColor":
        color = self._config.get("record", name, default=self.default_color)
        self._cache[name] = color
        return color

    def get(self, record_class: "BaseRecord") -> Optional["QColor"]:
        name = record_class.__name__
        with self._access_lock:
            try:
                return self._cache[name]
            except KeyError:
                return self._retrieve_color_from_config(name)

    def set(self, record_class: type, color: QColor) -> None:
        name = record_class.__name__
        with self._access_lock:
            self._config.set("record", name, color)
            self._cache[name] = color


class BaseRecord:
    ___record_family___ = RecordFamily.GENERIC | RecordFamily.ANTISTASI
    ___specificity___ = 0

    _color_cache: RecordColorCache = None
    extra_detail_views: tuple[str] = tuple()
    __slots__ = ("record_id",
                 "log_file",
                 "origin",
                 "start",
                 "end",
                 "message",
                 "recorded_at",
                 "log_level",
                 "marked",
                 "called_by",
                 "logged_from",
                 "has_multiline_message")

    def __init__(self,
                 record_id: int,
                 log_file: LogFile,
                 origin: "RecordOrigin",
                 start: int,
                 end: int,
                 message: str,
                 recorded_at: datetime,
                 log_level: "LogLevel",
                 marked: bool,
                 called_by: "ArmaFunction" = None,
                 logged_from: "ArmaFunction" = None) -> None:
        self.record_id = record_id
        self.log_file = log_file
        self.origin = origin
        self.start = start
        self.end = end
        self.message = message

        self.recorded_at = recorded_at
        self.log_level = log_level
        self.marked = marked
        self.called_by = called_by
        self.logged_from = logged_from
        self.has_multiline_message: bool = (self.end - self.start) > 0

    def get_data(self, name: str):
        try:
            return getattr(self, f"pretty_{name}")
        except AttributeError:

            return getattr(self, name)

    @property
    def server(self) -> "Server":
        return self.log_file.server

    @property
    def pretty_log_file(self) -> str:
        return str(self.log_file.name)

    @property
    def pretty_message(self) -> str:
        return self.get_formated_message(MessageFormat.PRETTY)

    @property
    def pretty_log_level(self) -> Optional[str]:
        return str(self.log_level) if self.log_level.id != 0 else None

    @property
    def pretty_recorded_at(self) -> str:
        return self.log_file.format_datetime(self.recorded_at)

    @classmethod
    @property
    def background_color(cls) -> Optional["QColor"]:
        return cls.get_background_color()

    @classmethod
    def get_background_color(cls) -> "QColor":
        return cls._color_cache.get(cls)

    @classmethod
    def set_background_color(cls, color: QColor):
        cls._color_cache.set(cls, color=color)

    def get_formated_message(self, msg_format: "MessageFormat" = MessageFormat.PRETTY) -> str:
        msg_format = MessageFormat(msg_format)

        if msg_format is MessageFormat.SHORT:
            text = shorten_string(self.message, max_length=30)

        elif msg_format is MessageFormat.ORIGINAL:
            text = self.log_file.original_file.get_lines(start=self.start, end=self.end)

        elif msg_format is MessageFormat.DISCORD:
            text = discord_format(in_record=self)

        else:
            text = self.message

        return text

    def get_db_item(self, database: "GidSqliteApswDatabase") -> "LogRecord":
        with database.connection_context() as ctx:
            return LogRecord.get_by_id(self.record_id)

    @classmethod
    def parse(cls, message: str) -> dict[str, Any]:
        return {}

    @classmethod
    def check(cls, log_record: "LogRecord") -> bool:
        return True

    @classmethod
    def from_db_item(cls, item: "LogRecord") -> "BaseRecord":
        return cls(record_id=item.id,
                   log_file=item.log_file,
                   origin=item.origin,
                   start=item.start,
                   end=item.end,
                   message=item.message.text,
                   recorded_at=item.recorded_at,
                   log_level=item.log_level,
                   marked=item.marked,
                   called_by=item.called_by,
                   logged_from=item.logged_from)

    @classmethod
    def from_model_dict(cls, model_dict: dict[str, Any], foreign_key_cache: "ForeignKeyCache", log_file: "LogFile" = None) -> "BaseRecord":

        if log_file is not None:
            model_dict['log_file'] = log_file

        return cls(record_id=model_dict["id"],
                   log_file=model_dict["log_file"],
                   origin=foreign_key_cache.get_origin_by_id(model_dict["origin"]),
                   start=model_dict['start'],
                   end=model_dict["end"],
                   message=model_dict["text"],
                   recorded_at=model_dict["recorded_at"],
                   log_level=foreign_key_cache.get_log_level_by_id(model_dict["log_level"]),
                   marked=model_dict["marked"],
                   called_by=foreign_key_cache.get_arma_file_by_id(model_dict["called_by"]),
                   logged_from=foreign_key_cache.get_arma_file_by_id(model_dict["logged_from"]))

    def __getattr__(self, name: str):
        if name == "id":
            return self.record_id
        if name == "record_class":
            return self.__class__
        if name == "server":
            return Server.get_by_id_cached(self.log_file.server_id)
        try:
            return super().__getattr__(name)
        except AttributeError:
            pass
        raise AttributeError(f"{self.__class__.__name__!r} does not have an attribute {name!r}")

    @property
    def pretty_name(self) -> str:
        return str(self)

    def __str__(self) -> str:
        return f"{self.origin}-Record at {self.pretty_recorded_at}"

    @classmethod
    def reset_colors(cls) -> None:
        log.warning("The method 'reset_colors' of the class %r is deprecated and does nothing.", cls)

    @property
    def single_line_message(self) -> str:
        pretty_message_lines = self.get_formated_message(MessageFormat.PRETTY).splitlines()
        if len(pretty_message_lines) > 1:
            msg = pretty_message_lines[0] + '...'
        else:
            msg = pretty_message_lines[0]
        return msg

    def __repr__(self) -> str:
        """
        Basic Repr
        !REPLACE!
        """
        return f'{self.__class__.__name__}'


# region[Main_Exec]
if __name__ == '__main__':
    pass

# endregion[Main_Exec]
