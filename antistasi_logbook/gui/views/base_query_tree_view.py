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
from gidapptools import get_logger
import PySide6
from PySide6 import QtCore, QtGui, QtWidgets
from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale, QMetaObject, QObject, QPoint, QRect, QSize, QTime, QUrl, Qt, QModelRoleData,
                            QAbstractTableModel, QAbstractItemModel, QAbstractListModel, QEvent, QModelIndex, Signal, Slot)
from PySide6.QtGui import (QAction, QBrush, QColor, QConicalGradient, QCursor, QFont, QFontDatabase, QGradient, QIcon, QImage, QKeySequence,
                           QLinearGradient, QPainter, QPalette, QPixmap, QRadialGradient, QTransform, QCloseEvent)
from PySide6.QtWidgets import (QApplication, QGridLayout, QMainWindow, QMenu, QMenuBar, QSizePolicy, QStatusBar, QWidget, QPushButton, QFrame, QFormLayout, QHeaderView, QLabel, QProgressBar, QProgressDialog,
                               QBoxLayout, QHBoxLayout, QVBoxLayout, QSizePolicy, QMessageBox, QLayout, QAbstractScrollArea, QGroupBox, QDockWidget, QTabWidget, QSystemTrayIcon, QTableView, QListView, QTreeView, QColumnView)
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


class BaseQueryTreeView(QTreeView):

    def __init__(self, icon: QIcon = None, name: str = None) -> None:
        self.icon = AllResourceItems.placeholder.get_as_icon() if icon is None else icon
        self.name = "" if name is None else name
        super().__init__()

    @property
    def header_view(self) -> QHeaderView:
        return self.header()

    def setup(self) -> "BaseQueryTreeView":
        self.header_view.setStretchLastSection(False)
        self.header_view.setSizeAdjustPolicy(QAbstractScrollArea.SizeAdjustPolicy.AdjustToContents)
        self.header_view.setSectionResizeMode(QHeaderView.ResizeToContents)
        # self.header_view.setCascadingSectionResizes(F)
        self.setSortingEnabled(True)
        self.setTextElideMode(Qt.ElideNone)
        self.setWordWrap(False)
        self.setAlternatingRowColors(True)
        self.setSizeAdjustPolicy(QAbstractScrollArea.SizeAdjustPolicy.AdjustToContents)

        return self

    def adjustSize(self) -> None:
        self.header_view.setStretchLastSection(False)
        self.header_view.setSizeAdjustPolicy(QAbstractScrollArea.SizeAdjustPolicy.AdjustToContents)
        self.header_view.setSectionResizeMode(QHeaderView.ResizeToContents)

        self.header_view.adjustSize()
        self.header_view.resizeSections()
        self.header_view.setSectionResizeMode(QHeaderView.Interactive)
        super().adjustSize()

    def setModel(self, model: PySide6.QtCore.QAbstractItemModel) -> None:
        super().setModel(model)

    def reset(self) -> None:
        log.debug("reseting %s", self)
        return super().reset()

    def event(self, event: QtCore.QEvent) -> bool:
        # log.debug("%s received event %r", self, event.type().name)
        return super().event(event)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name={self.name!r}, icon={self.icon}, model={self.model()!r})"

    def __str__(self) -> str:
        return f"{self.__class__.__name__}(name={self.name!r})"


class ServerQueryTreeView(BaseQueryTreeView):

    def __init__(self) -> None:
        super().__init__(icon=AllResourceItems.server_query_icon.get_as_icon(), name="Server")


class LogFilesQueryTreeView(BaseQueryTreeView):
    def __init__(self) -> None:
        super().__init__(icon=AllResourceItems.log_files_query_icon.get_as_icon(), name="Log-Files")


# region[Main_Exec]

if __name__ == '__main__':
    pass

# endregion[Main_Exec]
