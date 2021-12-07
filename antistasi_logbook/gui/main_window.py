
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
from PySide6.QtCore import QCoreApplication, QDate, QDateTime, QLocale, QMetaObject, QObject, QPoint, QRect, QSize, QTime, QUrl, Qt, QEvent, QThread, QThreadPool, QRunnable
from PySide6.QtGui import (QAction, QBrush, QColor, QConicalGradient, QCursor, QFont, QFontDatabase, QGradient, QIcon, QImage, QKeySequence,
                           QLinearGradient, QPainter, QPalette, QPixmap, QRadialGradient, QTransform, QCloseEvent)
from PySide6.QtWidgets import QSystemTrayIcon, QApplication, QGridLayout, QMainWindow, QMenu, QMessageBox, QMenuBar, QSizePolicy, QStatusBar, QWidget, QPushButton, QBoxLayout, QHBoxLayout, QVBoxLayout, QSizePolicy, QLayout
from threading import Thread
from PySide6 import QtCore, QtGui
from antistasi_logbook.gui.resources.antistasi_logbook_resources_accessor import AllResourceItems
from antistasi_logbook.utilities.misc import obj_inspection
from antistasi_logbook.gui.menu_bar import LogbookMenuBar
from antistasi_logbook.gui.main_widget import MainWidget
from antistasi_logbook.gui.sys_tray import LogbookSystemTray
from gidapptools.utility._debug_tools import obj_inspection
from gidapptools.general_helper.string_helper import StringCaseConverter
from antistasi_logbook.backend import Backend, GidSqliteApswDatabase
from antistasi_logbook.storage.models.models import RemoteStorage
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
META_INFO = get_meta_info()
# endregion[Constants]


class UpdateRunnable(QRunnable):
    def __init__(self, func, call_back) -> None:
        self.func = func
        self.call_back = call_back
        super().__init__()

    def run(self) -> None:
        self.func()
        log.info("done updating")
        self.call_back()


class AntistasiLogbookMainWindow(QMainWindow):

    def __init__(self, app: QApplication, config: "GidIniConfig") -> None:
        self.app = app
        self.config = config
        self.backend: "Backend" = None
        self.main_widget: QWidget = None
        self.menubar: QMenuBar = None
        self.statusbar: QStatusBar = None
        self.update_button: QPushButton = None
        self.sys_tray: "LogbookSystemTray" = None
        self.name: str = None
        self.title: str = None

        super().__init__()
        self.setup()

    @property
    def initial_size(self) -> list[int, int]:
        return self.config.get("main_window", "initial_size", default=[1000, 800])

    def setup(self) -> None:
        self.name = StringCaseConverter.convert_to(META_INFO.app_name, StringCaseConverter.TITLE)
        self.title = f"{self.name} {META_INFO.version}"
        self.setWindowTitle(self.title)

        self.set_menubar(LogbookMenuBar(self))
        self.setWindowIcon(self.app.icon)
        self.resize(*self.initial_size)
        self.set_main_widget(MainWidget(self))
        self.sys_tray = LogbookSystemTray(self, self.app)
        self.sys_tray.show()
        self.setup_statusbar()
        self.setup_backend()

    def setup_backend(self) -> None:
        db_path = self.config.get('database', "database_path", default=None)
        database = GidSqliteApswDatabase(db_path, config=self.config)
        self.backend = Backend(database=database, config=self.config)
        self.backend.start_up()
        self.update_button.clicked.connect(self._do_update)

    def setup_statusbar(self) -> None:
        self.statusbar = QStatusBar(self)
        self.update_button = QPushButton("Update")
        self.statusbar.addWidget(self.update_button)
        self.setStatusBar(self.statusbar)

    def set_menubar(self, menubar: QMenuBar) -> None:
        self.menubar = menubar
        self.setMenuBar(menubar)

    def set_main_widget(self, main_widget: QWidget) -> None:
        self.main_widget = main_widget
        self.setCentralWidget(main_widget)

    def _do_update(self) -> None:
        def _run_update():
            self.update_button.setEnabled(False)
            self.backend.updater()
            self.update_button.setEnabled(True)

        x = Thread(target=_run_update)
        x.start()

    def close(self) -> bool:
        return super().close()

    def event(self, event: QEvent) -> bool:
        # log.debug("received event %r", event)
        return super().event(event)

    def closeEvent(self, event: QCloseEvent):

        reply = QMessageBox.question(self, 'Message', 'Are you sure you want to quit?', QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.Yes:
            log.info("closing %r", self)
            self.backend.shutdown()
            event.accept()
        else:
            event.ignore()

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}"


        # region[Main_Exec]
if __name__ == '__main__':
    import dotenv
    dotenv.load_dotenv(r"D:\Dropbox\hobby\Modding\Programs\Github\My_Repos\Antistasi_Logbook\antistasi_logbook\nextcloud.env")
    _app = QApplication(sys.argv)

    _app.icon = AllResourceItems.placeholder.get_as_icon()
    m = AntistasiLogbookMainWindow(_app, META_CONFIG.get_config('general'))
    RemoteStorage.get(name="community_webdav").set_login_and_password(login=os.getenv("NEXTCLOUD_USERNAME"), password=os.getenv("NEXTCLOUD_PASSWORD"), store_in_db=False)
    m.show()
    _app.exec()


# endregion[Main_Exec]
