"""
WiP.

Soon.
"""

# region [Imports]

# * Standard Library Imports ---------------------------------------------------------------------------->
from typing import TYPE_CHECKING
from pathlib import Path

# * Qt Imports --------------------------------------------------------------------------------------->
from PySide6.QtGui import QAction
from PySide6.QtCore import QAbstractItemModel

# * Gid Imports ----------------------------------------------------------------------------------------->
from gidapptools import get_logger

# * Local Imports --------------------------------------------------------------------------------------->
from antistasi_logbook.gui.widgets.markdown_editor import MarkdownEditorDialog
from antistasi_logbook.gui.views.base_query_tree_view import BaseQueryTreeView
from antistasi_logbook.gui.resources.antistasi_logbook_resources_accessor import AllResourceItems

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


class ServerQueryTreeView(BaseQueryTreeView):
    enable_icon = AllResourceItems.check_mark_black_image.get_as_icon()
    disable_icon = AllResourceItems.close_cancel_image.get_as_icon()

    initially_hidden_columns: set[str] = {"id", "comments"}

    def __init__(self) -> None:
        super().__init__(name="Server")
        self.all_actions: set[QAction] = set()
        self.mark_icon = AllResourceItems.mark_image.get_as_icon()
        self.unmark_icon = AllResourceItems.unmark_image.get_as_icon()
        self._temp_set_comment_dialog: MarkdownEditorDialog = None
        self.original_model: QAbstractItemModel = None
        self.item_size_by_column_name = self._item_size_by_column_name.copy() | {"name": 100,
                                                                                 "local_path": 300,
                                                                                 "remote_path": 400,
                                                                                 "remote_storage": 175,
                                                                                 "update_enabled": 75,
                                                                                 "ip": 150,
                                                                                 "port": 50}

    def extra_setup(self):
        super().extra_setup()

        # region[Main_Exec]


if __name__ == '__main__':
    pass

# endregion[Main_Exec]
