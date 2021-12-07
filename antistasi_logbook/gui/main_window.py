
"""
WiP.

Soon.
"""

# region [Imports]

from antistasi_logbook import setup
setup()
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
from gidapptools import get_logger, get_meta_config, get_meta_info, get_meta_paths
import PySide6
# from __feature__ import true_property
from PySide6.QtCore import QCoreApplication, QDate, QDateTime, QLocale, QMetaObject, QObject, QPoint, QRect, QSize, QTime, QUrl, Qt
from PySide6.QtGui import (QAction, QBrush, QColor, QConicalGradient, QCursor, QFont, QFontDatabase, QGradient, QIcon, QImage, QKeySequence,
                           QLinearGradient, QPainter, QPalette, QPixmap, QRadialGradient, QTransform)
from PySide6.QtWidgets import QApplication, QGridLayout, QMainWindow, QMenu, QMenuBar, QSizePolicy, QStatusBar, QWidget, QPushButton, QBoxLayout, QHBoxLayout, QVBoxLayout, QSizePolicy, QLayout

from PySide6 import QtCore, QtGui
from antistasi_logbook.gui.resources.antistasi_logbook_resources_accessor import AllResourceItems
from antistasi_logbook.utilities.misc import obj_inspection
from gidapptools.gidapptools_qt.basics.menu_bar import MenuBar
if TYPE_CHECKING:
    from gidapptools.gid_config.interface import GidIniConfig
# endregion[Imports]

# region [TODO]


# endregion [TODO]

# region [Logging]


# endregion[Logging]

# region [Constants]

THIS_FILE_DIR = Path(__file__).parent.absolute()
log = get_logger(__name__)
META_CONFIG = get_meta_config()
META_PATHS = get_meta_paths()
# endregion[Constants]


class MainWidget(QWidget):

    def __init__(self, parent: Optional[PySide6.QtWidgets.QWidget] = None) -> None:
        self.button: QPushButton = None
        self.main_layout: QLayout = None
        super().__init__(parent=parent)
        self.setup()

    def setup(self) -> None:
        self.main_layout = QGridLayout(self)
        self.setLayout(self.main_layout)
        self.button = QPushButton(text="wuff", icon=AllResourceItems.antistasi_logo_gun_1.get_as_pixmap())
        self.main_layout.addWidget(self.button)


class AntistasiLogbookMainWindow(QMainWindow):

    def __init__(self, app: QApplication, config: "GidIniConfig") -> None:
        self.app = app
        self.config = config
        self.main_widget: QWidget = None
        self.menubar: QMenuBar = None
        self.statusbar: QStatusBar = None
        super().__init__()
        self.setup()

    @property
    def initial_size(self) -> list[int, int]:
        return self.config.get("main_window", "initial_size", default=[1000, 800])

    def setup(self) -> None:
        self.set_menubar(MenuBar(self))

        self.resize(*self.initial_size)
        self.setWindowIcon(AllResourceItems.arma_image_icon.get_as_pixmap())
        self.set_main_widget(MainWidget(self))

    def set_menubar(self, menubar: QMenuBar) -> None:
        self.menubar = menubar
        self.setMenuBar(menubar)

    def set_main_widget(self, main_widget: QWidget) -> None:
        self.main_widget = main_widget
        self.setCentralWidget(main_widget)

    def close(self) -> bool:
        return super().close()

    def closeEvent(self, event):
        log.info("closing application because of %s", event.type())
        self.close()


        # region[Main_Exec]
if __name__ == '__main__':
    _app = QApplication(sys.argv)
    m = AntistasiLogbookMainWindow(_app, META_CONFIG.get_config('general'))
    m.show()
    _app.exec()


# endregion[Main_Exec]
