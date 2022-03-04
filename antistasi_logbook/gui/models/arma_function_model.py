"""
WiP.

Soon.
"""

# region [Imports]

# * Standard Library Imports ---------------------------------------------------------------------------->
from typing import TYPE_CHECKING, Optional
from pathlib import Path

# * Qt Imports --------------------------------------------------------------------------------------->
from PySide6 import QtCore

# * Gid Imports ----------------------------------------------------------------------------------------->
from gidapptools import get_logger

# * Local Imports --------------------------------------------------------------------------------------->
from antistasi_logbook.storage.models.models import ArmaFunction
from antistasi_logbook.storage.models.custom_fields import FakeField
from antistasi_logbook.gui.models.base_query_data_model import BaseQueryDataModel

# * Type-Checking Imports --------------------------------------------------------------------------------->
if TYPE_CHECKING:
    pass

# endregion[Imports]

# region [TODO]


# endregion [TODO]

# region [Logging]


# endregion[Logging]

# region [Constants]

from gidapptools.general_helper.timing import get_dummy_profile_decorator_in_globals

THIS_FILE_DIR = Path(__file__).parent.absolute()
log = get_logger(__name__)

# endregion[Constants]


class ArmaFunctionModel(BaseQueryDataModel):
    extra_columns = {FakeField("file_name", "File Name"), FakeField("function_name", "Function Name")}
    _item_size_by_column_name = {"link": 250, "local_path": 250}

    def __init__(self, parent: Optional[QtCore.QObject] = None) -> None:

        super().__init__(ArmaFunction, parent=parent)
        self.filter_item = None


# region[Main_Exec]
if __name__ == '__main__':
    pass

# endregion[Main_Exec]
