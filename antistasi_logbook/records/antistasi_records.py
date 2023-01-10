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

# * Gid Imports ----------------------------------------------------------------------------------------->
from gidapptools import get_logger
from gidapptools.general_helper.enums import MiscEnum
from gidapptools.general_helper.general_classes import DecorateAbleList

# * Local Imports --------------------------------------------------------------------------------------->
from antistasi_logbook.records.enums import RecordFamily, MessageFormat
from antistasi_logbook.records.base_record import BaseRecord
from antistasi_logbook.utilities.parsing_misc import parse_text_array

# * Type-Checking Imports --------------------------------------------------------------------------------->
if TYPE_CHECKING:
    pass
    from antistasi_logbook.storage.models.models import LogRecord

# endregion [Imports]

# region [TODO]


# endregion [TODO]

# region [Logging]


# endregion [Logging]

# region [Constants]


THIS_FILE_DIR = Path(__file__).parent.absolute()
log = get_logger(__name__)
# endregion [Constants]

ALL_ANTISTASI_RECORD_CLASSES: DecorateAbleList[type["BaseAntistasiRecord"]] = DecorateAbleList()


@ALL_ANTISTASI_RECORD_CLASSES
class BaseAntistasiRecord(BaseRecord):
    ___record_family___ = RecordFamily.ANTISTASI
    ___specificity___ = 1
    ___function___: str = None

    __slots__ = tuple()

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


@ALL_ANTISTASI_RECORD_CLASSES
class PerformanceRecord(BaseAntistasiRecord):
    ___record_family___ = RecordFamily.ANTISTASI
    ___specificity___ = 10
    ___function___ = "A3A_fnc_logPerformance"
    performance_regex = re.compile(r"(?P<name>\w+\s?\w*)(?:\:\s?)(?P<value>\d[\d\.]*)")

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


@ALL_ANTISTASI_RECORD_CLASSES
class IsNewCampaignRecord(BaseAntistasiRecord):
    ___record_family___ = RecordFamily.ANTISTASI
    ___specificity___ = 20
    ___function___ = "A3A_fnc_initServer"

    __slots__ = tuple()

    @classmethod
    def check(cls, log_record: "LogRecord") -> bool:
        if "Creating new campaign with ID" in log_record.message:
            return True

        return False


@ALL_ANTISTASI_RECORD_CLASSES
class FFPunishmentRecord(BaseAntistasiRecord):
    ___record_family___ = RecordFamily.ANTISTASI
    ___specificity___ = 10
    ___function___ = ("A3A_fnc_punishment_FF", "A3A_fnc_punishment")
    punishment_type_regex = re.compile(r"(?P<punishment_type>[A-Z]+)")

    extra_detail_views = ("punishment_type",)
    __slots__ = ("_punishment_type",)

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


@ALL_ANTISTASI_RECORD_CLASSES
class UpdatePreferenceRecord(BaseAntistasiRecord):
    ___record_family___ = RecordFamily.ANTISTASI
    ___specificity___ = 20
    ___function___ = "A3A_fnc_updatePreference"

    msg_start_regex = re.compile(r"(?P<category>[a-zA-Z]+)\_preference")
    extra_detail_views = ("category", "array_data")

    __slots__ = ("_category",
                 "_array_data")

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._category = self.msg_start_regex.match(self.message.lstrip()).group("category")
        self._array_data: list[list[Any]] = None

    @property
    def category(self) -> str:
        if self._category is None:
            self._category = self.msg_start_regex.match(self.message.lstrip()).group("category")
        return self._category

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


@ALL_ANTISTASI_RECORD_CLASSES
class CreateConvoyInputRecord(BaseAntistasiRecord):
    ___record_family___ = RecordFamily.ANTISTASI
    ___specificity___ = 20
    ___function___ = "A3A_fnc_createConvoy"

    extra_detail_views = ("array_data",)
    __slots__ = ("_array_data",)

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


@ALL_ANTISTASI_RECORD_CLASSES
class SaveParametersRecord(BaseAntistasiRecord):
    ___specificity___ = 20
    ___function___ = "A3A_fnc_saveLoop"

    extra_detail_views = ("kv_data",)
    __slots__ = ("_kv_data",)

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


@ALL_ANTISTASI_RECORD_CLASSES
class ResourceCheckRecord(BaseAntistasiRecord):
    ___specificity___ = 20
    ___function___ = "A3A_fnc_economicsAI"
    side_regex = re.compile(r"(?P<side>\w+)\sarsenal")

    extra_detail_views = ("side", "stats")
    __slots__ = ("_stats",
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


@ALL_ANTISTASI_RECORD_CLASSES
class FreeSpawnPositionsRecord(BaseAntistasiRecord):
    ___specificity___ = 20
    ___function___ = "A3A_fnc_freeSpawnPositions"
    place_regex = re.compile(r"Spawn places for (?P<place>\w+)", re.IGNORECASE)

    extra_detail_views = ("place", "array_data")
    __slots__ = ("_array_data",
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


@ALL_ANTISTASI_RECORD_CLASSES
class SelectReinfUnitsRecord(BaseAntistasiRecord):
    ___specificity___ = 20
    ___function___ = "A3A_fnc_selectReinfUnits"
    parse_regex = re.compile(r"units selected vehicle is (?P<unit>\w+) crew is (?P<crew>.*(?= cargo is)) cargo is (?P<cargo>.*)", re.IGNORECASE)

    extra_detail_views = ("crew_array_data",
                          "cargo_array_data", "unit")
    __slots__ = ("_crew_array_data",
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


@ALL_ANTISTASI_RECORD_CLASSES
class ChangingSidesRecord(BaseAntistasiRecord):
    ___specificity___ = 30
    ___function___ = "A3A_fnc_markerChange"

    parse_regex = re.compile(r"Changing side of (?P<location>[\w\d]+) to (?P<side>\w+)")
    extra_detail_views = ("location_name", "side")
    __slots__ = ("_location_name",
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


@ALL_ANTISTASI_RECORD_CLASSES
class ToggleLockRecord(BaseAntistasiRecord):
    ___specificity___ = 20
    ___function___ = "HR_GRG_fnc_toggleLock"

    extra_detail_views = ("vehicle_id", "player_name", "lock_status")
    __slots__ = ("_vehicle_id",
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


@ALL_ANTISTASI_RECORD_CLASSES
class QRFAvailableRecord(BaseAntistasiRecord):
    ___specificity___ = 20
    ___function___ = "A3A_fnc_SUP_QRFAvailable"

    __slots__ = tuple()

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

    @classmethod
    def check(cls, log_record: "LogRecord") -> bool:
        return True


@ALL_ANTISTASI_RECORD_CLASSES
class PatrolCommanderRecord(BaseAntistasiRecord):
    ___specificity___ = 20
    ___function___ = "A3A_fnc_patrolCommander"

    parse_regex = re.compile(r"(\||^)(?P<key>.*?)\:\s*(?P<value>.*?)(?=\||$)")
    extra_detail_views = ("group", "current_orders", "group_state", "client")
    __slots__ = ("_group",
                 "_current_orders",
                 "_group_state",
                 "_client")

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._group = None
        self._current_orders = None
        self._group_state = None
        self._client = None

    @property
    def group(self) -> str:
        if self._group is None:
            self.collect_data()
        return self._group

    @property
    def current_orders(self):
        if self._current_orders is None:
            self.collect_data()
        return self._current_orders

    @property
    def group_state(self):
        if self._group_state is None:
            self.collect_data()
        return self._group_state

    @property
    def client(self):
        if self._client is None:
            self.collect_data()
        return self._client

    @classmethod
    def parse(cls, message: str) -> dict[str, Any]:
        _out = {}
        for match in cls.parse_regex.finditer(message.removeprefix("PATCOM |")):
            _out[match.group("key").strip()] = match.group("value").strip()
            log.debug(match.groupdict())
        if len(_out) <= 0:
            return None
        return _out

    def collect_data(self):
        data = self.parse(self.message)
        if data is None:
            self._group = MiscEnum.ERROR
            self._current_orders = MiscEnum.ERROR
            self._group_state = MiscEnum.ERROR
            self._client = MiscEnum.ERROR
        else:
            self._group = data.get("Group", MiscEnum.NOT_FOUND)
            self._current_orders = data.get("Current Orders", MiscEnum.NOT_FOUND)
            self._group_state = data.get("Group State", MiscEnum.NOT_FOUND)
            self._client = data.get("Client", MiscEnum.NOT_FOUND)

    @classmethod
    def check(cls, log_record: "LogRecord") -> bool:
        if log_record.message.strip().startswith("PATCOM"):
            return True
        return False


@ALL_ANTISTASI_RECORD_CLASSES
class HeadlessClientConnected(BaseAntistasiRecord):

    ___specificity___ = 20
    ___function___ = "A3A_fnc_addHC"
    __slots__ = ("_number",)
    extra_detail_views: tuple[str] = ("number",)

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._number: int = None

    @property
    def number(self) -> int:
        if self._number is None:
            self._number = self.parse(self.message)
        return self._number

    @classmethod
    def parse(cls, message: str) -> dict[str, Any]:
        cleaned_message = message.casefold().removeprefix("headless client connected:").strip().removesuffix(".").strip()
        cleaned_message = cleaned_message.strip("[]")
        if "," in cleaned_message:
            return int(cleaned_message.split(",")[-1])
        return int(cleaned_message)

    @classmethod
    def check(cls, log_record: "LogRecord") -> bool:
        if log_record.message.strip().startswith("Headless Client Connected"):
            return True

        return False


@ALL_ANTISTASI_RECORD_CLASSES
class HeadlessClientDisconnected(BaseAntistasiRecord):
    ___specificity___ = 20
    ___function___ = "A3A_fnc_onPlayerDisconnect"
    __slots__ = ("_number",)

    parse_regex = re.compile(r"Player disconnected with id HC(?P<number>\d+) and unit hc[\w\d\_]* on side LOGIC")
    extra_detail_views: tuple[str] = ("number",)

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._number: int = None

    @property
    def number(self) -> int:
        if self._number is None:
            self._number = self.parse(self.message)
        return self._number

    @classmethod
    def parse(cls, message: str) -> dict[str, Any]:
        _number = cls.parse_regex.match(message.strip()).group("number")
        return int(_number)

    @classmethod
    def check(cls, log_record: "LogRecord") -> bool:
        if cls.parse_regex.match(log_record.message.strip()):
            return True

        return False


# B_G_Soldier_F killed by GUER
@ALL_ANTISTASI_RECORD_CLASSES
class KilledBy(BaseAntistasiRecord):
    ___specificity___ = 10
    ___function___ = ("A3A_fnc_initServer", "fn_initServer.sqf")
    __slots__ = ("_victim", "_killer")
    parse_regex = re.compile(r"(?P<victim>\w+)? ?killed by (?P<killer>.*)")
    extra_detail_views: tuple[str] = ("victim", "killer")

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._victim: str = MiscEnum.NOTHING
        self._killer: str = MiscEnum.NOTHING

    @property
    def victim(self) -> Optional[str]:
        if self._victim is MiscEnum.NOTHING:
            parsed_data = self.parse(self.message)
            self._victim = parsed_data.get("victim", None)
            self._killer = parsed_data.get("killer", None)
        return self._victim

    @property
    def killer(self) -> Optional[str]:
        if self._killer is MiscEnum.NOTHING:
            parsed_data = self.parse(self.message)
            self._victim = parsed_data.get("victim", None)
            self._killer = parsed_data.get("killer", None)
        return self._killer

    @classmethod
    def parse(cls, message: str) -> dict[str, Any]:
        return cls.parse_regex.match(message.strip()).groupdict()

    @classmethod
    def check(cls, log_record: "LogRecord") -> bool:
        if "killed by " in log_record.message:
            return True
        return False


@ALL_ANTISTASI_RECORD_CLASSES
class FlagCaptureCompleted(BaseAntistasiRecord):
    ___specificity___ = 10
    ___function___ = "A3A_fnc_mrkWIN"
    __slots__ = ("captured_by_side", "_flag_name", "_flag_ingame_coordinates", "_squad_name", "_player_name")
    parse_regex = re.compile(r".*(?P<flag_ingame_coordinates>\d{8})\s+\((?P<flag_name>\w+)\)\:.*by\s(((?P<squad_name>.*?\d+\:\d+)?\s\((?P<player_name>.*?)\))|(?P<player_name_no_squad>.*))")
    extra_detail_views: tuple[str] = ("flag_name", "flag_ingame_coordinates", "squad_name", "player_name")

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.captured_by_side = "GUER"
        self._flag_name: str = MiscEnum.NOTHING
        self._flag_ingame_coordinates: str = MiscEnum.NOTHING
        self._squad_name: str = MiscEnum.NOTHING
        self._player_name: str = MiscEnum.NOTHING

    def gather_parsed_data(self) -> None:
        parsed_data = self.parse(self.message)
        self._flag_name = parsed_data.get("flag_name")
        self._flag_ingame_coordinates = parsed_data.get("flag_ingame_coordinates")
        self._squad_name = parsed_data.get("squad_name")
        if self._squad_name is None:
            self._player_name = parsed_data.get("player_name_no_squad")
        else:
            self._player_name = parsed_data.get("player_name")

    @property
    def flag_name(self) -> Optional[str]:
        if self._flag_name is MiscEnum.NOTHING:
            self.gather_parsed_data()

        return self._flag_name

    @property
    def flag_ingame_coordinates(self) -> Optional[str]:
        if self._flag_ingame_coordinates is MiscEnum.NOTHING:
            self.gather_parsed_data()

        return self._flag_ingame_coordinates

    @property
    def squad_name(self) -> Optional[str]:
        if self._squad_name is MiscEnum.NOTHING:
            self.gather_parsed_data()

        return self._squad_name

    @property
    def player_name(self) -> Optional[str]:
        if self._player_name is MiscEnum.NOTHING:
            self.gather_parsed_data()

        return self._player_name

    @classmethod
    def parse(cls, message: str) -> dict[str, Any]:
        message = message.rsplit(" | Client:", 1)[0]
        return cls.parse_regex.match(message.strip()).groupdict()

    @classmethod
    def check(cls, log_record: "LogRecord") -> bool:
        if "Flag capture completed by " in log_record.message:
            return True
        return False


ALL_ANTISTASI_RECORD_CLASSES: set[type["BaseAntistasiRecord"]] = set(ALL_ANTISTASI_RECORD_CLASSES)
# region [Main_Exec]


if __name__ == '__main__':
    pass

# endregion [Main_Exec]
