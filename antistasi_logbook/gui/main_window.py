"""
WiP.

Soon.
"""

# region [Imports]
import antistasi_logbook
antistasi_logbook.setup()
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
from antistasi_logbook.gui.raw_widgets.main_window import Ui_MainWindow
from gidapptools import get_logger, get_meta_config, get_meta_info, get_meta_paths
from PySide6 import QtCore
from PySide6 import QtWidgets

from antistasi_logbook.backend import Backend, GidSqliteApswDatabase
from antistasi_logbook.storage.models.models import database as database_proxy, RemoteStorage
from antistasi_logbook.gui.raw_widgets.version_dialog import Ui_VersionDialog
from PySide6.QtCore import QCoreApplication, QDate, QDateTime, QLocale, QMetaObject, QObject, QPoint, QRect, QSize, QTime, QUrl, Qt
from PySide6.QtGui import (QAction, QBrush, QColor, QConicalGradient, QCursor, QFont, QFontDatabase, QGradient, QIcon, QImage, QKeySequence,
                           QLinearGradient, QPainter, QPalette, QPixmap, QRadialGradient, QTransform)
from PySide6.QtWidgets import QApplication, QGridLayout, QMainWindow, QMenu, QMenuBar, QSizePolicy, QStatusBar, QWidget, QVBoxLayout, QLabel, QLineEdit
if TYPE_CHECKING:
    from gidapptools.gid_config.interface import GidIniConfig
    from gidapptools.meta_data.meta_info import MetaInfo
# endregion[Imports]

# region [TODO]


# endregion [TODO]

# region [Logging]


# endregion[Logging]

# region [Constants]

THIS_FILE_DIR = Path(__file__).parent.absolute()
log = get_logger(__name__)
CONFIG = get_meta_config().get_config("general")
META_INFO = get_meta_info()
# endregion[Constants]


class AppInfoDialog(QtWidgets.QDialog):

    def __init__(self) -> None:
        super().__init__()

        self.label_font = self.create_label_font()
        self.parts = []
        self.setupUi()

    def create_label_font(self) -> QFont:
        font = QFont()
        font.setPointSize(19)
        font.setBold(True)
        return font

    def create_new_part(self, label_text: str, data_text: str) -> None:
        label = QLabel(self)
        label.setText(label_text)
        label.setFont(self.label_font)
        label.setAlignment(Qt.AlignCenter)

        data = QLineEdit(self)
        data.setReadOnly(True)
        data.setText(data_text)
        data.setAlignment(Qt.AlignCenter)

        self.parts.append((label, data))

    def setupUi(self):
        self.resize(400, 100)
        self.setMaximumSize(QSize(400, 100))
        self.verticalLayout = QVBoxLayout(self)

        for label, data in self.parts:
            self.verticalLayout.addWidget(label)
            self.verticalLayout.addWidget(data)


class MenuBar(QMenuBar):

    def __init__(self, parent: Optional[QtWidgets.QWidget] = None) -> None:
        super().__init__(parent=parent)
        self.actions_map = defaultdict(dict)
        self.file_menu = self.add_new_menu("File")
        self.edit_menu = self.add_new_menu("Edit")
        self.view_menu = self.add_new_menu("View")
        self.settings_menu = self.add_new_menu("Settings")
        self.help_menu = self.add_new_menu("Help")

    def add_new_menu(self, menu_name: str, menu_title: str = None) -> QMenu:
        menu = QMenu(self)
        menu_title = menu_title or menu_name
        menu_name = menu_name.casefold()
        menu.setTitle(menu_title)
        self.addAction(menu.menuAction())
        return menu

    def add_new_action(self, menu: Union[str, QMenu], action_name: str, action_title: str = None):
        action_title = action_title or action_name
        action_name = action_name.casefold()
        if isinstance(menu, str):
            menu_name = menu.casefold()
            menu = getattr(self, f"{menu_name}_menu")
        else:
            menu_name = menu.title().casefold()
        action = QAction()

        action.setText(action_title)
        menu.addAction(action)
        self.actions_map[menu_name][action_name] = action


class MainWindow(Ui_MainWindow, QtWidgets.QMainWindow):

    def __init__(self, backend: "Backend", config: "GidIniConfig") -> None:
        super().__init__()
        super().setupUi(self)
        self.config = config

        self.backend = backend

        self.setup()

    def setup(self) -> None:
        self.menubar = MenuBar(self)

        self.setMenuBar(self.menubar)
        self.menubar.add_new_action(self.menubar.file_menu, "Exit")
        self.menubar.add_new_action(self.menubar.help_menu, "About")
        self.menubar.actions_map["file"]["exit"].triggered.connect(self.close)
        self.menubar.actions_map["help"]["about"].triggered.connect(self.show_about)
        self.start_update_button = QtWidgets.QPushButton(text="start updating")

        self.statusbar.addWidget(self.start_update_button)
        self.start_update_button.clicked.connect(self.backend.update_manager.start)

    def setup_menubar(self):
        self.menubar = MenuBar(self)

    def show_about(self) -> None:
        x = AppInfoDialog()

        x.exec()

    def closeEvent(self, event: QtCore.QEvent):
        self.backend.shutdown()
        log.info(event.type())
        event.accept()
# region[Main_Exec]


if __name__ == '__main__':
    import dotenv
    dotenv.load_dotenv(r"D:\Dropbox\hobby\Modding\Programs\Github\My_Repos\Antistasi_Logbook\antistasi_logbook\nextcloud.env")
    backend = Backend(database=GidSqliteApswDatabase(config=CONFIG), config=CONFIG, database_proxy=database_proxy)
    backend.start_up(overwrite=False)
    RemoteStorage.get(name="community_webdav").set_login_and_password(login=os.getenv("NEXTCLOUD_USERNAME"), password=os.getenv("NEXTCLOUD_PASSWORD"))
    y = QtWidgets.QApplication([])
    x = MainWindow(backend=backend, config=CONFIG)
    x.resize(800, 600)
    x.show()

    sys.exit(y.exec())
# endregion[Main_Exec]
