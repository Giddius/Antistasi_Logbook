"""
WiP.

Soon.
"""

# region [Imports]

# * Standard Library Imports ---------------------------------------------------------------------------->
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING
from pathlib import Path
from functools import cached_property

# * Third Party Imports --------------------------------------------------------------------------------->
from antistasi_logbook.records.enums import RecordFamily, MessageFormat

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

# endregion[Constants]


class AbstractRecord(ABC):
    ___record_family___: RecordFamily = ...
    ___specificity___: int = ...
    ___has_multiline_message___: bool = False

    @classmethod
    @abstractmethod
    def check(cls, raw_record: "RawRecord") -> bool:
        ...

    @abstractmethod
    def get_formated_message(self, msg_format: "MessageFormat" = MessageFormat.PRETTY) -> str:
        return self.message

    @cached_property
    def pretty_message(self) -> str:
        return self.get_formated_message(MessageFormat.PRETTY)

# region[Main_Exec]


if __name__ == '__main__':
    pass

# endregion[Main_Exec]
