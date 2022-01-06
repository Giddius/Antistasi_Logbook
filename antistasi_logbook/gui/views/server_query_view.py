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
from PySide6 import (QtCore, QtGui, QtWidgets, Qt3DAnimation, Qt3DCore, Qt3DExtras, Qt3DInput, Qt3DLogic, Qt3DRender, QtAxContainer, QtBluetooth,
                     QtCharts, QtConcurrent, QtDataVisualization, QtDesigner, QtHelp, QtMultimedia, QtMultimediaWidgets, QtNetwork, QtNetworkAuth,
                     QtOpenGL, QtOpenGLWidgets, QtPositioning, QtPrintSupport, QtQml, QtQuick, QtQuickControls2, QtQuickWidgets, QtRemoteObjects,
                     QtScxml, QtSensors, QtSerialPort, QtSql, QtStateMachine, QtSvg, QtSvgWidgets, QtTest, QtUiTools, QtWebChannel, QtWebEngineCore,
                     QtWebEngineQuick, QtWebEngineWidgets, QtWebSockets, QtXml)

from PySide6.QtCore import (QByteArray, QCoreApplication, QDate, QDateTime, QEvent, QLocale, QMetaObject, QModelIndex, QModelRoleData, QMutex,
                            QMutexLocker, QObject, QPoint, QRect, QRecursiveMutex, QRunnable, QSettings, QSize, QThread, QThreadPool, QTime, QUrl,
                            QWaitCondition, Qt, QAbstractItemModel, QAbstractListModel, QAbstractTableModel, Signal, Slot)

from PySide6.QtGui import (QAction, QBrush, QColor, QConicalGradient, QCursor, QFont, QFontDatabase, QFontMetrics, QGradient, QIcon, QImage,
                           QKeySequence, QLinearGradient, QPainter, QPalette, QPixmap, QRadialGradient, QTransform)

from PySide6.QtWidgets import (QApplication, QBoxLayout, QCheckBox, QColorDialog, QColumnView, QComboBox, QDateTimeEdit, QDialogButtonBox,
                               QDockWidget, QDoubleSpinBox, QFontComboBox, QFormLayout, QFrame, QGridLayout, QGroupBox, QHBoxLayout, QHeaderView,
                               QLCDNumber, QLabel, QLayout, QLineEdit, QListView, QListWidget, QMainWindow, QMenu, QMenuBar, QMessageBox,
                               QProgressBar, QProgressDialog, QPushButton, QSizePolicy, QSpacerItem, QSpinBox, QStackedLayout, QStackedWidget,
                               QStatusBar, QStyledItemDelegate, QSystemTrayIcon, QTabWidget, QTableView, QTextEdit, QTimeEdit, QToolBox, QTreeView,
                               QVBoxLayout, QWidget, QAbstractItemDelegate, QAbstractItemView, QAbstractScrollArea, QRadioButton, QFileDialog, QButtonGroup)

from peewee import Field
from antistasi_logbook.gui.widgets.markdown_editor import MarkdownEditorDialog
from antistasi_logbook.storage.models.models import Server
from antistasi_logbook.gui.resources.antistasi_logbook_resources_accessor import AllResourceItems
from gidapptools import get_logger
from antistasi_logbook.gui.views.base_query_tree_view import BaseQueryTreeView
from antistasi_logbook.gui.misc import CustomRole
if TYPE_CHECKING:
    from antistasi_logbook.gui.main_window import AntistasiLogbookMainWindow
    from antistasi_logbook.gui.application import AntistasiLogbookApplication

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


class ServerContextMenuAction(QAction):
    clicked = Signal(object, object, QModelIndex)

    def __init__(self, item: Server, column: Field, index: QModelIndex, icon: QIcon = None, text: str = None, parent=None):
        super().__init__(**{k: v for k, v in dict(icon=icon, text=text, parent=parent).items() if v is not None})
        self.item = item
        self.column = column
        self.index = index
        self.triggered.connect(self.on_triggered)

    @Slot()
    def on_triggered(self):
        self.clicked.emit(self.item, self.column, self.index)


class ServerQueryTreeView(BaseQueryTreeView):
    enable_icon = AllResourceItems.check_mark_black_image.get_as_icon()
    disable_icon = AllResourceItems.close_cancel_image.get_as_icon()

    initially_hidden_columns: set[str] = {"id", "comments"}

    def __init__(self) -> None:
        super().__init__(name="Server")
        self.all_actions: set[QAction] = set()
        self.mark_icon = AllResourceItems.mark_image.get_as_icon()
        self.unmark_icon = AllResourceItems.unmark_image.get_as_icon()
        self._temp_set_comment_dialog: MarkdownEditorDialog = None

    def extra_setup(self):
        super().extra_setup()

    def setup_context_menu(self, item: Server, column: Field, index: QModelIndex) -> QMenu:
        menu = QMenu(self)
        update_action = None
        if item.update_enabled is True:
            update_action = ServerContextMenuAction(item, column, index, self.disable_icon, f"DISABLE Update for {item.pretty_name!r}", self)
        elif item.update_enabled is False and item.name.casefold() not in {"eventserver", "no_server"}:
            update_action = ServerContextMenuAction(item, column, index, self.enable_icon, f"ENABLE Update for {item.pretty_name!r}", self)
        else:
            _forbidden_action = QAction(AllResourceItems.forbidden_image.get_as_icon(), f"Not possible for Server {item.pretty_name}", self)
            _forbidden_action.setEnabled(False)
            menu.addAction(_forbidden_action)
        if update_action is not None:
            update_action.clicked.connect(self.change_updates_enabled_option)
            menu.addAction(update_action)

        if item.marked is True:
            marked_action = ServerContextMenuAction(item, column, index, self.unmark_icon, f"Remove Mark from {item.pretty_name!r}", self)
        elif item.marked is False:
            marked_action = ServerContextMenuAction(item, column, index, self.mark_icon, f"Mark {item.pretty_name!r}", self)

        marked_action.clicked.connect(self.change_marked_option)
        menu.addAction(marked_action)
        set_comment_action = ServerContextMenuAction(item, column, index, text="Set Comment", parent=self)
        set_comment_action.clicked.connect(self.open_comment_dialog)
        menu.addAction(set_comment_action)
        return menu

    def contextMenuEvent(self, event: PySide6.QtGui.QContextMenuEvent) -> None:
        index = self.indexAt(event.pos())
        if index.isValid() is False or index.row() == -1 or index.column() == -1:
            event.ignore()
            return

        item = self.model.content_items[index.row()]
        column = self.model.columns[index.column()]

        menu = self.setup_context_menu(item, column, index)
        menu.exec(event.globalPos())

    @Slot(object, object, QModelIndex)
    def open_comment_dialog(self, item: Server, column: Field, index: QModelIndex):
        def _update_comment(text: str):
            self.model.setData(self.model.index(index.row(), self.model.get_column_index("comments"), QModelIndex()), text, Qt.DisplayRole)
        self._temp_set_comment_dialog = MarkdownEditorDialog(text=item.comments, parent=self)
        self._temp_set_comment_dialog.dialog_accepted.connect(_update_comment)
        self._temp_set_comment_dialog.show()

    @Slot(object, object, QModelIndex)
    def change_updates_enabled_option(self, item: Server, column: Field, index: QModelIndex):
        self.model.setData(index, not item.update_enabled, CustomRole.UPDATE_ENABLED_ROLE)

    @Slot(object, object, QModelIndex)
    def change_marked_option(self, item: Server, column: Field, index: QModelIndex):
        self.model.setData(index, not item.marked, CustomRole.MARKED_ROLE)
        # region[Main_Exec]


if __name__ == '__main__':
    pass

# endregion[Main_Exec]
