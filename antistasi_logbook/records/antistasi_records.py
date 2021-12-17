"""
WiP.

Soon.
"""

# region [Imports]

# * Standard Library Imports ---------------------------------------------------------------------------->
import re
from typing import TYPE_CHECKING, Any, Union, Optional
from pathlib import Path

# * Third Party Imports --------------------------------------------------------------------------------->
import pp
from antistasi_logbook.records.base_record import BASE_SLOTS, BaseRecord, RecordFamily
from antistasi_logbook.utilities.parsing_misc import parse_text_array
from antistasi_logbook.records.abstract_record import RecordFamily, MessageFormat

# * Gid Imports ----------------------------------------------------------------------------------------->
from gidapptools import get_logger
from gidapptools.general_helper.enums import MiscEnum
from gidapptools.general_helper.color.color_item import Color, RGBColor

if TYPE_CHECKING:
    # * Third Party Imports --------------------------------------------------------------------------------->
    from antistasi_logbook.parsing.parser import RawRecord

# endregion[Imports]

# region [TODO]


# endregion [TODO]

# region [Logging]


# endregion[Logging]

# region [Constants]

THIS_FILE_DIR = Path(__file__).parent.absolute()
log = get_logger(__name__)
# endregion[Constants]

ALL_ANTISTASI_RECORD_CLASSES: set[type[BaseRecord]] = set()
# "[ASU] Perf-profiling : FPS=11.1111 nbPlayers=28 nbAIs=421"


class PerfProfilingRecord(BaseRecord):
    ___record_family___ = RecordFamily.GENERIC
    ___specificity___ = 10
    __slots__ = tuple(BASE_SLOTS)

    @classmethod
    def check(cls, raw_record: "RawRecord") -> bool:
        if raw_record.parsed_data.get("message").strip().startswith("[ASU] Perf-profiling"):
            return True

        return False

    @property
    def background_color(self) -> Optional[RGBColor]:
        if self.qt_attributes.background_color is MiscEnum.NOTHING:
            self.qt_attributes.background_color = Color.get_color_by_name("green").with_alpha(0.75).qcolor
        return self.qt_attributes.background_color


ALL_ANTISTASI_RECORD_CLASSES.add(PerfProfilingRecord)


class BaseAntistasiRecord(BaseRecord):
    ___record_family___ = RecordFamily.ANTISTASI
    ___specificity___ = 1
    ___has_multiline_message___ = False
    __slots__ = tuple(BASE_SLOTS)

    @property
    def background_color(self) -> Optional[RGBColor]:
        if self.qt_attributes.background_color is MiscEnum.NOTHING:
            self.qt_attributes.background_color = Color.get_color_by_name("White").with_alpha(0.01).qcolor
        return self.qt_attributes.background_color

    @classmethod
    def check(cls, raw_record: "RawRecord") -> bool:
        return True


ALL_ANTISTASI_RECORD_CLASSES.add(BaseAntistasiRecord)


class PerformanceRecord(BaseAntistasiRecord):
    ___record_family___ = RecordFamily.ANTISTASI
    ___specificity___ = 10
    ___has_multiline_message___ = True
    performance_regex = re.compile(r"(?P<name>\w+\s?\w*)(?:\:\s?)(?P<value>\d[\d\.]*)")
    __slots__ = tuple(BASE_SLOTS + ["_stats"])

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._stats: dict[str, Union[float, int]] = None

    @property
    def background_color(self) -> Optional[RGBColor]:
        if self.qt_attributes.background_color is MiscEnum.NOTHING:
            self.qt_attributes.background_color = Color.get_color_by_name("LightSteelBlue").with_alpha(0.25).qcolor
        return self.qt_attributes.background_color

    @property
    def stats(self) -> dict[str, Union[int, float]]:
        if self._stats is None:
            self._stats = self._get_stats()
        return self._stats

    def _get_stats(self) -> dict[str, Union[int, float]]:
        data = {item.group('name'): item.group('value') for item in self.performance_regex.finditer(self.message)}
        return {k: float(v) if '.' in v else int(v) for k, v in data.items()}

    def get_formated_message(self, msg_format: "MessageFormat" = MessageFormat.PRETTY) -> str:
        if msg_format is MessageFormat.PRETTY:
            _out = []
            for k, v in self.stats.items():
                try:
                    _full_num, _after_comma = str(v).split('.')
                    _comma = "."
                except ValueError:
                    _full_num = str(v)
                    _comma = ""
                    _after_comma = ""
                _out.append(f"{k:<25}{_full_num:>25}{_comma}{_after_comma}")
            return '\n'.join(_out).strip()
        return super().get_formated_message(msg_format=format)

    @classmethod
    def check(cls, raw_record: "RawRecord") -> bool:
        logged_from = raw_record.parsed_data.get("logged_from")

        if logged_from is None:
            return False

        if logged_from == "logPerformance":

            return True

        return False


ALL_ANTISTASI_RECORD_CLASSES.add(PerformanceRecord)


class IsNewCampaignRecord(BaseAntistasiRecord):
    ___record_family___ = RecordFamily.ANTISTASI
    ___specificity___ = 20
    __slots__ = tuple(BASE_SLOTS)

    @property
    def background_color(self) -> Optional[RGBColor]:
        if self.qt_attributes.background_color is MiscEnum.NOTHING:
            self.qt_attributes.background_color = Color.get_color_by_name("LightGreen").with_alpha(0.25).qcolor
        return self.qt_attributes.background_color

    @classmethod
    def check(cls, raw_record: "RawRecord") -> bool:
        logged_from = raw_record.parsed_data.get("logged_from")

        if logged_from is None:
            return False
        if logged_from == "initServer" and "Creating new campaign with ID" in raw_record.parsed_data.get("message"):
            return True

        return False


ALL_ANTISTASI_RECORD_CLASSES.add(IsNewCampaignRecord)


class FFPunishmentRecord(BaseAntistasiRecord):
    ___record_family___ = RecordFamily.ANTISTASI
    ___specificity___ = 10
    punishment_type_regex = re.compile(r"(?P<punishment_type>[A-Z]+)")
    __slots__ = tuple(BASE_SLOTS + ["_punishment_type"])

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._punishment_type: str = None

    @property
    def background_color(self) -> Optional[RGBColor]:
        if self.qt_attributes.background_color is MiscEnum.NOTHING:
            self.qt_attributes.background_color = Color.get_color_by_name("OliveDrab").with_alpha(0.25).qcolor
        return self.qt_attributes.background_color

    @property
    def punishment_type(self) -> str:
        if self._punishment_type is None:
            self._punishment_type = self.punishment_type_regex.search(self.message).group("punishment_type")
        return self._punishment_type

    @classmethod
    def check(cls, raw_record: "RawRecord") -> bool:
        logged_from = raw_record.parsed_data.get("logged_from")

        if logged_from is None:
            return False
        if logged_from in {"punishment_FF", "punishment"}:
            return True

        return False


ALL_ANTISTASI_RECORD_CLASSES.add(FFPunishmentRecord)


class UpdatePreferenceRecord(BaseAntistasiRecord):
    ___record_family___ = RecordFamily.ANTISTASI
    ___specificity___ = 20
    ___has_multiline_message___ = True

    msg_start_regex = re.compile(r"(?P<category>[a-zA-Z]+)\_preference")

    __slots__ = tuple(BASE_SLOTS + ["category", "_array_data"])

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.category = self.msg_start_regex.match(self.message.lstrip()).group("category")
        self._array_data: list[list[Any]] = None

    @property
    def background_color(self) -> Optional[RGBColor]:
        if self.qt_attributes.background_color is MiscEnum.NOTHING:
            self.qt_attributes.background_color = Color.get_color_by_name("Peru").with_alpha(0.25).qcolor
        return self.qt_attributes.background_color

    @property
    def array_data(self) -> list[list[Any]]:
        if self._array_data is None:
            self._array_data = parse_text_array(self.msg_start_regex.sub('', self.message).strip())
        return self._array_data

    @classmethod
    def check(cls, raw_record: "RawRecord") -> bool:
        logged_from = raw_record.parsed_data.get("logged_from")

        if logged_from is None:
            return False
        if logged_from in {"updatePreference"} and cls.msg_start_regex.match(raw_record.parsed_data.get("message").lstrip()):
            return True
        return False

    def get_formated_message(self, msg_format: "MessageFormat" = MessageFormat.PRETTY) -> str:
        if msg_format is MessageFormat.PRETTY:
            return f"{self.category}_preference\n" + pp.fmt(self.array_data, indent=4)
        return super().get_formated_message(msg_format=format)


ALL_ANTISTASI_RECORD_CLASSES.add(UpdatePreferenceRecord)


class CreateConvoyInputRecord(BaseAntistasiRecord):
    ___record_family___ = RecordFamily.ANTISTASI
    ___specificity___ = 20
    ___has_multiline_message___ = True
    __slots__ = tuple(BASE_SLOTS + ["_array_data"])

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._array_data: list[list[Any]] = None

    @property
    def background_color(self) -> Optional[RGBColor]:
        if self.qt_attributes.background_color is MiscEnum.NOTHING:
            self.qt_attributes.background_color = Color.get_color_by_name("Wheat").with_alpha(0.25).qcolor
        return self.qt_attributes.background_color

    @property
    def array_data(self) -> list[list[Any]]:
        if self._array_data is None:
            array_txt = self.message[self.message.find('['):]
            self._array_data = parse_text_array(array_txt)
        return self._array_data

    @classmethod
    def check(cls, raw_record: "RawRecord") -> bool:
        logged_from = raw_record.parsed_data.get("logged_from")

        if logged_from is None:
            return
        if logged_from in {"createConvoy"} and raw_record.parsed_data.get("message").casefold().startswith("input"):
            return True
        return False

    def get_formated_message(self, msg_format: "MessageFormat" = MessageFormat.PRETTY) -> str:
        if msg_format is MessageFormat.PRETTY:
            txt = "Input is "
            array_data_text_lines = pp.fmt(self.array_data).replace("'", '"').replace('"WEST"', 'WEST').replace('"EAST"', 'EAST').splitlines()
            txt_len = len(txt)
            txt += array_data_text_lines[0] + '\n'
            for line in array_data_text_lines[1:]:
                txt += ' ' * txt_len + line + '\n'
            return txt
        return super().get_formated_message(format=format)


ALL_ANTISTASI_RECORD_CLASSES.add(CreateConvoyInputRecord)


class SaveParametersRecord(BaseAntistasiRecord):
    ___specificity___ = 20
    ___has_multiline_message___ = True
    __slots__ = tuple(BASE_SLOTS + ["_array_data"])

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._array_data: list[list[Any]] = None

    @property
    def background_color(self) -> Optional[RGBColor]:
        if self.qt_attributes.background_color is MiscEnum.NOTHING:
            self.qt_attributes.background_color = Color.get_color_by_name("PeachPuff").with_alpha(0.25).qcolor
        return self.qt_attributes.background_color

    @property
    def array_data(self) -> list[list[Any]]:
        if self._array_data is None:
            array_txt = self.message[self.message.find('['):]
            self._array_data = parse_text_array(array_txt)
            if self._array_data == "ERROR":
                self._array_data = [self.message]
        return self._array_data

    @classmethod
    def check(cls, raw_record: "RawRecord") -> bool:
        logged_from = raw_record.parsed_data.get("logged_from")

        if logged_from is None:
            return
        if logged_from in {"saveLoop"} and '[' in raw_record.parsed_data.get("message") and ']' in raw_record.parsed_data.get("message"):
            return True
        return False

    def get_formated_message(self, msg_format: "MessageFormat" = MessageFormat.PRETTY) -> str:
        if msg_format is MessageFormat.PRETTY:
            txt = "Saving Params: "
            array_data_text_lines = pp.fmt(self.array_data).replace("'", '"').replace('"false"', 'false').replace('"true"', 'true').splitlines()
            txt_len = len(txt)
            txt += array_data_text_lines[0] + '\n'
            for line in array_data_text_lines[1:]:
                txt += ' ' * txt_len + line + '\n'
            return txt
        return super().get_formated_message(format=format)


ALL_ANTISTASI_RECORD_CLASSES.add(SaveParametersRecord)


class ResourceCheckRecord(BaseAntistasiRecord):
    ___specificity___ = 20
    ___has_multiline_message___ = True
    side_regex = re.compile(r"(?P<side>\w+)\sarsenal")
    __slots__ = tuple(BASE_SLOTS + ["_array_data", "_stats", "side"])

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._array_data: list[list[Any]] = None
        self._stats: dict[str, float] = None
        self.side = self.side_regex.match(self.message).group("side")

    @property
    def background_color(self) -> Optional[RGBColor]:
        if self.qt_attributes.background_color is MiscEnum.NOTHING:
            self.qt_attributes.background_color = Color.get_color_by_name("DarkSalmon").with_alpha(0.25).qcolor
        return self.qt_attributes.background_color

    @property
    def stats(self) -> dict[str, float]:
        if self._stats is None:
            _ = self.array_data
        return self._stats

    @property
    def array_data(self) -> list[list[Any]]:
        if self._array_data is None:
            array_txt = self.message[self.message.find('['):]
            self._array_data = parse_text_array(array_txt)
            self._stats = {}

            for key, value in self._array_data:
                self._stats[key] = value
        return self._array_data

    @classmethod
    def check(cls, raw_record: "RawRecord") -> bool:
        logged_from = raw_record.parsed_data.get("logged_from")

        if logged_from is None:
            return
        if logged_from in {"economicsAI"} and '[' in raw_record.parsed_data.get("message") and ']' in raw_record.parsed_data.get("message"):
            return True
        return False

    def get_formated_message(self, msg_format: "MessageFormat" = MessageFormat.PRETTY) -> str:
        if msg_format is MessageFormat.PRETTY:
            _out = [f"{self.side} arsenal", "--------------------"]
            for k, v in self.stats.items():
                try:
                    _full_num, _after_comma = str(v).split('.')
                    _comma = "."
                except ValueError:
                    _full_num = str(v)
                    _comma = ""
                    _after_comma = ""
                _out.append(f"{k:<30}{_full_num:>30}{_comma}{_after_comma}")
            return '\n'.join(_out).strip()
        return super().get_formated_message(msg_format=format)


ALL_ANTISTASI_RECORD_CLASSES.add(ResourceCheckRecord)
# region[Main_Exec]


if __name__ == '__main__':
    pass

# endregion[Main_Exec]
