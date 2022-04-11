"""
WiP.

Soon.
"""

# region [Imports]

# * Standard Library Imports ---------------------------------------------------------------------------->
from typing import TYPE_CHECKING
from pathlib import Path

# * Qt Imports --------------------------------------------------------------------------------------->
from PySide6.QtGui import QPainter
from PySide6.QtCore import Qt, QRect, QSize, QModelIndex
from PySide6.QtWidgets import QStyle, QStyledItemDelegate

# * Gid Imports ----------------------------------------------------------------------------------------->
from gidapptools import get_logger

# * Local Imports --------------------------------------------------------------------------------------->
from antistasi_logbook.gui.misc import CustomRole
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


class BaseItemDelegate(QStyledItemDelegate):
    def handle_background(self, painter: QPainter, option, index: QModelIndex):

        item_background = index.model().data(index, Qt.BackgroundRole)
        if item_background:
            painter.fillRect(option.rect, item_background)
        if option.state & QStyle.State_Selected:
            color = option.widget.palette().highlight().color()
            color.setAlpha(50)
            painter.fillRect(option.rect, color)
        elif option.state & QStyle.State_MouseOver:
            color = option.widget.palette().highlight().color()
            color.setAlpha(25)
            painter.fillRect(option.rect, color)

    def sizeHint(self, option, index):
        """ Returns the size needed to display the item in a QSize object. """
        return QSize(20, 20)

    def __repr__(self) -> str:
        """
        Basic Repr
        !REPLACE!
        """
        return f'{self.__class__.__name__}'


class MarkedImageDelegate(BaseItemDelegate):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.pixmaps = {True: AllResourceItems.mark_image.get_as_pixmap(25, 25), False: AllResourceItems.unmark_image.get_as_pixmap(25, 25)}

    def paint(self, painter: QPainter, option, index: QModelIndex):
        self.handle_background(painter, option, index)
        raw_data = index.model().data(index, CustomRole.RAW_DATA)
        painter.setRenderHint(QPainter.SmoothPixmapTransform, True)
        target_rect = QRect(option.rect)
        target_rect.setHeight(25)
        target_rect.setWidth(25)
        target_rect.moveCenter(option.rect.center())
        painter.drawPixmap(target_rect, self.pixmaps[raw_data])


class BoolImageDelegate(BaseItemDelegate):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.pixmaps = {True: AllResourceItems.check_mark_green_image.get_as_pixmap(25, 25), False: AllResourceItems.close_cancel_image.get_as_pixmap(25, 25)}

    def paint(self, painter: QPainter, option, index: QModelIndex):
        self.handle_background(painter, option, index)

        raw_data = index.model().data(index, CustomRole.RAW_DATA)
        if raw_data is True:
            painter.setRenderHint(QPainter.SmoothPixmapTransform, True)
            target_rect = QRect(option.rect)
            target_rect.setHeight(25)
            target_rect.setWidth(25)
            target_rect.moveCenter(option.rect.center())
            painter.drawPixmap(target_rect, self.pixmaps[raw_data])

        return f'{self.__class__.__name__}'

# region[Main_Exec]


if __name__ == '__main__':
    pass

# endregion[Main_Exec]
