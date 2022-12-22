"""
WiP.

Soon.
"""

# region [Imports]

# * Standard Library Imports ---------------------------------------------------------------------------->
from typing import TYPE_CHECKING, Union, Iterable
from pathlib import Path
from operator import and_
from functools import reduce

# * Qt Imports --------------------------------------------------------------------------------------->
from PySide6.QtGui import QDrag, QAction, QPixmap, QMouseEvent, QDesktopServices
from PySide6.QtCore import Qt, QUrl, Signal, QMimeData
from PySide6.QtWidgets import QLabel, QWidget, QComboBox, QLineEdit, QFileDialog, QFormLayout, QMainWindow, QVBoxLayout, QApplication

# * Gid Imports ----------------------------------------------------------------------------------------->
from gidapptools import get_logger
from gidapptools.gidapptools_qt.widgets.spinner_widget import BusyPushButton

# * Local Imports --------------------------------------------------------------------------------------->
from antistasi_logbook.storage.models.models import Message, LogRecord
from antistasi_logbook.gui.widgets.base_tool_bar import BaseToolBar
from antistasi_logbook.gui.models.log_records_model import LogRecordsModel
from antistasi_logbook.gui.views.log_records_query_view import LogRecordsQueryView
from antistasi_logbook.gui.widgets.form_widgets.type_widgets import PathValueField
from antistasi_logbook.gui.resources.antistasi_logbook_resources_accessor import AllResourceItems

# * Type-Checking Imports --------------------------------------------------------------------------------->
if TYPE_CHECKING:
    from antistasi_logbook.gui.application import AntistasiLogbookApplication
    from antistasi_logbook.storage.models.models import LogFile
    from antistasi_logbook.gui.views.log_files_query_view import LogFilesQueryTreeView

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
            self.drag_start_pos = event.position().toPoint()

        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if event.buttons() & Qt.LeftButton and (event.position().toPoint() - self.drag_start_pos).manhattanLength() >= QApplication.startDragDistance():

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


class FindLogRecordsForm(QWidget):
    search_done = Signal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setLayout(QFormLayout())
        self.setup_fields()

        self.start_search_button = BusyPushButton(text="Search", disable_while_spinning=True, spinner_size=None)
        self.start_search_button.pressed.connect(self.search)
        self.layout.addWidget(self.start_search_button)
        self.setObjectName(self.__class__.__name__)
        self._tab_id: int = None
        self._model: LogRecordsModel = None
        self.search_done.connect(self.show_result)

    def setup_fields(self) -> None:
        self.search_text_field = QLineEdit()
        self.layout.addRow("Search for:", self.search_text_field)

        self.filter_by_server_field = QComboBox()

    def _set_query(self):
        query_filter = []
        text = rf"%{self.search_text_field.text()}%"
        query_filter.append((Message.text ** text))
        self._model.filter_item = reduce(and_, query_filter)
        self._model.ordered_by = (LogRecord.log_file, LogRecord.recorded_at)
        log.info("amount to query: %r", self._model.amount_items_to_query())
        self._model.refresh()

    def search(self):
        self.search_text_field.setEnabled(False)
        self._model = LogRecordsModel()
        future = self.app.gui_thread_pool.submit(self._set_query)
        future.add_done_callback(lambda x: self.search_done.emit())
        self.start_search_button.start_spinner_while_future(future)

    def show_result(self):
        view = LogRecordsQueryView(parent=None)
        view.setModel(self._model)
        _id = self.app.main_window.main_widget.main_tabs_widget.add_normal_tab(view, icon=AllResourceItems.zoom_in_cursor_image.get_as_icon(), label=f"SEARCH {self.search_text_field.text()!r}")
        self.app.main_window.main_widget.main_tabs_widget.setCurrentIndex(_id)
        self.search_text_field.setEnabled(True)

    def _close_tab(self, index: int):
        if index == self._tab_id:
            self.app.main_window.main_widget.main_tabs_widget.removeTab(self._tab_id)

    @property
    def layout(self) -> QFormLayout:
        return super().layout()

    @property
    def app(self) -> "AntistasiLogbookApplication":
        return QApplication.instance()

    def show(self) -> None:
        self.app.extra_windows.add_window(self)

        return super().show()


class PathSelectValueField(PathValueField):

    def open_path_browser(self, checked: bool = False):
        file_name, _ = QFileDialog.getOpenFileName(caption="Select File", dir=str(self.base_dir), filter=f"*{self.file_extension}")
        if file_name:
            file_name = Path(file_name)
            self.path_part.setText(file_name.as_posix())
            self.base_dir = file_name.parent if file_name.is_file() else file_name


class LogFileToolBar(BaseToolBar):

    def __init__(self, parent: Union[QMainWindow, QWidget] = None) -> None:
        super().__init__(parent, "Log-Files")

    def setup_actions(self):
        super().setup_actions()
        self.add_local_log_file_action = QAction(AllResourceItems.add_local_log_file_image.get_as_icon(), "Add Local Log-File", self)
        self.addAction(self.add_local_log_file_action)
        self.export_action_widget = DragIconLabel(pixmap=AllResourceItems.txt_file_image.get_as_pixmap(), text="Original File", parent=self)
        self.addWidget(self.export_action_widget)
        self.show_records_action = QAction(AllResourceItems.log_records_tab_icon_image.get_as_icon(), "Show Records", self)
        self.addAction(self.show_records_action)
        self.find_log_records_action = QAction(AllResourceItems.search_page_symbol_image.get_as_icon(), "Find Log-records", self)
        self.addAction(self.find_log_records_action)

        self.find_log_records_action.triggered.connect(self.on_find_log_records)

    def on_find_log_records(self):
        form = FindLogRecordsForm(parent=None)
        form.show()


# region[Main_Exec]
if __name__ == '__main__':
    pass

# endregion[Main_Exec]
