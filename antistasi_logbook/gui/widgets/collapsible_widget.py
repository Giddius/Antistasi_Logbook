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


THIS_FILE_DIR = Path(__file__).parent.absolute()
log = get_logger(__name__)

# endregion[Constants]


class EmptyPlaceholderWidget(QWidget):

    @property
    def has_content(self) -> bool:
        return False


class CollapsibleGroupBox(QGroupBox):
    _expand_prefix = "▼"
    _collapse_prefix = "▲"
    _expand_text = "show"
    _collapse_text = "hide"
    _no_content_text = ""
    _no_content_prefix = ""

    def __init__(self, text: str = None, content: QWidget = None, start_expanded: bool = True, parent=None):
        super().__init__(parent=parent)
        self.setLayout(QGridLayout())
        self.layout.setAlignment(Qt.AlignCenter)
        self.setFlat(True)
        self.setAlignment(Qt.AlignCenter)
        self.no_content_prefix = str(self._no_content_prefix)
        self.no_content_text = str(self._no_content_text)
        self.expand_prefix = str(self._expand_prefix)
        self.collapse_prefix = str(self._collapse_prefix)
        self.expand_text = str(self._expand_text)
        self.collapse_text = str(self._collapse_text)
        self.text = text
        self.content = content or EmptyPlaceholderWidget()
        self.layout.addWidget(self.content)
        self.expanded = True
        self.setTitle(self.full_text)
        self.original_cursor = self.cursor()
        self.current_cursor = self.cursor()
        if start_expanded is False:
            self.set_expanded(False)

    @property
    def has_content(self) -> bool:
        return getattr(self.content, "has_content", self.content is not None)

    @property
    def full_text(self) -> str:

        if self.has_content is False:
            text = self.no_content_text
            prefix = self.no_content_prefix

        elif self.expanded is True:
            text = self.text or self.collapse_text
            prefix = self.collapse_prefix + " "

        else:
            text = self.text or self.expand_prefix
            prefix = self.expand_prefix + " "
        return f"{prefix}{text}"

    @ property
    def layout(self) -> QGridLayout:
        return super().layout()

    def mousePressEvent(self, event: PySide6.QtGui.QMouseEvent) -> None:
        if not self.contentsRect().contains(event.position().toPoint()):
            self.on_title_clicked()

    def event(self, event: PySide6.QtCore.QEvent) -> bool:
        if event.type() == QEvent.HoverMove:
            if self.has_content is True and not self.contentsRect().contains(event.position().toPoint()) and self.current_cursor is not Qt.PointingHandCursor:
                self.setCursor(Qt.PointingHandCursor)
            elif self.contentsRect().contains(event.position().toPoint()) and self.current_cursor is not self.original_cursor:
                self.setCursor(self.original_cursor)

        return super().event(event)

    def leaveEvent(self, event: PySide6.QtCore.QEvent) -> None:
        self.setCursor(self.original_cursor)
        return super().leaveEvent(event)

    def on_title_clicked(self):
        if self.has_content:
            self.set_expanded(not self.expanded)

    def set_expanded(self, value: bool):
        self.expanded = value
        self.content.setVisible(value)
        self.setTitle(self.full_text)

    def set_content(self, content: QWidget) -> None:
        if self.has_content is True:
            self.layout.removeWidget(self.content)
        self.content = content
        self.layout.addWidget(self.content)
        self.setTitle(self.full_text)

        if self.has_content is False and self.expanded is True:
            self.set_expanded(False)
# region[Main_Exec]


if __name__ == '__main__':
    pass

# endregion[Main_Exec]
