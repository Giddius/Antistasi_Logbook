"""
WiP.

Soon.
"""

# region [Imports]

# * Standard Library Imports ---------------------------------------------------------------------------->
from typing import TYPE_CHECKING, Optional, Any
from pathlib import Path

# * Third Party Imports --------------------------------------------------------------------------------->
from peewee import Field, Query
from antistasi_logbook.storage.models.models import Server, GameMap, LogFile
from antistasi_logbook.gui.models.base_query_data_model import BaseQueryDataModel, INDEX_TYPE
from functools import reduce
from operator import or_, and_
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
                           QKeySequence, QLinearGradient, QPainter, QPalette, QPixmap, QRadialGradient, QTransform, Qt)

from PySide6.QtWidgets import (QApplication, QBoxLayout, QCheckBox, QColorDialog, QColumnView, QComboBox, QDateTimeEdit, QDialogButtonBox,
                               QDockWidget, QDoubleSpinBox, QFontComboBox, QFormLayout, QFrame, QGridLayout, QGroupBox, QHBoxLayout, QHeaderView,
                               QLCDNumber, QLabel, QLayout, QLineEdit, QListView, QListWidget, QMainWindow, QMenu, QMenuBar, QMessageBox,
                               QProgressBar, QProgressDialog, QPushButton, QSizePolicy, QSpacerItem, QSpinBox, QStackedLayout, QStackedWidget,
                               QStatusBar, QStyledItemDelegate, QSystemTrayIcon, QTabWidget, QTableView, QTextEdit, QTimeEdit, QToolBox, QTreeView,
                               QVBoxLayout, QWidget, QAbstractItemDelegate, QAbstractItemView, QAbstractScrollArea, QRadioButton, QFileDialog, QButtonGroup)

from datetime import datetime, timedelta, timezone
from dateutil.tz import UTC
from tzlocal import get_localzone
# * Gid Imports ----------------------------------------------------------------------------------------->
from gidapptools import get_logger
from peewee import JOIN
if TYPE_CHECKING:
    # * Third Party Imports --------------------------------------------------------------------------------->
    from antistasi_logbook.backend import Backend
    from antistasi_logbook.storage.models.models import BaseModel

# endregion[Imports]

# region [TODO]


# endregion [TODO]

# region [Logging]


# endregion[Logging]

# region [Constants]

THIS_FILE_DIR = Path(__file__).parent.absolute()
log = get_logger(__name__)
# endregion[Constants]


class FakeField:

    def __init__(self, name: str, verbose_name: str) -> None:
        self.name = name
        self.verbose_name = verbose_name
        self.help_text = None


class LogFilesModel(BaseQueryDataModel):

    def __init__(self, backend: "Backend", parent: Optional[QtCore.QObject] = None, show_unparsable: bool = False) -> None:
        self.show_unparsable = show_unparsable
        super().__init__(backend, LogFile, parent=parent)
        self.ordered_by = (-LogFile.modified_at, LogFile.server)
        self.filters = {}

    @property
    def column_names_to_exclude(self) -> set[str]:
        _out = self._column_names_to_exclude.union({'header_text', 'startup_text', 'utc_offset', 'last_parsed_datetime', 'last_parsed_line_number', "remote_path"})
        if self.show_unparsable is False:
            _out.add("unparsable")
        return _out

    @property
    def column_ordering(self) -> dict[str, int]:
        return self._column_ordering | {"server": 2, "remote_path": 100}

    def on_filter_newer_than(self, dt: datetime):
        if not isinstance(dt, datetime):
            dt = None
        if dt is None and "newer_than" in self.filters:
            del self.filters["newer_than"]
            self.refresh()

        if dt is not None:
            self.filters["newer_than"] = (LogFile.modified_at >= dt)
            self.refresh()

    def on_filter_by_new_campaign(self, checked):
        if not checked and "new_campaign" in self.filters:
            del self.filters["new_campaign"]
            self.refresh()

        elif checked:
            self.filters["new_campaign"] = (LogFile.is_new_campaign == True)
            self.refresh()

    def on_filter_older_than(self, dt: datetime):
        if not isinstance(dt, datetime):
            dt = None
        if dt is None and "older_than" in self.filters:
            del self.filters["older_than"]
            self.refresh()

        if dt is not None:
            self.filters["older_than"] = (LogFile.modified_at <= dt)
            self.refresh()

    def filter_by_server(self, server_id: int):

        if server_id == -1 and "server" in self.filters:
            del self.filters["server"]
            self.refresh()

        elif server_id != -1:
            self.filters["server"] = (LogFile.server_id == server_id)
            self.refresh()

    def filter_by_game_map(self, game_map_id: int):

        if game_map_id == -1 and "game_map" in self.filters:
            del self.filters["game_map"]
            self.refresh()

        elif game_map_id != -1:
            self.filters["game_map"] = (LogFile.game_map_id == game_map_id)
            self.refresh()

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
        if len(self.filters.values()) != 0:
            query = query.where(reduce(and_, self.filters.values()))
        return query.order_by(*self.ordered_by)

    def get_content(self) -> "BaseQueryDataModel":
        with self.backend.database:
            self.content_items = list(self.get_query().execute())

        return self

    def get_columns(self) -> "BaseQueryDataModel":
        columns = [field for field_name, field in LogFile._meta.fields.items() if field_name not in self.column_names_to_exclude]
        columns.append(FakeField(name="amount_log_records", verbose_name="Amount Log Records"))
        self.columns = tuple(sorted(columns, key=lambda x: self.column_ordering.get(x.name.casefold(), 99)))
        return self

    def _get_tool_tip_data(self, index: INDEX_TYPE) -> Any:
        item = self.content_items[index.row()]
        column = self.columns[index.column()]
        if column.name == "marked":
            if item.marked is True:
                return "This Log-File is marked"
            else:
                return "This Log-File is not marked"
        elif column.name == "game_map":
            if item.game_map.map_image_low_resolution is not None:
                return f'<b>{item.game_map.map_image_low_resolution.stem.removesuffix("_thumbnail").replace("_"," ").title()}</b><br><img src="{item.game_map.map_image_low_resolution.as_posix()}">'
        return super()._get_tool_tip_data(index)
# region[Main_Exec]


if __name__ == '__main__':
    pass

# endregion[Main_Exec]
