"""
WiP.

Soon.
"""

# region [Imports]

# * Standard Library Imports ---------------------------------------------------------------------------->
from typing import TYPE_CHECKING, Callable
from pathlib import Path

# * Qt Imports --------------------------------------------------------------------------------------->
from PySide6.QtGui import QIcon, QAction
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QMenu, QLabel, QApplication, QWidgetAction, QSystemTrayIcon

# * Gid Imports ----------------------------------------------------------------------------------------->
from gidapptools import get_logger

# * Local Imports --------------------------------------------------------------------------------------->
from antistasi_logbook.gui.resources.antistasi_logbook_resources_accessor import AllResourceItems

# * Type-Checking Imports --------------------------------------------------------------------------------->
if TYPE_CHECKING:
    from antistasi_logbook.gui.application import AntistasiLogbookApplication

# endregion [Imports]

# region [TODO]


# endregion [TODO]

# region [Logging]


# endregion [Logging]

# region [Constants]

THIS_FILE_DIR = Path(__file__).parent.absolute()
log = get_logger(__name__)
# endregion [Constants]


class LogbookSystemTray(QSystemTrayIcon):

    def __init__(self) -> None:
        self.tray_icon = self.app.icon
        self.menu: QMenu = None
        self.menu_title: QLabel = None

        super().__init__(self.tray_icon, self.app)
        self.setup()

    @property
    def app(self) -> "AntistasiLogbookApplication":
        return QApplication.instance()

    @property
    def main_window(self):
        return self.app.main_window

    def setup(self) -> None:
        self.setup_menu()

    def setup_menu(self) -> None:
        self.menu = QMenu(self.main_window)
        self.add_menu_title()
        self.hide_show_action = self.add_action("Minimize to Tray", connect_to=self.switch_main_window_visible, icon=AllResourceItems.hidden_image.get_as_icon())

        self.close_action = self.add_action("Close", connect_to=self.main_window.close, icon=AllResourceItems.close_cancel_image.get_as_icon())
        self.setContextMenu(self.menu)

    def add_menu_title(self) -> None:
        widget_action = QWidgetAction(self.menu)
        self.menu_title = QLabel(self.main_window.name)
        self.menu_title.setAlignment(Qt.AlignCenter)
        self.menu_title.setStyleSheet("background-color: rgba(87,80,68,200); color: white; font: bold 14px;margin: 6px")

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
        for dock_widget in self.main_window.dock_widgets:
            dock_widget.setVisible(not main_window_visible)
        for window in self.app.extra_windows.values():
            window.setVisible(not main_window_visible)
        text = "Minimize to Tray" if main_window_visible is False else "Open"
        icon = AllResourceItems.hidden_image.get_as_icon() if main_window_visible is False else AllResourceItems.view_image.get_as_icon()
        self.hide_show_action.setText(text)
        self.hide_show_action.setIcon(icon)

    def send_update_finished_message(self, msg: str = None):
        if msg is None:
            self.showMessage("Update finished!", "The Database is now up to date!", self.app.icon, 15 * 1000)
        else:
            self.showMessage("Update finished!", msg, self.app.icon, 15 * 1000)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(app={self.app!r})"
    # region [Main_Exec]


if __name__ == '__main__':
    pass

# endregion [Main_Exec]
