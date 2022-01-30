"""
WiP.

Soon.
"""

# region [Imports]

# * Standard Library Imports ---------------------------------------------------------------------------->
import sys
import subprocess
from typing import Optional
from pathlib import Path, WindowsPath

# * Qt Imports --------------------------------------------------------------------------------------->
from PySide6.QtGui import QPalette, QDesktopServices
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QPushButton, QApplication

# * Third Party Imports --------------------------------------------------------------------------------->
from yarl import URL

# * Gid Imports ----------------------------------------------------------------------------------------->
from gidapptools import get_logger
from gidapptools.general_helper.typing_helper import implements_protocol

# * Local Imports --------------------------------------------------------------------------------------->
from antistasi_logbook.gui.widgets.data_view_widget.type_fields.base_type_field import TypeFieldProtocol

# endregion[Imports]

# region [TODO]


# endregion [TODO]

# region [Logging]


# endregion[Logging]

# region [Constants]

THIS_FILE_DIR = Path(__file__).parent.absolute()
log = get_logger(__name__)
# endregion[Constants]


@implements_protocol(TypeFieldProtocol)
class URLTypeField(QPushButton):
    ___typus___ = URL

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.url: URL = None
        self._set_link_color()

    @property
    def url_text(self) -> Optional[str]:
        if self.url is not None:
            return str(self.url)

    def set_size(self, h, w):
        pass

    def set_value(self, value: URL):
        self.url = value
        self.setText(self.url_text)
        self.pressed.connect(self.open_link)

    def open_link(self):
        QDesktopServices.openUrl(self.url_text)

    def _set_link_color(self):
        link_color = QApplication.instance().palette().color(QPalette.Button.Link)
        r = link_color.red()
        g = link_color.green()
        b = link_color.blue()
        self.setStyleSheet(f"color: rgb({', '.join(str(i) for i in [r,g,b])})")
        self.setCursor(Qt.PointingHandCursor)

    @classmethod
    def add_to_type_field_table(cls, table: dict):
        table[cls.___typus___] = cls
        return table


@implements_protocol(TypeFieldProtocol)
class PathTypeField(QPushButton):
    ___typus___ = Path

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.path = None
        self._set_link_color()

    def set_size(self, h, w):
        pass

    def set_value(self, value: Path):
        self.path = value
        self.setText(self.path_text)
        self.pressed.connect(self.open_folder)

    @property
    def path_text(self) -> Optional[str]:
        if self.path is not None:
            return str(self.path)

    def _set_link_color(self):
        link_color = QApplication.instance().palette().color(QPalette.Button.Link)
        r = link_color.red()
        g = link_color.green()
        b = link_color.blue()
        self.setStyleSheet(f"color: rgb({', '.join(str(i) for i in [r,g,b])})")
        self.setCursor(Qt.PointingHandCursor)

    def open_folder(self):
        safe_path = str(self.path)
        if self.path.is_dir() is False and self.path.is_file() is True:
            safe_path = str(self.path.parent)

        if sys.platform == 'darwin':
            subprocess.run(['open', '--', safe_path], check=False)
        elif sys.platform == 'linux2':
            subprocess.run(['gnome-open', '--', safe_path], check=False)
        elif sys.platform == 'win32':
            subprocess.run(['explorer', safe_path], check=False)

    @classmethod
    def add_to_type_field_table(cls, table: dict):
        table[cls.___typus___] = cls
        table[WindowsPath] = cls
        return table


# region[Main_Exec]


if __name__ == '__main__':
    pass

# endregion[Main_Exec]
