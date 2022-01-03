"""
WiP.

Soon.
"""

# region [Imports]

# * Standard Library Imports ---------------------------------------------------------------------------->
from typing import Optional
from pathlib import Path

# * Third Party Imports --------------------------------------------------------------------------------->
from antistasi_logbook.gui.resources.antistasi_logbook_resources_accessor import AllResourceItems

# * PyQt5 Imports --------------------------------------------------------------------------------------->
from PySide6.QtWidgets import QWidget

# * Gid Imports ----------------------------------------------------------------------------------------->
from gidapptools.gidapptools_qt.basics.menu_bar import BaseMenuBar

# endregion[Imports]

# region [TODO]


# endregion [TODO]

# region [Logging]


# endregion[Logging]

# region [Constants]

THIS_FILE_DIR = Path(__file__).parent.absolute()

# endregion[Constants]


class LogbookMenuBar(BaseMenuBar):

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent=parent, auto_connect_standard_actions=True)

    def setup_menus(self) -> None:
        super().setup_menus()
        self.database_menu = self.add_new_menu("Database", add_before=self.help_menu.menuAction())
        self.single_update_action = self.add_new_action(self.database_menu, "Update Once")
        self.database_menu.addSeparator()
        self.reset_database_action = self.add_new_action(self.database_menu, "Reset Database")
        self.reset_database_action.setIcon(AllResourceItems.warning_sign_round_yellow_image.get_as_icon())
        self.open_settings_window_action = self.add_new_action(self.settings_menu, "Open Settings")

        self.exit_action.setIcon(AllResourceItems.close_cancel_image.get_as_icon())
        self.test_menu = self.add_new_menu("test")
        self.folder_action = self.add_new_action(self.help_menu, "folder")


# region[Main_Exec]


if __name__ == '__main__':
    pass

# endregion[Main_Exec]
