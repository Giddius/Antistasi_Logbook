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
from typing import TYPE_CHECKING, Protocol, Union, Callable, Iterable, Optional, Mapping, Any, IO, TextIO, BinaryIO, Hashable, Generator, Literal, TypeVar, TypedDict, AnyStr
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

from gidapptools import get_logger
from antistasi_logbook.gui.widgets.data_view_widget.type_fields.base_type_field import TypeFieldProtocol
from gidapptools.general_helper.typing_helper import implements_protocol
from antistasi_logbook.gui.resources.antistasi_logbook_resources_accessor import AllResourceItems
# endregion[Imports]

# region [TODO]


# endregion [TODO]

# region [Logging]


# endregion[Logging]

# region [Constants]

THIS_FILE_DIR = Path(__file__).parent.absolute()
log = get_logger(__name__)
# endregion[Constants]


@implements_protocol(TypeFieldProtocol)
class BoolTypeField(QLabel):
    ___typus___: type = bool

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        # self.setLayoutDirection(Qt.RightToLeft)
        self.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self._image_size: QSize = QSize(50, 50)
        self.image_table = {True: AllResourceItems.check_mark_green_image.get_as_pixmap(),
                            False: AllResourceItems.close_cancel_image.get_as_pixmap()}

    def set_size(self, w: int, h: int) -> None:
        self._image_size = QSize(w, h)
        if self.pixmap() is not None:
            self.setPixmap(self.pixmap().scaled(self._image_size, Qt.KeepAspectRatioByExpanding))

    def set_value(self, value: bool) -> None:
        self.clear()
        pixmap = self.image_table.get(value, None)
        if pixmap is None:

            self.setText('-')
        else:
            if self._image_size is not None:
                pixmap = pixmap.scaled(self._image_size, Qt.KeepAspectRatioByExpanding)
            self.setPixmap(pixmap)

    @classmethod
    def add_to_type_field_table(cls, table: dict):
        table[cls.___typus___] = cls
        return table


@implements_protocol(TypeFieldProtocol)
class StringTypeField(QLabel):
    ___typus___: type = str

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setLayoutDirection(Qt.RightToLeft)
        self.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.setTextFormat(Qt.MarkdownText)

    def set_size(self, h, w):
        pass

    def set_value(self, value: str):
        self.setText(f"`{value}`")

    @classmethod
    def add_to_type_field_table(cls, table: dict):
        table[cls.___typus___] = cls
        return table


@implements_protocol(TypeFieldProtocol)
class IntTypeField(StringTypeField):
    ___typus___: type = int

    def set_value(self, value: int):
        return super().set_value(str(value))


@implements_protocol(TypeFieldProtocol)
class FloatTypeField(StringTypeField):
    ___typus___: type = float

    def set_value(self, value: float):
        return super().set_value(str(value))


@implements_protocol(TypeFieldProtocol)
class ListTypeField(QListWidget):
    ___typus___: type = list

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.values = None

    def set_size(self, h, w):
        pass

    def set_value(self, value: list):
        self.values = value
        self.addItems(str(i) for i in value)

    @classmethod
    def add_to_type_field_table(cls, table: dict):
        table[cls.___typus___] = cls
        return table


# region[Main_Exec]
if __name__ == '__main__':
    pass

# endregion[Main_Exec]
