"""
WiP.

Soon.
"""

# region [Imports]

# * Standard Library Imports ---------------------------------------------------------------------------->
import os
from typing import TYPE_CHECKING, Optional
from pathlib import Path

# * Third Party Imports --------------------------------------------------------------------------------->
from peewee import Query

# * Qt Imports --------------------------------------------------------------------------------------->
import PySide6
from PySide6 import (QtCore, QtGui, QtWidgets, Qt3DAnimation, Qt3DCore, Qt3DExtras, Qt3DInput, Qt3DLogic, Qt3DRender, QtAxContainer, QtBluetooth,
                     QtCharts, QtConcurrent, QtDataVisualization, QtDesigner, QtHelp, QtMultimedia, QtMultimediaWidgets, QtNetwork, QtNetworkAuth,
                     QtOpenGL, QtOpenGLWidgets, QtPositioning, QtPrintSupport, QtQml, QtQuick, QtQuickControls2, QtQuickWidgets, QtRemoteObjects,
                     QtScxml, QtSensors, QtSerialPort, QtSql, QtStateMachine, QtSvg, QtSvgWidgets, QtTest, QtUiTools, QtWebChannel, QtWebEngineCore,
                     QtWebEngineQuick, QtWebEngineWidgets, QtWebSockets, QtXml)

from PySide6.QtCore import (QByteArray, QCoreApplication, QDate, QDateTime, QEvent, QLocale, QMetaObject, QModelIndex, QModelRoleData, QMutex,
                            QMutexLocker, QObject, QPoint, QRect, QRecursiveMutex, QRunnable, QSettings, QSize, QThread, QThreadPool, QTime, QUrl,
                            QWaitCondition, Qt, QAbstractItemModel, QAbstractListModel, QAbstractTableModel, Signal, Slot, QIdentityProxyModel)

from PySide6.QtGui import (QAction, QBrush, QColor, QConicalGradient, QCursor, QFont, QFontDatabase, QFontMetrics, QGradient, QIcon, QImage,
                           QKeySequence, QLinearGradient, QPainter, QPalette, QPixmap, QRadialGradient, QTransform)

from PySide6.QtWidgets import (QApplication, QBoxLayout, QCheckBox, QColorDialog, QColumnView, QComboBox, QDateTimeEdit, QDialogButtonBox,
                               QDockWidget, QDoubleSpinBox, QFontComboBox, QFormLayout, QFrame, QGridLayout, QGroupBox, QHBoxLayout, QHeaderView,
                               QLCDNumber, QLabel, QLayout, QLineEdit, QListView, QListWidget, QMainWindow, QMenu, QMenuBar, QMessageBox,
                               QProgressBar, QProgressDialog, QPushButton, QSizePolicy, QSpacerItem, QSpinBox, QStackedLayout, QStackedWidget,
                               QStatusBar, QStyledItemDelegate, QSystemTrayIcon, QTabWidget, QTableView, QTextEdit, QTimeEdit, QToolBox, QTreeView,
                               QVBoxLayout, QWidget, QAbstractItemDelegate, QAbstractItemView, QAbstractScrollArea, QRadioButton, QFileDialog, QButtonGroup)

# * Gid Imports ----------------------------------------------------------------------------------------->
from gidapptools import get_logger

# * Local Imports --------------------------------------------------------------------------------------->
from antistasi_logbook.storage.models.models import Server, RemoteStorage
from antistasi_logbook.gui.models.base_query_data_model import INDEX_TYPE, Field, BaseModel, BaseQueryDataModel, ModelContextMenuAction
from antistasi_logbook.gui.models.proxy_models.base_proxy_model import BaseProxyModel
# * Type-Checking Imports --------------------------------------------------------------------------------->
if TYPE_CHECKING:
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


def get_int_from_name(name: str, default: int = -1) -> int:
    int_string = ''.join(c for c in name if c.isnumeric())
    try:
        return int(int_string)
    except ValueError:
        return default


class ServerModel(BaseQueryDataModel):
    extra_columns = set()
    color_config_name = "server"

    def __init__(self, parent: Optional[QtCore.QObject] = None, show_local_files_server: bool = False) -> None:
        self.show_local_files_server = show_local_files_server
        super().__init__(db_model=Server, parent=parent)
        self.ordered_by = (-Server.name, Server.id)
        self.data_role_table = self.data_role_table | {Qt.BackgroundRole: self._get_background_data}

    def _get_background_data(self, index: INDEX_TYPE):
        item, colum = self.get(index)
        _out = self.color_config.get(self.color_config_name, item.name, default=QColor(255, 255, 255, 0))

        return _out

    def get_query(self) -> "Query":
        query = Server.select(Server, RemoteStorage).join(RemoteStorage).switch(Server)
        if self.show_local_files_server is False:
            query = query.where((Server.remote_path.is_null(False)))
        if self.filter_item is not None:
            query = query.where(self.filter_item)
        return query.order_by(*self.ordered_by)

    def get_content(self) -> "BaseQueryDataModel":
        def _sort_func(item: Server) -> int:
            is_main = item.name.casefold().startswith("main")
            name_number = get_int_from_name(item.name, 100)
            return is_main, -name_number

        with self.backend.database:
            self.content_items = sorted(list(self.get_query().execute()), key=_sort_func, reverse=True)
            self.original_sort_order = tuple(i.id for i in self.content_items)

        return self

    def add_context_menu_actions(self, menu: "CustomContextMenu", index: QModelIndex):
        super().add_context_menu_actions(menu, index)
        item, column = self.get(index)
        if item is None or column is None:
            return
        update_enabled_text = f"Enable Updates for {item}" if item.update_enabled is False else f"Disable Updates for {item.pretty_name}"
        update_enabled_action = ModelContextMenuAction(item, column, index, text=update_enabled_text, parent=menu)
        update_enabled_action.clicked.connect(self.change_update_enabled)
        menu.add_action(update_enabled_action, "Edit")

        change_remote_path_action = ModelContextMenuAction(item, column, index, text=f"Change Remote-Path for {item.pretty_name!r}", parent=menu)
        change_remote_path_action.clicked.connect(self.change_remote_path)
        menu.add_action(change_remote_path_action, "Edit")

    @Slot(object, object, QModelIndex)
    def change_update_enabled(self, item: BaseModel, column: Field, index: QModelIndex):
        update_enabled_index = self.index(index.row(), self.get_column_index("update_enabled"), index.parent())
        self.setData(update_enabled_index, not item.update_enabled, role=Qt.DisplayRole)

    @Slot(object, object, QModelIndex)
    def change_remote_path(self, item: BaseModel, column: Field, index: QModelIndex):
        change_remote_path_index = self.index(index.row(), self.get_column_index("remote_path"), index.parent())
        new_path, accepted = QInputDialog.getText(self.parent(), f'New Remote-Path for {item.pretty_name!r}',
                                                  f"please enter an valid path for {item.pretty_name!r}\n if this is a Next-Cloud server, the Path is CASE-SENSITIVE!", QLineEdit.EchoMode.Normal)
        if not accepted:
            return
        new_remote_path = new_path.replace(os.pathsep, "/").lstrip("/")
        self.setData(change_remote_path_index, new_remote_path, role=Qt.DisplayRole)


# region[Main_Exec]
if __name__ == '__main__':
    pass

# endregion[Main_Exec]
