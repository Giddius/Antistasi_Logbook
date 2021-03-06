"""
WiP.

Soon.
"""

# region [Imports]

# * Standard Library Imports ---------------------------------------------------------------------------->
from typing import TYPE_CHECKING, Optional
from pathlib import Path

# * Qt Imports --------------------------------------------------------------------------------------->
from PySide6.QtCore import Qt, QModelIndex, QSortFilterProxyModel

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

from gidapptools.general_helper.timing import get_dummy_profile_decorator_in_globals
get_dummy_profile_decorator_in_globals()
THIS_FILE_DIR = Path(__file__).parent.absolute()
log = get_logger(__name__)

# endregion[Constants]


class BaseProxyModel(QSortFilterProxyModel):
    @profile
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setRecursiveFilteringEnabled(False)
        self.setFilterCaseSensitivity(Qt.CaseInsensitive)
        self.setSortRole(CustomRole.RAW_DATA)

    @property
    def source(self) -> "BaseQueryDataModel":
        return super().sourceModel()

    @profile
    def add_context_menu_actions(self, menu: "CustomContextMenu", index: QModelIndex):
        self.source.add_context_menu_actions(menu=menu, index=self.mapToSource(index))

    def get(self, index: QModelIndex) -> Optional[tuple["Field", "BaseModel"]]:
        return self.source.get(self.mapToSource(index))

    @profile
    def __getattr__(self, name: str):
        return getattr(self.sourceModel(), name)

# region[Main_Exec]


if __name__ == '__main__':
    pass

# endregion[Main_Exec]
