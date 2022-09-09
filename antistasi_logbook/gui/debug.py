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
from hashlib import md5
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
from peewee import JOIN, fn, prefetch
import pandas as pd
from concurrent.futures import Future
import apsw
from argparse import Action
from gidapptools import get_logger
from gidapptools.general_helper.conversion import number_to_pretty, bytes2human
from antistasi_logbook.storage.models.models import DatabaseMetaData, LogRecord, GameMap, RecordClass, LogFile, Server, Message, LogLevel, RecordOrigin, ArmaFunction, ArmaFunctionAuthorPrefix
if TYPE_CHECKING:
    from antistasi_logbook.gui.main_window import AntistasiLogbookMainWindow
    from antistasi_logbook.gui.application import AntistasiLogbookApplication
    from antistasi_logbook.gui.widgets.debug_widgets import DebugDockWidget

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


def disable(in_func):
    in_func.is_disabled = True
    return in_func


def show_parser_argument_full_text_data(argument_index: int):
    parser_argument = QApplication.instance().argument_doc_items[argument_index]

    return parser_argument.get_html()


def show_parser_usage():
    return QApplication.instance().get_argument_parser().format_usage()


def get_all_widgets():
    app: "AntistasiLogbookApplication" = QApplication.instance()
    _out = {}
    for w in app.allWidgets():

        _out[str(w)] = w.metaObject().className()

    return _out


def get_all_windows():
    app: "AntistasiLogbookApplication" = QApplication.instance()
    return {str(i): i for i in app.allWindows()}


def do_incremental_vacuum():
    def _vac_func(*args, **kwargs):
        log.debug("%r || %r", args, kwargs)
        return 100
    app: "AntistasiLogbookApplication" = QApplication.instance()
    db = app.backend.database

    cur: apsw.Cursor = db.cursor()
    cur.execute("PRAGMA auto_vacuum(2);")

    conn: apsw.Connection = cur.getconnection()

    conn.autovacuum_pages(None)
    result = conn.changes()
    cur.close()
    return result


def show_average_file_size_per_log_file():
    raw = LogFile.average_file_size_per_log_file()
    return bytes2human(raw)


def show_amount_messages_compared_to_amount_records():
    app: "AntistasiLogbookApplication" = QApplication.instance()
    db = app.backend.database
    with db.connection_context() as ctx:
        amount_messages = Message.select(Message.id).count()
        amount_records = LogRecord.select(LogRecord.id).count()

    if amount_records == 0:
        factor = None
    else:
        factor = round(amount_messages / amount_records, ndigits=3)
    return {"messages": amount_messages, "records": amount_records, "messages/record": factor}


def show_database_file_size():
    app: "AntistasiLogbookApplication" = QApplication.instance()
    db = app.backend.database
    raw = db.database_file_size
    return bytes2human(raw)


def check_hash_functions():
    app: "AntistasiLogbookApplication" = QApplication.instance()
    db = app.backend.database
    with db.connection_context() as ctx:
        log.debug("starting to collect data")
        start_time = perf_counter()
        query = Message.select(fn.murmurhash(Message.text), Message.text).tuples().iterator()
        data = {i[0]: i[1] for i in query}
        time_taken = round(perf_counter() - start_time, ndigits=4)
        log.debug("finished collecting, it took %r s", time_taken)
        log.debug("collected %r data", len(data))

    return {k: v for k, v in list(data.items())[:100]}


def setup_debug_widget(debug_dock_widget: "DebugDockWidget") -> None:
    app: AntistasiLogbookApplication = QApplication.instance()
    debug_dock_widget.add_show_attr_button(attr_name="amount_log_records", obj=LogRecord)
    debug_dock_widget.add_show_attr_button(attr_name="amount_log_files", obj=LogFile)
    debug_dock_widget.add_show_attr_button(attr_name="get_amount_meta_data_items", obj=DatabaseMetaData)
    for attr_name in ["applicationVersion",
                      "organizationName",
                      "applicationDisplayName",
                      "desktopFileName",
                      "font",
                      "applicationDirPath",
                      "applicationFilePath",
                      "applicationPid",
                      "arguments",
                      "libraryPaths",
                      "isQuitLockEnabled"]:
        debug_dock_widget.add_show_attr_button(attr_name=attr_name, obj=app)

    debug_dock_widget.add_show_func_result_button(get_all_widgets, "widgets")
    debug_dock_widget.add_show_func_result_button(get_all_windows, "widgets")
    debug_dock_widget.add_show_func_result_button(do_incremental_vacuum, "database")
    debug_dock_widget.add_show_func_result_button(show_average_file_size_per_log_file, "database")
    debug_dock_widget.add_show_func_result_button(show_database_file_size, "database")
    debug_dock_widget.add_show_func_result_button(show_amount_messages_compared_to_amount_records, "database")
    debug_dock_widget.add_show_func_result_button(check_hash_functions, "database")

# region[Main_Exec]


if __name__ == '__main__':
    pass

# endregion[Main_Exec]
