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

from PySide6.QtCore import (QByteArray, QMimeData, QCoreApplication, QDate, QDateTime, QEvent, QLocale, QMetaObject, QModelIndex, QModelRoleData, QMutex,
                            QMutexLocker, QObject, QPoint, QRect, QRecursiveMutex, QRunnable, QSettings, QSize, QThread, QThreadPool, QTime, QUrl,
                            QWaitCondition, Qt, QAbstractItemModel, QAbstractListModel, QAbstractTableModel, Signal, Slot)

from PySide6.QtGui import (QAction, QDrag, QBrush, QMouseEvent, QDesktopServices, QColor, QConicalGradient, QCursor, QFont, QFontDatabase, QFontMetrics, QGradient, QIcon, QImage,
                           QKeySequence, QLinearGradient, QPainter, QPalette, QPixmap, QRadialGradient, QTransform)

from PySide6.QtWidgets import (QApplication, QStyleOptionToolBar, QToolBar, QBoxLayout, QCheckBox, QColorDialog, QColumnView, QComboBox, QDateTimeEdit, QDialogButtonBox,
                               QDockWidget, QDoubleSpinBox, QFontComboBox, QFormLayout, QFrame, QGridLayout, QGroupBox, QHBoxLayout, QHeaderView,
                               QLCDNumber, QLabel, QLayout, QLineEdit, QListView, QListWidget, QMainWindow, QMenu, QMenuBar, QMessageBox,
                               QProgressBar, QProgressDialog, QPushButton, QSizePolicy, QSpacerItem, QSpinBox, QStackedLayout, QStackedWidget,
                               QStatusBar, QStyledItemDelegate, QSystemTrayIcon, QTabWidget, QTableView, QTextEdit, QTimeEdit, QToolBox, QTreeView,
                               QVBoxLayout, QWidget, QAbstractItemDelegate, QAbstractItemView, QAbstractScrollArea, QRadioButton, QFileDialog, QButtonGroup)

from antistasi_logbook.gui.resources.antistasi_logbook_resources_accessor import AllResourceItems
from gidapptools import get_logger

if TYPE_CHECKING:
    from antistasi_logbook.gui.main_window import AntistasiLogbookMainWindow
    from antistasi_logbook.gui.application import AntistasiLogbookApplication
    from antistasi_logbook.storage.models.models import LogFile
    from antistasi_logbook.gui.views.log_files_query_view import LogFilesQueryTreeView
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


class DragIconLabel(QWidget):
    pixmap_width = 50
    pixmap_height = 50

    def __init__(self, pixmap: QPixmap, text: str = None, items: Iterable["LogFilesQueryTreeView"] = None, parent=None):
        super().__init__(parent=parent)
        self.setLayout(QVBoxLayout())
        self.items = items
        self.drag_start_pos = None
        self._pixmap = pixmap.scaled(self.parent().iconSize(), Qt.KeepAspectRatioByExpanding, Qt.TransformationMode.SmoothTransformation)
        self.icon_label = QLabel(parent=self)
        self.icon_label.setPixmap(self._pixmap)
        self.icon_label.setAlignment(Qt.AlignHCenter | Qt.AlignBottom)

        self.layout.addWidget(self.icon_label)

        self.text_label = QLabel(text or "", parent=self)
        self.text_label.setAlignment(Qt.AlignHCenter | Qt.AlignBottom)
        self.layout.addWidget(self.text_label)
        self.layout.setAlignment(Qt.AlignCenter)
        self.setToolTip("Drag and drop into the folder where you want to save the file")
        self.setEnabled(False)

    @property
    def layout(self) -> QVBoxLayout:
        return super().layout()

    def set_items(self, items: Iterable["LogFile"]):
        self.items = items
        if self.items is not None:
            self.setEnabled(True)
        else:
            self.setEnabled(False)

    def mouseDoubleClickEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.LeftButton:
            for item in self.items:
                original_file: Path = item.original_file.to_file()
                QDesktopServices.openUrl(QUrl.fromLocalFile(original_file))

        else:
            super().mouseDoubleClickEvent(event)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.LeftButton:
            self.drag_start_pos = event.pos()

        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if event.buttons() & Qt.LeftButton and (event.pos() - self.drag_start_pos).manhattanLength() >= QApplication.startDragDistance():

            if self.items:
                try:
                    drag = QDrag(self)
                    drag.setPixmap(self._pixmap)
                    self.icon_label.clear()
                    mime_data = QMimeData()
                    urls = []
                    for item in self.items:

                        original_file: Path = item.original_file.to_file()
                        urls.append(QUrl.fromLocalFile(original_file))

                    mime_data.setData("text/plain", b"")
                    mime_data.setUrls(urls)
                    drag.setMimeData(mime_data)
                    drag.exec(Qt.CopyAction)
                finally:
                    self.icon_label.setPixmap(self._pixmap)
        else:
            super().mouseMoveEvent(event)


class BaseToolBar(QToolBar):

    def __init__(self, parent: Union[QMainWindow, QWidget] = None, title: str = None) -> None:
        super().__init__(*[i for i in (parent, title) if i])
        self.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        self.setOrientation(Qt.Horizontal)
        self.setMovable(False)
        self.setFloatable(False)
        self.setAllowedAreas(Qt.TopToolBarArea)
        self.setIconSize(QSize(35, 35))
        self.setMinimumHeight(85)
        self.setup_actions()

    def setup_actions(self):
        self.addSeparator()


class LogFileToolBar(BaseToolBar):

    def __init__(self, parent: Union[QMainWindow, QWidget] = None) -> None:
        super().__init__(parent, "Log-Files")

    def setup_actions(self):
        super().setup_actions()
        self.export_action_widget = DragIconLabel(pixmap=AllResourceItems.txt_file_image.get_as_pixmap(), text="Original File", parent=self)
        self.addWidget(self.export_action_widget)
        self.show_records_action = QAction(AllResourceItems.log_records_tab_icon_image.get_as_icon(), "Show Records", self)
        self.addAction(self.show_records_action)


# region[Main_Exec]
if __name__ == '__main__':
    pass

# endregion[Main_Exec]
