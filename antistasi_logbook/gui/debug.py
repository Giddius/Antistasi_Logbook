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
from peewee import JOIN, fn
import pandas as pd
from concurrent.futures import Future
import apsw
from argparse import Action
from gidapptools import get_logger
from gidapptools.general_helper.conversion import number_to_pretty
from antistasi_logbook.storage.models.models import DatabaseMetaData, LogRecord, GameMap, RecordClass, LogFile
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


@disable
def count_unique_messages():
    app: AntistasiLogbookApplication = QApplication.instance()
    db = app.backend.database
    with db.connection_context() as ctx:
        counter = Counter()
        query = LogRecord.select(LogRecord.message)
        for record in query.iterator():
            counter.update([record.message])

    log.debug("finished collecting")

    _out = {k: a for k, a in counter.most_common(n=5)}
    log.debug("finished converting to dict")
    return _out


@disable
def get_all_killed_by():
    app: AntistasiLogbookApplication = QApplication.instance()
    db = app.backend.database
    _out = defaultdict(dict)
    idx = 0
    with db.connection_context() as ctx:

        killed_by_record_class: RecordClass = RecordClass.get(name="KilledBy")
        _actual_record_class = killed_by_record_class.record_class

        for record in LogRecord.select(LogRecord.recorded_at, LogRecord.message, LogRecord.log_file, LogFile.name).join_from(LogRecord, LogFile).switch(LogRecord).where(LogRecord.record_class_id == killed_by_record_class.id).order_by(LogRecord.recorded_at).iterator():
            idx += 1
            if idx % 100_000 == 0:
                log.debug("handled %s", number_to_pretty(idx))
            parsed_data = _actual_record_class.parse(record.message)
            victim = parsed_data["victim"]
            killer = parsed_data["killer"]
            log_file_name = record.log_file.name
            if victim is not None and victim.strip().startswith("C_man") is False and victim.strip() not in {"Goat_random_F", } and victim.strip().casefold().startswith("land_") is False and killer is not None:
                _out[log_file_name][record.recorded_at.isoformat()] = (victim, killer)

    with open("blah.json", "w", encoding='utf-8', errors='ignore') as f:
        json.dump(_out, f, default=str, sort_keys=False, indent=4)
    with open("blah.csv", "w", encoding='utf-8', errors='ignore') as f:
        for log_file, values in _out.items():
            for datum, message in values.items():
                f.write(f"{log_file},{datum},{message[0]},{message[1]}\n")
    return Path("blah.csv").read_text(encoding='utf-8', errors='ignore')


def all_log_record_message_size():
    app: AntistasiLogbookApplication = QApplication.instance()
    db = app.backend.database

    def get_b_sizes(_db):
        with _db:
            # b_size = LogRecord.select(fn.SUM(fn.LENGHT(LogRecord.message))).scalar()
            query_string = """SELECT MAX(LENGTH(message)), MIN(LENGTH(message)) FROM LogRecord;"""
            cur: apsw.Cursor = _db.cursor()
            cur = cur.execute(query_string)
            res = cur.fetchone()
            return res[0], res[1]

    def _get_max_text(_db, max_length):
        with _db:
            query_string = """SELECT message from LogRecord ORDER BY LENGTH(message) DESC;"""
            cur: apsw.Cursor = _db.cursor()
            cur = cur.execute(query_string)
            _out = []
            for i in range(5):
                _out.append(cur.fetchone()[0])
            return _out

    fut: Future = db.backend.thread_pool.submit(get_b_sizes, _db=db)

    max_size, min_size = fut.result()

    fut_2 = db.backend.thread_pool.submit(_get_max_text, _db=db, max_length=max_size)

    max_texts = fut_2.result()
    _out_dict = {"max size": max_size, "min size": min_size}
    for idx, text in enumerate(max_texts):

        _out_dict[f"largest_text_{idx+1}"] = text
    return _out_dict


def setup_debug_widget(debug_dock_widget: "DebugDockWidget") -> None:
    app: AntistasiLogbookApplication = QApplication.instance()
    debug_dock_widget.add_show_attr_button(attr_name="amount_log_records", obj=LogRecord)
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
    debug_dock_widget.add_show_func_result_button(count_unique_messages, "record_message")
    debug_dock_widget.add_show_func_result_button(get_all_killed_by, "killed_by_all")
    debug_dock_widget.add_show_func_result_button(all_log_record_message_size, "column_sizes")
# region[Main_Exec]


if __name__ == '__main__':
    pass

# endregion[Main_Exec]
