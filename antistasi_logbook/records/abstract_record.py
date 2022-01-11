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

# * Local Imports --------------------------------------------------------------------------------------->
from antistasi_logbook.records.enums import RecordFamily, MessageFormat

# * Type-Checking Imports --------------------------------------------------------------------------------->
if TYPE_CHECKING:
    from antistasi_logbook.storage.models.models import LogRecord

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
    def check(cls, log_record: "LogRecord") -> bool:
        ...

    # @classmethod
    # @abstractmethod
    # def check_from_raw_record(cls, raw_record:"RawRecord")->bool:
    #     ...

    # @classmethod
    # @abstractmethod
    # def check_from_log_record(cls, log_record:"LogRecord")->bool:
    #     ...

    @abstractmethod
    def get_formated_message(self, msg_format: "MessageFormat" = MessageFormat.PRETTY) -> str:
        return self.message

    @cached_property
    def single_line_message(self) -> str:
        pretty_message_lines = self.get_formated_message(MessageFormat.PRETTY).splitlines()
        if len(pretty_message_lines) > 1:
            return pretty_message_lines[0] + '...'
        else:
            return pretty_message_lines[0]


# region[Main_Exec]

if __name__ == '__main__':
    pass

# endregion[Main_Exec]
