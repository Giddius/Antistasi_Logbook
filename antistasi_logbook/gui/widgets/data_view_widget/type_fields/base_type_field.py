"""
WiP.

Soon.
"""

# region [Imports]

# * Standard Library Imports ---------------------------------------------------------------------------->
from typing import Any, Protocol, runtime_checkable
from pathlib import Path

# * Gid Imports ----------------------------------------------------------------------------------------->
from gidapptools import get_logger

# endregion[Imports]

# region [TODO]


# endregion [TODO]

# region [Logging]


# endregion[Logging]

# region [Constants]

THIS_FILE_DIR = Path(__file__).parent.absolute()
log = get_logger(__name__)
# endregion[Constants]


@runtime_checkable
class TypeFieldProtocol(Protocol):

    def set_value(self, value: Any) -> None:
        ...

    def set_size(self, h: int, w: int) -> None:
        ...

    @classmethod
    def add_to_type_field_table(cls, table):
        ...


# region[Main_Exec]
if __name__ == '__main__':
    pass

# endregion[Main_Exec]
