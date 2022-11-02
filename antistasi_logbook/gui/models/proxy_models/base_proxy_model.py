"""
WiP.

Soon.
"""

# region [Imports]

# * Standard Library Imports ---------------------------------------------------------------------------->
from typing import TYPE_CHECKING, Union, Optional
from pathlib import Path

# * Qt Imports --------------------------------------------------------------------------------------->
from PySide6.QtCore import Qt, QModelIndex, QSortFilterProxyModel
from PySide6.QtWidgets import QAbstractItemView
# * Gid Imports ----------------------------------------------------------------------------------------->
from gidapptools import get_logger

# * Local Imports --------------------------------------------------------------------------------------->
from antistasi_logbook.gui.misc import CustomRole

# * Type-Checking Imports --------------------------------------------------------------------------------->
if TYPE_CHECKING:
    from peewee import Field

    from antistasi_logbook.storage.models.models import BaseModel
    from antistasi_logbook.gui.models.base_query_data_model import CustomContextMenu, BaseQueryDataModel

# endregion[Imports]

# region [TODO]


# endregion [TODO]

# region [Logging]


# endregion[Logging]

# region [Constants]


THIS_FILE_DIR = Path(__file__).parent.absolute()
log = get_logger(__name__)

# endregion[Constants]


class BaseProxyModel(QSortFilterProxyModel):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setRecursiveFilteringEnabled(False)
        self.setFilterCaseSensitivity(Qt.CaseInsensitive)
        self.setSortRole(CustomRole.RAW_DATA)

    @property
    def source(self) -> "BaseQueryDataModel":
        return super().sourceModel()

    def setFilterRegularExpression(self, pattern: str):
        super().setFilterRegularExpression(pattern)
        try:
            current_index = self.parent().currentIndex()
            if current_index and current_index.isValid():
                self.parent().scrollTo(current_index, QAbstractItemView.ScrollHint.PositionAtCenter)
        except Exception as e:
            log.error(e, exc_info=True)

    def setFilterFixedString(self, pattern: str) -> None:
        super().setFilterFixedString(pattern)
        try:
            current_index = self.parent().currentIndex()
            if current_index and current_index.isValid():
                self.parent().scrollTo(current_index, QAbstractItemView.ScrollHint.PositionAtCenter)
        except Exception as e:
            log.error(e, exc_info=True)

    def add_context_menu_actions(self, menu: "CustomContextMenu", index: QModelIndex):
        self.source.add_context_menu_actions(menu=menu, index=self.mapToSource(index))

    def get(self, index: Union[QModelIndex, int]) -> Optional[tuple["Field", "BaseModel"]]:
        if isinstance(index, int):
            actual_index = self.index(index, 0, QModelIndex())
            actual_index = self.mapToSource(actual_index).row()
        else:
            actual_index = self.mapToSource(index)
        return self.source.get(actual_index)

    def __getattr__(self, name: str):
        return getattr(self.sourceModel(), name)

# region[Main_Exec]


if __name__ == '__main__':
    pass

# endregion[Main_Exec]
