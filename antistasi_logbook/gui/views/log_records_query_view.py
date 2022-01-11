"""
WiP.

Soon.
"""

# region [Imports]

# * Standard Library Imports ---------------------------------------------------------------------------->
from typing import TYPE_CHECKING
from pathlib import Path

# * Qt Imports --------------------------------------------------------------------------------------->
from PySide6.QtWidgets import QHeaderView

# * Gid Imports ----------------------------------------------------------------------------------------->
from gidapptools import get_logger

# * Local Imports --------------------------------------------------------------------------------------->
from antistasi_logbook.gui.views.base_query_tree_view import BaseQueryTreeView

# * Type-Checking Imports --------------------------------------------------------------------------------->
if TYPE_CHECKING:
    pass

# endregion[Imports]

# region [TODO]


# endregion [TODO]

# region [Logging]


# endregion[Logging]

# region [Constants]

THIS_FILE_DIR = Path(__file__).parent.absolute()
log = get_logger(__name__)
# endregion[Constants]


class LogRecordsQueryView(BaseQueryTreeView):
    initially_hidden_columns: set[str] = {"id", "comments"}

    def __init__(self) -> None:
        super().__init__(name="Log-Records")

    def extra_setup(self):
        super().extra_setup()
        self.setSortingEnabled(False)

    @property
    def header_view(self) -> QHeaderView:
        return self.header()

    def pre_set_model(self):
        super().pre_set_model()

    def post_set_model(self):
        super().post_set_model()

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}"


# region[Main_Exec]

if __name__ == '__main__':
    pass

# endregion[Main_Exec]
