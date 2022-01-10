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

from gidapptools import get_logger
from gidapptools.general_helper.string_helper import StringCaseConverter, StringCase
from gidapptools.general_helper.enums import MiscEnum
import attr
import pp
from antistasi_logbook.gui.widgets.data_view_widget.type_fields import TypeFieldProtocol, TYPE_FIELD_TABLE
if TYPE_CHECKING:

    # * Third Party Imports --------------------------------------------------------------------------------->
    from antistasi_logbook.records.abstract_record import AbstractRecord
    from antistasi_logbook.records.base_record import BaseRecord
    from antistasi_logbook.gui.application import AntistasiLogbookApplication
    from antistasi_logbook.backend import Backend
    from gidapptools.gid_config.interface import GidIniConfig
# endregion[Imports]

# region [TODO]


# endregion [TODO]

# region [Logging]


# endregion[Logging]

# region [Constants]

THIS_FILE_DIR = Path(__file__).parent.absolute()
log = get_logger(__name__)
# endregion[Constants]


class DataRow:
    def __init__(self, name: str, value: Any, type_widget: type["TypeFieldProtocol"] = MiscEnum.NOTHING, position: int = None) -> None:
        self.name = name
        self.value = value
        self.type_widget = type_widget
        self.position = position
        self._value_widget: QWidget = MiscEnum.NOTHING
        self._label: QLabel = None

    @property
    def label(self) -> str:
        if self._label is None:

            self._label = QLabel('<b>' + StringCaseConverter.convert_to(self.name, StringCase.TITLE) + ':' + '</b>')
        return self._label

    @property
    def value_widget(self) -> Optional[QWidget]:
        if self.type_widget is None or self.type_widget is MiscEnum.NOTHING:
            return
        if self._value_widget is MiscEnum.NOTHING:
            self._value_widget = self.type_widget()
            self._value_widget.set_value(self.value)
        return self._value_widget

    def get_sort_key(self) -> int:
        if self.position in {None, MiscEnum.NOTHING}:
            return 9999999
        return self.position


def wrap_in_tag(text: str, tag: str) -> str:
    return f"<{tag}>{text}</{tag}>"


class TitleLabel(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setAlignment(Qt.AlignCenter)
        self.setProperty("is_title_label", True)
        self.setup()

    def setup(self):
        self._modify_font()

    def _modify_font_point_size(self, old_size: int) -> int:
        return int(old_size * 1.5)

    def _modify_font(self):
        font: QFont = self.font()
        font.setPointSize(self._modify_font_point_size(font.pointSize()))
        self.setFont(font)

    def _modify_text(self, text: str) -> str:
        new_text = text
        new_text = wrap_in_tag(new_text, "b")
        new_text = wrap_in_tag(new_text, "u")
        return new_text

    def setText(self, text: str) -> None:
        text = self._modify_text(text)

        return super().setText(text)


class DataView(QWidget):

    def __init__(self, parent: Optional[PySide6.QtWidgets.QWidget] = None, show_none: bool = False, title: str = None) -> None:
        super().__init__(parent=parent)
        self._is_built: bool = False
        self.show_none = show_none
        self.setLayout(QFormLayout())
        self.setup_layout()
        self.title = title
        self.title_label = TitleLabel()
        self.layout.addRow(self.title_label)
        self.title_label.setVisible(False)
        self.rows: dict[str, DataRow] = {}

    def setup_layout(self):
        self.layout.setHorizontalSpacing(50)
        self.layout.setVerticalSpacing(25)

    def set_title(self, title: str):
        if title in {None, ""}:
            title = None
        self.title = title
        self.rebuild()

    def set_show_none(self, value: bool) -> None:
        old_show_none = self.show_none
        if old_show_none is not value:
            self.show_none = value
            self.rebuild()

    @property
    def layout(self) -> QFormLayout:
        return super().layout()

    @property
    def app(self) -> "AntistasiLogbookApplication":
        return QApplication.instance()

    @property
    def backend(self) -> "Backend":
        return self.app.backend

    def add_row(self, name: str, value: Any, type_widget=MiscEnum.NOTHING, position: int = MiscEnum.NOTHING):
        data_row = DataRow(name=name, value=value, position=position, type_widget=type_widget)
        self.rows[name] = data_row

    def determine_type_widget(self, value: Any) -> Optional["TypeFieldProtocol"]:
        typus = type(value)
        type_widget = TYPE_FIELD_TABLE.get(typus)

        return type_widget

    def clear(self):
        pass

    def rebuild(self):
        self.clear()
        if self.title is not None:
            self.title_label.setText(self.title)
            self.title_label.setVisible(True)
        else:
            self.title_label.setVisible(False)
        for row in sorted(self.rows.values(), key=lambda x: x.get_sort_key()):
            if row.type_widget is MiscEnum.NOTHING:
                row.type_widget = self.determine_type_widget(row.value)
            if row.value_widget is None:
                continue
            self.layout.addRow(row.label, row.value_widget)
            row.value_widget.set_size(self.fontMetrics().height(), self.fontMetrics().height())
            row.position = int(self.layout.getWidgetPosition(row.value_widget)[0])

        self.repaint()
        self._is_built = True

    def show(self):
        self.app.extra_windows.add(self)
        self.rebuild()

        return super().show()

    def closeEvent(self, event: PySide6.QtGui.QCloseEvent) -> None:
        self.app.extra_windows.remove(self)
        return super().closeEvent(event)
# region[Main_Exec]


if __name__ == '__main__':
    pass

# endregion[Main_Exec]
