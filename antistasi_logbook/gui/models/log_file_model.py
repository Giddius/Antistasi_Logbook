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
from gidapptools import get_logger
from gidapptools.general_helper.conversion import bytes2human
from antistasi_logbook.storage.models.models import Server, RemoteStorage, LogFile, RecordClass, LogRecord, AntstasiFunction, setup_db, DatabaseMetaData, GameMap, LogLevel
import PySide6
from gidapptools.general_helper.string_helper import StringCaseConverter
from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale, QMetaObject, QObject, QPoint, QRect, QSize, QTime, QUrl, Qt,
                            QAbstractTableModel, QAbstractItemModel, QAbstractListModel, QEvent, QModelIndex)
from PySide6.QtGui import (QAction, QBrush, QColor, QConicalGradient, QCursor, QFont, QFontDatabase, QGradient, QIcon, QImage, QKeySequence,
                           QLinearGradient, QPainter, QPalette, QPixmap, QRadialGradient, QTransform, QCloseEvent)
from PySide6.QtWidgets import (QApplication, QGridLayout, QMainWindow, QMenu, QMenuBar, QSizePolicy, QStatusBar, QWidget, QPushButton, QLabel, QProgressBar, QProgressDialog,
                               QBoxLayout, QHBoxLayout, QVBoxLayout, QSizePolicy, QMessageBox, QLayout, QGroupBox, QStyledItemDelegate, QAbstractItemDelegate, QDockWidget, QTabWidget, QSystemTrayIcon, QTableView, QListView, QTreeView, QColumnView)
if TYPE_CHECKING:
    from antistasi_logbook.backend import Backend
# endregion[Imports]

# region [TODO]


# endregion [TODO]

# region [Logging]


# endregion[Logging]

# region [Constants]

THIS_FILE_DIR = Path(__file__).parent.absolute()
log = get_logger(__name__)
# endregion[Constants]


class LinkDelegate(QStyledItemDelegate):
    def paint(self, painter: PySide6.QtGui.QPainter, option: PySide6.QtWidgets.QStyleOptionViewItem, index: Union[PySide6.QtCore.QModelIndex, PySide6.QtCore.QPersistentModelIndex]) -> None:

        return super().paint(painter, option, index)

    def setEditorData(self, editor: PySide6.QtWidgets.QWidget, index: Union[PySide6.QtCore.QModelIndex, PySide6.QtCore.QPersistentModelIndex]) -> None:

        log.critical(f"{type(editor)=}")

        log.critical(f"{editor=}")

        return super().setEditorData(editor, index)


class LogFileModel(QAbstractTableModel):
    strict_exclude_columns: set[str] = {'id', 'header_text', 'startup_text', 'utc_offset', 'last_parsed_datetime', 'last_parsed_line_number', "comments"}
    default_column_ordering: dict[str, int] = {"marked": 0, "name": 1}

    def __init__(self, backend: "Backend", parent: Optional[PySide6.QtCore.QObject] = None) -> None:
        super().__init__(parent=parent)
        self.backend = backend
        self.columns_to_exclude = self.strict_exclude_columns.copy().union({"remote_path"})
        self.log_file_items = self.backend.database.get_log_files(ordered_by=LogFile.modified_at)
        self.raw_column_names = tuple(sorted(LogFile._meta.columns, key=lambda x: self.default_column_ordering.get(x, 999)))
        self._column_names: tuple[str] = None

    @ property
    def column_names(self) -> tuple[str]:
        if self._column_names is None:
            self._column_names = [col for col in self.raw_column_names if col not in self.columns_to_exclude]
        return self._column_names

    def get_log_file_items(self) -> None:
        self.log_file_items = self.backend.database.get_log_files(ordered_by=LogFile.modified_at)

    def data(self, index: QModelIndex, role) -> Any:
        if not index.isValid():
            return
        item = self.log_file_items[index.row()]
        column_name = self.column_names[index.column()]
        if role == Qt.DisplayRole:

            _out = getattr(item, column_name)
            if _out is None:
                _out = '-'
            elif column_name == "unparsable":
                _out = "❌" if _out is True else ""
            elif column_name == "marked":
                _out = "⭐" if _out is True else ""

            elif column_name == "size":
                _out = bytes2human(_out)

            elif column_name == "is_new_campaign":
                _out = "✅" if _out is True else ""
            return str(_out)

        elif role == Qt.DecorationRole:
            pass

        elif role == Qt.TextAlignmentRole:
            return Qt.AlignCenter

        elif role == Qt.BackgroundRole:
            if item.unparsable is True:
                return QColor(75, 75, 75, 125)

    def rowCount(self, index) -> int:
        return len(self.log_file_items)

    def columnCount(self, index) -> int:
        return len(self.column_names)

    def headerData(self, section: int, orientation, role: int = None) -> Any:
        if orientation == Qt.Horizontal:
            column_name = self.column_names[section]
            if role == Qt.DisplayRole:
                if column_name == "marked":
                    return "⭐"
                return StringCaseConverter.convert_to(column_name, StringCaseConverter.TITLE)
            elif role == Qt.FontRole:
                font = QFont()
                font.setBold(True)
                font.setPointSize(10)
                return font

    def update(self, update_started: bool = False):
        self.get_log_file_items()
        self.modelReset.emit()
# region[Main_Exec]


if __name__ == '__main__':
    pass

# endregion[Main_Exec]
