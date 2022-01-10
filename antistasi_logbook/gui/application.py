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
from weakref import WeakSet
import PySide6
from PySide6 import (QtCore, QtGui, QtWidgets, Qt3DAnimation, Qt3DCore, Qt3DExtras, Qt3DInput, Qt3DLogic, Qt3DRender, QtAxContainer, QtBluetooth,
                     QtCharts, QtConcurrent, QtDataVisualization, QtDesigner, QtHelp, QtMultimedia, QtMultimediaWidgets, QtNetwork, QtNetworkAuth,
                     QtOpenGL, QtOpenGLWidgets, QtPositioning, QtPrintSupport, QtQml, QtQuick, QtQuickControls2, QtQuickWidgets, QtRemoteObjects,
                     QtScxml, QtSensors, QtSerialPort, QtSql, QtStateMachine, QtSvg, QtSvgWidgets, QtTest, QtUiTools, QtWebChannel, QtWebEngineCore,
                     QtWebEngineQuick, QtWebEngineWidgets, QtWebSockets, QtXml)

from PySide6.QtCore import (QByteArray, QLibrary, QLibraryInfo, QCoreApplication, QDate, QDateTime, QEvent, QLocale, QMetaObject, QModelIndex, QModelRoleData, QMutex,
                            QMutexLocker, QObject, QPoint, QRect, QRecursiveMutex, QRunnable, QSettings, QSize, QThread, QThreadPool, QTime, QUrl,
                            QWaitCondition, Qt, QAbstractItemModel, QAbstractListModel, QAbstractTableModel, Signal, Slot)

from PySide6.QtGui import (QAction, QGuiApplication, QBrush, QColor, QConicalGradient, QCursor, QFont, QFontDatabase, QFontMetrics, QGradient, QIcon, QImage,
                           QKeySequence, QLinearGradient, QPainter, QPalette, QPixmap, QRadialGradient, QTransform)

from PySide6.QtWidgets import (QApplication, QBoxLayout, QCheckBox, QColorDialog, QColumnView, QComboBox, QDateTimeEdit, QDialogButtonBox,
                               QDockWidget, QDoubleSpinBox, QFontComboBox, QFormLayout, QFrame, QGridLayout, QGroupBox, QHBoxLayout, QHeaderView,
                               QLCDNumber, QLabel, QLayout, QLineEdit, QListView, QListWidget, QMainWindow, QMenu, QMenuBar, QMessageBox,
                               QProgressBar, QProgressDialog, QPushButton, QSizePolicy, QSpacerItem, QSpinBox, QStackedLayout, QStackedWidget,
                               QStatusBar, QStyledItemDelegate, QSystemTrayIcon, QTabWidget, QTableView, QTextEdit, QTimeEdit, QToolBox, QTreeView,
                               QVBoxLayout, QWidget, QAbstractItemDelegate, QAbstractItemView, QAbstractScrollArea, QRadioButton, QFileDialog, QButtonGroup)
from gidapptools import get_logger, get_meta_info, get_meta_paths, get_meta_config
from jinja2 import Environment, BaseLoader
from gidapptools.gid_config.interface import EntryTypus
if TYPE_CHECKING:
    from antistasi_logbook.backend import Backend
    from gidapptools.gid_config.interface import GidIniConfig
    from antistasi_logbook.gui.main_window import AntistasiLogbookMainWindow, LogbookSystemTray
    from gidapptools.gidapptools_qt.resources.resources_helper import PixmapResourceItem
# endregion[Imports]

# region [TODO]


# endregion [TODO]

# region [Logging]


# endregion[Logging]

# region [Constants]

THIS_FILE_DIR = Path(__file__).parent.absolute()
log = get_logger(__name__)
META_INFO = get_meta_info()
META_PATHS = get_meta_paths()
COLOR_CONFIG = get_meta_config().get_config("color")
# endregion[Constants]


ABOUT_TEMPLATE = """
<dl>
    {% for key, value in data.items() %}
    <dt><b><u>{{key}}:</u></b></dt>
    <dd>{{value}}</dd>
    {% endfor %}
</dl>"""


def _qcolor(value: str, mode: str = 'decode', **named_arguments) -> float:
    if mode == "decode":
        if value:
            r, g, b, a = (int(i.strip()) for i in value.split(',') if i.strip())
            return QColor(r, g, b, a)

    elif mode == "encode":
        if value:
            return ', '.join(str(i) for i in value.getRgb())


def _handle_qcolor(value: Any, sub_arguments: dict[str, str]) -> EntryTypus:
    return EntryTypus(original_value=value, base_typus=QColor)


COLOR_CONFIG.add_spec_value_handler("qcolor", _handle_qcolor)
COLOR_CONFIG.add_converter_function(QColor, _qcolor)

COLOR_CONFIG.reload()


class AntistasiLogbookApplication(QApplication):

    def __init__(self, argvs: Iterable[str] = None):
        super().__init__(argvs)
        self.backend: "Backend" = None
        self.icon: QIcon = None
        self.meta_info = None
        self.meta_paths = None
        self.available_font_families = None
        self.jinja_environment = None
        self.main_window: "AntistasiLogbookMainWindow" = None
        self.sys_tray: "LogbookSystemTray" = None
        self.extra_windows = WeakSet()
        self.gui_thread_pool: ThreadPoolExecutor = None
        self.is_setup: bool = False

    def setup(self, backend: "Backend", icon: "PixmapResourceItem") -> None:
        if self.is_setup is True:
            return

        self.gui_thread_pool = ThreadPoolExecutor(5, thread_name_prefix="gui")
        self.backend = backend
        self.icon = icon.get_as_icon() if icon is not None else icon
        self.meta_info = get_meta_info()
        self.meta_paths = get_meta_paths()

        self.available_font_families = set(QFontDatabase().families())
        self.jinja_environment = Environment(loader=BaseLoader)

        self.color_config = COLOR_CONFIG
        self.backend.start_up()
        self.setApplicationName(self.meta_info.app_name)
        self.setApplicationDisplayName(self.meta_info.pretty_app_name)
        self.setApplicationVersion(self.meta_info.version)
        self.setOrganizationName(self.meta_info.pretty_app_author)
        self.setOrganizationDomain(str(self.meta_info.url))

        font: QFont = self.font()
        font.setFamily("Roboto Medium")
        font.setPointSize(10)

        self.setFont(font)
        self.is_setup = True

    @ classmethod
    def with_high_dpi_scaling(cls, argvs: Iterable[str] = None):
        cls.setAttribute(Qt.AA_EnableHighDpiScaling, True)
        cls.setAttribute(QtCore.Qt.AA_UseHighDpiPixmaps, True)
        # cls.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.Round)
        QGuiApplication.setDesktopSettingsAware(True)
        return cls(argvs=argvs)

    @property
    def config(self) -> "GidIniConfig":
        return self.backend.config

    @property
    def is_dev(self) -> bool:
        dev_mode = self.config.get("debug", "dev_mode")
        return any(value is True for value in [dev_mode, self.meta_info.is_dev])

    def format_datetime(self, date_time: datetime) -> str:
        if self.config.get("time", "use_local_timezone", default=False) is True:
            date_time = date_time.astimezone(tz=self.meta_info.local_tz)
        time_format = self.config.get("time", "time_format", default='%Y-%m-%d %H:%M:%S.%f')
        if time_format == "iso":
            return date_time.isoformat()
        if time_format == "local":
            time_format = "%x %X"

        _out = date_time.strftime(time_format)
        if "%f" in time_format:
            _out = _out[:-3]
        return _out

    def _get_about_text(self) -> str:
        text_parts = {"Name": self.applicationDisplayName(),
                      "Author": self.organizationName(),
                      "Link": f'<a href="{self.organizationDomain()}">{self.organizationDomain()}</a>',
                      "Version": self.applicationVersion(),
                      "Dev Mode": self.meta_info.pretty_is_dev,
                      "Operating System": self.meta_info.os,
                      "Python Version": self.meta_info.python_version}

        # text = "<dl>"
        # for k, v in text_parts.items():
        #     text += f"<dt><b>{k.title()}:</b></dt><dd>{v}</dd><br>"
        # text += "</dl>"
        # return text
        return self.jinja_environment.from_string(ABOUT_TEMPLATE).render(data=text_parts)

    def show_about(self) -> None:
        title = f"About {self.applicationDisplayName()}"
        text = self._get_about_text()
        QMessageBox.about(self.main_window, title, text)

    def show_about_qt(self) -> None:
        self.aboutQt()

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name={self.applicationDisplayName()!r})"


# region[Main_Exec]
if __name__ == '__main__':
    pass

# endregion[Main_Exec]
