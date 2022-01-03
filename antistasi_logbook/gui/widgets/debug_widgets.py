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
from antistasi_logbook.gui.resources.antistasi_logbook_resources_accessor import AllResourceItems
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
                           QKeySequence, QLinearGradient, QPainter, QPalette, QPixmap, QRadialGradient, QTransform, QFontInfo)

from PySide6.QtWidgets import (QApplication, QBoxLayout, QCheckBox, QColorDialog, QColumnView, QComboBox, QDateTimeEdit, QDialogButtonBox,
                               QDockWidget, QDoubleSpinBox, QFontComboBox, QFormLayout, QFrame, QGridLayout, QGroupBox, QHBoxLayout, QHeaderView,
                               QLCDNumber, QLabel, QLayout, QLineEdit, QListView, QListWidget, QMainWindow, QMenu, QMenuBar, QMessageBox,
                               QProgressBar, QProgressDialog, QPushButton, QSizePolicy, QSpacerItem, QSpinBox, QStackedLayout, QStackedWidget,
                               QStatusBar, QStyledItemDelegate, QSystemTrayIcon, QTabWidget, QTableView, QTextEdit, QTimeEdit, QToolBox, QTreeView,
                               QVBoxLayout, QWidget, QAbstractItemDelegate, QAbstractItemView, QAbstractScrollArea, QRadioButton, QFileDialog, QButtonGroup)

from gidapptools import get_logger
from antistasi_logbook.gui.widgets.dock_widget import BaseDockWidget
import pp
# endregion[Imports]

# region [TODO]


# endregion [TODO]

# region [Logging]


# endregion[Logging]

# region [Constants]

THIS_FILE_DIR = Path(__file__).parent.absolute()
log = get_logger(__name__)

# endregion[Constants]


class IconTextLabel(QWidget):
    def __init__(self, parent=None, text: str = None, icon: QPixmap = None):
        super().__init__(parent=parent)
        self.setLayout(QHBoxLayout())
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.icon_label = QLabel(self)
        self.text_label = QLabel(self)
        if icon is not None:
            self.icon_label.setPixmap(icon)

        if text is not None:
            self.text_label.setText(text)

        self.layout.addWidget(self.icon_label)
        self.layout.addWidget(self.text_label)
        self.layout.setAlignment(Qt.AlignCenter)

    @property
    def layout(self) -> QVBoxLayout:
        return super().layout()


class PathButton(QPushButton):

    def __init__(self, path: Union[str, os.PathLike, Path], parent=None):
        super().__init__(parent=parent)
        self.path = Path(path).resolve()
        self.is_file = self.path.is_file()
        self.is_dir = self.path.is_dir()
        self.setText(self.path.as_posix())

        link_color = QApplication.instance().palette().color(QPalette.Button.Link)
        r = link_color.red()
        g = link_color.green()
        b = link_color.blue()
        self.setStyleSheet(f"color: rgb({', '.join(str(i) for i in [r,g,b])})")
        self.setCursor(Qt.PointingHandCursor)

        self.pressed.connect(self.open_folder)

    def open_folder(self):
        safe_path = str(self.path)
        if self.is_dir is False and self.is_file is True:
            safe_path = str(self.path.parent)

        if sys.platform == 'darwin':
            subprocess.run(['open', '--', safe_path], check=False)
        elif sys.platform == 'linux2':
            subprocess.run(['gnome-open', '--', safe_path], check=False)
        elif sys.platform == 'win32':
            subprocess.run(['explorer', safe_path], check=False)

    @staticmethod
    def check_if_path(path: Union[str, os.PathLike, Path]) -> bool:
        if isinstance(path, os.PathLike):
            return True
        try:
            maybe_path = Path(path)
            if maybe_path.exists() is True:
                return True

            if maybe_path.resolve().exists() is True:
                return True
        except TypeError:
            return False
        return False


class PathListWidget(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setLayout(QFormLayout())

    @property
    def layout(self) -> QFormLayout:
        return super().layout()

    def addItems(self, items: Iterable[Union[str, os.PathLike, Path]]):
        for item in items:
            widget = PathButton(item, self)
            self.layout.addRow('▶', widget)


class FontInfoWidget(QWidget):
    attr_names = ("family",
                  "style",
                  "pointSize",
                  "weight",
                  "bold",
                  "italic",
                  "overline",
                  "pixelSize",
                  "strikeOut",
                  "styleHint",
                  "styleName",
                  "underline",
                  "exactMatch",
                  "fixedPitch",
                  "pointSizeF",
                  "legacyWeight")

    def __init__(self, font: QFont, parent=None):
        super().__init__(parent=parent)
        self.setLayout(QFormLayout())
        self.target_font = font
        self.target_font_info = QFontInfo(self.target_font)
        for attr_name in self.attr_names:
            value = getattr(self.target_font_info, attr_name)()
            widget = QLabel()
            widget.setText(str(value))
            self.layout.addRow(attr_name, widget)

    @property
    def layout(self) -> QFormLayout:
        return super().layout()


class DebugDialog(QWidget):
    def __init__(self, title: str, key_text: str, value_data: Any, category: "DebugCategoryBox") -> None:
        super().__init__(parent=None)
        self.setLayout(QVBoxLayout())
        self.setWindowTitle(title)
        self.setStyleSheet("""QTextEdit {
            background: transparent
            }
            """)
        self.category = category
        self.key_text = key_text
        self.value_data = value_data
        self.value_widget = None

        self.key_text_widget = QTextEdit(self)
        self.key_text_widget.setAlignment(Qt.AlignCenter)
        self.key_text_widget.setReadOnly(True)
        self.key_text_widget.setFrameStyle(QFrame.NoFrame)
        self.key_text_widget.setHtml(self.key_text)
        self.key_text_widget.setSizeAdjustPolicy(QTextEdit.AdjustToContents)
        self.key_text_widget.adjustSize()

        self.key_text_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        self.layout.addWidget(self.key_text_widget, 0)

        self.make_line()

        self.value_widget = self.make_value_widget(self.value_data)
        self.layout.addWidget(self.value_widget, 1)

        self.layout.addStretch()
        self.resize(1000, 400)

    def closeEvent(self, event: PySide6.QtGui.QCloseEvent) -> None:
        self.category.current_display_dialog = None
        super().closeEvent(event)

    def make_line(self):
        self.line = QFrame(self)
        self.line.setFrameShape(QFrame.HLine)
        self.line.setFrameShadow(QFrame.Sunken)

        self.layout.addWidget(self.line, 0)

    def make_value_widget(self, data: Any):
        if isinstance(data, defaultdict):
            data = dict(data)
        if PathButton.check_if_path(data) is True:
            return PathButton(data, self)

        if isinstance(data, QFont):
            return FontInfoWidget(data, self)

        elif isinstance(data, (list, tuple, set, frozenset)):
            if all(PathButton.check_if_path(i) for i in data):
                widget = PathListWidget(self)
                widget.addItems(sorted(data))
            else:
                widget = QListWidget(self)
                widget.addItems(str(i) for i in sorted(data))
            return widget

        elif isinstance(data, bool):
            text = str(data).title()
            if data is True:
                icon = AllResourceItems.check_mark_green_image.get_as_pixmap(50, 50)
            elif data is False:
                icon = AllResourceItems.close_cancel_image.get_as_pixmap(50, 50)
            return IconTextLabel(self, text, icon)

        elif isinstance(data, dict):
            widget = QWidget(self)
            widget.setLayout(QFormLayout())
            for key, value in data.items():
                widget.layout().addRow(key, self.make_value_widget(value))
            return widget

        else:
            log.debug("value_data has an unset type. (type: %r)", type(data))
            widget = QTextEdit(self)
            widget.setText(str(data))
            widget.setReadOnly(True)
            widget.setFrameStyle(QFrame.NoFrame)
            return widget

    @property
    def layout(self) -> QVBoxLayout:
        return super().layout()

    def close(self) -> bool:
        log.debug("closing %r", self)
        self.category.current_display_dialog = None
        return super().close()

    def show(self) -> None:
        if self.category.current_display_dialog is not None:
            self.category.current_display_dialog.close()
        self.category.current_display_dialog = self
        return super().show()


class ShowAttrButton(QPushButton):

    def __init__(self, attr_name: str, obj: object, parent=None):
        super().__init__(parent=parent)
        self.attr_name = attr_name
        self.obj = obj
        self.category_name = f"Show '{obj.__class__.__name__}'-attribute"
        self.setText(f"Show `{self.attr_name}`")

        self.pressed.connect(self.show_info_box)

    def show_info_box(self):
        title = self.attr_name

        attr_value = getattr(self.obj, self.attr_name)
        if callable(attr_value):
            attr_value = attr_value()

        key_text = f"Attribute <i><b>{self.attr_name!r}</b></i> of object <i><b>{self.obj!r}</b></i> is:"

        dialog = DebugDialog(title=title, key_text=key_text, value_data=attr_value, category=self.parent())
        dialog.show()


class DebugCategoryBox(QGroupBox):

    def __init__(self, name: str, layout_class: QVBoxLayout, parent=None):
        super().__init__(parent=parent)
        self.name = name
        self.setTitle(self.name)
        self.setLayout(layout_class())
        self.widgets: dict[str, QWidget] = {}
        self.current_display_dialog: DebugDialog = None

    @ property
    def layout(self) -> QLayout:
        return super().layout()

    def add_widget(self, name: str, widget: QWidget):
        self.layout.addWidget(widget)
        widget.setParent(self)
        self.widgets[name] = widget


class DebugContentWidget(QWidget):

    def __init__(self, parent: Optional[PySide6.QtWidgets.QWidget] = None,) -> None:
        super().__init__(parent=parent)
        self.setLayout(QVBoxLayout())
        self.categories: dict[str, DebugCategoryBox] = {}

    @ property
    def layout(self) -> QVBoxLayout:
        return super().layout()

    def add_category(self, name: str, layout_class: QLayout = QVBoxLayout):
        category = DebugCategoryBox(name=name, layout_class=layout_class)
        self.layout.addWidget(category)
        self.categories[name] = category


class DebugDockWidget(BaseDockWidget):

    def __init__(self, parent: QMainWindow):
        super().__init__(parent=parent,
                         title="DEBUG",
                         start_floating=True,
                         start_hidden=True,
                         add_menu_bar_action=True,
                         allowed_areas=Qt.NoDockWidgetArea)
        self.setWidget(DebugContentWidget(self))

    @property
    def widget(self) -> DebugContentWidget:
        return super().widget()

    def add_widget(self, name: str, category: str, widget: QWidget):
        if category not in self.widget.categories:
            self.widget.add_category(name=category)

        category_box: DebugCategoryBox = self.widget.categories[category]
        category_box.add_widget(name=name, widget=widget)

    def add_show_attr_button(self, attr_name: str, obj: object):

        button = ShowAttrButton(attr_name=attr_name, obj=obj, parent=self)
        self.add_widget(button.text(), button.category_name, button)
# region[Main_Exec]


if __name__ == '__main__':
    pass

# endregion[Main_Exec]
