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
from gidapptools.general_helper.string_helper import StringCaseConverter
from colorhash import ColorHash
from peewee import Query, Select
from antistasi_logbook.storage.models.models import Server, RemoteStorage, LogFile, RecordClass, LogRecord, AntstasiFunction, setup_db, DatabaseMetaData, GameMap, LogLevel
import PySide6
from PySide6 import QtCore, QtGui, QtWidgets
from antistasi_logbook.gui.models.base_query_data_model import BaseQueryDataModel
from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale, QMetaObject, QObject, QPoint, QRect, QSize, QTime, QUrl, Qt,
                            QAbstractTableModel, QAbstractItemModel, QAbstractListModel, QEvent, QModelIndex)
from PySide6.QtGui import (QAction, QBrush, QColor, QConicalGradient, QCursor, QFont, QFontDatabase, QGradient, QIcon, QImage, QKeySequence,
                           QLinearGradient, QPainter, QPalette, QPixmap, QRadialGradient, QTransform, QCloseEvent)
from PySide6.QtWidgets import (QApplication, QGridLayout, QMainWindow, QMenu, QMenuBar, QSizePolicy, QStatusBar, QWidget, QPushButton, QLabel, QProgressBar, QProgressDialog,
                               QBoxLayout, QHBoxLayout, QVBoxLayout, QSizePolicy, QMessageBox, QLayout, QGroupBox, QDockWidget, QTabWidget, QSystemTrayIcon, QTableView, QListView, QTreeView, QColumnView)
if TYPE_CHECKING:
    from antistasi_logbook.backend import Backend

    from antistasi_logbook.backend import Backend
    from antistasi_logbook.storage.models.models import BaseModel
    from antistasi_logbook.records.abstract_record import AbstractRecord
# endregion[Imports]

# region [TODO]


# endregion [TODO]

# region [Logging]


# endregion[Logging]

# region [Constants]

THIS_FILE_DIR = Path(__file__).parent.absolute()

# endregion[Constants]
SERVER_COLOR_ALPHA = 50
SERVER_COLORS = {"no_server": QColor(25, 25, 25, 100),
                 "mainserver_1": QColor(0, 255, 0, SERVER_COLOR_ALPHA),
                 "mainserver_2": QColor(250, 1, 217, SERVER_COLOR_ALPHA),
                 "testserver_1": QColor(0, 127, 255, SERVER_COLOR_ALPHA),
                 "testserver_2": QColor(235, 149, 0, SERVER_COLOR_ALPHA),
                 "testserver_3": QColor(255, 0, 0, SERVER_COLOR_ALPHA),
                 "eventserver": QColor(62, 123, 79, SERVER_COLOR_ALPHA)}


class ServerModel(BaseQueryDataModel):
    strict_exclude_columns: set[str] = {'id', 'remote_storage', "comments"}

    def __init__(self, backend: "Backend", parent: Optional[QtCore.QObject] = None, show_local_files_server: bool = False) -> None:
        self.show_local_files_server = show_local_files_server
        super().__init__(backend, db_model=Server, parent=parent)
        self.ordered_by = (-Server.update_enabled, Server.name, Server.id)

    @property
    def column_names_to_exclude(self) -> set[str]:
        return self._column_names_to_exclude.union({'remote_storage'})

    @property
    def column_ordering(self) -> dict[str, int]:
        return self._column_ordering

    def get_query(self) -> "Query":
        query = Server.select().join(RemoteStorage).switch(Server)
        if self.show_local_files_server is False:
            query = query.where(Server.remote_path != None)
        return query.order_by(*self.ordered_by)

    def get_content(self) -> "BaseQueryDataModel":
        self.content_items = list(self.get_query().execute())
        return self

    def get_columns(self) -> "BaseQueryDataModel":
        columns = [field for field_name, field in Server._meta.fields.items() if field_name not in self.column_names_to_exclude]
        self.columns = sorted(columns, key=lambda x: self.column_ordering.get(x.name.casefold(), 99))
        return self


# region[Main_Exec]


if __name__ == '__main__':
    pass

# endregion[Main_Exec]
