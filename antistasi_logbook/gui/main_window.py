
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
from PySide6.QtCore import QCoreApplication, QDate, QDateTime, QLocale, QMetaObject, QObject, QPoint, QRect, QSize, QTime, QByteArray, QUrl, Qt, QEvent, QSettings, QThread, QThreadPool, QRunnable, Signal, Slot
from PySide6.QtGui import (QAction, QBrush, QColor, QConicalGradient, QCursor, QFont, QFontDatabase, QGradient, QIcon, QImage, QKeySequence,
                           QLinearGradient, QPainter, QPalette, QPixmap, QRadialGradient, QTransform, QCloseEvent)
from PySide6.QtWidgets import QSystemTrayIcon, QApplication, QGridLayout, QMainWindow, QMenu, QMessageBox, QMenuBar, QSizePolicy, QStatusBar, QWidget, QPushButton, QBoxLayout, QHBoxLayout, QVBoxLayout, QSizePolicy, QLayout

from threading import Thread, Event
from PySide6 import QtCore, QtGui
from antistasi_logbook.gui.resources.antistasi_logbook_resources_accessor import AllResourceItems
from antistasi_logbook.utilities.misc import obj_inspection
from antistasi_logbook.gui.menu_bar import LogbookMenuBar
from antistasi_logbook.gui.main_widget import MainWidget
from antistasi_logbook.gui.sys_tray import LogbookSystemTray
from gidapptools.utility._debug_tools import obj_inspection
from gidapptools.general_helper.string_helper import StringCaseConverter
from antistasi_logbook.backend import Backend, GidSqliteApswDatabase
from antistasi_logbook.storage.models.models import RemoteStorage, Server, LogRecord
from antistasi_logbook.gui.status_bar import LogbookStatusBar
from antistasi_logbook.gui.misc import UpdaterSignaler
import pp
import atexit
from weakref import WeakSet
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


class SignalCollectingThreadPool(ThreadPoolExecutor):

    def __init__(self, max_workers: int = None, thread_name_prefix: str = None, initializer: Callable = None, initargs: tuple[Any] = None) -> None:
        super().__init__(max_workers=max_workers, thread_name_prefix=thread_name_prefix, initializer=initializer, initargs=initargs)
        self.abort_signals: WeakSet[Event] = WeakSet()

    def add_abort_signal(self, signal: Event) -> None:
        self.abort_signals.add(signal)

    def shutdown(self, wait: bool = None, *, cancel_futures: bool = None) -> None:
        for abort_signal in self.abort_signals:
            abort_signal.set()
        return super().shutdown(wait=wait, cancel_futures=cancel_futures)


class AntistasiLogbookMainWindow(QMainWindow):
    update_started = Signal()
    update_finished = Signal()

    def __init__(self, app: QApplication, config: "GidIniConfig") -> None:
        self.app = app
        self.config = config
        self.backend: "Backend" = None
        self.main_widget: MainWidget = None
        self.menubar: QMenuBar = None
        self.statusbar: LogbookStatusBar = None
        self.thread_pool = SignalCollectingThreadPool(5, thread_name_prefix='gui_update')

        self.sys_tray: "LogbookSystemTray" = None
        self.name: str = None
        self.title: str = None

        super().__init__()
        self.setup()

    @property
    def initial_size(self) -> list[int, int]:
        return self.config.get("main_window", "initial_size", default=[1600, 1000])

    def setup(self) -> None:
        settings = QSettings(f"{META_INFO.app_name}_settings", "main_window")
        self.name = StringCaseConverter.convert_to(META_INFO.app_name, StringCaseConverter.TITLE)
        self.title = f"{self.name} {META_INFO.version}"
        self.setWindowTitle(self.title)

        self.set_menubar(LogbookMenuBar(self))
        self.setWindowIcon(self.app.icon)
        geometry = settings.value('geometry', QByteArray())
        if geometry.size():
            self.restoreGeometry(geometry)
        else:
            self.resize(*self.initial_size)
        self.set_main_widget(MainWidget(self))
        self.sys_tray = LogbookSystemTray(self, self.app)
        self.sys_tray.show()

        self.setup_backend()
        self.setup_statusbar()
        self.backend.updater.signaler.update_started.connect(self.statusbar.switch_labels)
        self.backend.updater.signaler.update_finished.connect(self.statusbar.switch_labels)

        self.backend.updater.signaler.update_info.connect(self.statusbar.start_progress_bar)
        self.backend.updater.signaler.update_increment.connect(self.statusbar.increment_progress_bar)
        self.main_widget.setup_views()
        self.backend.updater.signaler.update_finished.connect(self.main_widget.server_tab.model().refresh)
        self.backend.updater.signaler.update_finished.connect(self.main_widget.log_files_tab.model().refresh)

    def setup_backend(self) -> None:
        db_path = self.config.get('database', "database_path", default=None)
        database = GidSqliteApswDatabase(db_path, config=self.config)
        self.backend = Backend(database=database, config=self.config, update_signaler=UpdaterSignaler())
        self.backend.start_up()
        self.menubar.single_update_action.triggered.connect(self._single_update)
        self.menubar.reset_database_action.triggered.connect(self._reset_database)

    def setup_statusbar(self) -> None:
        self.statusbar = LogbookStatusBar(self)
        self.setStatusBar(self.statusbar)

    def set_menubar(self, menubar: QMenuBar) -> None:
        self.menubar = menubar
        self.setMenuBar(menubar)

    def set_main_widget(self, main_widget: QWidget) -> None:
        self.main_widget = main_widget
        self.setCentralWidget(main_widget)

    def _reset_database(self) -> None:
        reply = QMessageBox.warning(self, 'THIS IS IRREVERSIBLE', 'Are you sure you want to REMOVE the existing Database and REBUILD it?', QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.menubar.single_update_action.setEnabled(False)
            self.statusbar.last_updated_label.shutdown()
            self.backend.remove_and_reset_database()
            self.statusbar.last_updated_label.start_timer()
            self.menubar.single_update_action.setEnabled(True)

    def _single_update(self) -> None:
        def _run_update():
            self.menubar.single_update_action.setEnabled(False)
            self.update_started.emit()
            self.backend.updater()
            self.update_finished.emit()
            self.menubar.single_update_action.setEnabled(True)

        x = Thread(target=_run_update)
        x.start()

    def close(self) -> bool:
        log.debug("%r executing 'close'", self)
        return super().close()

    def event(self, event: QEvent) -> bool:
        # log.debug("received event %r", event.type().name)
        return super().event(event)

    def closeEvent(self, event: QCloseEvent):

        reply = QMessageBox.question(self, 'Message', 'Are you sure you want to quit?', QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.Yes:
            log.info("closing %r", self)
            self.thread_pool.shutdown(wait=True, cancel_futures=True)
            self.backend.shutdown()
            log.debug('%r accepting event %r', self, event.type().name)
            settings = QSettings(f"{META_INFO.app_name}_settings", "main_window")
            settings.setValue('geometry', self.saveGeometry())
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
    x = LogRecord.select().where(LogRecord.record_class_id == 5).count()
    print(x)
    m.show()
    _app.exec()


# endregion[Main_Exec]
