"""
WiP.

Soon.
"""

# region [Imports]

# * Standard Library Imports ---------------------------------------------------------------------------->
from typing import TYPE_CHECKING, Union, Iterable
from pathlib import Path

# * Qt Imports --------------------------------------------------------------------------------------->
from PySide6.QtGui import QDrag, QAction, QPixmap, QMouseEvent, QDesktopServices
from PySide6.QtCore import Qt, QUrl, QSize, QMimeData
from PySide6.QtWidgets import QLabel, QWidget, QToolBar, QMainWindow, QVBoxLayout, QApplication

# * Gid Imports ----------------------------------------------------------------------------------------->
from gidapptools import get_logger

# * Local Imports --------------------------------------------------------------------------------------->
from antistasi_logbook.gui.resources.antistasi_logbook_resources_accessor import AllResourceItems

# * Type-Checking Imports --------------------------------------------------------------------------------->
if TYPE_CHECKING:
    from antistasi_logbook.storage.models.models import LogFile
    from antistasi_logbook.gui.views.log_files_query_view import LogFilesQueryTreeView
    from antistasi_logbook.gui.models.base_query_data_model import BaseQueryDataModel
    from antistasi_logbook.gui.application import AntistasiLogbookApplication

# endregion[Imports]

# region [TODO]


# endregion [TODO]

# region [Logging]


# endregion[Logging]

# region [Constants]


THIS_FILE_DIR = Path(__file__).parent.absolute()
log = get_logger(__name__)

# endregion[Constants]


class DragIconLabel(QWidget):
    pixmap_width = 50
    pixmap_height = 50

    def __init__(self, pixmap: QPixmap, text: str = None, items: Iterable["LogFilesQueryTreeView"] = None, parent=None):
        super().__init__(parent=parent)
        self.setLayout(QVBoxLayout())
        self.items = items
        self.drag_start_pos = None
        self._pixmap = pixmap.scaled(self.parent().iconSize(), Qt.KeepAspectRatioByExpanding, Qt.TransformationMode.SmoothTransformation)
        self.icon_label = QLabel(parent=self)
        self.icon_label.setPixmap(self._pixmap)
        self.icon_label.setAlignment(Qt.AlignHCenter | Qt.AlignBottom)

        self.layout.addWidget(self.icon_label)

        self.text_label = QLabel(text or "", parent=self)
        self.text_label.setAlignment(Qt.AlignHCenter | Qt.AlignBottom)
        self.layout.addWidget(self.text_label)
        self.layout.setAlignment(Qt.AlignCenter)
        self.setToolTip("Drag and drop into the folder where you want to save the file")
        self.setEnabled(False)

    @property
    def layout(self) -> QVBoxLayout:
        return super().layout()

    def set_items(self, items: Iterable["LogFile"]):
        self.items = items
        if self.items is not None:
            self.setEnabled(True)
        else:
            self.setEnabled(False)

    def mouseDoubleClickEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.LeftButton:
            for item in self.items:
                original_file: Path = item.original_file.to_file()
                QDesktopServices.openUrl(QUrl.fromLocalFile(original_file))

        else:
            super().mouseDoubleClickEvent(event)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.LeftButton:
            self.drag_start_pos = event.pos()

        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if event.buttons() & Qt.LeftButton and (event.pos() - self.drag_start_pos).manhattanLength() >= QApplication.startDragDistance():

            if self.items:
                try:
                    drag = QDrag(self)
                    drag.setPixmap(self._pixmap)
                    self.icon_label.clear()
                    mime_data = QMimeData()
                    urls = []
                    for item in self.items:

                        original_file: Path = item.original_file.to_file()
                        urls.append(QUrl.fromLocalFile(original_file))

                    mime_data.setData("text/plain", b"")
                    mime_data.setUrls(urls)
                    drag.setMimeData(mime_data)
                    drag.exec(Qt.CopyAction)
                finally:
                    self.icon_label.setPixmap(self._pixmap)
        else:
            super().mouseMoveEvent(event)

    def __repr__(self) -> str:
        """
        Basic Repr
        !REPLACE!
        """
        return f'{self.__class__.__name__}'


class BaseToolBar(QToolBar):

    def __init__(self, parent: Union[QMainWindow, QWidget] = None, title: str = None) -> None:
        super().__init__(*[i for i in (parent, title) if i])
        self.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        self.setOrientation(Qt.Horizontal)
        self.setMovable(False)
        self.setFloatable(False)
        self.setAllowedAreas(Qt.TopToolBarArea)
        self.setIconSize(QSize(35, 35))
        self.setMinimumHeight(85)
        self.setup_actions()

    def setup_actions(self):
        self.addSeparator()

    @property
    def app(self) -> "AntistasiLogbookApplication":
        return QApplication.instance()

    def __repr__(self) -> str:
        """
        Basic Repr
        !REPLACE!
        """
        return f'{self.__class__.__name__}'


class LogFileToolBar(BaseToolBar):

    def __init__(self, parent: Union[QMainWindow, QWidget] = None) -> None:
        super().__init__(parent, "Log-Files")

    def setup_actions(self):
        super().setup_actions()
        self.export_action_widget = DragIconLabel(pixmap=AllResourceItems.txt_file_image.get_as_pixmap(), text="Original File", parent=self)
        self.addWidget(self.export_action_widget)
        self.show_records_action = QAction(AllResourceItems.log_records_tab_icon_image.get_as_icon(), "Show Records", self)
        self.addAction(self.show_records_action)


class LogRecordToolBar(BaseToolBar):

    def __init__(self, parent: Union[QMainWindow, QWidget] = None) -> None:
        super().__init__(parent, "Log-Records")

    def set_title_from_log_file(self, log_file: "LogFile"):
        self.setWindowTitle(f"Log-Records of {log_file}")

    def setup_actions(self):
        super().setup_actions()
        self.font_settings_action = QAction(AllResourceItems.font_settings_image.get_as_icon(), "Font Settings", self)
        self.addAction(self.font_settings_action)


# region[Main_Exec]
if __name__ == '__main__':
    pass

# endregion[Main_Exec]
