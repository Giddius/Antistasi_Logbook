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
from functools import wraps, partial, lru_cache, singledispatch, total_ordering, cached_property, reduce
from operator import or_
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
from peewee import Query, Select, Field, JOIN
from PySide6 import QtCore, QtGui, QtWidgets
from colorhash import ColorHash
from antistasi_logbook.gui.models.base_query_data_model import BaseQueryDataModel
from gidapptools.general_helper.string_helper import StringCaseConverter
from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale, QMetaObject, QObject, QPoint, QRect, QSize, QTime, QUrl, Qt, QRunnable, QThreadPool, Slot,
                            QAbstractTableModel, QAbstractItemModel, QAbstractListModel, QEvent, QModelIndex)
from PySide6.QtGui import (QAction, QBrush, QColor, QConicalGradient, QCursor, QFont, QFontDatabase, QGradient, QIcon, QImage, QKeySequence,
                           QLinearGradient, QPainter, QPalette, QPixmap, QRadialGradient, QTransform, QCloseEvent)
from PySide6.QtWidgets import (QApplication, QGridLayout, QMainWindow, QMenu, QMenuBar, QSizePolicy, QStatusBar, QWidget, QPushButton, QLabel, QProgressBar, QProgressDialog,
                               QBoxLayout, QHBoxLayout, QVBoxLayout, QSizePolicy, QMessageBox, QLayout, QGroupBox, QStyledItemDelegate, QAbstractItemDelegate, QDockWidget, QTabWidget, QSystemTrayIcon, QTableView, QListView, QTreeView, QColumnView)
from antistasi_logbook.records.antistasi_records import PerformanceRecord
from gidapptools import get_logger
import pp
if TYPE_CHECKING:
    from antistasi_logbook.backend import Backend

    from antistasi_logbook.backend import Backend
    from antistasi_logbook.storage.models.models import BaseModel
    from antistasi_logbook.records.abstract_record import AbstractRecord
    from antistasi_logbook.gui.models.base_query_data_model import INDEX_TYPE
# endregion[Imports]

# region [TODO]


# endregion [TODO]

# region [Logging]


# endregion[Logging]

# region [Constants]

THIS_FILE_DIR = Path(__file__).parent.absolute()
log = get_logger(__name__)
# endregion[Constants]


class LogRecordsModel(BaseQueryDataModel):

    bool_images = {True: None,
                   False: None}

    def __init__(self, backend: "Backend") -> None:
        super().__init__(backend, LogRecord)
        self.filter = []
        self.ordered_by = LogRecord.recorded_at

    @property
    def column_names_to_exclude(self) -> set[str]:
        return self._column_names_to_exclude.union({"log_file"})

    def get_query(self) -> "Query":
        query = LogRecord.select()
        for _join_model in [LogFile, LogLevel, RecordClass]:
            query = query.join(_join_model).switch(LogRecord)
        logged_from_alias = AntstasiFunction.alias()
        query = query.join(AntstasiFunction, on=LogRecord.called_by, join_type=JOIN.LEFT_OUTER).switch(LogRecord).join(logged_from_alias, on=LogRecord.logged_from, join_type=JOIN.LEFT_OUTER)
        query = query.where(reduce(or_, self.filter))
        return query.order_by(self.ordered_by)

    def _get_display_data(self, index: "INDEX_TYPE") -> Any:
        item = self.content_items[index.row()]
        column = self.columns[index.column()]
        if column.name == "message":
            return item.pretty_message
        data = item.get_data(column.name)
        if data is None:
            return self.on_display_data_none(role=Qt.DisplayRole, item=item, column=column)
        if isinstance(data, bool):
            return self.on_display_data_bool(role=Qt.DisplayRole, item=item, column=column, value=data)
        return str(data)

    def get_content(self) -> "BaseQueryDataModel":
        self.content_items = [i.to_record_class() for i in self.get_query()]
        return self

    def get_columns(self) -> "BaseQueryDataModel":
        columns = [field for field_name, field in LogRecord._meta.fields.items() if field_name not in self.column_names_to_exclude]
        self.columns = tuple(sorted(columns, key=lambda x: self.column_ordering.get(x.name.casefold(), 99)))
        return self

    def refresh(self) -> None:
        self.layoutAboutToBeChanged.emit()
        self.get_columns()
        if self.content_items is None:
            self.content_items = []
        else:
            self.content_items.clear()
        self.layoutChanged.emit()

        self.layoutAboutToBeChanged.emit()

        for idx, item in enumerate(self.get_query().execute()):
            record_item = item.to_record_class()

            self.content_items.append(record_item)
            if idx % 250 == 0:
                self.layoutChanged.emit()

        self.modelReset.emit()

    def generator_refresh(self):
        return self.refresh()


# region[Main_Exec]
if __name__ == '__main__':
    pass

# endregion[Main_Exec]
