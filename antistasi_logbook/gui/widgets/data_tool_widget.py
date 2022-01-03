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
from functools import wraps, partial, lru_cache, singledispatch, total_ordering, cached_property
from importlib import import_module, invalidate_caches
from contextlib import contextmanager, asynccontextmanager, nullcontext, closing, ExitStack, suppress
from statistics import mean, mode, stdev, median, variance, pvariance, harmonic_mean, median_grouped
from collections import Counter, ChainMap, deque, namedtuple, defaultdict
from urllib.parse import urlparse
from importlib.util import find_spec, module_from_spec, spec_from_file_location
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from importlib.machinery import SourceFileLoader
from dateutil.tz import UTC
from tzlocal import get_localzone
from antistasi_logbook.gui.resources.antistasi_logbook_resources_accessor import AllResourceItems
import PySide6
from PySide6 import (QtCore, QtGui, QtWidgets, Qt3DAnimation, Qt3DCore, Qt3DExtras, Qt3DInput, Qt3DLogic, Qt3DRender, QtAxContainer, QtBluetooth,
                     QtCharts, QtConcurrent, QtDataVisualization, QtDesigner, QtHelp, QtMultimedia, QtMultimediaWidgets, QtNetwork, QtNetworkAuth,
                     QtOpenGL, QtOpenGLWidgets, QtPositioning, QtPrintSupport, QtQml, QtQuick, QtQuickControls2, QtQuickWidgets, QtRemoteObjects,
                     QtScxml, QtSensors, QtSerialPort, QtSql, QtStateMachine, QtSvg, QtSvgWidgets, QtTest, QtUiTools, QtWebChannel, QtWebEngineCore,
                     QtWebEngineQuick, QtWebEngineWidgets, QtWebSockets, QtXml)

from PySide6.QtCore import (QByteArray, QCoreApplication, QDate, QDateTime, QEvent, QSysInfo, QLocale, QMetaObject, QModelIndex, QModelRoleData, QMutex,
                            QMutexLocker, QObject, QPoint, QRect, QRecursiveMutex, QRunnable, QSettings, QSize, QThread, QThreadPool, QTime, QUrl,
                            QWaitCondition, Qt, QAbstractItemModel, QAbstractListModel, QAbstractTableModel, Signal, Slot)

from PySide6.QtGui import (QAction, QBrush, QColor, QConicalGradient, QCursor, QFont, QFontDatabase, QFontMetrics, QGradient, QIcon, QImage,
                           QKeySequence, QLinearGradient, QPainter, QPalette, QPixmap, QRadialGradient, QTransform, Qt)

from PySide6.QtWidgets import (QApplication, QBoxLayout, QCheckBox, QColorDialog, QColumnView, QComboBox, QDateTimeEdit, QCalendarWidget, QDialogButtonBox,
                               QDockWidget, QDoubleSpinBox, QFontComboBox, QFormLayout, QFrame, QGridLayout, QGroupBox, QHBoxLayout, QHeaderView,
                               QLCDNumber, QLabel, QLayout, QLineEdit, QListView, QListWidget, QMainWindow, QMenu, QMenuBar, QMessageBox,
                               QProgressBar, QProgressDialog, QPushButton, QSizePolicy, QSpacerItem, QSpinBox, QStackedLayout, QStackedWidget,
                               QStatusBar, QStyledItemDelegate, QSystemTrayIcon, QTabWidget, QTableView, QTextEdit, QTimeEdit, QToolBox, QTreeView,
                               QVBoxLayout, QWidget, QAbstractItemDelegate, QAbstractItemView, QAbstractScrollArea, QRadioButton, QFileDialog, QButtonGroup)

from gidapptools import get_logger
if TYPE_CHECKING:
    from antistasi_logbook.backend import Backend
    from antistasi_logbook.gui.application import AntistasiLogbookApplication
    from gidapptools.gid_config.interface import GidIniConfig
# endregion[Imports]

# region [TODO]


# endregion [TODO]

# region [Logging]


# endregion[Logging]

# region [Constants]

THIS_FILE_DIR = Path(__file__).parent.absolute()
log = get_logger(__name__)
# endregion[Constants]


def _get_local_utc_offset_string():
    value = int(get_localzone()._zone.utcoffset(datetime.now()).total_seconds() // 3600)
    if value > 0:
        return f"+{value!s}"

    return f"{value!s}"


class BaseDataToolPage(QWidget):
    name: str = None
    icon_name: str = None

    def __init__(self, parent: Optional[PySide6.QtWidgets.QWidget] = None) -> None:
        super().__init__(parent=parent)
        self.setLayout(QFormLayout(self))
        self.layout.setLabelAlignment(Qt.AlignLeft | Qt.AlignVCenter)

    @property
    def app(self) -> "AntistasiLogbookApplication":
        return QApplication.instance()

    @property
    def backend(self) -> "Backend":
        return self.app.backend

    @property
    def config(self) -> "GidIniConfig":
        return self.app.config

    @property
    def layout(self) -> QFormLayout:
        return super().layout()

    @cached_property
    def icon(self) -> Optional[QIcon]:
        if self.icon_name is None:
            return
        return getattr(AllResourceItems, self.icon_name).get_as_icon()


class BaseDataToolWidget(QWidget):
    def __init__(self, parent: Optional[PySide6.QtWidgets.QWidget] = None, ) -> None:
        super().__init__(parent=parent)
        self.setLayout(QGridLayout(self))
        self.tool_box = QToolBox()
        self.layout.addWidget(self.tool_box)

        self.pages: dict[str, BaseDataToolPage] = {}

    def add_page(self, page: BaseDataToolPage):
        if page.name is None or page.icon is None:

            raise AttributeError(f"{page} has to have 'name' and 'icon' set, {page.name=} , {page.icon=}.")

        self.tool_box.addItem(page, page.icon, page.name)
        self.pages[page.name.casefold()] = page

    def get_page_by_name(self, name: str) -> BaseDataToolPage:
        return self.pages[name.casefold()]

    @property
    def layout(self) -> QFormLayout:
        return super().layout()

    @property
    def app(self) -> "AntistasiLogbookApplication":
        return AntistasiLogbookApplication.instance()

    @property
    def backend(self) -> "Backend":
        return self.app.backend

    @property
    def config(self) -> "GidIniConfig":
        return self.app.config


class LogFileSearchPage(BaseDataToolPage):
    name: str = "Search"
    icon_name: str = "log_file_search_page_symbol_image"


class TimeSpanFilterWidget(QGroupBox):
    older_than_changed = Signal(datetime)
    newer_than_changed = Signal(datetime)

    def __init__(self, parent=None) -> None:
        super().__init__(parent=parent)
        self.setLayout(QFormLayout(self))
        self.timezone_selector = QComboBox()
        self.timezone_selector.addItems(["UTC", "LOCAL"])
        self.timezone_selector.currentTextChanged.connect(self.on_timezone_change)
        self.layout.addRow("Time-Zone", self.timezone_selector)

        self.use_newer_than_filter = QCheckBox(text='Only newer than')
        self.newer_than_selection = QDateTimeEdit(datetime.now(tz=UTC) - timedelta(days=1))
        self.newer_than_selection.setDisplayFormat(QLocale.system().dateTimeFormat(QLocale.LongFormat) + ' UTC')
        self.newer_than_selection.setCalendarPopup(True)
        self.newer_than_selection.setTimeSpec(Qt.UTC)
        self.newer_than_selection.setEnabled(False)
        self.use_newer_than_filter.toggled.connect(self.on_use_newer_than_filter_checked)
        self.newer_than_selection.dateTimeChanged.connect(self.on_newer_than_date_time_changed)
        self.layout.addRow(self.use_newer_than_filter, self.newer_than_selection)

        self.use_older_than_filter = QCheckBox(text='Only older than')
        self.older_than_selection = QDateTimeEdit(datetime.now(tz=UTC))
        self.older_than_selection.setDisplayFormat(QLocale.system().dateTimeFormat(QLocale.LongFormat) + ' UTC')
        self.older_than_selection.setCalendarPopup(True)
        self.older_than_selection.setTimeSpec(Qt.UTC)
        self.older_than_selection.setEnabled(False)
        self.use_older_than_filter.toggled.connect(self.on_use_older_than_filter_checked)
        self.older_than_selection.dateTimeChanged.connect(self.on_older_than_date_time_changed)
        self.layout.addRow(self.use_older_than_filter, self.older_than_selection)

    @property
    def app(self) -> "AntistasiLogbookApplication":
        return QApplication.instance()

    def on_timezone_change(self, text: str):
        if text == "UTC":
            self.newer_than_selection.setTimeSpec(Qt.UTC)
            self.newer_than_selection.setDisplayFormat(QLocale.system().dateTimeFormat(QLocale.LongFormat) + ' UTC')
            self.older_than_selection.setTimeSpec(Qt.UTC)
            self.older_than_selection.setDisplayFormat(QLocale.system().dateTimeFormat(QLocale.LongFormat) + ' UTC')

        elif text == "LOCAL":
            self.newer_than_selection.setTimeSpec(Qt.TimeZone)
            self.newer_than_selection.setDisplayFormat(QLocale.system().dateTimeFormat(QLocale.LongFormat) + ' ' + _get_local_utc_offset_string())
            self.older_than_selection.setTimeSpec(Qt.TimeZone)
            self.older_than_selection.setDisplayFormat(QLocale.system().dateTimeFormat(QLocale.LongFormat) + ' ' + _get_local_utc_offset_string())

    def on_newer_than_date_time_changed(self, dt: QDateTime):
        py_dt: datetime = dt.toPython()
        log.debug("newer than raw_datetime=%r", py_dt)
        py_dt = py_dt.astimezone(tz=UTC)
        self.newer_than_changed.emit(py_dt)

    def on_older_than_date_time_changed(self, dt: QDateTime):
        py_dt: datetime = dt.toPython()
        log.debug("older than raw_datetime=%r", py_dt)
        py_dt = py_dt.astimezone(tz=UTC)
        self.older_than_changed.emit(py_dt)

    def on_use_newer_than_filter_checked(self, checked: bool):
        self.newer_than_selection.setEnabled(checked)
        if checked:
            self.newer_than_changed.emit(self.newer_than_selection.dateTime())
        else:
            self.newer_than_changed.emit(None)

    def on_use_older_than_filter_checked(self, checked: bool):
        self.older_than_selection.setEnabled(checked)
        if checked:
            self.older_than_changed.emit(self.older_than_selection.dateTime())
        else:
            self.older_than_changed.emit(None)

    @property
    def layout(self) -> QFormLayout:
        return super().layout()


class LogFileFilterPage(BaseDataToolPage):
    name: str = "Filter"
    icon_name: str = "log_file_filter_page_symbol_image"

    filter_by_server_changed = Signal(int)
    filter_by_game_map_changed = Signal(int)

    def __init__(self, parent: Optional[PySide6.QtWidgets.QWidget] = None) -> None:
        super().__init__(parent=parent)

        self.show_unparsable_check_box = QCheckBox()
        self.show_unparsable_check_box.setLayoutDirection(Qt.RightToLeft)

        self.layout.addRow("Show unparsable Log-Files", self.show_unparsable_check_box)

        self.filter_by_server_combo_box = QComboBox()
        self.filter_by_server_combo_box.addItems([""] + [i.pretty_name for i in self.backend.database.get_all_server() if i.name != "NO_SERVER"])
        self.layout.addRow("Filter by Server", self.filter_by_server_combo_box)
        self.filter_by_server_combo_box.currentTextChanged.connect(self.on_filter_by_server_changed)

        self.time_span_filter_box = TimeSpanFilterWidget()
        self.layout.addRow("Filter by Modified at", self.time_span_filter_box)

        self.filter_by_game_map_combo_box = QComboBox()
        self.filter_by_game_map_combo_box.addItems([""] + [i.full_name for i in self.backend.database.get_all_game_maps()])
        self.layout.addRow("Filter by Game Map", self.filter_by_game_map_combo_box)
        self.filter_by_game_map_combo_box.currentTextChanged.connect(self.on_filter_by_game_map_changed)

        self.filter_by_new_campaign = QCheckBox()
        self.filter_by_new_campaign.setLayoutDirection(Qt.RightToLeft)

        self.layout.addRow("Show only new campaigns", self.filter_by_new_campaign)

    def on_filter_by_server_changed(self, name: str):
        if name == "":

            self.filter_by_server_changed.emit(-1)
        else:
            server_id = {s.pretty_name: s.id for s in self.backend.database.get_all_server()}.get(name)
            self.filter_by_server_changed.emit(server_id)

    def on_filter_by_game_map_changed(self, name: str):
        if name == "":
            log.debug("server_id present = ''")
            self.filter_by_game_map_changed.emit(-1)
        else:
            game_map_id = {g.full_name: g.id for g in self.backend.database.get_all_game_maps()}.get(name)
            self.filter_by_game_map_changed.emit(game_map_id)


class LogFileDataToolWidget(BaseDataToolWidget):

    def __init__(self, parent: Optional[PySide6.QtWidgets.QWidget] = None) -> None:
        super().__init__(parent=parent)

        self.add_page(LogFileFilterPage(self))
        self.add_page(LogFileSearchPage(self))

# region[Main_Exec]


if __name__ == '__main__':
    pass

# endregion[Main_Exec]
