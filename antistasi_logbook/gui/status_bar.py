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
from dateutil.tz import UTC
import PySide6
from gidapptools import get_logger
from gidapptools.gid_signal.interface import get_signal
from gidapptools.general_helper.conversion import seconds2human
from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale, QMetaObject, QObject, QPoint, QRect, QSize, QTime, QUrl, Qt, Slot, Signal,
                            QAbstractTableModel, QAbstractItemModel, QAbstractListModel, QEvent)
from PySide6.QtGui import (QAction, QBrush, QColor, QConicalGradient, QCursor, QFont, QFontDatabase, QGradient, QIcon, QImage, QKeySequence,
                           QLinearGradient, QPainter, QPalette, QPixmap, QRadialGradient, QTransform, QCloseEvent)
from PySide6.QtWidgets import (QApplication, QGridLayout, QMainWindow, QMenu, QMenuBar, QSizePolicy, QStatusBar, QWidget, QPushButton,
                               QBoxLayout, QHBoxLayout, QVBoxLayout, QSizePolicy, QMessageBox, QLayout, QGroupBox, QDockWidget, QTabWidget, QSystemTrayIcon, QLabel, QProgressBar, QProgressDialog)

if TYPE_CHECKING:
    from antistasi_logbook.gui.main_window import AntistasiLogbookMainWindow, Backend
    from antistasi_logbook.storage.models.models import DatabaseMetaData
    from antistasi_logbook.updating.updater import Updater
# endregion[Imports]

# region [TODO]


# endregion [TODO]

# region [Logging]


# endregion[Logging]

# region [Constants]

THIS_FILE_DIR = Path(__file__).parent.absolute()
log = get_logger(__name__)
# endregion[Constants]


class LastUpdatedLabel(QLabel):
    min_unit_progression_table = {timedelta(seconds=0): "second",
                                  timedelta(minutes=5): "minute",
                                  timedelta(hours=5): "hour",
                                  timedelta(days=5): "day",
                                  timedelta(weeks=5): "week"}

    def __init__(self, status_bar: "LogbookStatusBar", parent=None) -> None:
        super().__init__(parent=parent)
        self.status_bar = status_bar
        self.timer_id: int = None
        self.refresh_interval: int = 1000 * 10
        self.min_unit = "second"
        self.last_triggered: datetime = None
        self.setup()

    def set_refresh_interval(self, new_interval: int) -> None:
        if new_interval == self.refresh_interval:
            return
        self.refresh_interval = new_interval
        self.start_timer()

    @property
    def last_update_finished_at(self) -> "datetime":
        return self.status_bar.backend.session_meta_data.get_absolute_last_update_finished_at()

    def setup(self) -> None:
        self.refresh_text()
        self.start_timer()

    def refresh_text(self) -> None:
        log.debug("refreshing %s text", self)
        if self.last_update_finished_at is None:
            text = "Never Updated"
        else:
            delta = self._time_since_last_update_finished()
            delta_text = seconds2human(round(delta.total_seconds(), -1), min_unit=[v for k, v in self.min_unit_progression_table.items() if k <= delta][-1])
            text = f"Last update finished {delta_text} ago"
        self.setText(text)
        self.update()

    def start_timer(self) -> None:
        if self.timer_id is not None:
            self.killTimer(self.timer_id)
        self.timer_id = self.startTimer(self.refresh_interval, Qt.VeryCoarseTimer)

    def _time_since_last_update_finished(self) -> timedelta:
        now = datetime.now(tz=UTC)
        return now - self.last_update_finished_at

    def timerEvent(self, event: PySide6.QtCore.QTimerEvent) -> None:
        if event.timerId() == self.timer_id:
            self.last_triggered = datetime.now(tz=UTC)
            self.refresh_text()

    def shutdown(self):
        if self.timer_id is not None:
            self.killTimer(self.timer_id)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(status_bar={self.status_bar!r})"

    def __str__(self) -> str:
        last_triggered = f"last_triggered={self.last_triggered.strftime('%Y-%m-%d %H:%M:%S UTC')!r}" if self.last_triggered is not None else f"last_triggered={self.last_triggered!r}"
        return f"{self.__class__.__name__}(interval={seconds2human(self.refresh_interval/1000)!r}, {last_triggered})"


class LogbookStatusBar(QStatusBar):

    def __init__(self, main_window: "AntistasiLogbookMainWindow") -> None:
        super().__init__(parent=main_window)
        self.main_window = main_window
        self.last_updated_label: LastUpdatedLabel = None
        self.update_running_label: QLabel = None
        self.update_progress: QProgressBar = None
        self.setup()

    @property
    def backend(self) -> "Backend":
        return self.main_window.backend

    def setup(self) -> None:
        self.setup_labels()
        self.update_progress = QProgressBar()
        self.insertWidget(2, self.update_progress, 2)
        self.update_progress.hide()

    def setup_labels(self) -> None:
        self.update_running_label = QLabel()
        self.update_running_label.setText("Updating...")
        self.update_running_label.hide()
        self.last_updated_label = LastUpdatedLabel(self)
        self.current_label = self.last_updated_label
        self.insertWidget(0, self.last_updated_label, 1)
        self.insertWidget(1, self.update_running_label, 1)

    def switch_labels(self, update_start: bool) -> None:
        if update_start is True:
            self.last_updated_label.hide()
            self.update_running_label.show()
            self.update_progress.show()
        else:
            self.update_running_label.hide()
            self.update_progress.hide()
            self.last_updated_label.show()

    @Slot(int, str)
    def start_progress_bar(self, max_amount: int, server_name: str):
        self.update_progress.reset()
        self.update_progress.setMaximum(max_amount)
        self.update_running_label.setText(f"Updating Server {server_name.title()}")

    def increment_progress_bar(self):
        self.update_progress.setValue(self.update_progress.value() + 1)


# region[Main_Exec]
if __name__ == '__main__':
    pass

# endregion[Main_Exec]
