"""
WiP.

Soon.
"""

# region [Imports]

# * Standard Library Imports ---------------------------------------------------------------------------->
from enum import Enum, Flag, auto, unique
from typing import TYPE_CHECKING
from pathlib import Path

# * Type-Checking Imports --------------------------------------------------------------------------------->
if TYPE_CHECKING:
    from antistasi_logbook.storage.models.models import RecordOrigin

# endregion [Imports]

# region [TODO]


# endregion [TODO]

# region [Logging]


# endregion [Logging]

# region [Constants]

THIS_FILE_DIR = Path(__file__).parent.absolute()

# endregion [Constants]


@ unique
class LogLevelEnum(Enum):
    NO_LEVEL = 0
    DEBUG = 1
    INFO = 2
    WARNING = 3
    CRITICAL = 4
    ERROR = 5

    @ classmethod
    def _missing_(cls, value: str):
        if value is None:
            return cls.NO_LEVEL
        mod_value = value.casefold()
        _out = {member.name.casefold(): member for member in cls.__members__.values()}.get(mod_value, None)
        if _out is None:
            raise ValueError("%r is not a valid %s" % (value, cls.__name__))
        return _out

    @classmethod
    @property
    def all_possible_names(cls) -> list[str]:
        return [member.name.title() for member in cls.__members__.values() if member is not cls.NO_LEVEL]


@ unique
class PunishmentActionEnum(Enum):
    WARNING = 1
    DAMAGE = 2
    COLLISION = 3
    RELEASE = 4
    GUILTY = 5
    NO_ACTION = 0

    @ classmethod
    def _missing_(cls, value: str):
        if value is None:
            return cls.NO_ACTION
        mod_value = value.casefold()
        _out = {member.name.casefold(): member for member in cls.__members__.values()}.get(mod_value, None)
        if _out is None:
            raise ValueError("%r is not a valid %s" % (value, cls.__name__))
        return _out

    @classmethod
    @property
    def all_possible_names(cls) -> list[str]:
        return [member.name.upper() for member in cls.__members__.values() if member is not cls.NO_ACTION]


class MessageFormat(Enum):
    PRETTY = auto()
    SHORT = auto()
    ORIGINAL = auto()
    DISCORD = auto()

    @ classmethod
    def _missing_(cls, value: str):
        mod_value = value.casefold()
        for member in cls.__members__.values():
            if member.name.casefold() == mod_value:
                return member

        raise ValueError("%r is not a valid %s" % (value, cls.__name__))


class RecordFamily(Flag):
    GENERIC = auto()
    ANTISTASI = auto()

    @classmethod
    def from_record_origin(cls, record_origin: "RecordOrigin") -> "RecordFamily":
        name = record_origin.name
        return cls._member_map_.get(name.upper())


class MessageTypus(Enum):
    TEXT = auto()
    TABLE = auto()
    LIST = auto()
    JSON = auto()
    SQF = auto()


# region [Main_Exec]
if __name__ == '__main__':
    pass

# endregion [Main_Exec]
