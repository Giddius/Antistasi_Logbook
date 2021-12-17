"""
WiP.

Soon.
"""

# region [Imports]

# * Standard Library Imports ---------------------------------------------------------------------------->
from typing import TYPE_CHECKING, Union
from pathlib import Path

# * Third Party Imports --------------------------------------------------------------------------------->
from antistasi_logbook.storage.models.models import Server, LogFile, LogRecord

# * Gid Imports ----------------------------------------------------------------------------------------->
from gidapptools import get_logger

if TYPE_CHECKING:

    # * Third Party Imports --------------------------------------------------------------------------------->
    from antistasi_logbook.records.abstract_record import AbstractRecord

# endregion[Imports]

# region [TODO]


# endregion [TODO]

# region [Logging]


# endregion[Logging]

# region [Constants]

THIS_FILE_DIR = Path(__file__).parent.absolute()
log = get_logger(__name__)
# endregion[Constants]

VIEW_ABLE_ITEMS_TYPE = Union["AbstractRecord", "LogRecord", "LogFile", "Server"]


# region[Main_Exec]
if __name__ == '__main__':
    pass

# endregion[Main_Exec]
