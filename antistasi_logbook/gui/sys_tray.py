"""
WiP.

Soon.
"""

# region [Imports]

# * Standard Library Imports ---------------------------------------------------------------------------->
from typing import TYPE_CHECKING, Callable
from pathlib import Path

# * Third Party Imports --------------------------------------------------------------------------------->
from antistasi_logbook.gui.resources.antistasi_logbook_resources_accessor import AllResourceItems

# * PyQt5 Imports --------------------------------------------------------------------------------------->
from PySide6.QtGui import QIcon, QAction
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QMenu, QLabel, QApplication, QWidgetAction, QSystemTrayIcon

if TYPE_CHECKING:
    # * Third Party Imports --------------------------------------------------------------------------------->
    from antistasi_logbook.gui.main_window import AntistasiLogbookMainWindow

# endregion[Imports]

# region [TODO]


# endregion [TODO]

# region [Logging]


# endregion[Logging]

# region [Constants]

THIS_FILE_DIR = Path(__file__).parent.absolute()

# endregion[Constants]


class LogbookSystemTray(QSystemTrayIcon):

    def __init__(self, main_window: "AntistasiLogbookMainWindow", app: "QApplication") -> None:
        self.main_window = main_window
        self.app = app
        self.tray_icon = self.app.icon
        self.menu: QMenu = None
        self.menu_title: QLabel = None

        super().__init__(self.tray_icon, self.main_window)
        self.setup()

    def setup(self) -> None:
        self.setup_menu()

    def setup_menu(self) -> None:
        self.menu = QMenu(self.main_window)
        self.menu.setStyleSheet("border: 1px solid black;background-color: white;margin: 4px")

        self.add_menu_title()
        self.hide_show_action = self.add_action("Minimize to Tray", connect_to=self.switch_main_window_visible, icon=AllResourceItems.hidden_image.get_as_icon())

        self.close_action = self.add_action("Close", connect_to=self.main_window.close, icon=AllResourceItems.close_cancel_image.get_as_icon())
        self.setContextMenu(self.menu)

    def add_menu_title(self) -> None:
        widget_action = QWidgetAction(self.menu)
        self.menu_title = QLabel(self.main_window.name)
        self.menu_title.setAlignment(Qt.AlignCenter)
        self.menu_title.setStyleSheet(f"background-color: rgba(87,80,68,200); color: white; font: bold 14px;margin: 6px")

        widget_action.setDefaultWidget(self.menu_title)
        self.menu.addAction(widget_action)

    def add_action(self, title: str, connect_to: Callable = None, icon: QIcon = None, enabled: bool = True) -> QAction:
        action = QAction(title)

        if icon is not None:
            action.setIcon(icon)

        self.menu.addAction(action)

        if connect_to is not None:
            action.triggered.connect(connect_to)
        action.setEnabled(enabled)
        return action

    def switch_main_window_visible(self):
        main_window_visible = self.main_window.isVisible()
        self.main_window.setVisible(not main_window_visible)
        text = "Minimize to Tray" if main_window_visible is False else "Open"
        icon = AllResourceItems.hidden_image.get_as_icon() if main_window_visible is False else AllResourceItems.view_image.get_as_icon()
        self.hide_show_action.setText(text)
        self.hide_show_action.setIcon(icon)

    def send_update_finished_message(self):

        self.showMessage("Update finished!", "The Database is now up to date!", QSystemTrayIcon.MessageIcon.Information, 15 * 1000)

    # region[Main_Exec]


if __name__ == '__main__':
    pass

# endregion[Main_Exec]
