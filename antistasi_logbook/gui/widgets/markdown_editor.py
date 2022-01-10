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
                            QWaitCondition, Qt, QAbstractItemModel, QAbstractListModel, QAbstractTableModel, Signal, Slot, QTimer)

from PySide6.QtGui import (QAction, QBrush, QColor, QConicalGradient, QCursor, QFont, QFontDatabase, QFontMetrics, QGradient, QIcon, QImage,
                           QKeySequence, QLinearGradient, QPainter, QPalette, QPixmap, QRadialGradient, QTextDocument, QTransform)

from PySide6.QtWidgets import (QApplication, QTextBrowser, QBoxLayout, QCheckBox, QColorDialog, QColumnView, QComboBox, QDateTimeEdit, QDialogButtonBox,
                               QDockWidget, QDoubleSpinBox, QFontComboBox, QFormLayout, QFrame, QGridLayout, QGroupBox, QHBoxLayout, QHeaderView,
                               QLCDNumber, QLabel, QLayout, QLineEdit, QListView, QListWidget, QMainWindow, QMenu, QMenuBar, QMessageBox,
                               QProgressBar, QProgressDialog, QPushButton, QSizePolicy, QSpacerItem, QSpinBox, QStackedLayout, QStackedWidget,
                               QStatusBar, QStyledItemDelegate, QSystemTrayIcon, QTabWidget, QTableView, QTextEdit, QTimeEdit, QToolBox, QTreeView,
                               QVBoxLayout, QWidget, QAbstractItemDelegate, QAbstractItemView, QAbstractScrollArea, QRadioButton, QFileDialog, QDialog, QButtonGroup)


from gidapptools import get_logger

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


class AddTitleDialog(QDialog):
    title_accepted = Signal(str)

    def __init__(self, parent: Optional[PySide6.QtWidgets.QWidget] = None) -> None:
        super().__init__(parent=parent)

        self.setLayout(QFormLayout())
        self.level_selector = QSpinBox(self)
        self.level_selector.setMinimum(1)
        self.layout.addRow("Level", self.level_selector)

        self.text_input = QLineEdit(self)
        self.layout.addRow("Text", self.text_input)
        self.buttons = QDialogButtonBox(QDialogButtonBox.Cancel | QDialogButtonBox.Ok, Qt.Horizontal)
        self.buttons.setCenterButtons(True)
        self.buttons.rejected.connect(self.on_cancelled)
        self.buttons.accepted.connect(self.on_accepted)
        self.layout.addWidget(self.buttons)

    def color_text_input(self, clear: bool = True):
        if clear is False:
            self.text_input.setStyleSheet("background-color: rgba(179, 58, 58,200)")
        else:
            self.text_input.setStyleSheet("")

    def on_cancelled(self):
        self.close()

    def on_accepted(self):
        if not self.text_input.text():
            self.color_text_input(False)
            self._single_shot_timer = QTimer.singleShot(1 * 1000, self.color_text_input)
            return
        level_text = '#' * self.level_selector.value()
        title = f"\n{level_text} {self.text_input.text()}\n"
        self.title_accepted.emit(title)
        self.close()

    @property
    def layout(self) -> QFormLayout:
        return super().layout()


class AddLinkDialog(QDialog):
    link_accepted = Signal(str)

    def __init__(self, parent: Optional[PySide6.QtWidgets.QWidget] = None) -> None:
        super().__init__(parent=parent)

        self.setLayout(QFormLayout())
        self.link_text_input = QLineEdit(self)
        self.layout.addRow("text", self.link_text_input)

        self.link_url_input = QLineEdit(self)
        self.layout.addRow("URL", self.link_url_input)
        self.buttons = QDialogButtonBox(QDialogButtonBox.Cancel | QDialogButtonBox.Ok, Qt.Horizontal)
        self.buttons.setCenterButtons(True)
        self.buttons.rejected.connect(self.on_cancelled)
        self.buttons.accepted.connect(self.on_accepted)
        self.layout.addWidget(self.buttons)

    @property
    def layout(self) -> QFormLayout:
        return super().layout()

    def color_inputs(self, input_field: QLineEdit = None):
        if input_field is None:
            self.link_text_input.setStyleSheet("")
            self.link_url_input.setStyleSheet("")
            self.text_input.setStyleSheet("background-color: rgba(179, 58, 58,200)")
        else:
            input_field.setStyleSheet("background-color: rgba(179, 58, 58,200)")

    def on_cancelled(self):
        self.close()

    def on_accepted(self):
        if not self.link_text_input.text():
            self.color_inputs(self.link_text_input)
            self._single_shot_timer = QTimer.singleShot(1 * 1000, self.color_inputs)
            return

        if not self.link_url_input.text():
            self.color_inputs(self.link_url_input)
            self._single_shot_timer = QTimer.singleShot(1 * 1000, self.color_inputs)
            return

        link_text = f"[{self.link_text_input.text()}]({self.link_url_input.text()})"
        self.link_accepted.emit(link_text)
        self.close()


class MarkdownEditor(QWidget):
    accepted = Signal(str)
    cancelled = Signal()

    def __init__(self, text: str = None, parent: Optional[PySide6.QtWidgets.QWidget] = None) -> None:
        super().__init__(parent=parent)
        self.preset_text = text
        self.setLayout(QVBoxLayout())
        self.editor_layout = QHBoxLayout()
        self.layout.addLayout(self.editor_layout)

        self.input_widget: QTextEdit = None
        self.preview_widget: QTextBrowser = None
        self.buttons: QDialogButtonBox = None
        self.input_extras_box: QGroupBox = None
        self.input_extras: dict[str, QPushButton] = {}
        self.temp_dialog = None
        self.setup()

    def setup(self):
        self.setup_input_widget()
        self.setup_input_extras()
        self.setup_preview_widget()

        self.setup_buttons()
        if self.preset_text is not None:
            self.input_widget.setPlainText(self.preset_text)
            self.update_preview()

    def setup_input_widget(self):
        self.input_layout = QVBoxLayout(self)

        self.input_widget = QTextEdit(self)
        font: QFont = self.input_widget.font()
        font.setStyleHint(QFont.Monospace)
        self.input_widget.setFont(font)
        self.input_widget.setAcceptRichText(False)
        self.input_widget.setAutoFormatting(QTextEdit.AutoAll)
        self.input_widget.textChanged.connect(self.update_preview)
        self.input_layout.addWidget(self.input_widget)
        self.input_extras_box = QGroupBox()
        self.input_extras_box.setLayout(QHBoxLayout())

        self.input_layout.addWidget(self.input_extras_box)
        self.editor_layout.addLayout(self.input_layout)

    def setup_input_extras(self):
        add_title_button = QPushButton("add Title")
        add_title_button.pressed.connect(self.add_title)
        self.input_extras["add_title"] = add_title_button

        add_separator_button = QPushButton("add Separator")
        add_separator_button.pressed.connect(self.add_separator)
        self.input_extras["add_separator"] = add_separator_button

        add_link_button = QPushButton("add Link")
        add_link_button.pressed.connect(self.add_link)
        self.input_extras["add_link"] = add_link_button

        for widget in self.input_extras.values():
            self.input_extras_box.layout().addWidget(widget)

    def setup_preview_widget(self):
        self.preview_box = QGroupBox("Preview")
        self.preview_box.setCheckable(True)
        self.preview_box.setChecked(True)
        self.preview_box.setLayout(QGridLayout())

        self.preview_widget = QTextBrowser(self)

        self.preview_box.toggled.connect(self.preview_widget.setVisible)
        self.preview_widget.setReadOnly(True)

        self.preview_widget.setStyleSheet("background-color: rgba(255,255,255,0)")
        self.preview_widget.setOpenExternalLinks(True)
        self.preview_widget.setOpenLinks(True)
        self.preview_box.layout().addWidget(self.preview_widget)
        self.editor_layout.addWidget(self.preview_box)

    def setup_buttons(self):
        self.buttons = QDialogButtonBox(QDialogButtonBox.Cancel | QDialogButtonBox.Ok, Qt.Horizontal)
        self.buttons.rejected.connect(self.on_cancelled)
        self.buttons.accepted.connect(self.on_accepted)
        self.buttons.setCenterButtons(True)
        self.layout.addWidget(self.buttons)

    def update_preview(self):
        self.preview_widget.setMarkdown(self.input_widget.toMarkdown(QTextDocument.MarkdownDialectGitHub))

    def on_accepted(self):
        self.accepted.emit(self.input_widget.toMarkdown(QTextDocument.MarkdownDialectGitHub).strip())

    def on_cancelled(self):
        self.cancelled.emit()

    def add_separator(self):
        self.input_widget.insertPlainText("\n---\n")

    def add_title(self):
        self.temp_dialog = AddTitleDialog(self)
        self.temp_dialog.title_accepted.connect(self.input_widget.insertPlainText)
        self.temp_dialog.show()

    def add_link(self):
        self.temp_dialog = AddLinkDialog(self)
        self.temp_dialog.link_accepted.connect(self.input_widget.insertPlainText)
        self.temp_dialog.show()

    @property
    def layout(self) -> QHBoxLayout:
        return super().layout()


class MarkdownEditorDialog(QDialog):
    dialog_accepted = Signal(str)
    dialog_cancelled = Signal()

    def __init__(self, text: str = None, parent: Optional[PySide6.QtWidgets.QWidget] = ...) -> None:
        super().__init__(parent=parent)
        self.setLayout(QGridLayout())
        self.markdown_editor = MarkdownEditor(text=text)
        self.layout().addWidget(self.markdown_editor)
        self.markdown_editor.accepted.connect(self.on_accepted)
        self.markdown_editor.cancelled.connect(self.on_cancelled)
        self.setModal(True)
        self.resize(1000, 750)

    def on_accepted(self, text: str):
        log.debug("setting result of %r to %r", self, QDialog.Accepted)

        self.dialog_accepted.emit(text)
        self.done(QDialog.Accepted)

    def on_cancelled(self):
        log.debug("setting result of %r to %r", self, QDialog.Accepted)

        self.dialog_cancelled.emit()
        self.done(QDialog.Rejected)

    @classmethod
    def show_dialog(cls, text: str = None, parent=None) -> tuple[bool, Optional[str]]:
        dialog = cls(text=text, parent=parent)
        dialog.setModal(True)

        if dialog.exec() == QDialog.Accepted:
            return True, dialog.markdown_editor.input_widget.toMarkdown(QTextDocument.MarkdownDialectGitHub).strip()

        return False, None


# region[Main_Exec]
if __name__ == '__main__':
    pass

# endregion[Main_Exec]
