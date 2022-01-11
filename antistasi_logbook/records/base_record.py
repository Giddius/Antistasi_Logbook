"""
WiP.

Soon.
"""

# region [Imports]

# * Standard Library Imports ---------------------------------------------------------------------------->
from typing import TYPE_CHECKING, Any, Union, Optional
from pathlib import Path
from datetime import datetime

# * Third Party Imports --------------------------------------------------------------------------------->
import attr

# * Gid Imports ----------------------------------------------------------------------------------------->
from gidapptools import get_logger
from gidapptools.general_helper.color.color_item import Color

# * Local Imports --------------------------------------------------------------------------------------->
from antistasi_logbook.records.abstract_record import RecordFamily, MessageFormat, AbstractRecord

try:
    from PySide6.QtGui import QColor
    from PySide6.QtCore import QSize
    PYSIDE6_AVAILABLE = True
except ImportError:
    PYSIDE6_AVAILABLE = False
# * Gid Imports ----------------------------------------------------------------------------------------->
from gidapptools.general_helper.enums import MiscEnum
from gidapptools.general_helper.string_helper import shorten_string

# * Type-Checking Imports --------------------------------------------------------------------------------->
if TYPE_CHECKING:
    from antistasi_logbook.storage.database import GidSqliteApswDatabase
    from antistasi_logbook.storage.models.models import LogFile, LogLevel, LogRecord, RecordOrigin, AntstasiFunction
    from antistasi_logbook.parsing.foreign_key_cache import ForeignKeyCache

# endregion[Imports]

# region [TODO]


# endregion [TODO]

# region [Logging]


# endregion[Logging]

# region [Constants]
from gidapptools.general_helper.timing import get_dummy_profile_decorator_in_globals
get_dummy_profile_decorator_in_globals()
THIS_FILE_DIR = Path(__file__).parent.absolute()
log = get_logger(__name__)
# endregion[Constants]


@attr.s(slots=True, auto_attribs=True, auto_detect=True, weakref_slot=True)
class QtAttributes:
    # background_color: "QColor" = attr.ib(default=MiscEnum.NOTHING)
    message_size_hint: "QSize" = attr.ib(default=None)


@attr.s(slots=True, auto_attribs=True, auto_detect=True, weakref_slot=True)
class PrettyAttributeCache:
    pretty_recorded_at: str = attr.ib(default=MiscEnum.NOTHING)
    pretty_log_level: str = attr.ib(default=MiscEnum.NOTHING)
    pretty_message: str = attr.ib(default=MiscEnum.NOTHING)


BASE_SLOTS: list[str] = ["record_id",
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
                         "qt_attributes",
                         "pretty_attribute_cache"]


class BaseRecord(AbstractRecord):
    ___record_family___ = RecordFamily.GENERIC | RecordFamily.ANTISTASI
    ___specificity___ = 0
    foreign_key_cache: "ForeignKeyCache" = None
    _background_qcolor: Union["QColor", MiscEnum] = MiscEnum.NOTHING
    __slots__ = tuple(BASE_SLOTS)

    def __init__(self,
                 record_id: int,
                 log_file: "LogFile",
                 origin: "RecordOrigin",
                 start: int,
                 end: int,
                 message: str,
                 recorded_at: datetime,
                 log_level: "LogLevel",
                 marked: bool,
                 called_by: "AntstasiFunction" = None,
                 logged_from: "AntstasiFunction" = None) -> None:
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
        self.qt_attributes: QtAttributes = QtAttributes()
        self.pretty_attribute_cache: PrettyAttributeCache = PrettyAttributeCache()

    def get_data(self, name: str):
        _out = getattr(self, f"pretty_{name}", MiscEnum.NOTHING)
        if _out is MiscEnum.NOTHING:

            # log.warning("no pretty data for %r, pretty_attribute_cache=%r", name, self.pretty_attribute_cache)

            return getattr(self, name)
        return _out

    @property
    def pretty_message(self) -> str:
        if self.pretty_attribute_cache.pretty_message is MiscEnum.NOTHING:
            self.pretty_attribute_cache.pretty_message = self.get_formated_message(MessageFormat.PRETTY)
        return self.pretty_attribute_cache.pretty_message

    @property
    def pretty_log_level(self) -> Optional[str]:
        if self.pretty_attribute_cache.pretty_log_level is MiscEnum.NOTHING:
            self.pretty_attribute_cache.pretty_log_level = str(self.log_level) if self.log_level.id != 0 else None
        return self.pretty_attribute_cache.pretty_log_level

    @property
    def pretty_recorded_at(self) -> str:
        if self.pretty_attribute_cache.pretty_recorded_at is MiscEnum.NOTHING:
            self.pretty_attribute_cache.pretty_recorded_at = self.log_file.format_datetime(self.recorded_at)
        return self.pretty_attribute_cache.pretty_recorded_at

    @property
    def background_color(self) -> Optional["QColor"]:
        if self._background_qcolor is MiscEnum.NOTHING:
            self._background_qcolor = self.get_background_color()
        return self._background_qcolor

    def get_background_color(self) -> "QColor":
        return Color.get_color_by_name("Gray").with_alpha(0.1).qcolor

    def get_formated_message(self, msg_format: "MessageFormat" = MessageFormat.PRETTY) -> str:
        if msg_format is MessageFormat.SHORT:
            return shorten_string(self.message, max_length=30)

        if msg_format is MessageFormat.ORIGINAL:
            return f"{self.pretty_recorded_at} {self.message}"
        return self.message

    def get_db_item(self, database: "GidSqliteApswDatabase") -> "LogRecord":
        from antistasi_logbook.storage.models.models import LogRecord
        with database:
            return LogRecord.get_by_id(self.record_id)

    @classmethod
    @profile
    def check(cls, log_record: "LogRecord") -> bool:
        return True

    @classmethod
    @profile
    def from_db_item(cls, item: "LogRecord") -> "BaseRecord":
        return cls(record_id=item.id,
                   log_file=item.log_file,
                   origin=item.origin,
                   start=item.start,
                   end=item.end,
                   message=item.message,
                   recorded_at=item.recorded_at,
                   log_level=item.log_level,
                   marked=item.marked,
                   called_by=item.called_by,
                   logged_from=item.logged_from)

    @classmethod
    @profile
    def from_model_dict(cls, model_dict: dict[str, Any], log_file: "LogFile" = None) -> "BaseRecord":

        if log_file is not None:
            model_dict['log_file'] = log_file

        return cls(record_id=model_dict["id"],
                   log_file=model_dict["log_file"],
                   origin=cls.foreign_key_cache.get_origin_by_id(model_dict["origin"]),
                   start=model_dict['start'],
                   end=model_dict["end"],
                   message=model_dict["message"],
                   recorded_at=model_dict["recorded_at"],
                   log_level=cls.foreign_key_cache.get_log_level_by_id(model_dict['log_level']),
                   marked=model_dict["marked"],
                   called_by=cls.foreign_key_cache.get_antistasi_file_by_id(model_dict["called_by"]),
                   logged_from=cls.foreign_key_cache.get_antistasi_file_by_id(model_dict["logged_from"]))

    def __getattr__(self, name: str):
        if name == "id":
            return self.record_id
        if name == "record_class":
            return self.__class__
        raise AttributeError(f"{self!r} does not have an attribute {name!r}")

    def __str__(self) -> str:
        return f"{self.origin}-Record at {self.pretty_recorded_at}"

    @classmethod
    def reset_colors(cls) -> None:
        BaseRecord._background_qcolor = MiscEnum.NOTHING
        for sub_class in BaseRecord.__subclasses__():
            sub_class._background_qcolor = MiscEnum.NOTHING


# region[Main_Exec]
if __name__ == '__main__':
    pass

# endregion[Main_Exec]
