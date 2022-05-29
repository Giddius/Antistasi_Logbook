"""
WiP.

Soon.
"""

# region [Imports]

# * Standard Library Imports ---------------------------------------------------------------------------->
import re
from typing import TYPE_CHECKING, Union, Iterable, Any
from pathlib import Path

# * Third Party Imports --------------------------------------------------------------------------------->
import pp

# * Gid Imports ----------------------------------------------------------------------------------------->
from gidapptools import get_logger
from gidapptools.general_helper.enums import MiscEnum
from gidapptools.general_helper.string_helper import fix_multiple_quotes, escape_doubled_quotes

# * Local Imports --------------------------------------------------------------------------------------->
from antistasi_logbook.records.base_record import BaseRecord, RecordFamily, MessageFormat
from antistasi_logbook.utilities.parsing_misc import parse_text_array


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

THIS_FILE_DIR = Path(__file__).parent.absolute()
log = get_logger(__name__)
# endregion[Constants]

ALL_GENERIC_RECORD_CLASSES: set[type[BaseRecord]] = set()
# "[ASU] Perf-profiling : FPS=11.1111 nbPlayers=28 nbAIs=421"


class PerfProfilingRecord(BaseRecord):

    ___record_family___ = RecordFamily.GENERIC
    ___specificity___ = 10
    performance_regex = re.compile(r"(?P<name>(FPS)|(nbPlayers)|(nbAIs))\=(?P<value>[\d\.]+)")

    __slots__ = ("_stats",)

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._stats: dict[str, Union[float, int]] = None

    @property
    def stats(self) -> dict[str, Union[int, float]]:
        if self._stats is None:
            self._stats = self.parse(self.message)
        return self._stats

    @classmethod
    def parse(cls, message: str) -> dict[str, Union[int, float]]:
        data = {item.group('name'): item.group('value') for item in cls.performance_regex.finditer(message)}
        data = {k: float(v) if '.' in v else int(v) for k, v in data.items()}
        cleaned_data = {"ServerFPS": data["FPS"], "Players": data["nbPlayers"]}

        return cleaned_data

    @classmethod
    def check(cls, log_record: "LogRecord") -> bool:
        if log_record.message.strip().startswith("[ASU] Perf-profiling"):
            return True

        return False


ALL_GENERIC_RECORD_CLASSES.add(PerfProfilingRecord)


class TFEInfoSettings(BaseRecord):
    ___record_family___ = RecordFamily.GENERIC
    ___specificity___ = 10

    extra_detail_views: Iterable[str] = ("array_data",)
    __slots__ = ("_array_data",)

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

    extra_detail_views: Iterable[str] = ("player_name", "player_id", "array_data")
    __slots__ = ("_array_data",
                 "_player_name",
                 "_player_id")

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._array_data: list = None
        self._player_name: str = None
        self._player_id: str = None

    @property
    def array_data(self) -> list:
        if self._array_data is None:
            self._collect_values()
        return self._array_data

    @property
    def player_name(self) -> str:
        if self._player_name is None:
            self._collect_values()
        return self._player_name

    @property
    def player_id(self) -> str:
        if self._player_id is None:
            self._collect_values()
        return self._player_id

    def _collect_values(self) -> None:
        data = self.parse(self.message)
        self._array_data = data["array_data"]
        self._player_name = data["player_name"]
        self._player_id = data["player_id"]

    @classmethod
    def parse(cls, message: str) -> dict[str, Any]:
        _out = {"player_name": None,
                "player_id": None,
                "array_data": None}

        data_array_text = message.removeprefix("[TFE] Info: Player disconnected:").strip()
        _, player_id, player_name, *rest = data_array_text.strip("[]").split(",")
        _out["player_name"] = player_name.strip('" ')
        _out["player_id"] = player_id.strip('" ')

        array_data = parse_text_array(escape_doubled_quotes(fix_multiple_quotes(data_array_text, 2)))
        if array_data is MiscEnum.ERROR:
            array_data = ["PARSING ERROR"]
        _out["array_data"] = array_data
        return _out

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

    __slots__ = ("_array_data",
                 "_player_name",
                 "_player_id")
    extra_detail_views: Iterable[str] = ("player_name", "player_id", "array_data")

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._array_data: list = None
        self._player_name: str = None
        self._player_id: str = None

    @property
    def array_data(self) -> list:
        if self._array_data is None:
            self._collect_values()
        return self._array_data

    @property
    def player_name(self) -> str:
        if self._player_name is None:
            self._collect_values()
        return self._player_name

    @property
    def player_id(self) -> str:
        if self._player_id is None:
            self._collect_values()
        return self._player_id

    def _collect_values(self) -> None:
        data = self.parse(self.message)
        self._array_data = data["array_data"]
        self._player_name = data["player_name"]
        self._player_id = data["player_id"]

    @classmethod
    def parse(cls, message: str) -> dict[str, Any]:
        _out = {"player_name": None,
                "player_id": None,
                "array_data": None}

        data_array_text = message.removeprefix("[TFE] Info: Player connected:").strip()
        _, player_id, player_name, *rest = data_array_text.strip("[]").split(",")
        _out["player_name"] = player_name.strip('" ')
        _out["player_id"] = player_id.strip('" ')

        array_data = parse_text_array(escape_doubled_quotes(fix_multiple_quotes(data_array_text, 2)))
        if array_data is MiscEnum.ERROR:
            array_data = ["PARSING ERROR"]
        _out["array_data"] = array_data
        return _out

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


class SendTfarRadioRequestResponseEvent(BaseRecord):
    ___record_family___ = RecordFamily.GENERIC
    ___specificity___ = 10
    parse_regex = re.compile(r"\[(?P<number_1>\d+)\]\s*(?P<number_2>[\d\.]+)")

    __slots__ = ("_number_1",
                 "_number_2")
    extra_detail_views: Iterable[str] = ("number_1", "number_2")

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._number_1: int = None
        self._number_2: float = None

    @property
    def number_1(self) -> int:
        if self._number_1 is None:
            data = self.parse(self.message)
            self._number_1 = data.get("number_1")
            self._number_2 = data.get("number_2")
        return self._number_1

    @property
    def number_2(self) -> float:
        if self._number_2 is None:
            data = self.parse(self.message)
            self._number_1 = data["number_1"]
            self._number_2 = data["number_2"]
        return self._number_2

    @classmethod
    def parse(cls, message: str) -> dict[str, Any]:
        if match := cls.parse_regex.search(message):
            number_1 = int(match.group("number_1"))
            number_2 = float(match.group("number_2"))
            return {"number_1": number_1, "number_2": number_2}
        return super().parse(message)

    @classmethod
    def check(cls, log_record: "LogRecord") -> bool:
        if log_record.message.strip().startswith("Send TFAR_RadioRequestResponseEvent"):
            return True

        return False


ALL_GENERIC_RECORD_CLASSES.add(SendTfarRadioRequestResponseEvent)


# region[Main_Exec]


if __name__ == '__main__':
    pass

# endregion[Main_Exec]
