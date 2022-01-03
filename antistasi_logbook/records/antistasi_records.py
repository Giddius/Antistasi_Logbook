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
from antistasi_logbook.records.base_record import BASE_SLOTS, BaseRecord, RecordFamily, MessageTypus
from antistasi_logbook.utilities.parsing_misc import parse_text_array
from antistasi_logbook.records.abstract_record import RecordFamily, MessageFormat

# * Gid Imports ----------------------------------------------------------------------------------------->
from gidapptools import get_logger
from gidapptools.general_helper.enums import MiscEnum
from gidapptools.general_helper.color.color_item import Color, RGBColor

if TYPE_CHECKING:
    # * Third Party Imports --------------------------------------------------------------------------------->
    from antistasi_logbook.parsing.parser import RawRecord
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

ALL_ANTISTASI_RECORD_CLASSES: set[type[BaseRecord]] = set()


class BaseAntistasiRecord(BaseRecord):
    ___record_family___ = RecordFamily.ANTISTASI
    ___specificity___ = 1
    ___has_multiline_message___ = False
    _background_qcolor: Union["QColor", MiscEnum] = MiscEnum.NOTHING
    __slots__ = tuple(BASE_SLOTS)

    def get_background_color(self):
        return Color.get_color_by_name("White").with_alpha(0.01).qcolor

    @classmethod
    def check(cls, raw_record: "RawRecord") -> bool:
        return True


ALL_ANTISTASI_RECORD_CLASSES.add(BaseAntistasiRecord)


class PerformanceRecord(BaseAntistasiRecord):
    ___record_family___ = RecordFamily.ANTISTASI
    ___specificity___ = 10
    ___has_multiline_message___ = True
    performance_regex = re.compile(r"(?P<name>\w+\s?\w*)(?:\:\s?)(?P<value>\d[\d\.]*)")
    _background_qcolor: Union["QColor", MiscEnum] = MiscEnum.NOTHING
    __slots__ = tuple(BASE_SLOTS + ["_stats"])

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._stats: dict[str, Union[float, int]] = None

    def get_background_color(self):
        return Color.get_color_by_name("LightSteelBlue").with_alpha(0.5).qcolor

    @property
    def stats(self) -> dict[str, Union[int, float]]:
        if self._stats is None:
            self._stats = self._get_stats()
        return self._stats

    def _get_stats(self) -> dict[str, Union[int, float]]:
        data = {item.group('name'): item.group('value') for item in self.performance_regex.finditer(self.message)}
        return {k: float(v) if '.' in v else int(v) for k, v in data.items()} | {"timestamp": self.recorded_at}

    def get_formated_message(self, msg_format: "MessageFormat" = MessageFormat.PRETTY) -> str:
        if msg_format is MessageFormat.PRETTY:
            _out = ["Performance Stats", "-" * 10]
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
    _background_qcolor: Union["QColor", MiscEnum] = MiscEnum.NOTHING
    __slots__ = tuple(BASE_SLOTS)

    def get_background_color(self):
        return Color.get_color_by_name("LightGreen").with_alpha(0.5).qcolor

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
    _background_qcolor: Union["QColor", MiscEnum] = MiscEnum.NOTHING
    __slots__ = tuple(BASE_SLOTS + ["_punishment_type"])

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._punishment_type: str = None

    def get_background_color(self):
        return Color.get_color_by_name("OliveDrab").with_alpha(0.5).qcolor

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
    _background_qcolor: Union["QColor", MiscEnum] = MiscEnum.NOTHING
    msg_start_regex = re.compile(r"(?P<category>[a-zA-Z]+)\_preference")

    __slots__ = tuple(BASE_SLOTS + ["category", "_array_data"])

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.category = self.msg_start_regex.match(self.message.lstrip()).group("category")
        self._array_data: list[list[Any]] = None

    def get_background_color(self):
        return Color.get_color_by_name("Peru").with_alpha(0.5).qcolor

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
            return f"{self.category}_preference\n" + pp.fmt(self.array_data).replace("'", '"')
        return super().get_formated_message(msg_format=format)


ALL_ANTISTASI_RECORD_CLASSES.add(UpdatePreferenceRecord)


class CreateConvoyInputRecord(BaseAntistasiRecord):
    ___record_family___ = RecordFamily.ANTISTASI
    ___specificity___ = 20
    ___has_multiline_message___ = True
    _background_qcolor: Union["QColor", MiscEnum] = MiscEnum.NOTHING
    __slots__ = tuple(BASE_SLOTS + ["_array_data"])

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._array_data: list[list[Any]] = None

    def get_background_color(self):
        return Color.get_color_by_name("Wheat").with_alpha(0.5).qcolor

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
    _background_qcolor: Union["QColor", MiscEnum] = MiscEnum.NOTHING
    __slots__ = tuple(BASE_SLOTS + ["_kv_data"])

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._kv_data: dict[str, Any] = None

    def get_background_color(self):
        return Color.get_color_by_name("PeachPuff").with_alpha(0.5).qcolor

    @property
    def kv_data(self) -> dict[str, Any]:
        if self._kv_data is None:
            array_txt = self.message[self.message.find('['):]
            self._kv_data = parse_text_array(array_txt)
            if self._kv_data == "ERROR":
                self._kv_data = {self.message: "PARSING ERROR"}
            else:
                self._kv_data = {k: v for k, v in self._kv_data}
        return self._kv_data

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
            txt_lines = ["Saving Params: ", '-' * 10]
            for k, v in self.kv_data.items():
                key = k.strip('"').strip("'")
                value = v
                if v == "true":
                    value = "Yes"
                elif v == "false":
                    value = "No"
                new_line = f"◘ {key:<40}{value:>10}"
                txt_lines += [new_line, '┄' * int(len(new_line) * 0.9)]
            return '\n'.join(txt_lines)
        return super().get_formated_message(format=format)


ALL_ANTISTASI_RECORD_CLASSES.add(SaveParametersRecord)


class ResourceCheckRecord(BaseAntistasiRecord):
    ___specificity___ = 20
    ___has_multiline_message___ = True
    side_regex = re.compile(r"(?P<side>\w+)\sarsenal")
    _background_qcolor: Union["QColor", MiscEnum] = MiscEnum.NOTHING
    __slots__ = tuple(BASE_SLOTS + ["_array_data", "_stats", "side"])

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._array_data: list[list[Any]] = None
        self._stats: dict[str, float] = None
        self.side = self.side_regex.match(self.message).group("side")

    def get_background_color(self):
        return Color.get_color_by_name("DarkSalmon").with_alpha(0.5).qcolor

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
            _out = [f"{self.side} arsenal", "-" * 10]
            for k, v in self.stats.items():
                try:
                    _full_num, _after_comma = str(v).split('.')
                    _comma = "."
                except ValueError:
                    _full_num = str(v)
                    _comma = ""
                    _after_comma = ""
                _out.append(f"{k:<50}{_full_num:>25}{_comma}{_after_comma}")
            return '\n'.join(_out).strip()
        return super().get_formated_message(msg_format=format)


ALL_ANTISTASI_RECORD_CLASSES.add(ResourceCheckRecord)


class FreeSpawnPositionsRecord(BaseAntistasiRecord):
    ___specificity___ = 20
    ___has_multiline_message___ = True
    place_regex = re.compile(r"Spawn places for (?P<place>\w+)", re.IGNORECASE)
    _background_qcolor: Union["QColor", MiscEnum] = MiscEnum.NOTHING
    __slots__ = tuple(BASE_SLOTS + ["_array_data", "_stats", "place"])

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._array_data: list[list[Any]] = None
        self.place = self.place_regex.search(self.message).group("place")

    def get_background_color(self):
        return Color.get_color_by_name("pink").with_alpha(0.5).qcolor

    @property
    def array_data(self) -> list[list[Any]]:
        if self._array_data is None:
            array_txt = self.message[self.message.find('['):]
            self._array_data = parse_text_array(array_txt)
            if self._array_data == "ERROR":
                self._array_data = [self.message]
        return self._array_data

    def get_formated_message(self, msg_format: "MessageFormat" = MessageFormat.PRETTY) -> str:
        if msg_format is MessageFormat.PRETTY:
            txt = f"Spawn places for {self.place}"
            array_data_text_lines = pp.fmt(self.array_data).replace("'", '"').replace('"false"', 'false').replace('"true"', 'true').splitlines()
            txt_len = len(txt)
            txt += array_data_text_lines[0] + '\n'
            for line in array_data_text_lines[1:]:
                txt += ' ' * txt_len + line + '\n'
            return txt
        return super().get_formated_message(format=format)

    @classmethod
    def check(cls, raw_record: "RawRecord") -> bool:
        logged_from = raw_record.parsed_data.get("logged_from")

        if logged_from is None:
            return
        if logged_from in {"freeSpawnPositions"} and raw_record.parsed_data.get("message").startswith("spawn places for") and '[' in raw_record.parsed_data.get("message") and ']' in raw_record.parsed_data.get("message"):
            return True
        return False


ALL_ANTISTASI_RECORD_CLASSES.add(FreeSpawnPositionsRecord)


class SelectReinfUnitsRecord(BaseAntistasiRecord):
    ___specificity___ = 20
    ___has_multiline_message___ = True
    parse_regex = re.compile(r"units selected vehicle is (?P<unit>\w+) crew is (?P<crew>.*(?= cargo is)) cargo is (?P<cargo>.*)", re.IGNORECASE)
    _background_qcolor: Union["QColor", MiscEnum] = MiscEnum.NOTHING
    __slots__ = tuple(BASE_SLOTS + ["crew_array_data", "cargo_array_data", "unit", "crew_raw_text", "cargo_raw_text"])

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.unit: str = None
        self.crew_raw_text: str = None
        self.cargo_raw_text: str = None
        self.crew_array_data: list[list[Any]] = None
        self.cargo_array_data: list[list[Any]] = None
        self.parse_it()

    def get_background_color(self):
        return Color.get_color_by_name("Gold").with_alpha(0.5).qcolor

    def parse_it(self):
        match = self.parse_regex.search(self.message)
        if match:
            self.unit = match.group("unit")
            self.crew_raw_text = match.group("crew")
            self.cargo_raw_text = match.group("cargo")
            self.crew_array_data = parse_text_array(self.crew_raw_text)
            self.cargo_array_data = parse_text_array(self.cargo_raw_text)
        else:
            log.critical(self.message)

    def get_formated_message(self, msg_format: "MessageFormat" = MessageFormat.PRETTY) -> str:
        if msg_format is MessageFormat.PRETTY:
            crew_text = pp.fmt(self.crew_array_data).replace("'", '"')
            cargo_text = pp.fmt(self.cargo_array_data).replace("'", '"')
            return f"units selected vehicle is\n\"{self.unit}\"\n\ncrew is\n{crew_text}\n\ncargo is\n{cargo_text}"
        return super().get_formated_message(format=format)

    @classmethod
    def check(cls, raw_record: "RawRecord") -> bool:
        logged_from = raw_record.parsed_data.get("logged_from")

        if logged_from is None:
            return
        if logged_from in {"selectReinfUnits"} and '[' in raw_record.parsed_data.get("message") and ']' in raw_record.parsed_data.get("message"):
            return True
        return False


ALL_ANTISTASI_RECORD_CLASSES.add(SelectReinfUnitsRecord)
# region[Main_Exec]


if __name__ == '__main__':
    pass

# endregion[Main_Exec]
