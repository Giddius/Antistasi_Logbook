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

from antistasi_logbook.gui.resources.antistasi_logbook_resources_accessor import AllResourceItems
from gidapptools import get_logger
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

from PySide6.QtWidgets import (QApplication, QBoxLayout, QCheckBox, QColorDialog, QColumnView, QStyle, QComboBox, QDateTimeEdit, QDialogButtonBox,
                               QDockWidget, QDoubleSpinBox, QFontComboBox, QFormLayout, QFrame, QGridLayout, QGroupBox, QHBoxLayout, QHeaderView,
                               QLCDNumber, QLabel, QLayout, QLineEdit, QListView, QListWidget, QMainWindow, QMenu, QMenuBar, QMessageBox,
                               QProgressBar, QProgressDialog, QPushButton, QSizePolicy, QSpacerItem, QSpinBox, QStackedLayout, QStackedWidget,
                               QStatusBar, QStyledItemDelegate, QSystemTrayIcon, QTabWidget, QTableView, QTextEdit, QTimeEdit, QToolBox, QTreeView,
                               QVBoxLayout, QWidget, QAbstractItemDelegate, QAbstractItemView, QAbstractScrollArea, QRadioButton, QFileDialog, QStyleOptionViewItem, QButtonGroup)
from antistasi_logbook.gui.misc import CustomRole
if TYPE_CHECKING:
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


class MarkedImageDelegate(QStyledItemDelegate):
    @profile
    def __init__(self, parent=None):
        super().__init__(parent)
        self.pixmaps = {True: AllResourceItems.mark_image.get_as_pixmap(25, 25), False: AllResourceItems.unmark_image.get_as_pixmap(25, 25)}

    @profile
    def paint(self, painter: QPainter, option, index: QModelIndex):
        self.handle_background(painter, option, index)
        raw_data = index.model().data(index, CustomRole.RAW_DATA)
        painter.setRenderHint(QPainter.SmoothPixmapTransform, True)
        target_rect = QRect(option.rect)
        target_rect.setHeight(25)
        target_rect.setWidth(25)
        target_rect.moveCenter(option.rect.center())
        painter.drawPixmap(target_rect, self.pixmaps[raw_data])

    @profile
    def handle_background(self, painter: QPainter, option, index: QModelIndex):

        item_background = index.model().data(index, Qt.BackgroundRole)
        if item_background:
            painter.fillRect(option.rect, item_background)
        if option.state & QStyle.State_Selected:
            color = option.palette.highlight().color()
            color.setAlpha(50)
            painter.fillRect(option.rect, color)
        elif option.state & QStyle.State_MouseOver:
            color = option.palette.highlight().color()
            color.setAlpha(25)
            painter.fillRect(option.rect, color)

    def sizeHint(self, option, index):
        """ Returns the size needed to display the item in a QSize object. """
        return QSize(20, 20)


class BoolImageDelegate(QStyledItemDelegate):
    @profile
    def __init__(self, parent=None):
        super().__init__(parent)
        self.pixmaps = {True: AllResourceItems.check_mark_green_image.get_as_pixmap(25, 25), False: AllResourceItems.close_cancel_image.get_as_pixmap(25, 25)}

    @profile
    def paint(self, painter: QPainter, option, index: QModelIndex):
        self.handle_background(painter, option, index)

        raw_data = index.model().data(index, CustomRole.RAW_DATA)
        if raw_data is True:
            painter.setRenderHint(QPainter.SmoothPixmapTransform, True)
            target_rect = QRect(option.rect)
            target_rect.setHeight(25)
            target_rect.setWidth(25)
            target_rect.moveCenter(option.rect.center())
            painter.drawPixmap(target_rect, self.pixmaps[raw_data])

    @profile
    def handle_background(self, painter: QPainter, option, index: QModelIndex):

        item_background = index.model().data(index, Qt.BackgroundRole)
        if item_background:
            painter.fillRect(option.rect, item_background)
        if option.state & QStyle.State_Selected:
            color = option.palette.highlight().color()
            color.setAlpha(50)
            painter.fillRect(option.rect, color)
        elif option.state & QStyle.State_MouseOver:
            color = option.palette.highlight().color()
            color.setAlpha(25)
            painter.fillRect(option.rect, color)

    @profile
    def sizeHint(self, option, index):
        """ Returns the size needed to display the item in a QSize object. """
        return QSize(20, 20)


# region[Main_Exec]

if __name__ == '__main__':
    pass

# endregion[Main_Exec]
