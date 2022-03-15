"""
WiP.

Soon.
"""

# region [Imports]

# * Standard Library Imports ---------------------------------------------------------------------------->
import re
from typing import TYPE_CHECKING, Any, Union
from pathlib import Path

# * Third Party Imports --------------------------------------------------------------------------------->
import pp

# * Gid Imports ----------------------------------------------------------------------------------------->
from gidapptools import get_logger
from gidapptools.general_helper.enums import MiscEnum

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

ALL_ANTISTASI_RECORD_CLASSES: set[type[BaseRecord]] = set()


class BaseAntistasiRecord(BaseRecord):
    ___record_family___ = RecordFamily.ANTISTASI
    ___specificity___ = 1
    ___function___: str = None

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
        return True

    def get_formated_message(self, msg_format: "MessageFormat" = MessageFormat.PRETTY) -> str:
        if msg_format is MessageFormat.ORIGINAL:
            text = f"{self.pretty_recorded_at} | Antistasi | {self.pretty_log_level} | File: {self.logged_from.function_name} | {self.message}"
            if self.called_by is not None:
                text += f" | Called By: {self.called_by.function_name}"
            return text

        return super().get_formated_message(msg_format=msg_format)


ALL_ANTISTASI_RECORD_CLASSES.add(BaseAntistasiRecord)


class PerformanceRecord(BaseAntistasiRecord):
    ___record_family___ = RecordFamily.ANTISTASI
    ___specificity___ = 10
    ___function___ = "A3A_fnc_logPerformance"
    performance_regex = re.compile(r"(?P<name>\w+\s?\w*)(?:\:\s?)(?P<value>\d[\d\.]*)")
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
                 "_stats")

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
        return data

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
        return super().get_formated_message(msg_format=msg_format)

    @classmethod
    def check(cls, log_record: "LogRecord") -> bool:
        return True


ALL_ANTISTASI_RECORD_CLASSES.add(PerformanceRecord)


class IsNewCampaignRecord(BaseAntistasiRecord):
    ___record_family___ = RecordFamily.ANTISTASI
    ___specificity___ = 20
    ___function___ = "A3A_fnc_initServer"
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
        if "Creating new campaign with ID" in log_record.message:
            return True

        return False


ALL_ANTISTASI_RECORD_CLASSES.add(IsNewCampaignRecord)


class FFPunishmentRecord(BaseAntistasiRecord):
    ___record_family___ = RecordFamily.ANTISTASI
    ___specificity___ = 10
    ___function___ = ("A3A_fnc_punishment_FF", "A3A_fnc_punishment")
    punishment_type_regex = re.compile(r"(?P<punishment_type>[A-Z]+)")
    _background_qcolor: Union["QColor", MiscEnum] = MiscEnum.NOTHING
    extra_detail_views = ("punishment_type",)
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
                 "_punishment_type")

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._punishment_type: str = None

    @property
    def punishment_type(self) -> str:
        if self._punishment_type is None:
            self._punishment_type = self.parse(self.message)["punishment_type"]
        return self._punishment_type

    @classmethod
    def parse(cls, message: str) -> dict[str, Any]:
        return cls.punishment_type_regex.search(message).groupdict()

    @classmethod
    def check(cls, log_record: "LogRecord") -> bool:
        return True


ALL_ANTISTASI_RECORD_CLASSES.add(FFPunishmentRecord)


class UpdatePreferenceRecord(BaseAntistasiRecord):
    ___record_family___ = RecordFamily.ANTISTASI
    ___specificity___ = 20
    ___function___ = "A3A_fnc_updatePreference"
    _background_qcolor: Union["QColor", MiscEnum] = MiscEnum.NOTHING
    msg_start_regex = re.compile(r"(?P<category>[a-zA-Z]+)\_preference")
    extra_detail_views = ("category", "array_data")

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
                 "category",
                 "_array_data")

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.category = self.msg_start_regex.match(self.message.lstrip()).group("category")
        self._array_data: list[list[Any]] = None

    @property
    def array_data(self) -> list[list[Any]]:
        if self._array_data is None:
            self._array_data = self.parse(self.message)
        return self._array_data

    @classmethod
    def parse(cls, message: str) -> list[list[Any]]:
        return parse_text_array(cls.msg_start_regex.sub('', message).strip())

    @classmethod
    def check(cls, log_record: "LogRecord") -> bool:
        if cls.msg_start_regex.match(log_record.message.lstrip()) and "[" in log_record.message:
            return True
        return False

    def get_formated_message(self, msg_format: "MessageFormat" = MessageFormat.PRETTY) -> str:
        if msg_format is MessageFormat.PRETTY:
            return f"{self.category}_preference\n" + pp.fmt(self.array_data).replace("'", '"')
        return super().get_formated_message(msg_format=msg_format)


ALL_ANTISTASI_RECORD_CLASSES.add(UpdatePreferenceRecord)


class CreateConvoyInputRecord(BaseAntistasiRecord):
    ___record_family___ = RecordFamily.ANTISTASI
    ___specificity___ = 20
    ___function___ = "A3A_fnc_createConvoy"
    _background_qcolor: Union["QColor", MiscEnum] = MiscEnum.NOTHING
    extra_detail_views = ("array_data",)
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
        self._array_data: list[list[Any]] = None

    @property
    def array_data(self) -> list[list[Any]]:
        if self._array_data is None:
            self._array_data = self.parse(self.message)["array_data"]
        return self._array_data

    @classmethod
    def parse(cls, message: str) -> dict[str, Any]:
        array_txt = message[message.find('['):message.rfind("]") + 1]
        _array_data = parse_text_array(array_txt)
        return {"array_data": _array_data}

    @classmethod
    def check(cls, log_record: "LogRecord") -> bool:
        if log_record.message.casefold().startswith("input"):
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
        return super().get_formated_message(msg_format=msg_format)


ALL_ANTISTASI_RECORD_CLASSES.add(CreateConvoyInputRecord)


class SaveParametersRecord(BaseAntistasiRecord):
    ___specificity___ = 20
    ___function___ = "A3A_fnc_saveLoop"
    _background_qcolor: Union["QColor", MiscEnum] = MiscEnum.NOTHING
    extra_detail_views = ("kv_data",)
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
                 "_kv_data")

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._kv_data: dict[str, Any] = None

    @property
    def kv_data(self) -> dict[str, Any]:
        if self._kv_data is None:
            self._kv_data = self.parse(self.message)
        return self._kv_data

    @classmethod
    def parse(cls, message: str) -> dict[str, Any]:
        array_txt = message[message.find('['):message.rfind("]") + 1]
        _kv_data = parse_text_array(array_txt)
        if _kv_data is MiscEnum.ERROR:
            _kv_data = {"PARSING ERROR": array_txt}
        else:
            _kv_data = {k: v for k, v in _kv_data}
        return _kv_data

    @classmethod
    def check(cls, log_record: "LogRecord") -> bool:
        if '[' in log_record.message and ']' in log_record.message:
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
                new_line = f"◘ {key:<30}{value:>10}"
                txt_lines += [new_line, '┄' * int(len(new_line) * 0.9)]
            return '\n'.join(txt_lines)
        return super().get_formated_message(msg_format=msg_format)


ALL_ANTISTASI_RECORD_CLASSES.add(SaveParametersRecord)


class ResourceCheckRecord(BaseAntistasiRecord):
    ___specificity___ = 20
    ___function___ = "A3A_fnc_economicsAI"
    side_regex = re.compile(r"(?P<side>\w+)\sarsenal")
    _background_qcolor: Union["QColor", MiscEnum] = MiscEnum.NOTHING
    extra_detail_views = ("side", "stats")
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
                 "_stats",
                 "_side")

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._stats: dict[str, float] = None
        self._side: str = None

    @property
    def stats(self) -> dict[str, float]:
        if self._stats is None:
            data = self.parse(self.message)
            self._side = data.pop("side")
            self._stats = data
        return self._stats

    @property
    def side(self) -> str:
        if self._side is None:
            data = self.parse(self.message)
            self._side = data.pop("side")
            self._stats = data
        return self._side

    @classmethod
    def parse(cls, message: str) -> dict[str, Any]:
        side = cls.side_regex.match(message).groupdict()
        array_txt = message[message.find('['):message.rfind("]") + 1]
        _array_data = parse_text_array(array_txt)
        if _array_data is MiscEnum.ERROR:
            return side | {"PARSING ERROR": array_txt}
        else:
            return side | {k: v for k, v in _array_data}

    @classmethod
    def check(cls, log_record: "LogRecord") -> bool:
        if '[' in log_record.message and ']' in log_record.message:
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
        return super().get_formated_message(msg_format=msg_format)


ALL_ANTISTASI_RECORD_CLASSES.add(ResourceCheckRecord)


class FreeSpawnPositionsRecord(BaseAntistasiRecord):
    ___specificity___ = 20
    ___function___ = "A3A_fnc_freeSpawnPositions"
    place_regex = re.compile(r"Spawn places for (?P<place>\w+)", re.IGNORECASE)
    _background_qcolor: Union["QColor", MiscEnum] = MiscEnum.NOTHING
    extra_detail_views = ("place", "array_data")
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
                 "_array_data",
                 "_stats",
                 "_place")

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._array_data: list[list[Any]] = None
        self._place = None

    @property
    def array_data(self) -> list[list[Any]]:
        if self._array_data is None:
            data = self.parse(self.message)
            self._place = data["place"]
            self._array_data = data["array_data"]
        return self._array_data

    @property
    def place(self) -> str:
        if self._place is None:
            data = self.parse(self.message)
            self._place = data["place"]
            self._array_data = data["array_data"]
        return self._place

    @classmethod
    def parse(cls, message: str) -> dict[str, Any]:
        place = cls.place_regex.search(message).groupdict()
        array_txt = message[message.find('['):message.rfind("]") + 1]
        _array_data = parse_text_array(array_txt)
        if _array_data is MiscEnum.ERROR:
            return place | {"array_data": "PARSING ERROR"}
        else:
            return place | {"array_data": _array_data}

    def get_formated_message(self, msg_format: "MessageFormat" = MessageFormat.PRETTY) -> str:
        if msg_format is MessageFormat.PRETTY:
            txt = f"Spawn places for {self.place}"
            array_data_text_lines = pp.fmt(self.array_data).replace("'", '"').replace('"false"', 'false').replace('"true"', 'true').splitlines()
            txt_len = len(txt)
            txt += array_data_text_lines[0] + '\n'
            for line in array_data_text_lines[1:]:
                txt += ' ' * txt_len + line + '\n'
            return txt
        return super().get_formated_message(msg_format=msg_format)

    @classmethod
    def check(cls, log_record: "LogRecord") -> bool:
        if log_record.message.startswith("spawn places for") and '[' in log_record.message and ']' in log_record.message:
            return True
        return False


ALL_ANTISTASI_RECORD_CLASSES.add(FreeSpawnPositionsRecord)


class SelectReinfUnitsRecord(BaseAntistasiRecord):
    ___specificity___ = 20
    ___function___ = "A3A_fnc_selectReinfUnits"
    parse_regex = re.compile(r"units selected vehicle is (?P<unit>\w+) crew is (?P<crew>.*(?= cargo is)) cargo is (?P<cargo>.*)", re.IGNORECASE)
    _background_qcolor: Union["QColor", MiscEnum] = MiscEnum.NOTHING
    extra_detail_views = ("crew_array_data", "cargo_array_data", "unit")
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
                 "_crew_array_data",
                 "_cargo_array_data",
                 "_unit")

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._unit: str = None
        self._crew_array_data: list[list[Any]] = None
        self._cargo_array_data: list[list[Any]] = None

    @property
    def unit(self) -> str:
        if self._unit is None:
            self._get_data()
        return self._unit

    @property
    def crew_array_data(self) -> list[list[Any]]:
        if self._crew_array_data is None:
            self._get_data()
        return self._crew_array_data

    @property
    def cargo_array_data(self) -> list[list[Any]]:
        if self._cargo_array_data is None:
            self._get_data()
        return self._cargo_array_data

    def _get_data(self) -> None:
        data = self.parse(self.message)
        if data is None:
            self._unit = MiscEnum.ERROR
            self._crew_array_data = MiscEnum.ERROR
            self._cargo_array_data = MiscEnum.ERROR
        else:
            self._unit = data["unit"]
            self._crew_array_data = data["crew_array_data"]
            self._cargo_array_data = data["cargo_array_data"]

    @classmethod
    def parse(cls, message: str) -> dict[str, Any]:
        match = cls.parse_regex.search(message)
        if match:
            return {"unit": match.group("unit"),
                    "crew_array_data": parse_text_array(match.group("crew")),
                    "cargo_array_data": parse_text_array(match.group("cargo"))}

        else:
            log.critical(message)

    def get_formated_message(self, msg_format: "MessageFormat" = MessageFormat.PRETTY) -> str:
        if msg_format is MessageFormat.PRETTY:
            crew_text = pp.fmt(self.crew_array_data).replace("'", '"')
            cargo_text = pp.fmt(self.cargo_array_data).replace("'", '"')
            return f"units selected vehicle is\n\"{self.unit}\"\n\ncrew is\n{crew_text}\n\ncargo is\n{cargo_text}"
        return super().get_formated_message(msg_format=msg_format)

    @classmethod
    def check(cls, log_record: "LogRecord") -> bool:
        if '[' in log_record.message and ']' in log_record.message:
            return True
        return False


ALL_ANTISTASI_RECORD_CLASSES.add(SelectReinfUnitsRecord)


class ChangingSidesRecord(BaseAntistasiRecord):
    ___specificity___ = 30
    ___function___ = "A3A_fnc_markerChange"
    _background_qcolor: Union["QColor", MiscEnum] = MiscEnum.NOTHING
    parse_regex = re.compile(r"Changing side of (?P<location>[\w\d]+) to (?P<side>\w+)")
    extra_detail_views = ("location_name", "side")
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
                 "_location_name",
                 "_side")

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._location_name: str = None
        self._side: str = None

    @property
    def location_name(self) -> str:
        if self._location_name is None:
            self._get_data()
        return self._location_name

    @property
    def side(self) -> str:
        if self._side is None:
            self._get_data()
        return self._side

    def _get_data(self) -> None:
        data = self.parse(self.message)
        if data is None:
            self._location_name = MiscEnum.ERROR
            self._side = MiscEnum.ERROR
        else:
            self._location_name = data["location_name"]
            self._side = data["side"]

    @classmethod
    def parse(cls, message: str) -> dict[str, Any]:
        if match := cls.parse_regex.search(message):
            return {"location_name": match.group("location"),
                    "side": match.group("side")}
        else:
            log.critical(message)

    @classmethod
    def check(cls, log_record: "LogRecord") -> bool:
        if log_record.message.strip().startswith("Changing side of"):
            return True
        return False


ALL_ANTISTASI_RECORD_CLASSES.add(ChangingSidesRecord)


class ToggleLockRecord(BaseAntistasiRecord):
    ___specificity___ = 20
    ___function___ = "HR_GRG_fnc_toggleLock"
    _background_qcolor: Union["QColor", MiscEnum] = MiscEnum.NOTHING
    extra_detail_views = ("vehicle_id", "player_name", "lock_status")
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
                 "_vehicle_id",
                 "_player_name",
                 "_lock_status")

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._vehicle_id: str = None
        self._player_name: str = None
        self._lock_status: bool = None

    @property
    def vehicle_id(self) -> str:
        if self._vehicle_id is None:
            self._get_data()
        return self._vehicle_id

    @property
    def player_name(self) -> str:
        if self._player_name is None:
            self._get_data()
        return self._player_name

    @property
    def lock_status(self) -> str:
        if self._lock_status is None:
            self._get_data()
        return self._lock_status

    def _get_data(self) -> None:
        data = self.parse(self.message)
        if data is None:
            self._vehicle_id = MiscEnum.ERROR
            self._player_name = MiscEnum.ERROR
            self._lock_status = MiscEnum.ERROR
        else:
            self._vehicle_id = data["vehicle_id"]
            self._player_name = data["player_name"]
            self._lock_status = data["lock_status"]

    @classmethod
    def parse(cls, message: str) -> dict[str, Any]:
        try:
            id_part, player_part, lock_part = message.split("|")
            vehicle_id = id_part.strip().removeprefix("Lock state toggled for Vehicle ID:").strip()
            player_name = player_part.strip().removeprefix("By:").strip()
            raw_lock_status = lock_part.strip().removeprefix("Locked:").strip()
            if raw_lock_status.casefold() == "true":
                lock_status = True

            elif raw_lock_status.casefold() == "false":
                lock_status = False
            else:
                raise TypeError(f"Unable to convert {raw_lock_status!r} to bool")
            return {"vehicle_id": vehicle_id, "player_name": player_name, "lock_status": lock_status}
        except ValueError as e:
            log.debug("ValueError with message %r of %r", message, cls.__name__)
            log.error(e, exc_info=True, extra={"text": message})

    @classmethod
    def check(cls, log_record: "LogRecord") -> bool:
        if log_record.message.strip().startswith("Lock state toggled for Vehicle ID:"):
            return True
        return False


ALL_ANTISTASI_RECORD_CLASSES.add(ToggleLockRecord)


class QRFAvailableRecord(BaseAntistasiRecord):
    ___specificity___ = 20
    ___function___ = "A3A_fnc_SUP_QRFAvailable"
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

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

    @classmethod
    def check(cls, log_record: "LogRecord") -> bool:
        return True


ALL_ANTISTASI_RECORD_CLASSES.add(QRFAvailableRecord)


# region[Main_Exec]


if __name__ == '__main__':
    pass

# endregion[Main_Exec]
