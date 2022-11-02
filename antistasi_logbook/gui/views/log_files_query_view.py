"""
WiP.

Soon.
"""

# region [Imports]

# * Standard Library Imports ---------------------------------------------------------------------------->
from typing import TYPE_CHECKING
from pathlib import Path

# * Qt Imports --------------------------------------------------------------------------------------->
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QToolBar

# * Gid Imports ----------------------------------------------------------------------------------------->
from gidapptools import get_logger

# * Local Imports --------------------------------------------------------------------------------------->
from antistasi_logbook.gui.widgets.tool_bars import LogFileToolBar
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


class LogFilesQueryTreeView(BaseQueryTreeView):
    initially_hidden_columns: set[str] = {"id", "comments"}

    def __init__(self) -> None:
        super().__init__(name="Log-Files")
        self.item_size_by_column_name = self._item_size_by_column_name.copy() | {"name": 300,
                                                                                 "modified_at": 175,
                                                                                 "created_at": 175,
                                                                                 "size": 75,
                                                                                 "version": 125,
                                                                                 "game_map": 125,
                                                                                 "is_new_campaign": 100,
                                                                                 "campaign_id": 100,
                                                                                 "server": 100,
                                                                                 "max_mem": 100,
                                                                                 "amount_warnings": 75,
                                                                                 "amount_errors": 75,
                                                                                 "amount_log_records": 75,
                                                                                 "utc_offset": 100,
                                                                                 "time_frame": 250,
                                                                                 "unparsable": 100}

    def create_tool_bar_item(self) -> QToolBar:
        tool_bar = LogFileToolBar()
        self.current_items_changed.connect(tool_bar.export_action_widget.set_items)
        return tool_bar

    def post_set_model(self):
        super().post_set_model()
        self.sortByColumn(self.model.get_column_index("modified_at"), Qt.DescendingOrder)


# region[Main_Exec]

if __name__ == '__main__':
    pass

# endregion[Main_Exec]
