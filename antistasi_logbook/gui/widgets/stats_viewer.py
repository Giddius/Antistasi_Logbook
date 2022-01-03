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
from PySide6 import (QtCore, QtGui, QtWidgets, Qt3DAnimation, Qt3DCore, Qt3DExtras, Qt3DInput, Qt3DLogic, Qt3DRender, QtAxContainer, QtBluetooth,
                     QtCharts, QtConcurrent, QtDataVisualization, QtDesigner, QtHelp, QtMultimedia, QtMultimediaWidgets, QtNetwork, QtNetworkAuth,
                     QtOpenGL, QtOpenGLWidgets, QtPositioning, QtPrintSupport, QtQml, QtQuick, QtQuickControls2, QtQuickWidgets, QtRemoteObjects,
                     QtScxml, QtSensors, QtSerialPort, QtSql, QtStateMachine, QtSvg, QtSvgWidgets, QtTest, QtUiTools, QtWebChannel, QtWebEngineCore,
                     QtWebEngineQuick, QtWebEngineWidgets, QtWebSockets, QtXml)

from PySide6.QtCore import (QByteArray, QCoreApplication, QDate, QDateTime, QEvent, QLocale, QMetaObject, QModelIndex, QModelRoleData, QMutex,
                            QMutexLocker, QObject, QPoint, QRect, QRecursiveMutex, QRunnable, QSettings, QSize, QThread, QThreadPool, QTime, QUrl,
                            QWaitCondition, Qt, QAbstractItemModel, QAbstractListModel, QAbstractTableModel, Signal, Slot)

from PySide6.QtGui import (QAction, QBrush, QColor, QConicalGradient, QPen, QCursor, QFont, QFontDatabase, QFontMetrics, QGradient, QIcon, QImage,
                           QKeySequence, QLinearGradient, QPainter, QPalette, QPixmap, QRadialGradient, QTransform)

from PySide6.QtWidgets import (QApplication, QBoxLayout, QCheckBox, QColorDialog, QColumnView, QComboBox, QDateTimeEdit, QDialogButtonBox,
                               QDockWidget, QDoubleSpinBox, QFontComboBox, QFormLayout, QFrame, QGridLayout, QGroupBox, QHBoxLayout, QHeaderView,
                               QLCDNumber, QLabel, QLayout, QLineEdit, QListView, QListWidget, QMainWindow, QMenu, QMenuBar, QMessageBox,
                               QProgressBar, QProgressDialog, QPushButton, QSizePolicy, QSpacerItem, QSpinBox, QStackedLayout, QStackedWidget,
                               QStatusBar, QStyledItemDelegate, QSystemTrayIcon, QTabWidget, QTableView, QTextEdit, QTimeEdit, QToolBox, QTreeView,
                               QVBoxLayout, QWidget, QAbstractItemDelegate, QAbstractItemView, QAbstractScrollArea, QRadioButton, QFileDialog, QButtonGroup)


import pyqtgraph as pg
from gidapptools import get_logger
if TYPE_CHECKING:
    # * Third Party Imports --------------------------------------------------------------------------------->
    from antistasi_logbook.gui.main_window import AntistasiLogbookMainWindow
    from antistasi_logbook.backend import Backend
    from antistasi_logbook.gui.application import AntistasiLogbookApplication
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
COLORS = ["red", "tan", "blue", "gold", "gray", "lime", "peru", "pink", "plum", "teal", "brown", "coral", "green",
          "olive", "wheat", "white", "bisque", "indigo", "maroon", "orange", "purple", "sienna", "tomato", "yellow"]


class ColorSelector(QGroupBox):
    color_changed = Signal(str, QColor)

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setLayout(QFormLayout())
        self.layout.setVerticalSpacing(5)
        self.key_map: dict[pg.ColorButton, str] = {}

    def add_key(self, key: str, color: QColor = None):
        color_selector = pg.ColorButton()
        self.layout.addRow(key, color_selector)
        if color is not None:
            color_selector.setColor(color)
        color_selector.sigColorChanged.connect(self.color_change_proxy)
        self.key_map[color_selector] = key

    @Slot(object)
    def color_change_proxy(self, button: pg.ColorButton):
        key = self.key_map[button]
        color = button.color()
        self.color_changed.emit(key, color)

    @property
    def layout(self) -> QFormLayout:
        return super().layout()


class ControlBox(QGroupBox):

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setLayout(QFormLayout())
        self.line_width_selector = QSpinBox()
        self.line_width_selector.setMinimum(1)
        self.line_width_selector.setMaximum(99)

        self.layout.addRow("Line width", self.line_width_selector)

        self.color_box = ColorSelector()
        self.layout.addRow("Colors", self.color_box)

    @property
    def layout(self) -> QFormLayout:
        return super().layout()


class StatsWindow(QMainWindow):

    def __init__(self, stat_data: list[dict[str, Any]], title: str, parent=None):
        super().__init__(parent=parent)
        self.setCentralWidget(QWidget(self))
        self.centralWidget().setLayout(QHBoxLayout())
        self.plot_widget = pg.PlotWidget(axisItems={'bottom': pg.DateAxisItem()}, title=title)
        self.plots: dict[str, pg.PlotItem] = {}
        self.control_box = ControlBox()
        self.stat_data = sorted(stat_data, key=lambda x: x.get("timestamp"), reverse=False)
        self.available_colors = COLORS.copy()
        random.shuffle(self.available_colors)
        self.legend = pg.LegendItem((80, 80), 50, colCount=2)

        self.setup()

    @property
    def layout(self) -> QHBoxLayout:
        return self.centralWidget().layout()

    @cached_property
    def keys(self) -> list[str]:
        return [k for k in self.stat_data[0].keys() if k != "timestamp"]

    @cached_property
    def all_timestamps(self) -> list[float]:
        return [i.get("timestamp").timestamp() for i in self.stat_data]

    @property
    def app(self) -> "AntistasiLogbookApplication":
        return QApplication.instance()

    def setup(self):
        self.general_setup()
        self.plot_setup()
        self.control_setup()

    def general_setup(self):
        self.status_bar = QStatusBar(self)
        self.status_bar.setLayoutDirection(Qt.LeftToRight)
        self.setStatusBar(self.status_bar)
        self.control_box.setFixedWidth(300)
        self.layout.addWidget(self.control_box, 0)
        self.layout.addWidget(self.plot_widget, 2)

    def plot_setup(self):
        self.vertical_crosshair = pg.InfiniteLine(angle=90, movable=False)
        self.horizontal_crosshair = pg.InfiniteLine(angle=0, movable=False)
        self.plot_widget.addItem(self.horizontal_crosshair, ignoreBounds=True)
        self.plot_widget.addItem(self.vertical_crosshair, ignoreBounds=True)
        self.vertical_crosshair.setVisible(False)
        self.horizontal_crosshair.setVisible(False)
        self.plot_widget.setMouseEnabled(True)
        self.legend.setParentItem(self.plot_widget.getPlotItem())

        for idx, key in enumerate(self.keys):
            data = (self.all_timestamps, [i.get(key) for i in self.stat_data])
            item = self.plot_widget.plot(*data, pen=pg.mkPen(self.available_colors[idx], width=2), antialias=False, name=key)
            self.legend.addItem(item, key)
            self.plots[key] = item
            if item.name().casefold() != "serverfps":
                item.setVisible(False)

            self.plot_widget.sceneObj.sigMouseMoved.connect(self.mouse_moved_in_plot)

    def mouse_moved_in_plot(self, pos) -> None:
        def set_vertical(point):
            if point.x() > self.all_timestamps[0] and point.x() < self.all_timestamps[-1]:
                date_time = datetime.fromtimestamp(point.x(), tz=UTC)
                self.status_bar.showMessage(self.app.format_datetime(date_time))
                self.vertical_crosshair.setVisible(True)
                self.vertical_crosshair.setPos(point.x())
            else:
                self.status_bar.clearMessage()
                self.vertical_crosshair.setVisible(False)

        def set_horizontal(point):
            pass

            self.horizontal_crosshair.setVisible(False)

        if self.plot_widget.sceneBoundingRect().contains(pos):
            mousePoint = self.plot_widget.getPlotItem().vb.mapSceneToView(pos)

            set_vertical(mousePoint)
            set_horizontal(mousePoint)

    def control_setup(self):
        self.control_box.line_width_selector.setValue(2)
        self.control_box.line_width_selector.valueChanged.connect(self.change_pen_widths)
        for key in self.keys:
            self.control_box.color_box.add_key(key)
        self.control_box.color_box.color_changed.connect(self.change_pen_color)

    @Slot(float)
    def change_pen_widths(self, new_width: float):
        for item in self.plots.values():
            new_pen = item.opts["pen"]
            if not isinstance(new_pen, QPen):
                continue
            new_pen.setWidth(new_width)
            item.setPen(new_pen)

    @Slot(str, QColor)
    def change_pen_color(self, key: str, color: QColor):
        item = self.plots[key]
        new_pen = item.opts["pen"]
        new_pen.setColor(color)
        item.setPen(new_pen)

    def add_line_at(self, date_time: datetime):
        time_stamp = date_time.timestamp()
        self.plot_widget.addLine(x=time_stamp, pen=pg.mkPen("red", width=3))


# region[Main_Exec]

if __name__ == '__main__':
    pass

# endregion[Main_Exec]
