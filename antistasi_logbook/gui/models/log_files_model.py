"""
WiP.

Soon.
"""

# region [Imports]

# * Standard Library Imports ---------------------------------------------------------------------------->
from typing import TYPE_CHECKING, Any, Optional
from pathlib import Path

# * Qt Imports --------------------------------------------------------------------------------------->
from PySide6 import QtCore
from PySide6.QtCore import Qt, Slot, QModelIndex
import PySide6
from PySide6 import (QtCore, QtGui, QtWidgets, Qt3DAnimation, Qt3DCore, Qt3DExtras, Qt3DInput, Qt3DLogic, Qt3DRender, QtAxContainer, QtBluetooth,
                     QtCharts, QtConcurrent, QtDataVisualization, QtDesigner, QtHelp, QtMultimedia, QtMultimediaWidgets, QtNetwork, QtNetworkAuth,
                     QtOpenGL, QtOpenGLWidgets, QtPositioning, QtPrintSupport, QtQml, QtQuick, QtQuickControls2, QtQuickWidgets, QtRemoteObjects,
                     QtScxml, QtSensors, QtSerialPort, QtSql, QtStateMachine, QtSvg, QtSvgWidgets, QtTest, QtUiTools, QtWebChannel, QtWebEngineCore,
                     QtWebEngineQuick, QtWebEngineWidgets, QtWebSockets, QtXml)

from PySide6.QtCore import (QByteArray, QCoreApplication, QDate, QDateTime, QEvent, QLocale, QMetaObject, QModelIndex, QModelRoleData, QMutex,
                            QMutexLocker, QObject, QPoint, QRect, QRecursiveMutex, QRunnable, QSettings, QSize, QThread, QThreadPool, QTime, QUrl,
                            QWaitCondition, QMimeData, Qt, QAbstractItemModel, QFileInfo, QAbstractListModel, QAbstractTableModel, Signal, Slot)

from PySide6.QtGui import (QAction, QDrag, QBrush, QMouseEvent, QDesktopServices, QColor, QConicalGradient, QCursor, QFont, QFontDatabase, QFontMetrics, QGradient, QIcon, QImage,
                           QKeySequence, QLinearGradient, QPainter, QPalette, QPixmap, QRadialGradient, QTransform)

from PySide6.QtWidgets import (QApplication, QBoxLayout, QCheckBox, QColorDialog, QColumnView, QComboBox, QDateTimeEdit, QDialogButtonBox,
                               QDockWidget, QDoubleSpinBox, QFontComboBox, QFormLayout, QFrame, QGridLayout, QGroupBox, QHBoxLayout, QHeaderView,
                               QLCDNumber, QLabel, QLayout, QLineEdit, QListView, QListWidget, QMainWindow, QMenu, QMenuBar, QMessageBox,
                               QProgressBar, QProgressDialog, QPushButton, QSizePolicy, QSpacerItem, QSpinBox, QStackedLayout, QStackedWidget,
                               QStatusBar, QStyledItemDelegate, QSystemTrayIcon, QTabWidget, QTableView, QTextEdit, QTimeEdit, QToolBox, QTreeView,
                               QVBoxLayout, QWidget, QAbstractItemDelegate, QAbstractItemView, QAbstractScrollArea, QRadioButton, QFileDialog, QButtonGroup)

# * Third Party Imports --------------------------------------------------------------------------------->
from peewee import JOIN, Field, Query

# * Gid Imports ----------------------------------------------------------------------------------------->
from gidapptools import get_logger

# * Local Imports --------------------------------------------------------------------------------------->
from antistasi_logbook.storage.models.models import Server, GameMap, LogFile
from antistasi_logbook.storage.models.custom_fields import FakeField
from antistasi_logbook.gui.models.base_query_data_model import INDEX_TYPE, BaseQueryDataModel, ModelContextMenuAction
from antistasi_logbook.gui.resources.antistasi_logbook_resources_accessor import AllResourceItems
# * Type-Checking Imports --------------------------------------------------------------------------------->
if TYPE_CHECKING:
    from antistasi_logbook.storage.models.models import BaseModel
    from antistasi_logbook.gui.views.base_query_tree_view import CustomContextMenu

# endregion[Imports]

# region [TODO]


# endregion [TODO]

# region [Logging]


# endregion[Logging]

# region [Constants]

THIS_FILE_DIR = Path(__file__).parent.absolute()
log = get_logger(__name__)
# endregion[Constants]


class DragIconLabel(QLabel):
    pixmap_width = 50
    pixmap_height = 50

    def __init__(self, pixmap: QPixmap, item: "LogFile", parent=None):
        super().__init__(parent=parent)
        self.item = item
        self.drag_start_pos = None
        self._pixmap = pixmap.scaled(QSize(self.pixmap_width, self.pixmap_height), Qt.KeepAspectRatioByExpanding, Qt.TransformationMode.SmoothTransformation)
        self.setAlignment(Qt.AlignCenter)
        self.setPixmap(self._pixmap)
        self.setToolTip("Drag and drop into the folder where you want to save the file")

    def mouseDoubleClickEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.LeftButton:
            original_file: Path = self.item.original_file.to_file()
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
            drag = QDrag(self)
            drag.setPixmap(self._pixmap)
            self.clear()
            mime_data = QMimeData()

            original_file: Path = self.item.original_file.to_file()

            mime_data.setData("text/plain", b"")
            mime_data.setUrls([QUrl.fromLocalFile(original_file)])
            drag.setMimeData(mime_data)
            drag.exec(Qt.CopyAction)

            self.setPixmap(self._pixmap)
        else:
            super().mouseMoveEvent(event)


class DragTargetWindow(QWidget):

    def __init__(self, item: "LogFile", parent: Optional[PySide6.QtWidgets.QWidget] = None, f: PySide6.QtCore.Qt.WindowFlags = None) -> None:
        super().__init__(*(i for i in [parent, f] if i))
        self.item = item
        self.setLayout(QVBoxLayout())
        self.drag_start_label = DragIconLabel(AllResourceItems.txt_file_image.get_as_pixmap(), item=self.item, parent=self)
        self.layout.addWidget(self.drag_start_label)
        self.close_button = QPushButton("close")
        self.close_button.clicked.connect(self.close)
        self.layout.addWidget(self.close_button)
        self.setWindowModality(Qt.ApplicationModal)
        self.setWindowFlags(Qt.WindowFlags() | Qt.FramelessWindowHint)

    @property
    def layout(self) -> QVBoxLayout:
        return super().layout()


class LogFilesModel(BaseQueryDataModel):
    extra_columns = {FakeField(name="amount_log_records", verbose_name="Records"),
                     FakeField("time_frame", "Time Frame"),
                     FakeField(name="amount_errors", verbose_name="Errors"),
                     FakeField(name="amount_warnings", verbose_name="Warnings")}
    strict_exclude_columns = {"startup_text", "remote_path", "header_text", "original_file"}

    def __init__(self, parent: Optional[QtCore.QObject] = None) -> None:
        self.show_unparsable = False
        super().__init__(LogFile, parent=parent)
        self.ordered_by = (-LogFile.modified_at, LogFile.server)
        self.filter_item = None
        self.currently_reparsing: bool = False

    def add_context_menu_actions(self, menu: "CustomContextMenu", index: QModelIndex):
        super().add_context_menu_actions(menu, index)
        item, column = self.get(index)

        if item is None or column is None:
            return
        force_reparse_action = ModelContextMenuAction(item, column, index, text=f"Force Reparse {item.name}", parent=menu)
        force_reparse_action.clicked.connect(self.reparse_log_file)
        if self.currently_reparsing is True:
            force_reparse_action.setEnabled(False)
        menu.add_action(force_reparse_action)

        get_original_file_option = ModelContextMenuAction(item, column, index, text=f"Get original file '{item.name}.txt'", parent=menu)
        get_original_file_option.clicked.connect(self.get_original_file)
        menu.add_action(get_original_file_option)

    @Slot(object, object, QModelIndex)
    def reparse_log_file(self, item: LogFile, column: Field, index: QModelIndex):
        def _actual_reparse(log_file: LogFile):
            self.backend.updater.process_log_file(log_file=log_file, force=True)
            self.backend.updater.update_record_classes(server=log_file.server, force=True)
            self.refresh()

        def _callback(future):
            self.layoutChanged.emit()
            self.currently_reparsing = False

        self.currently_reparsing = True
        self.layoutAboutToBeChanged.emit()
        task = self.backend.thread_pool.submit(_actual_reparse, item)
        task.add_done_callback(_callback)

    @Slot(object, object, QModelIndex)
    def get_original_file(self, item: LogFile, column: Field, index: QModelIndex):
        self.drag_window = DragTargetWindow(item=item)
        pos = QCursor.pos()
        self.drag_window.move(pos)
        self.drag_window.show()

    def change_show_unparsable(self, show_unparsable):
        if show_unparsable and self.show_unparsable is False:
            self.show_unparsable = True
            self.refresh()

        elif not show_unparsable and self.show_unparsable is True:
            self.show_unparsable = False
            self.refresh()

    def on_display_data_bool(self, role: int, item: "BaseModel", column: "Field", value: bool) -> str:
        if role == Qt.DisplayRole:
            if column.name in {"is_new_campaign"}:
                return ''

            return super().on_display_data_bool(role=role, item=item, column=column, value=value)
        if role == Qt.DecorationRole:
            if column.name in {"is_new_campaign"}:
                return self.bool_images[True] if value is True else None

            return super().on_display_data_bool(role=role, item=item, column=column, value=value)

    def get_query(self) -> "Query":
        query = LogFile.select().join(GameMap, join_type=JOIN.LEFT_OUTER).switch(LogFile).join(Server).switch(LogFile)
        if self.show_unparsable is False:
            query = query.where(LogFile.unparsable == False)
        if self.filter_item is not None:
            query = query.where(self.filter_item)
        return query.order_by(*self.ordered_by)

    def get_content(self) -> "BaseQueryDataModel":
        with self.backend.database:
            self.content_items = list(self.get_query().execute())

        return self

    def _get_tool_tip_data(self, index: INDEX_TYPE) -> Any:
        item = self.content_items[index.row()]
        column = self.columns[index.column()]
        if column.name == "marked":
            if item.marked is True:
                return "This Log-File is marked"
            else:
                return "This Log-File is not marked"

        return super()._get_tool_tip_data(index)
# region[Main_Exec]


if __name__ == '__main__':
    pass

# endregion[Main_Exec]
