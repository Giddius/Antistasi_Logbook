"""
WiP.

Soon.
"""

# region [Imports]

# * Standard Library Imports ---------------------------------------------------------------------------->
from time import sleep
from typing import TYPE_CHECKING, Any, Union, Iterable, Callable, Optional, Mapping
from pathlib import Path
from operator import or_
from functools import reduce, cache
from threading import Lock, Event
from collections import namedtuple

# * Third Party Imports --------------------------------------------------------------------------------->
from peewee import Field, Query
from antistasi_logbook.storage.models.models import LogRecord, RecordClass, LogFile
from antistasi_logbook.gui.models.base_query_data_model import BaseQueryDataModel
from antistasi_logbook.gui.resources.antistasi_logbook_resources_accessor import AllResourceItems

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

from PySide6.QtWidgets import (QApplication, QDataWidgetMapper, QBoxLayout, QCheckBox, QColorDialog, QColumnView, QComboBox, QDateTimeEdit, QDialogButtonBox,
                               QDockWidget, QDoubleSpinBox, QFontComboBox, QFormLayout, QFrame, QGridLayout, QGroupBox, QHBoxLayout, QHeaderView,
                               QLCDNumber, QLabel, QLayout, QLineEdit, QListView, QListWidget, QMainWindow, QMenu, QMenuBar, QMessageBox,
                               QProgressBar, QProgressDialog, QPushButton, QSizePolicy, QSpacerItem, QSpinBox, QStackedLayout, QStackedWidget,
                               QStatusBar, QStyledItemDelegate, QSystemTrayIcon, QTabWidget, QTableView, QTextEdit, QTimeEdit, QToolBox, QTreeView,
                               QVBoxLayout, QWidget, QAbstractItemDelegate, QAbstractItemView, QAbstractScrollArea, QRadioButton, QFileDialog, QButtonGroup)

import pp
# * Gid Imports ----------------------------------------------------------------------------------------->
from gidapptools import get_logger
from gidapptools.general_helper.color.color_item import Color
from concurrent.futures import ThreadPoolExecutor, wait, ALL_COMPLETED
import attr
if TYPE_CHECKING:
    # * Third Party Imports --------------------------------------------------------------------------------->
    from antistasi_logbook.backend import Backend
    from antistasi_logbook.records.abstract_record import AbstractRecord
    from antistasi_logbook.records.base_record import BaseRecord
    from antistasi_logbook.gui.models.base_query_data_model import INDEX_TYPE

# endregion[Imports]

# region [TODO]


# endregion [TODO]

# region [Logging]


# endregion[Logging]

# region [Constants]
from gidapptools.general_helper.timing import get_dummy_profile_decorator_in_globals
get_dummy_profile_decorator_in_globals()
THIS_FILE_DIR = Path(__file__).parent.absolute()
log = get_logger(__name__)
# endregion[Constants]


def get_qsize_from_font(font: QFont, text: str) -> QSize:
    fm = QFontMetrics(font)
    return fm.boundingRect(text=text).size()


class RefreshWorker(QThread):
    finished = Signal()

    def __init__(self, model: "LogRecordsModel", **kwargs):
        self.model = model
        self.kwargs = kwargs
        super().__init__()

    def run(self):
        self.model._generator_refresh(**self.kwargs)
        self.finished.emit()
        log.debug("finished refreshing %r", self.model)


@attr.s(slots=True, auto_attribs=True, auto_detect=True, weakref_slot=True)
class RefreshItem:
    record: "AbstractRecord" = attr.ib()
    idx: int = attr.ib()


class LogRecordsModel(BaseQueryDataModel):
    extra_columns = set()
    strict_exclude_columns = {"record_class"}
    bool_images = {True: AllResourceItems.check_mark_green_image.get_as_icon(),
                   False: AllResourceItems.close_black_image.get_as_icon()}

    def __init__(self, filter_data: dict[str, Any], parent=None) -> None:
        super().__init__(LogRecord, parent=parent)
        self.data_role_table = self.data_role_table | {Qt.BackgroundRole: self._get_background_data, Qt.FontRole: self._get_font_data}
        self.filter_data = {"server_profiling_record": (LogRecord.record_class != RecordClass.get(name="PerfProfilingRecord")), "antistasi_profiling_record": (LogRecord.record_class != RecordClass.get(name="PerformanceRecord"))} | filter_data
        self.ordered_by = (LogRecord.start, LogRecord.recorded_at)

    def get_query(self) -> "Query":

        query = LogRecord.select()
        for filter_stmt in self.filter_data.values():
            query = query.where(filter_stmt)

        return query.order_by(*self.ordered_by)

    @profile
    def _get_display_data(self, index: "INDEX_TYPE") -> Any:
        item = self.content_items[index.row()]
        column = self.columns[index.column()]

        data = item.get_data(column.name)
        if column.name == "message":
            return f"{item.message}"
        if data is None:
            return self.on_display_data_none(role=Qt.DisplayRole, item=item, column=column)
        if isinstance(data, bool):
            return self.on_display_data_bool(role=Qt.DisplayRole, item=item, column=column, value=data)
        return str(data)

    @profile
    def _get_background_data(self, index: "INDEX_TYPE") -> Any:
        item = self.content_items[index.row()]
        column = self.columns[index.column()]

        if item.log_level.name == "ERROR":
            return Color(225, 25, 23, 0.5, "error_red").qcolor
        elif item.log_level.name == "WARNING":
            return Color(255, 103, 0, 0.5, "warning_orange").qcolor
        return item.background_color

    @profile
    def _get_font_data(self, index: "INDEX_TYPE") -> Any:
        pass

    @profile
    def get_content(self) -> None:

        @profile
        def _get_record(_item_data, _all_log_files):
            record_class = self.backend.record_class_manager.get_by_id(_item_data.get('record_class'))
            log_file = _all_log_files[_item_data.get('log_file')]
            record_item = record_class.from_model_dict(_item_data, log_file=log_file)

            return record_item

        log.debug("starting getting content for %r", self)
        all_log_files = {log_file.id: log_file for log_file in self.backend.database.get_log_files()}
        # with self.backend.database:
        with ThreadPoolExecutor() as pool:
            self.content_items = list(pool.map(lambda x: _get_record(_item_data=x, _all_log_files=all_log_files), self.get_query().dicts().iterator()))

        log.debug("finished getting content for %r", self)


# region[Main_Exec]
if __name__ == '__main__':
    pass

# endregion[Main_Exec]
