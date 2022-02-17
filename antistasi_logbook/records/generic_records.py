"""
WiP.

Soon.
"""

# region [Imports]

# * Standard Library Imports ---------------------------------------------------------------------------->
import re
from typing import TYPE_CHECKING, Union, Iterable
from pathlib import Path

# * Third Party Imports --------------------------------------------------------------------------------->
import pp

# * Gid Imports ----------------------------------------------------------------------------------------->
from gidapptools import get_logger
from gidapptools.general_helper.enums import MiscEnum
from gidapptools.general_helper.string_helper import fix_multiple_quotes
from gidapptools.general_helper.color.color_item import Color

# * Local Imports --------------------------------------------------------------------------------------->
from antistasi_logbook.records.base_record import BaseRecord, RecordFamily
from antistasi_logbook.utilities.parsing_misc import parse_text_array
from antistasi_logbook.records.abstract_record import RecordFamily, MessageFormat

# * Type-Checking Imports --------------------------------------------------------------------------------->
if TYPE_CHECKING:
    from PySide6.QtGui import QColor

    from antistasi_logbook.storage.models.models import LogRecord

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

ALL_GENERIC_RECORD_CLASSES: set[type[BaseRecord]] = set()
# "[ASU] Perf-profiling : FPS=11.1111 nbPlayers=28 nbAIs=421"


class PerfProfilingRecord(BaseRecord):
    ___record_family___ = RecordFamily.GENERIC
    ___specificity___ = 10
    _background_qcolor: Union["QColor", MiscEnum] = MiscEnum.NOTHING
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
                 "qt_attributes",
                 "pretty_attribute_cache")

    @classmethod
    def check(cls, log_record: "LogRecord") -> bool:
        if log_record.message.strip().startswith("[ASU] Perf-profiling"):
            return True

        return False


ALL_GENERIC_RECORD_CLASSES.add(PerfProfilingRecord)


class TFEInfoSettings(BaseRecord):
    ___record_family___ = RecordFamily.GENERIC
    ___specificity___ = 10
    _background_qcolor: Union["QColor", MiscEnum] = MiscEnum.NOTHING
    extra_detail_views: Iterable[str] = ("array_data",)
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
                 "qt_attributes",
                 "pretty_attribute_cache",
                 "_array_data")

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._array_data = None

    @property
    def array_data(self):
        if self._array_data is None:
            clean_message = self.message.replace('\n', ' ').replace('\\n', ' ').replace('""', '"')
            clean_message = re.sub(r"\s{2,}", " ", clean_message)

            self._array_data = parse_text_array(clean_message[clean_message.find("[", 5):])
        return self._array_data

    def get_formated_message(self, msg_format: "MessageFormat" = MessageFormat.PRETTY) -> str:
        if msg_format is MessageFormat.PRETTY:
            text = self.message[:self.message.find('[', 5) - 1] + '\n'
            text += pp.fmt(self.array_data).replace("'", '"')
            return text
        return super().get_formated_message(msg_format=msg_format)

    @classmethod
    def check(cls, log_record: "LogRecord") -> bool:
        if log_record.message.startswith("[TFE] Info: Settings:"):
            return True

        return False


ALL_GENERIC_RECORD_CLASSES.add(TFEInfoSettings)


class PlayerDisconnected(BaseRecord):
    ___record_family___ = RecordFamily.GENERIC
    ___specificity___ = 10
    _background_qcolor: Union["QColor", MiscEnum] = MiscEnum.NOTHING
    extra_detail_views: Iterable[str] = ("player_name", "player_id", "array_data")
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
                 "qt_attributes",
                 "pretty_attribute_cache",
                 "array_data",
                 "player_name",
                 "player_id")

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.array_data: list = None
        self.player_name: str = None
        self.player_id: str = None
        self.parse_it()

    def parse_it(self):

        data_array_text = self.message.removeprefix("[TFE] Info: Player disconnected:").strip()
        _, player_id, player_name, *rest = data_array_text.strip("[]").split(",")
        self.player_name = player_name.strip('" ')
        self.player_id = player_id.strip('" ')

        self.array_data = parse_text_array(fix_multiple_quotes(data_array_text))

    def get_formated_message(self, msg_format: "MessageFormat" = MessageFormat.PRETTY) -> str:
        if msg_format is MessageFormat.PRETTY:
            text = "[TFE] Info: Player disconnected: "
            text += pp.fmt(self.array_data).replace("'", '"')
            return text

        return super().get_formated_message(msg_format=msg_format)

    @classmethod
    def check(cls, log_record: "LogRecord") -> bool:
        if log_record.message.startswith("[TFE] Info: Player disconnected:"):
            return True

        return False


ALL_GENERIC_RECORD_CLASSES.add(PlayerDisconnected)


class PlayerConnected(BaseRecord):
    ___record_family___ = RecordFamily.GENERIC
    ___specificity___ = 10
    _background_qcolor: Union["QColor", MiscEnum] = MiscEnum.NOTHING
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
                 "qt_attributes",
                 "pretty_attribute_cache",
                 "array_data",
                 "player_name",
                 "player_id")
    extra_detail_views: Iterable[str] = ("player_name", "player_id", "array_data")

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.array_data: list = None
        self.player_name: str = None
        self.player_id: str = None
        self.parse_it()

    def parse_it(self):

        data_array_text = self.message.removeprefix("[TFE] Info: Player connected:").strip()
        _, player_id, player_name, *rest = data_array_text.strip("[]").split(",")
        self.player_name = player_name.strip('" ')
        self.player_id = player_id.strip('" ')

        self.array_data = parse_text_array(fix_multiple_quotes(data_array_text))

    def get_formated_message(self, msg_format: "MessageFormat" = MessageFormat.PRETTY) -> str:
        if msg_format is MessageFormat.PRETTY:
            text = "[TFE] Info: Player connected: "
            text += pp.fmt(self.array_data).replace("'", '"')
            return text

        return super().get_formated_message(msg_format=msg_format)

    @classmethod
    def check(cls, log_record: "LogRecord") -> bool:
        if log_record.message.startswith("[TFE] Info: Player connected:"):
            return True

        return False


ALL_GENERIC_RECORD_CLASSES.add(PlayerConnected)

# region[Main_Exec]


if __name__ == '__main__':
    pass

# endregion[Main_Exec]
