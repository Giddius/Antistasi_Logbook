"""
WiP.

Soon.
"""

# region [Imports]

import os
import re
import sys
import json
import queue
import math
import base64
import pickle
import random
import shelve
import dataclasses
import shutil
import asyncio
import logging
import sqlite3
import platform
import importlib
import subprocess
import inspect

from time import sleep, process_time, process_time_ns, perf_counter, perf_counter_ns
from io import BytesIO, StringIO
from abc import ABC, ABCMeta, abstractmethod
from copy import copy, deepcopy
from enum import Enum, Flag, auto, unique
from time import time, sleep
from pprint import pprint, pformat
from pathlib import Path
from string import Formatter, digits, printable, whitespace, punctuation, ascii_letters, ascii_lowercase, ascii_uppercase
from timeit import Timer
from typing import TYPE_CHECKING, Union, Callable, Iterable, Optional, Mapping, Any, IO, TextIO, BinaryIO, Hashable, Generator, Literal, TypeVar, TypedDict, AnyStr
from zipfile import ZipFile, ZIP_LZMA
from datetime import datetime, timezone, timedelta
from tempfile import TemporaryDirectory
from textwrap import TextWrapper, fill, wrap, dedent, indent, shorten
from functools import wraps, partial, lru_cache, singledispatch, total_ordering, cached_property, reduce
from operator import add
from importlib import import_module, invalidate_caches
from contextlib import contextmanager, asynccontextmanager, nullcontext, closing, ExitStack, suppress
from statistics import mean, mode, stdev, median, variance, pvariance, harmonic_mean, median_grouped
from collections import Counter, ChainMap, deque, namedtuple, defaultdict
from urllib.parse import urlparse
from importlib.util import find_spec, module_from_spec, spec_from_file_location
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from importlib.machinery import SourceFileLoader
import PySide6
from PySide6 import (QtCore, QtGui, QtWidgets, Qt3DAnimation, Qt3DCore, Qt3DExtras, Qt3DInput, Qt3DLogic, Qt3DRender, QtAxContainer, QtBluetooth,
                     QtCharts, QtConcurrent, QtDataVisualization, QtDesigner, QtHelp, QtMultimedia, QtMultimediaWidgets, QtNetwork, QtNetworkAuth,
                     QtOpenGL, QtOpenGLWidgets, QtPositioning, QtPrintSupport, QtQml, QtQuick, QtQuickControls2, QtQuickWidgets, QtRemoteObjects,
                     QtScxml, QtSensors, QtSerialPort, QtSql, QtStateMachine, QtSvg, QtSvgWidgets, QtTest, QtUiTools, QtWebChannel, QtWebEngineCore,
                     QtWebEngineQuick, QtWebEngineWidgets, QtWebSockets, QtXml)

from PySide6.QtCore import (QByteArray, QCoreApplication, QDate, QDateTime, QEvent, QLocale, QMetaObject, QModelIndex, QModelRoleData, QMutex,
                            QMutexLocker, QObject, QPoint, QRect, QRecursiveMutex, QRunnable, QSettings, QSize, QThread, QThreadPool, QTime, QUrl,
                            QWaitCondition, Qt, QAbstractItemModel, QAbstractListModel, QAbstractTableModel, Signal, Slot)

from PySide6.QtGui import (QAction, QPen, QBrush, QColor, QConicalGradient, QCursor, QFont, QFontDatabase, QFontMetrics, QGradient, QIcon, QImage,
                           QKeySequence, QLinearGradient, QPainter, QPalette, QPixmap, QRadialGradient, QTransform)

from PySide6.QtWidgets import (QApplication, QBoxLayout, QCheckBox, QColorDialog, QColumnView, QComboBox, QDateTimeEdit, QDialogButtonBox,
                               QDockWidget, QDoubleSpinBox, QFontComboBox, QFormLayout, QFrame, QGridLayout, QGroupBox, QHBoxLayout, QHeaderView,
                               QLCDNumber, QLabel, QLayout, QLineEdit, QListView, QListWidget, QMainWindow, QMenu, QMenuBar, QMessageBox,
                               QProgressBar, QProgressDialog, QPushButton, QSizePolicy, QSpacerItem, QSpinBox, QStackedLayout, QStackedWidget,
                               QStatusBar, QStyledItemDelegate, QSystemTrayIcon, QTabWidget, QTableView, QTextEdit, QTimeEdit, QToolBox, QTreeView,
                               QVBoxLayout, QWidget, QAbstractItemDelegate, QAbstractItemView, QAbstractScrollArea, QRadioButton, QFileDialog, QButtonGroup)

import pyqtgraph as pg
from gidapptools import get_logger
from antistasi_logbook.utilities.date_time_utilities import DateTimeFrame
from antistasi_logbook.storage.models.models import LogFile, RecordClass, LogRecord
if TYPE_CHECKING:
    from antistasi_logbook.backend import Backend
    from antistasi_logbook.storage.database import GidSqliteApswDatabase
    from antistasi_logbook.gui.main_window import AntistasiLogbookMainWindow
    from antistasi_logbook.gui.application import AntistasiLogbookApplication

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


@unique
class StatScope(Enum):
    LOG_FILE = auto()
    CAMPAIGN = auto()


class BaseStatsItem:
    plot_extra_kwargs: dict[str, Any] = {"antialias": False,
                                         "autoDownsample": True}

    def __init__(self, name: str, data: dict[datetime, Union[int, float]] = None) -> None:
        self.name = name
        self._data = data or {}
        self.plot_data_item: pg.PlotDataItem = None

    def plot(self, plot_widget: pg.PlotWidget) -> pg.PlotDataItem:
        self.plot_data_item = plot_widget.plot(x=list(self._data.keys()),
                                               y=list(self._data.values()),
                                               pen=self.get_line_pen(),
                                               name=self.name,
                                               symbol=self.symbol,
                                               symbolSize=self.symbol_size,
                                               symbolPen=self.pen,
                                               **self.plot_extra_kwargs)

        try:
            legend: pg.LegendItem = getattr(plot_widget, "legend")
            legend.addItem(self.plot_data_item, self.name)
        except AttributeError:
            pass
        return self.plot_data_item

    def get_symbol_pen(self) -> QPen:
        return pg.mkPen(self.symbol_color, self.symbol_line_width)

    def get_line_pen(self) -> QPen:
        return pg.mkPen(self.color, self.line_width)

    @property
    def max_y(self) -> Union[int, float]:
        return max(self._data.values())

    @property
    def min_y(self) -> Union[int, float]:
        return min(self._data.values())

    @property
    def max_timestamp(self) -> datetime:
        return max(self._data.keys())

    @property
    def min_timestamp(self) -> datetime:
        return min(self._data.keys())

    @property
    def timeframe(self) -> DateTimeFrame:
        return DateTimeFrame(start=self.min_timestamp, end=self.max_timestamp)

    @property
    def line_width(self) -> int:
        return 1

    @property
    def color(self) -> QColor:
        return QColor(255, 255, 255, 255)

    @property
    def symbol_color(self) -> QColor:
        return QColor(255, 255, 255, 255)

    @property
    def symbol_line_width(self) -> int:
        return 1

    @property
    def symbol(self) -> str:
        return 'x'

    @property
    def symbol_size(self) -> int:
        return 5


class AbstractStatsModel(ABC):
    available_scopes: tuple[StatScope] = None
    stats_item_klass: type[BaseStatsItem] = BaseStatsItem

    def __init__(self, scope: StatScope, y_fixed_to_zero: bool = True) -> None:
        super().__init__()
        self.scope = scope
        self.y_fixed_to_zero = y_fixed_to_zero

        self.time_frame: DateTimeFrame = None
        self.items: dict[str, BaseStatsItem] = {}

    @property
    def app(self) -> "AntistasiLogbookApplication":
        return QApplication.instance()

    @property
    def backend(self) -> "Backend":
        return self.app.backend

    @property
    def database(self) -> "GidSqliteApswDatabase":
        return self.backend.database

    def get_new_stat_item(self, name: str) -> BaseStatsItem:
        return BaseStatsItem(name=name)

    @abstractmethod
    def collect_data(self) -> None:
        ...

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}(scope={self.scope!r}, y_fixed_to_zero={self.y_fixed_to_zero!r})'


class PerformanceStatsModel(AbstractStatsModel):

    def __init__(self, log_file: LogFile, scope: StatScope) -> None:
        super().__init__(scope, y_fixed_to_zero=True)
        self.log_file = log_file
        self.record_class: RecordClass = RecordClass.get(name="PerformanceRecord")

    def collect_data(self) -> None:
        def _insert_data_point(_name: str, _timestamp: datetime, _value: Union[int, float]):
            if _name not in self.items:
                self.items[_name] = self.get_new_stat_item(_name)
            self.items[_name]._data[_timestamp] = _value

        if self.scope is StatScope.LOG_FILE:
            query = LogRecord.select(LogRecord.message, LogRecord.recorded_at).where(LogRecord.log_file_id == self.log_file.id).where(LogRecord.record_class_id == self.record_class.id).order_by(-LogRecord.recorded_at)
        elif self.scope is StatScope.CAMPAIGN:
            sub_query = LogFile.select().where(LogFile.campaign_id == self.log_file.campaign_id)
            query = LogRecord.select(LogRecord.message, LogRecord.recorded_at).where(LogRecord.log_file_id << sub_query).where(LogRecord.record_class_id == self.record_class.id).order_by(-LogRecord.recorded_at)
        for (message, recorded_at) in self.database.execute(query):
            recorded_at = LogRecord.recorded_at.python_value(recorded_at)
            data = self.record_class.record_class.parse(message)
            for name, value in data.items():
                _insert_data_point(name, recorded_at, value)

        self.time_frame = reduce(add, (i.timeframe for i in self.items.values()))
# region[Main_Exec]


if __name__ == '__main__':
    pass

# endregion[Main_Exec]
