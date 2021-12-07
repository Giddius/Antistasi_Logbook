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
from gidapptools.general_helper.string_helper import make_attribute_name
import PySide6
from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale, QMetaObject, QObject, QPoint, QRect, QSize, QTime, QUrl, Qt,
                            QAbstractTableModel, QAbstractItemModel, QAbstractListModel)
from PySide6.QtGui import (QAction, QBrush, QColor, QConicalGradient, QCursor, QFont, QFontDatabase, QGradient, QIcon, QImage, QKeySequence,
                           QLinearGradient, QPainter, QPalette, QPixmap, QRadialGradient, QTransform)
from PySide6.QtWidgets import (QApplication, QGridLayout, QMainWindow, QMenu, QMenuBar, QSizePolicy, QStatusBar, QWidget, QPushButton, QLabel,
                               QBoxLayout, QHBoxLayout, QVBoxLayout, QSizePolicy, QLayout, QGroupBox, QDockWidget, QTabWidget, QSystemTrayIcon, QWidgetAction)
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


class LogbookSystemTray(QSystemTrayIcon):

    def __init__(self, main_window: "AntistasiLogbookMainWindow", app: "QApplication") -> None:
        self.main_window = main_window
        self.app = app
        self.tray_icon = self.app.icon
        self.menu: QMenu = None
        self.menu_title: QLabel = None

        super().__init__(self.tray_icon, self.main_window)
        self.setup()

    def setup(self) -> None:
        self.setup_menu()

    def setup_menu(self) -> None:
        self.menu = QMenu(self.main_window)
        self.menu.setStyleSheet(f"border: 1px solid black;background-color: white;margin: 4px")

        self.add_menu_title()
        self.hide_show_action = self.add_action("Minimize to Tray", connect_to=self.switch_main_window_visible, icon=AllResourceItems.hidden.get_as_icon())

        self.close_action = self.add_action("Close", connect_to=self.main_window.close, icon=AllResourceItems.close_cancel.get_as_icon())
        self.setContextMenu(self.menu)

    def add_menu_title(self) -> None:
        widget_action = QWidgetAction(self.menu)
        self.menu_title = QLabel(self.main_window.name)
        self.menu_title.setAlignment(Qt.AlignCenter)
        self.menu_title.setStyleSheet(f"background-color: rgba(87,80,68,200); color: white; font: bold 14px;margin: 6px")

        widget_action.setDefaultWidget(self.menu_title)
        self.menu.addAction(widget_action)

    def add_action(self, title: str, connect_to: Callable = None, icon: QIcon = None, enabled: bool = True) -> QAction:
        action = QAction(title)

        if icon is not None:
            action.setIcon(icon)

        self.menu.addAction(action)

        if connect_to is not None:
            action.triggered.connect(connect_to)
        action.setEnabled(enabled)
        return action

    def switch_main_window_visible(self):
        main_window_visible = self.main_window.isVisible()
        self.main_window.setVisible(not main_window_visible)
        text = "Minimize to Tray" if main_window_visible is False else "Open"
        icon = AllResourceItems.hidden.get_as_icon() if main_window_visible is False else AllResourceItems.view.get_as_icon()
        self.hide_show_action.setText(text)
        self.hide_show_action.setIcon(icon)

    # region[Main_Exec]


if __name__ == '__main__':
    pass

# endregion[Main_Exec]
