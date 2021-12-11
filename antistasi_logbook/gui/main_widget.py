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
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, Future, FIRST_EXCEPTION, FIRST_COMPLETED, ALL_COMPLETED, wait
from importlib.machinery import SourceFileLoader
import PySide6
import pp
from threading import Lock
from gidapptools import get_logger
from PySide6 import QtWidgets, QtGui
from antistasi_logbook.gui.models.server_model import ServerModel
from antistasi_logbook.gui.models.log_files_model import LogFilesModel
from antistasi_logbook.gui.models.log_records_model import LogRecordsModel
from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale, QMetaObject, QObject, QPoint, QRect, QSize, QTime, QUrl, Qt, QModelIndex, QThreadPool, QMutexLocker, QMutex, QRecursiveMutex, QWaitCondition,
                            QAbstractTableModel, QAbstractItemModel, QAbstractListModel)
from PySide6.QtGui import (QAction, QBrush, QColor, QConicalGradient, QCursor, QFont, QFontDatabase, QGradient, QIcon, QImage, QKeySequence,
                           QLinearGradient, QPainter, QPalette, QPixmap, QRadialGradient, QTransform)
from PySide6.QtWidgets import (QApplication, QGridLayout, QMainWindow, QMenu, QMenuBar, QSizePolicy, QStatusBar, QWidget, QPushButton, QFrame, QToolBox, QLabel, QFormLayout, QLCDNumber, QLineEdit,
                               QBoxLayout, QHBoxLayout, QVBoxLayout, QSizePolicy, QLayout, QGroupBox, QDockWidget, QTabWidget, QTableView, QListView, QTreeView, QColumnView, QHeaderView)
from antistasi_logbook.gui.resources.antistasi_logbook_resources_accessor import AllResourceItems
from antistasi_logbook.storage.models.models import Server, LogFile, LogRecord
from antistasi_logbook.gui.views.base_query_tree_view import ServerQueryTreeView, LogFilesQueryTreeView, BaseQueryTreeView, LogRecordsQueryTreeView
if TYPE_CHECKING:
    from antistasi_logbook.gui.main_window import AntistasiLogbookMainWindow
# endregion[Imports]

# region [TODO]


# endregion [TODO]

# region [Logging]


# endregion[Logging]

# region [Constants]

THIS_FILE_DIR = Path(__file__).parent.absolute()
log = get_logger(__name__)
# endregion[Constants]


class MainWidget(QWidget):
    query_result_lock = Lock()

    def __init__(self, main_window: "AntistasiLogbookMainWindow") -> None:
        super().__init__(parent=main_window)
        self.main_window = main_window
        self.info_widget: QGroupBox = None
        self.query_widget: QDockWidget = None
        self.detail_widget: QDockWidget = None
        self.main_tabs_widget: QTabWidget = None
        self.server_tab: ServerQueryTreeView = None
        self.log_files_tab: LogFilesQueryTreeView = None
        self.query_result_tab: QTableView = None
        self.temp_runnable = None
        self.setup()

    def setup(self) -> None:
        self.main_layout = QGridLayout(self)
        self.setLayout(self.main_layout)
        self.setup_info_widget()
        self.setup_query_widget()
        self.setup_detail_widget()
        self.setup_main_tabs_widget()

    def setup_info_widget(self) -> None:
        self.info_widget = QGroupBox(self)
        self.info_widget.setMinimumSize(QSize(0, 50))
        self.info_widget.setMaximumSize(QSize(16777215, 50))
        self.main_layout.addWidget(self.info_widget, 0, 0, 1, 3)

    def setup_query_widget(self) -> None:
        self.query_widget = QDockWidget("Query", self.parent())
        self.query_widget.setMinimumSize(QSize(100, 75))
        self.query_widget.setAllowedAreas(Qt.LeftDockWidgetArea)
        self.query_widget.setFeatures(QDockWidget.DockWidgetMovable | QDockWidget.DockWidgetFloatable | QDockWidget.DockWidgetClosable)
        view_action = self.query_widget.toggleViewAction()
        view_action.setText("Query")
        self.main_window.menubar.view_menu.addAction(view_action)
        self.main_window.addDockWidget(Qt.LeftDockWidgetArea, self.query_widget)
        # self.main_layout.addWidget(self.query_widget, 1, 0, 1, 1)

    def setup_detail_widget(self) -> None:
        self.detail_widget = QDockWidget("Details", self.parent())
        self.detail_widget.setMinimumSize(QSize(175, 100))

        self.detail_widget.setAllowedAreas(Qt.RightDockWidgetArea)
        self.detail_widget.setFeatures(QDockWidget.DockWidgetMovable | QDockWidget.DockWidgetFloatable | QDockWidget.DockWidgetClosable)
        self.detail_widget.setSizePolicy(QSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.MinimumExpanding))
        self.detail_widget.dockLocationChanged.connect(self.detail_widget_resize_on_undock)
        self.detail_widget.featuresChanged.connect(print)
        view_action = self.detail_widget.toggleViewAction()
        view_action.setText("Details")
        self.main_window.menubar.view_menu.addAction(view_action)
        self.main_window.addDockWidget(Qt.RightDockWidgetArea, self.detail_widget)
        self.detail_widget.hide()

    def setup_main_tabs_widget(self) -> None:
        self.main_tabs_widget = QTabWidget(self)
        size_policy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        size_policy.setHorizontalStretch(2)
        size_policy.setVerticalStretch(0)
        self.main_tabs_widget.setSizePolicy(size_policy)
        self.main_tabs_widget.setMinimumSize(QSize(250, 100))

        self.server_tab = ServerQueryTreeView().setup()

        self.main_tabs_widget.addTab(self.server_tab, self.server_tab.icon, self.server_tab.name)

        self.log_files_tab = LogFilesQueryTreeView().setup()
        self.log_files_tab.doubleClicked.connect(self.query_log_file)
        self.main_tabs_widget.addTab(self.log_files_tab, self.log_files_tab.icon, self.log_files_tab.name)

        self.query_result_tab = QTableView()
        self.query_result_tab.setWordWrap(False)
        self.query_result_tab.resizeColumnsToContents()

        self.main_tabs_widget.addTab(self.query_result_tab, AllResourceItems.placeholder.get_as_icon(), "Log-Records")

        self.main_layout.addWidget(self.main_tabs_widget, 1, 1, 1, 1)

    def setup_views(self) -> None:
        server_model = ServerModel(self.main_window.backend)
        self.main_window.thread_pool.submit(server_model.generator_refresh)
        self.server_tab.setModel(server_model)
        self.server_tab.adjustSize()

        log_file_model = LogFilesModel(self.main_window.backend)
        self.main_window.thread_pool.submit(log_file_model.generator_refresh)
        self.log_files_tab.setModel(log_file_model)
        self.log_files_tab.adjustSize()

    def detail_widget_resize_on_undock(self, area: Qt.DockWidgetArea) -> None:
        if area == Qt.NoDockWidgetArea:
            self.detail_widget.adjustSize()

    def query_log_file(self, index: QModelIndex):

        def dd(f: Future):
            try:
                if f.exception() is not None:
                    log.error(f.exception(), exc_info=True)
                self.temp_runnable = None
                self.query_result_tab.resizeColumnsToContents()
            finally:
                self.query_result_lock.release()

            log.info("finished future %r", f)

        aquired = self.query_result_lock.acquire(timeout=0.25)
        if aquired is False:
            log.debug("Unable to aquire the lock %r, returning", self.query_result_lock)
            return

        log_file = self.log_files_tab.model().content_items[index.row()]
        if self.query_result_tab.model() is None:

            log_record_model = LogRecordsModel(self.main_window.backend)
            self.query_result_tab.setModel(log_record_model)
        log_record_model = self.query_result_tab.model()
        log_record_model.filter.append(LogRecord.log_file == log_file)

        self.query_result_tab.setModel(log_record_model)
        log.debug("added model %r to %r", log_record_model, self.query_result_tab)
        t = self.main_window.thread_pool.submit(log_record_model.generator_refresh)

        t.add_done_callback(dd)
        log.debug("started thread")


# region[Main_Exec]
if __name__ == '__main__':
    pass

# endregion[Main_Exec]
