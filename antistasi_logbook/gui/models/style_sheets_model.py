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
from operator import or_
from importlib import import_module, invalidate_caches
from contextlib import contextmanager, asynccontextmanager, nullcontext, closing, ExitStack, suppress
from statistics import mean, mode, stdev, median, variance, pvariance, harmonic_mean, median_grouped
from collections import Counter, ChainMap, deque, namedtuple, defaultdict
from urllib.parse import urlparse
from importlib.util import find_spec, module_from_spec, spec_from_file_location
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from importlib.machinery import SourceFileLoader
from gidapptools.general_helper.string_helper import StringCase, StringCaseConverter
from antistasi_logbook.gui.resources.style_sheets import ALL_STYLE_SHEETS
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
import pp
from qt_material import list_themes
# endregion[Imports]

# region [TODO]


# endregion [TODO]

# region [Logging]


# endregion[Logging]

# region [Constants]

THIS_FILE_DIR = Path(__file__).parent.absolute()

# endregion[Constants]


class StyleSheetTag(Enum):
    NONE = auto()
    DEFAULT = auto()
    BASIC = auto()
    DARK = auto()
    LIGHT = auto()
    MIXED = auto()
    BROKEN = auto()

    def __str__(self) -> str:
        if self.name == "NONE":
            return '-'
        return self.name.title()

    @classmethod
    def _missing_(cls, name: object) -> Any:

        def _normalize_name(in_name: str) -> str:
            new_name = str(in_name)
            new_name = new_name.strip()
            new_name = new_name.replace('-', '_')
            new_name = new_name.replace(' ', '_')
            return new_name.casefold()
        if isinstance(name, str):

            mod_name = _normalize_name(name)
            if mod_name == "":
                return cls.NONE
            for member_name, member_value in cls.__members__.items():
                if member_name.casefold() == mod_name:
                    return cls(member_value)

        return super()._missing_(name)


class StoredStyleSheet:
    ___typus___ = "LOCAL"
    tag_line_regex = re.compile(r"\_\_TAGS\_\_\s*\:\s*(?P<tag_text>.*)")

    def __init__(self, path: Path) -> None:
        self.path = path
        self.name = self.path.stem
        self.pretty_name = StringCaseConverter.convert_to(self.name, StringCase.TITLE)
        self.display_data = f"{self.pretty_name} [{', '.join(str(tag) for tag in self.tags)}]"

    @property
    def is_broken(self):
        return StyleSheetTag.BROKEN in self.tags

    def get_data(self, role: Qt.ItemDataRole):
        if role == Qt.DisplayRole:
            return self.display_data

    @cached_property
    def tags(self) -> tuple[StyleSheetTag]:
        return self._get_tags()

    @property
    def content(self) -> str:
        return self.path.read_text(encoding='utf-8', errors='ignore')

    def _get_tags(self) -> tuple[str]:
        _tag_line_match: re.Match = None

        with self.path.open('r', encoding='utf-8', errors='ignore') as f:

            while _tag_line_match is None:
                line = next(f, "__END__").strip()
                if line == "__END__":
                    return tuple()
                _tag_line_match = self.tag_line_regex.match(line)
        _tag_text = _tag_line_match.group("tag_text")
        return tuple(StyleSheetTag(tag) for tag in _tag_text.split(','))

    @property
    def ___style_key___(self) -> str:
        return self.path.as_posix()

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name={self.name!r}, path={self.path.as_posix()!r}, tags={self.tags!r})"


class MaterialStyleSheet(StoredStyleSheet):
    ___typus___ = "MATERIAL"

    def __init__(self, name: str) -> None:
        self.name = name.removesuffix(".xml")
        self.pretty_name = StringCaseConverter.convert_to(self.name, StringCase.TITLE)
        self.display_data = self.pretty_name

    def _get_tags(self) -> tuple[str]:
        return tuple()

    @property
    def ___style_key___(self) -> str:
        return self.name + '.xml'

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name={self.name!r}, tags={self.tags!r})"


class StyleSheetsModel(QAbstractTableModel):

    def __init__(self, parent: Optional[PySide6.QtCore.QObject] = None) -> None:
        self.content_items: list[StoredStyleSheet] = list(self.get_items())
        super().__init__(parent=parent)

    def get_index_by_name(self, name: str) -> int:
        return {style.name: idx for idx, style in enumerate(self.content_items)}.get(name)

    def get_base_style_sheet_index(self):
        return {style.name: idx for idx, style in enumerate(self.content_items)}.get("base")

    def get_items(self) -> list[StoredStyleSheet]:
        all_items = list(StoredStyleSheet(i) for i in ALL_STYLE_SHEETS.values()) + list(MaterialStyleSheet(i) for i in list_themes())
        return [item for item in all_items if item.is_broken is False]

    def data(self, index: Union[PySide6.QtCore.QModelIndex, PySide6.QtCore.QPersistentModelIndex], role: int = None) -> Any:
        if not index.isValid():
            return
        item = self.content_items[index.row()]
        if role is None:
            return item

        return item.get_data(role)

    def rowCount(self, parent: Union[PySide6.QtCore.QModelIndex, PySide6.QtCore.QPersistentModelIndex] = ...) -> int:
        return len(self.content_items)

    def columnCount(self, parent: Union[PySide6.QtCore.QModelIndex, PySide6.QtCore.QPersistentModelIndex] = ...) -> int:
        return 1

# region[Main_Exec]


if __name__ == '__main__':
    x = [StoredStyleSheet(i) for i in ALL_STYLE_SHEETS.values()]
    for i in x:
        pp(i.display_data)

# endregion[Main_Exec]
