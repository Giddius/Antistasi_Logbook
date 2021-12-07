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
from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale, QMetaObject, QObject, QPoint, QRect, QSize, QTime, QUrl, Qt,
                            QAbstractTableModel, QAbstractItemModel, QAbstractListModel)
from PySide6.QtGui import (QAction, QBrush, QColor, QConicalGradient, QCursor, QFont, QFontDatabase, QGradient, QIcon, QImage, QKeySequence,
                           QLinearGradient, QPainter, QPalette, QPixmap, QRadialGradient, QTransform)
from PySide6.QtWidgets import (QApplication, QGridLayout, QMainWindow, QMenu, QMenuBar, QSizePolicy, QStatusBar, QWidget, QPushButton,
                               QBoxLayout, QHBoxLayout, QVBoxLayout, QSizePolicy, QLayout, QGroupBox, QDockWidget, QTabWidget)
from antistasi_logbook.gui.resources.antistasi_logbook_resources_accessor import AllResourceItems
if TYPE_CHECKING:
    from antistasi_logbook.gui.main_window import AntistasiLogbookMainWindow
# endregion[Imports]

# region [TODO]


# endregion [TODO]

# region [Logging]


# endregion[Logging]

# region [Constants]

THIS_FILE_DIR = Path(__file__).parent.absolute()

# endregion[Constants]


class MainWidget(QWidget):
    def __init__(self, main_window: "AntistasiLogbookMainWindow") -> None:
        super().__init__(parent=main_window)
        self.main_window = main_window
        self.info_widget: QGroupBox = None
        self.query_widget: QDockWidget = None
        self.detail_widget: QDockWidget = None
        self.main_tabs_widget: QTabWidget = None
        self.server_tab: QWidget = None
        self.log_files_tab: QWidget = None
        self.query_result_tab: QWidget = None
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
        self.query_widget.setMinimumSize(QSize(100, 50))
        self.query_widget.setAllowedAreas(Qt.LeftDockWidgetArea)
        self.query_widget.setFeatures(QDockWidget.DockWidgetMovable | QDockWidget.DockWidgetFloatable | QDockWidget.DockWidgetClosable)
        view_action = self.query_widget.toggleViewAction()
        view_action.setText("Query")
        self.main_window.menubar.view_menu.addAction(view_action)
        self.main_window.addDockWidget(Qt.LeftDockWidgetArea, self.query_widget)
        # self.main_layout.addWidget(self.query_widget, 1, 0, 1, 1)

    def setup_detail_widget(self) -> None:
        self.detail_widget = QDockWidget("Details", self.parent())
        self.detail_widget.setMinimumSize(QSize(150, 100))
        self.detail_widget.setAllowedAreas(Qt.RightDockWidgetArea)
        self.detail_widget.setFeatures(QDockWidget.DockWidgetMovable | QDockWidget.DockWidgetFloatable | QDockWidget.DockWidgetClosable)
        view_action = self.detail_widget.toggleViewAction()
        view_action.setText("Details")
        self.main_window.menubar.view_menu.addAction(view_action)
        self.main_window.addDockWidget(Qt.RightDockWidgetArea, self.detail_widget)
        # self.main_layout.addWidget(self.detail_widget, 1, 2, 1, 1)

    def setup_main_tabs_widget(self) -> None:
        self.main_tabs_widget = QTabWidget(self)
        size_policy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        size_policy.setHorizontalStretch(2)
        size_policy.setVerticalStretch(0)
        self.main_tabs_widget.setSizePolicy(size_policy)
        self.main_tabs_widget.setMinimumSize(QSize(250, 100))

        self.server_tab = QWidget()
        self.main_tabs_widget.addTab(self.server_tab, AllResourceItems.placeholder.get_as_icon(), "Server")
        self.log_files_tab = QWidget()
        self.main_tabs_widget.addTab(self.log_files_tab, AllResourceItems.placeholder.get_as_icon(), "Log-Files")
        self.query_result_tab = QWidget()
        self.main_tabs_widget.addTab(self.query_result_tab, AllResourceItems.placeholder.get_as_icon(), "Query Result")

        self.main_layout.addWidget(self.main_tabs_widget, 1, 1, 1, 1)


# region[Main_Exec]
if __name__ == '__main__':
    pass

# endregion[Main_Exec]
