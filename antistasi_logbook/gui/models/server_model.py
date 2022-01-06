"""
WiP.

Soon.
"""

# region [Imports]

# * Standard Library Imports ---------------------------------------------------------------------------->
from typing import TYPE_CHECKING, Optional, Any
from pathlib import Path

# * Third Party Imports --------------------------------------------------------------------------------->
from peewee import Query
from antistasi_logbook.storage.models.models import Server, RemoteStorage
from antistasi_logbook.gui.models.base_query_data_model import BaseQueryDataModel, INDEX_TYPE

# * PyQt5 Imports --------------------------------------------------------------------------------------->
import PySide6
from PySide6 import (QtCore, QtGui, QtWidgets, Qt3DAnimation, Qt3DCore, Qt3DExtras, Qt3DInput, Qt3DLogic, Qt3DRender, QtAxContainer, QtBluetooth,
                     QtCharts, QtConcurrent, QtDataVisualization, QtDesigner, QtHelp, QtMultimedia, QtMultimediaWidgets, QtNetwork, QtNetworkAuth,
                     QtOpenGL, QtOpenGLWidgets, QtPositioning, QtPrintSupport, QtQml, QtQuick, QtQuickControls2, QtQuickWidgets, QtRemoteObjects,
                     QtScxml, QtSensors, QtSerialPort, QtSql, QtStateMachine, QtSvg, QtSvgWidgets, QtTest, QtUiTools, QtWebChannel, QtWebEngineCore,
                     QtWebEngineQuick, QtWebEngineWidgets, QtWebSockets, QtXml)

from PySide6.QtCore import (QByteArray, QCoreApplication, QDate, QDateTime, QEvent, QLocale, QMetaObject, QModelIndex, QModelRoleData, QMutex,
                            QMutexLocker, QObject, QPoint, QRect, QRecursiveMutex, QRunnable, QSettings, QSize, QThread, QThreadPool, QTime, QUrl,
                            QWaitCondition, Qt, QAbstractItemModel, QAbstractListModel, QAbstractTableModel, Signal, Slot)

from PySide6.QtGui import (QAction, QBrush, QColor, QConicalGradient, QCursor, QFont, QFontDatabase, QFontMetrics, QGradient, QIcon, QImage,
                           QKeySequence, QLinearGradient, QPainter, QPalette, QPixmap, QRadialGradient, QTransform)

from PySide6.QtWidgets import (QApplication, QBoxLayout, QCheckBox, QColorDialog, QColumnView, QComboBox, QDateTimeEdit, QDialogButtonBox,
                               QDockWidget, QDoubleSpinBox, QFontComboBox, QFormLayout, QFrame, QGridLayout, QGroupBox, QHBoxLayout, QHeaderView,
                               QLCDNumber, QLabel, QLayout, QLineEdit, QListView, QListWidget, QMainWindow, QMenu, QMenuBar, QMessageBox,
                               QProgressBar, QProgressDialog, QPushButton, QSizePolicy, QSpacerItem, QSpinBox, QStackedLayout, QStackedWidget,
                               QStatusBar, QStyledItemDelegate, QSystemTrayIcon, QTabWidget, QTableView, QTextEdit, QTimeEdit, QToolBox, QTreeView,
                               QVBoxLayout, QWidget, QAbstractItemDelegate, QAbstractItemView, QAbstractScrollArea, QRadioButton, QFileDialog, QButtonGroup)

from gidapptools import get_logger
from antistasi_logbook.gui.misc import CustomRole
if TYPE_CHECKING:
    # * Third Party Imports --------------------------------------------------------------------------------->
    from antistasi_logbook.backend import Backend
    from peewee import ModelIndex
# endregion[Imports]

# region [TODO]


# endregion [TODO]

# region [Logging]


# endregion[Logging]

# region [Constants]

THIS_FILE_DIR = Path(__file__).parent.absolute()
log = get_logger(__name__)
# endregion[Constants]
SERVER_COLOR_ALPHA = 50
SERVER_COLORS = {"no_server": QColor(25, 25, 25, 100),
                 "mainserver_1": QColor(0, 255, 0, SERVER_COLOR_ALPHA),
                 "mainserver_2": QColor(250, 1, 217, SERVER_COLOR_ALPHA),
                 "testserver_1": QColor(0, 127, 255, SERVER_COLOR_ALPHA),
                 "testserver_2": QColor(235, 149, 0, SERVER_COLOR_ALPHA),
                 "testserver_3": QColor(255, 0, 0, SERVER_COLOR_ALPHA),
                 "eventserver": QColor(62, 123, 79, SERVER_COLOR_ALPHA)}


def get_int_from_name(name: str, default: int = -1) -> int:
    int_string = ''.join(c for c in name if c.isnumeric())
    try:
        return int(int_string)
    except ValueError:
        return default


class ServerModel(BaseQueryDataModel):
    extra_columns = set()

    def __init__(self, parent: Optional[QtCore.QObject] = None, show_local_files_server: bool = False) -> None:
        self.show_local_files_server = show_local_files_server
        super().__init__(db_model=Server, parent=parent)
        self.ordered_by = (-Server.name, Server.id)

    def get_query(self) -> "Query":
        query = Server.select().join(RemoteStorage).switch(Server)
        if self.show_local_files_server is False:
            query = query.where(Server.remote_path != None)
        return query.order_by(*self.ordered_by)

    def get_content(self) -> "BaseQueryDataModel":
        def _sort_func(item: Server) -> int:
            is_main = item.name.casefold().startswith("main")
            name_number = get_int_from_name(item.name, 100)
            return is_main, -name_number

        with self.backend.database:
            self.content_items = tuple(sorted(list(self.get_query().execute()), key=_sort_func, reverse=True))
            self.original_sort_order = tuple(i.id for i in self.content_items)
        log.debug("sort order = %r", self.content_items)
        return self

    def setData(self, index: "INDEX_TYPE", value: Any, role: int = ...) -> bool:
        item = self.content_items[index.row()]
        column = self.columns[index.column()]
        _out = False
        if role == Qt.DisplayRole:
            if column.name == "comments":
                with self.database.write_lock:
                    with self.database:
                        _out = bool(Server.update(comments=value).where(Server.id == item.id).execute())
        if role == CustomRole.UPDATE_ENABLED_ROLE:
            with self.database.write_lock:
                with self.database:
                    _out = bool(Server.update(update_enabled=value).where(Server.id == item.id).execute())

        elif role == CustomRole.MARKED_ROLE:
            with self.database.write_lock:
                with self.database:
                    _out = bool(Server.update(marked=value).where(Server.id == item.id).execute())

        else:
            _out = super().setData(index, value, role=role)
        self.refresh_item(index)
        return _out


# region[Main_Exec]
if __name__ == '__main__':
    pass

# endregion[Main_Exec]
