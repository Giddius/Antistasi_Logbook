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
from PySide6 import QtCore, QtGui, QtWidgets
from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale, QMetaObject, QObject, QPoint, QRect, QSize, QTime, QUrl, Qt, QModelRoleData,
                            QAbstractTableModel, QAbstractItemModel, QAbstractListModel, QEvent, QModelIndex, Signal, Slot)
from PySide6.QtGui import (QAction, QBrush, QColor, QConicalGradient, QCursor, QFont, QFontDatabase, QGradient, QIcon, QImage, QKeySequence,
                           QLinearGradient, QPainter, QPalette, QPixmap, QRadialGradient, QTransform, QCloseEvent)
from PySide6.QtWidgets import (QApplication, QGridLayout, QMainWindow, QMenu, QMenuBar, QSizePolicy, QStatusBar, QWidget, QPushButton, QFrame, QFormLayout, QLabel, QProgressBar, QProgressDialog,
                               QBoxLayout, QHBoxLayout, QVBoxLayout, QSizePolicy, QMessageBox, QLayout, QGroupBox, QDockWidget, QTabWidget, QSystemTrayIcon, QTableView, QListView, QTreeView, QColumnView)
# endregion[Imports]

# region [TODO]


# endregion [TODO]

# region [Logging]


# endregion[Logging]

# region [Constants]

THIS_FILE_DIR = Path(__file__).parent.absolute()

# endregion[Constants]


class UpdaterSignaler(QObject):
    update_started = Signal(bool)
    update_finished = Signal(bool)
    update_info = Signal(int, str)
    update_increment = Signal()

    def send_update_increment(self):
        self.update_increment.emit()

    def send_update_started(self):
        self.update_started.emit(True)

    def send_update_finished(self):
        self.update_finished.emit(False)

    def send_update_info(self, amount, name):
        self.update_info.emit(amount, name)


# region[Main_Exec]

if __name__ == '__main__':
    pass

# endregion[Main_Exec]
