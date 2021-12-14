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
from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale, QMetaObject, QObject, QPoint, QRect, QSize, QThread, QTime, QUrl, Qt, QRunnable, QThreadPool, Slot, Signal,
                            QAbstractTableModel, QAbstractItemModel, QAbstractListModel, QEvent, QModelIndex)
from PySide6.QtGui import (QAction, QBrush, QFontMetrics, QColor, QConicalGradient, QCursor, QFont, QFontDatabase, QGradient, QIcon, QImage, QKeySequence,
                           QLinearGradient, QPainter, QPalette, QPixmap, QRadialGradient, QTransform, QCloseEvent)
from PySide6.QtWidgets import (QApplication, QGridLayout, QMainWindow, QMenu, QMenuBar, QSizePolicy, QStatusBar, QWidget, QPushButton, QLabel, QProgressBar, QProgressDialog,
                               QBoxLayout, QHBoxLayout, QVBoxLayout, QSizePolicy, QMessageBox, QLayout, QGroupBox, QStyledItemDelegate, QAbstractItemDelegate, QDockWidget, QTabWidget, QSystemTrayIcon, QTableView, QListView, QTreeView, QColumnView)
from antistasi_logbook.records.antistasi_records import PerformanceRecord
from gidapptools import get_logger
from threading import Event, Condition, Lock
import pp
from playhouse.shortcuts import model_to_dict
from gidapptools.general_helper.color.color_item import Color
if TYPE_CHECKING:
    from antistasi_logbook.backend import Backend
    from antistasi_logbook.gui.views.log_records_query_table_view import LogRecordsQueryTreeView
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
from gidapptools.general_helper.timing import get_dummy_profile_decorator_in_globals
get_dummy_profile_decorator_in_globals()
THIS_FILE_DIR = Path(__file__).parent.absolute()
log = get_logger(__name__)
# endregion[Constants]


class WorkerThread(QThread):
    def __init__(self, func: Callable, parent=None, **kwargs):
        QThread.__init__(self, parent)
        self.func = func
        self.kwargs = kwargs

    def run(self):
        self.func(**self.kwargs)


RefreshItem = namedtuple("RefreshItem", ["idx", "item"])


class LogRecordsModel(BaseQueryDataModel):
    added_first_row = Signal()
    added_multiline_item = Signal(int)
    request_resize_to_contents = Signal(list)
    bool_images = {True: None,
                   False: None}

    def __init__(self, backend: "Backend", parent=None) -> None:
        super().__init__(backend, LogRecord, parent=parent)
        self.filter = []
        self.ordered_by = (LogRecord.start, LogRecord.recorded_at)
        self.generator_refresh_chunk_size = 100
        self.message_column_font = self._make_message_column_font()

    @property
    def resize_lock(self) -> Lock:
        return self.parent().resize_lock

    def _make_message_column_font(self) -> QFont:
        font = QFont()
        font.setFamily("Cascadia Mono")
        return font

    @property
    def column_names_to_exclude(self) -> set[str]:
        return self._column_names_to_exclude.union({"log_file", "record_class", "logged_from", "called_by"})

    def get_query(self) -> "Query":
        # logged_from_alias = AntstasiFunction.alias()
        # query = LogRecord.select().join(LogFile, on=LogRecord.log_file).switch(LogRecord).join(LogLevel, on=LogRecord.log_level).switch(
        #     LogRecord).join(RecordClass, on=LogRecord.record_class).switch(LogRecord).join(AntstasiFunction, on=LogRecord.called_by, join_type=JOIN.LEFT_OUTER).switch(
        #     LogRecord).join(logged_from_alias, on=LogRecord.logged_from, join_type=JOIN.LEFT_OUTER).switch(LogRecord).where(reduce(or_, self.filter)).order_by(*self.ordered_by)
        query = LogRecord.select().where(reduce(or_, self.filter)).order_by(*self.ordered_by)
        return query

    def _get_display_data(self, index: "INDEX_TYPE") -> Any:
        item = self.content_items[index.row()]
        column = self.columns[index.column()]
        if column.name == "message":
            return item.pretty_message
        data = getattr(item, column.name)
        if data is None:
            return self.on_display_data_none(role=Qt.DisplayRole, item=item, column=column)
        if isinstance(data, bool):
            return self.on_display_data_bool(role=Qt.DisplayRole, item=item, column=column, value=data)
        return str(data)

    def _get_background_data(self, index: "INDEX_TYPE") -> Any:
        item = self.content_items[index.row()]
        column = self.columns[index.column()]
        if item.log_level is None:
            log.critical("log_level is None for %r", item)
        elif item.log_level.name == "ERROR":
            return Color(225, 25, 23, 0.5, "error_red").qcolor

        return item.color

    def _make_size(self, item: Union["AbstractRecord", "LogRecord"]) -> Union["AbstractRecord", "LogRecord"]:
        message = item.pretty_message.strip()
        metrics = QFontMetrics(self.message_column_font)
        b_rect = metrics.boundingRect(message)
        width = b_rect.width()
        height = 0
        for line in message.splitlines():
            height += metrics.boundingRect(line).height()
        item.message_size_hint = QSize(width, height)
        return item

    def _get_size_hint_data(self, index: "INDEX_TYPE") -> Any:
        item = self.content_items[index.row()]
        column = self.columns[index.column()]
        if column.name == "message":
            # if item.message_size_hint is None:

            #     message = item.pretty_message.strip()
            #     metrics = QFontMetrics(self.message_column_font)
            #     b_rect = metrics.boundingRect(message)
            #     width = b_rect.width()
            #     height = 0
            #     for line in message.splitlines():
            #         height += metrics.boundingRect(line).height()
            #     item.message_size_hint = QSize(width, height)

            return item.message_size_hint

    def _get_font_data(self, index: "INDEX_TYPE") -> Any:
        column = self.columns[index.column()]
        if column.name == "message":
            return self.message_column_font

    def get_content(self) -> "BaseQueryDataModel":
        self.content_items = [i.to_record_class() for i in self.get_query()]
        return self

    def get_columns(self) -> "BaseQueryDataModel":
        columns = [field for field_name, field in LogRecord._meta.fields.items() if field_name not in self.column_names_to_exclude]
        self.columns = tuple(sorted(columns, key=lambda x: self.column_ordering.get(x.name.casefold(), 99)))
        return self

    # def refresh(self, abort_signal: Event = None) -> "LogRecordsModel":
    #     self.get_columns()

    #     items = []

    #     if self.content_items is None:
    #         self.content_items = []
    #     else:
    #         self.content_items.clear()
    #     self.modelReset.emit()
    #     idx = 0
    #     for item in self.get_query().execute():
    #         idx += 1
    #         record_item = item.to_record_class()

    #         items.append(RefreshItem(idx, record_item))
    #         if len(items) == self.generator_refresh_chunk_size:
    #             request_idxs = []
    #             self.beginInsertRows(QtCore.QModelIndex(), min(i.idx for i in items), max(i.idx for i in items))
    #             for i in items:
    #                 _item = i.item
    #                 if _item.___has_multiline_message___ is True:
    #                     request_idxs.append(i.idx)
    #                 self.content_items.append(self._make_size(_item))
    #             self.endInsertRows()
    #             if 5 in {i.idx for i in items}:
    #                 self.parent().resizeColumnsToContents()
    #             self.request_resize_to_contents.emit(request_idxs)

    #             items.clear()

    #     if len(items) != 0:
    #         self.beginInsertRows(QtCore.QModelIndex(), min(i.idx for i in items), max(i.idx for i in items))
    #         for i in items:
    #             _item = i.item
    #             if _item.___has_multiline_message___ is True:
    #                 request_idxs.append(i.idx)
    #             self.content_items.append(self._make_size(_item))
    #         self.endInsertRows()
    #         self.request_resize_to_contents.emit(request_idxs)
    #     return self, abort_signal
    @profile
    def _generator_refresh(self, abort_signal: Event = None) -> "LogRecordsModel":
        def to_pri(**kwargs):
            pp(dict(kwargs))
        self.layoutAboutToBeChanged.emit()
        self.get_columns()

        items = []

        if self.content_items is None:
            self.content_items = []
        else:
            self.content_items.clear()
        self.layoutChanged.emit()
        idx = 0
        with self.backend.database:
            for item_data in self.get_query().dicts():

                idx += 1
                record_class = self.backend.record_class_manager.get_by_id(item_data.get('record_class'))
                record_item = record_class.from_model_dict(item_data)
                items.append(RefreshItem(idx, record_item))
                if len(items) == self.generator_refresh_chunk_size:
                    self.beginInsertRows(QtCore.QModelIndex(), min(i.idx for i in items), max(i.idx for i in items))

                    self.content_items += [i.item for i in items]

                    self.endInsertRows()

                    items.clear()

                sleep(0.0)

        if len(items) != 0:
            self.beginInsertRows(QtCore.QModelIndex(), min(i.idx for i in items), max(i.idx for i in items))

            self.content_items += [i.item for i in items]
            self.endInsertRows()
            items.clear()
        self.parent().resizeColumnToContents([i for i, col in enumerate(self.columns) if col.name == "message"][0])

        return self, abort_signal

    def generator_refresh(self, abort_signal: Event = None) -> tuple["BaseQueryDataModel", Event]:
        return self._generator_refresh(abort_signal=abort_signal)


# region[Main_Exec]
if __name__ == '__main__':
    pass

# endregion[Main_Exec]
