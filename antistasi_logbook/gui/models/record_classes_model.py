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
from PySide6.QtGui import QColor
from PySide6.QtCore import Slot, QModelIndex
from PySide6.QtWidgets import QColorDialog

# * Third Party Imports --------------------------------------------------------------------------------->
from peewee import Field

# * Gid Imports ----------------------------------------------------------------------------------------->
from gidapptools import get_logger

# * Local Imports --------------------------------------------------------------------------------------->
from antistasi_logbook.storage.models.models import BaseModel, RecordClass
from antistasi_logbook.storage.models.custom_fields import FakeField
from antistasi_logbook.gui.widgets.better_color_dialog import BetterColorDialog
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


class RecordClassesModel(BaseQueryDataModel):
    extra_columns = {FakeField(name="record_family", verbose_name="Record Family"),
                     FakeField(name="specificity", verbose_name="Specificity"),
                     FakeField(name="amount_stored", verbose_name="Amount")}
    color_config_name = "record"
    _item_size_by_column_name: dict[str, int] = {"id": 30, "marked": 60, "record_family": 200, "specificity": 100, "name": 250}

    def __init__(self, parent: Optional[QtCore.QObject] = None) -> None:

        super().__init__(RecordClass, parent=parent)
        self.filter_item = None

    @Slot(object, object, QModelIndex)
    def change_color(self, item: BaseModel, column: Field, index: QModelIndex):

        accepted, color = BetterColorDialog.show_dialog(self.color_config.get(self.color_config_name, item.name, default=QColor(255, 255, 255, 0)), True)
        if accepted:
            log.debug("custom color count: %r", QColorDialog.customCount())
            log.debug("custom colors: %r", [(QColorDialog.customColor(i), QColorDialog.customColor(i).name()) for i in range(QColorDialog.customCount())])

            item.record_class.set_background_color(color)
            try:
                del item.background_color
            except AttributeError:
                pass


# region [Main_Exec]
if __name__ == '__main__':
    pass

# endregion [Main_Exec]
