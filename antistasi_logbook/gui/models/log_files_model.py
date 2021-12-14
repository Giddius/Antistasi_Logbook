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
from gidapptools.general_helper.conversion import bytes2human
from antistasi_logbook.storage.models.models import Server, RemoteStorage, LogFile, RecordClass, LogRecord, AntstasiFunction, setup_db, DatabaseMetaData, GameMap, LogLevel
import PySide6
from peewee import Query, Select, Field
from PySide6 import QtCore, QtGui, QtWidgets
from colorhash import ColorHash
from antistasi_logbook.gui.models.base_query_data_model import BaseQueryDataModel
from gidapptools.general_helper.string_helper import StringCaseConverter
from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale, QMetaObject, QObject, QPoint, QRect, QSize, QTime, QUrl, Qt,
                            QAbstractTableModel, QAbstractItemModel, QAbstractListModel, QEvent, QModelIndex)
from PySide6.QtGui import (QAction, QBrush, QColor, QConicalGradient, QCursor, QFont, QFontDatabase, QGradient, QIcon, QImage, QKeySequence,
                           QLinearGradient, QPainter, QPalette, QPixmap, QRadialGradient, QTransform, QCloseEvent)
from PySide6.QtWidgets import (QApplication, QGridLayout, QMainWindow, QMenu, QMenuBar, QSizePolicy, QStatusBar, QWidget, QPushButton, QLabel, QProgressBar, QProgressDialog,
                               QBoxLayout, QHBoxLayout, QVBoxLayout, QSizePolicy, QMessageBox, QLayout, QGroupBox, QStyledItemDelegate, QAbstractItemDelegate, QDockWidget, QTabWidget, QSystemTrayIcon, QTableView, QListView, QTreeView, QColumnView)
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
log = get_logger(__name__)
# endregion[Constants]


class FakeField:

    def __init__(self, name: str, verbose_name: str) -> None:
        self.name = name
        self.verbose_name = verbose_name
        self.help_text = None


class LogFilesModel(BaseQueryDataModel):

    def __init__(self, backend: "Backend", parent: Optional[QtCore.QObject] = None, show_unparsable: bool = False) -> None:
        self.show_unparsable = show_unparsable
        super().__init__(backend, LogFile, parent=parent)
        self.ordered_by = (-LogFile.modified_at, LogFile.server)

    @property
    def column_names_to_exclude(self) -> set[str]:
        _out = self._column_names_to_exclude.union({'header_text', 'startup_text', 'utc_offset', 'last_parsed_datetime', 'last_parsed_line_number'})
        if self.show_unparsable is False:
            _out.add("unparsable")
        return _out

    @property
    def column_ordering(self) -> dict[str, int]:
        return self._column_ordering | {"server": 2, "remote_path": 100}

    def on_display_data_bool(self, role: int, item: "BaseModel", column: "Field", value: bool) -> str:
        if role == Qt.DisplayRole:
            if column.name in {"is_new_campaign"}:
                return ''

            return super().on_display_data_bool(role=role, item=item, column=column, value=value)
        if role == Qt.DecorationRole:
            if column.name in {"is_new_campaign"}:
                return self.bool_images[True] if value is True else None

            return super().on_display_data_bool(role=role, item=item, column=column, value=value)

    def get_query(self) -> "Query":
        query = LogFile.select().join(GameMap).switch(LogFile).join(Server).switch(LogFile)
        if self.show_unparsable is False:
            query = query.where(LogFile.unparsable != True)
        return query.order_by(*self.ordered_by)

    def get_content(self) -> "BaseQueryDataModel":

        self.content_items = list(self.get_query().execute())

        return self

    def get_columns(self) -> "BaseQueryDataModel":
        columns = [field for field_name, field in LogFile._meta.fields.items() if field_name not in self.column_names_to_exclude]
        columns.append(FakeField(name="amount_log_records", verbose_name="Amount Log Records"))
        self.columns = tuple(sorted(columns, key=lambda x: self.column_ordering.get(x.name.casefold(), 99)))
        return self
# region[Main_Exec]


if __name__ == '__main__':
    pass

# endregion[Main_Exec]
