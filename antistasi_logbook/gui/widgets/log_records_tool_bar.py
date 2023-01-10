"""
WiP.

Soon.
"""

# region [Imports]

# * Standard Library Imports ---------------------------------------------------------------------------->
from typing import TYPE_CHECKING, Union
from pathlib import Path

# * Qt Imports --------------------------------------------------------------------------------------->
from PySide6.QtGui import QAction
from PySide6.QtWidgets import QWidget, QMainWindow

# * Local Imports --------------------------------------------------------------------------------------->
from antistasi_logbook.gui.widgets.base_tool_bar import BaseToolBar
from antistasi_logbook.gui.resources.antistasi_logbook_resources_accessor import AllResourceItems

# * Type-Checking Imports --------------------------------------------------------------------------------->
if TYPE_CHECKING:
    from antistasi_logbook.storage.models.models import LogFile

# endregion [Imports]

# region [TODO]


# endregion [TODO]

# region [Logging]


# endregion [Logging]

# region [Constants]

THIS_FILE_DIR = Path(__file__).parent.absolute()

# endregion [Constants]


class LogRecordToolBar(BaseToolBar):

    def __init__(self, parent: Union[QMainWindow, QWidget] = None) -> None:
        super().__init__(parent, "Log-Records")

    def set_title_from_log_file(self, log_file: "LogFile"):
        self.setWindowTitle(f"Log-Records of {log_file}")

    def setup_actions(self):
        super().setup_actions()
        self.font_settings_action = QAction(AllResourceItems.font_settings_image.get_as_icon(), "Font Settings", self)
        self.addAction(self.font_settings_action)


# region [Main_Exec]

if __name__ == '__main__':
    pass

# endregion [Main_Exec]
