"""
WiP.

Soon.
"""

# region [Imports]

# * Standard Library Imports ---------------------------------------------------------------------------->
from typing import TYPE_CHECKING, Any, Optional
from pathlib import Path

# * Qt Imports --------------------------------------------------------------------------------------->
from PySide6 import QtCore
from PySide6.QtCore import Signal

# * Third Party Imports --------------------------------------------------------------------------------->
from peewee import Field

# * Gid Imports ----------------------------------------------------------------------------------------->
from gidapptools import get_logger

# * Local Imports --------------------------------------------------------------------------------------->
from antistasi_logbook.storage.models.models import GameMap
from antistasi_logbook.gui.models.base_query_data_model import BaseQueryDataModel

# * Type-Checking Imports --------------------------------------------------------------------------------->
if TYPE_CHECKING:
    pass

# endregion [Imports]

# region [TODO]


# endregion [TODO]

# region [Logging]


# endregion [Logging]

# region [Constants]


THIS_FILE_DIR = Path(__file__).parent.absolute()
log = get_logger(__name__)

# endregion [Constants]


class GameMapModel(BaseQueryDataModel):

    strict_exclude_columns = {"map_image_low_resolution", "map_image_high_resolution", "coordinates"}
    avg_player_calculation_finished = Signal(float, object)

    def __init__(self, parent: Optional[QtCore.QObject] = None) -> None:

        super().__init__(GameMap, parent=parent)
        self.filter_item = None

    def _modify_display_data(self, data: Any, item: GameMap, column: "Field") -> str:
        if column.verbose_name == "Internal Name":
            return getattr(item, column.name)
        return super()._modify_display_data(data, item, column)


# region [Main_Exec]
if __name__ == '__main__':
    pass

# endregion [Main_Exec]
