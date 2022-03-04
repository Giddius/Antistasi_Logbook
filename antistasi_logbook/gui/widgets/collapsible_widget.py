"""
WiP.

Soon.
"""

# region [Imports]

# * Standard Library Imports ---------------------------------------------------------------------------->
from typing import TYPE_CHECKING
from pathlib import Path

# * Qt Imports --------------------------------------------------------------------------------------->
import PySide6
from PySide6.QtCore import Qt, QEvent
from PySide6.QtWidgets import QWidget, QGroupBox, QGridLayout

# * Gid Imports ----------------------------------------------------------------------------------------->
from gidapptools import get_logger

# * Type-Checking Imports --------------------------------------------------------------------------------->
if TYPE_CHECKING:
    pass

# endregion[Imports]

# region [TODO]


# endregion [TODO]

# region [Logging]


# endregion[Logging]

# region [Constants]

from gidapptools.general_helper.timing import get_dummy_profile_decorator_in_globals

THIS_FILE_DIR = Path(__file__).parent.absolute()
log = get_logger(__name__)

# endregion[Constants]


class CollapsibleGroupBox(QGroupBox):
    expand_prefix = "▼"
    collapse_prefix = "▲"

    def __init__(self, text: str = None, content: QWidget = None, start_expanded: bool = True, parent=None):
        super().__init__(parent=parent)
        self.setLayout(QGridLayout())
        self.layout.setAlignment(Qt.AlignCenter)
        self.setFlat(True)
        self.setAlignment(Qt.AlignCenter)
        self.text = text
        self.content = content

        self.layout.addWidget(self.content)

        self.expanded = True
        self.setTitle(self.full_text)
        self.original_cursor = self.cursor()
        self.current_cursor = self.cursor()
        if start_expanded is False:
            self.set_expanded(False)

    @property
    def full_text(self) -> str:
        text = self.text
        if self.expanded is True:
            if text is None:
                text = "hide"
            return f"{self.collapse_prefix} {text}"
        else:
            if text is None:
                text = "show"
            return f"{self.expand_prefix} {text}"

    @ property
    def layout(self) -> QGridLayout:
        return super().layout()

    def mousePressEvent(self, event: PySide6.QtGui.QMouseEvent) -> None:
        if not self.contentsRect().contains(event.pos()):
            self.on_title_clicked()

    def event(self, event: PySide6.QtCore.QEvent) -> bool:
        if event.type() == QEvent.HoverMove:
            if not self.contentsRect().contains(event.pos()) and self.current_cursor is not Qt.PointingHandCursor:
                self.setCursor(Qt.PointingHandCursor)
            elif self.contentsRect().contains(event.pos()) and self.current_cursor is not self.original_cursor:
                self.setCursor(self.original_cursor)

        return super().event(event)

    def leaveEvent(self, event: PySide6.QtCore.QEvent) -> None:
        self.setCursor(self.original_cursor)
        return super().leaveEvent(event)

    def on_title_clicked(self):
        self.expanded = not self.expanded
        self.content.setVisible(self.expanded)
        self.setTitle(self.full_text)

    def set_expanded(self, value: bool):
        self.expanded = value
        self.content.setVisible(value)
        self.setTitle(self.full_text)
# region[Main_Exec]


if __name__ == '__main__':
    pass

# endregion[Main_Exec]
