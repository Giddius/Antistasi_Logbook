"""
WiP.

Soon.
"""

# region [Imports]

# * Standard Library Imports ---------------------------------------------------------------------------->
from typing import TYPE_CHECKING, Union, Optional, Iterable, Any, Generator
from pathlib import Path

# * Third Party Imports --------------------------------------------------------------------------------->

from abc import ABC, ABCMeta, abstractmethod
# * Gid Imports ----------------------------------------------------------------------------------------->
from gidapptools import get_logger
import PySide6
from PySide6 import (QtCore, QtGui, QtWidgets, Qt3DAnimation, Qt3DCore, Qt3DExtras, Qt3DInput, Qt3DLogic, Qt3DRender, QtAxContainer, QtBluetooth,
                     QtCharts, QtConcurrent, QtDataVisualization, QtDesigner, QtHelp, QtMultimedia, QtMultimediaWidgets, QtNetwork, QtNetworkAuth,
                     QtOpenGL, QtOpenGLWidgets, QtPositioning, QtPrintSupport, QtQml, QtQuick, QtQuickControls2, QtQuickWidgets, QtRemoteObjects,
                     QtScxml, QtSensors, QtSerialPort, QtSql, QtStateMachine, QtSvg, QtSvgWidgets, QtTest, QtUiTools, QtWebChannel, QtWebEngineCore,
                     QtWebEngineQuick, QtWebEngineWidgets, QtWebSockets, QtXml)

from PySide6.QtCore import (QByteArray, QCoreApplication, QDate, QDateTime, QEvent, QLocale, QMetaObject, QModelIndex, QModelRoleData, QMutex,
                            QMutexLocker, QObject, QPoint, QRect, QRecursiveMutex, QRunnable, QSettings, QSize, QThread, QThreadPool, QTime, QUrl,
                            QWaitCondition, Qt, QUrl, QAbstractItemModel, QAbstractListModel, QAbstractTableModel, Signal, Slot)

from PySide6.QtGui import (QAction, QTextCursor, QBrush, QTextOption, QColor, QConicalGradient, QCursor, QFont, QFontDatabase, QFontMetrics, QGradient, QIcon, QImage,
                           QKeySequence, QSyntaxHighlighter, QTextCharFormat, QTextFormat, QTextBlockFormat, QTextListFormat, QTextTableFormat, QTextTable,
                           QTextTableCellFormat, QDesktopServices, QLinearGradient, QPainter, QFontInfo, QPalette, QPixmap, QRadialGradient, QTransform, Qt)

from PySide6.QtWidgets import (QApplication, QBoxLayout, QCheckBox, QColorDialog, QColumnView, QComboBox, QDateTimeEdit, QDialogButtonBox,
                               QDockWidget, QDoubleSpinBox, QFontComboBox, QFormLayout, QFrame, QGridLayout, QGroupBox, QHBoxLayout, QHeaderView,
                               QLCDNumber, QLabel, QLayout, QLineEdit, QListView, QListWidget, QMainWindow, QMenu, QMenuBar, QMessageBox,
                               QProgressBar, QProgressDialog, QPushButton, QSizePolicy, QSpacerItem, QSpinBox, QStackedLayout, QStackedWidget,
                               QStatusBar, QStyledItemDelegate, QSystemTrayIcon, QTabWidget, QTableView, QTextEdit, QTimeEdit, QToolBox, QTreeView,
                               QVBoxLayout, QWidget, QAbstractItemDelegate, QInputDialog, QAbstractItemView, QAbstractScrollArea, QRadioButton, QFileDialog, QListView, QButtonGroup)

from antistasi_logbook.storage.models.models import RecordClass, LogFile, ModLink, Server, LogRecord, LogLevel, GameMap, RemoteStorage, Mod, LogFileAndModJoin
from peewee import Field, IntegrityError
from antistasi_logbook.gui.resources.antistasi_logbook_resources_accessor import AllResourceItems
import pyqtgraph as pg
from gidapptools.general_helper.string_helper import StringCase, StringCaseConverter
import re
import attr
from antistasi_logbook.records.enums import MessageTypus
from antistasi_logbook.data.sqf_syntax_data import SQF_BUILTINS_REGEX
from gidapptools.general_helper.color.color_item import Color

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

VIEW_ABLE_ITEMS_TYPE = Union["AbstractRecord", "LogRecord", "LogFile", "Server"]


class ModModel(QAbstractTableModel):
    ace_compat_regex = re.compile(r"ace.*compat", re.IGNORECASE)
    column_names_to_exclude = {"id", "full_path", "mod_hash_short", "mod_hash", "marked", "comments", "link", "mod_dir"}

    def __init__(self, mods: Mod, parent: Optional[PySide6.QtCore.QObject] = None) -> None:
        super().__init__(parent=parent)
        self.mods = sorted(mods, key=lambda x: (x.official is True, x.default is True, self.ace_compat_regex.search(x.name) is not None, "rhs" in x.name.casefold(), "3cb" in x.name.casefold(), "cup" in x.name.casefold()))
        self.columns: tuple[Field] = self.get_columns()

    def get_columns(self) -> tuple[Field]:
        columns = sorted([field for field_name, field in Mod._meta.fields.items() if field_name not in self.column_names_to_exclude], key=lambda x: x.name != "name")

        return tuple(columns)

    def rowCount(self, parent: Union[PySide6.QtCore.QModelIndex, PySide6.QtCore.QPersistentModelIndex] = ...) -> int:
        return len(self.mods)

    def columnCount(self, parent: Union[PySide6.QtCore.QModelIndex, PySide6.QtCore.QPersistentModelIndex] = ...) -> int:
        return len(self.columns)

    def data(self, index: Union[PySide6.QtCore.QModelIndex, PySide6.QtCore.QPersistentModelIndex], role: int = ...) -> Any:
        if not index.isValid():
            return
        if not 0 <= index.row() < len(self.mods):
            return None
        item = self.mods[index.row()]
        column = self.columns[index.column()]
        if role == Qt.DisplayRole:
            return str(item.get_data(column.name))

        if role == Qt.BackgroundRole:
            if item.official is True:
                return Color.get_color_by_name("gray").with_alpha(0.25).qcolor

            if self.ace_compat_regex.search(item.name):
                return Color.get_color_by_name("brown").with_alpha(0.25).qcolor
            if "rhs" in item.name.casefold():
                return Color.get_color_by_name("red").with_alpha(0.25).qcolor
            if "3cb" in item.name.casefold():
                return Color.get_color_by_name("green").with_alpha(0.25).qcolor

            if "zeus" in item.name.casefold():
                return Color.get_color_by_name("blue").with_alpha(0.25).qcolor

            if "cup" in item.name.casefold():
                return Color.get_color_by_name("purple").with_alpha(0.25).qcolor

        if role == Qt.ToolTipRole:
            if item.link:
                return str(item.link)

    def headerData(self, section: int, orientation: PySide6.QtCore.Qt.Orientation, role: int = ...) -> Any:
        if orientation == Qt.Horizontal:
            column = self.columns[section]
            if role == Qt.DisplayRole:
                return column.name

    def add_link(self, index, link):
        item = self.mods[index.row()]
        link_item = ModLink(cleaned_mod_name=item.cleaned_name, link=link)
        try:
            link_item.save()
        except IntegrityError:
            link_item.update()


class ValueLineEdit(QLineEdit):
    style_sheet_data = """
    """

    def __init__(self, text: str = None, parent=None):
        super().__init__(text, parent=parent)
        self.setReadOnly(True)
        self.setAlignment(Qt.AlignCenter)
        self.setProperty("display_only", True)
        self.setStyleSheet(self.style_sheet_data)


class BaseDetailWidget(QWidget):

    def __init__(self, parent: Optional[PySide6.QtWidgets.QWidget] = None) -> None:
        super().__init__(parent=parent)
        self.setLayout(QFormLayout(self))

    @ property
    def layout(self) -> QFormLayout:
        return super().layout()

    @property
    def app(self) -> "AntistasiLogbookApplication":
        return QApplication.instance()

    @property
    def backend(self) -> "Backend":
        return self.app.backend

    @property
    def config(self) -> "GidIniConfig":
        return self.backend.config


class ServerDetailWidget(BaseDetailWidget):

    def __init__(self, server: Server, parent: Optional[PySide6.QtWidgets.QWidget] = None) -> None:
        super().__init__(parent=parent)
        self.server = server

        self.name_label = QLabel(text="Name")
        self.name_value = ValueLineEdit(self.server.name, parent=self)

        self.layout.addRow(self.name_label, self.name_value)

        self.amount_log_files_label = QLabel(text="Amount Log-Files")
        self.amount_log_files_value = QLCDNumber(3, self)
        self.amount_log_files_value.display(LogFile.select().where(LogFile.server == self.server).count())
        self.layout.addRow(self.amount_log_files_label, self.amount_log_files_value)

        self.remote_path_label = QLabel(text="Remote Path")
        self.remote_path_value = ValueLineEdit(self.server.remote_path.as_posix(), parent=self)

        self.layout.addRow(self.remote_path_label, self.remote_path_value)

        # TODO: Find Faster solution, or only on button press

        # self.player_stats_label = QLabel(text="Players")
        # axis = pg.DateAxisItem()
        # self.player_stats_value = pg.PlotWidget()
        # self.player_stats_value.getPlotItem().setAxisItems({'bottom': axis})
        # self.player_stats_value.getPlotItem().plot(*self.get_player_stats())

        # self.layout.addRow(self.player_stats_label, self.player_stats_value)

    def get_player_stats(self):
        log_files = LogFile.select().where(LogFile.server == self.server)
        all_log_files = {log_file.id: log_file for log_file in LogFile.select()}
        record_class = RecordClass.get(name="PerformanceRecord")
        conc_record_class = record_class.record_class
        x = []
        y = []
        for record in list(LogRecord.select().where((LogRecord.log_file << log_files) & (LogRecord.record_class == record_class)).order_by(LogRecord.recorded_at).dicts()):
            log_file = all_log_files.get(record.get("log_file"))
            item = conc_record_class.from_model_dict(record, log_file=log_file)
            x.append(item.recorded_at.timestamp())
            y.append(item.stats.get("Players"))

        return x, y


class LogFileDetailWidget(BaseDetailWidget):

    def __init__(self, log_file: LogFile, parent: Optional[PySide6.QtWidgets.QWidget] = None) -> None:
        super().__init__(parent=parent)
        self.log_file = log_file

        self.name_label = QLabel(text="Name")
        self.name_value = ValueLineEdit(self.log_file.name, parent=self)

        self.layout.addRow(self.name_label, self.name_value)

        self.modified_at_label = QLabel(text="Modified at")
        self.modified_at_value = ValueLineEdit(text=self.app.format_datetime(self.log_file.modified_at))

        self.server_label = QLabel(text="Server")
        self.server_value = ValueLineEdit(text=self.log_file.server.name, parent=self)
        self.layout.addRow(self.server_label, self.server_value)

        self.game_map_label = QLabel("Game Map", parent=self)
        self.game_map_value = ValueLineEdit(text=self.log_file.game_map.full_name, parent=self)
        if self.log_file.game_map.map_image_low_resolution is not None:
            self.game_map_value.setToolTip(f'<b>{self.log_file.game_map.map_image_low_resolution.stem.removesuffix("_thumbnail").replace("_"," ").title()}</b><br><img src="{self.log_file.game_map.map_image_low_resolution.as_posix()}">')

        self.layout.addRow(self.game_map_label, self.game_map_value)

        self.version_label = QLabel("Version", parent=self)
        self.version_value = ValueLineEdit(text=str(self.log_file.version), parent=self)
        self.layout.addRow(self.version_label, self.version_value)

        self.campaign_id_label = QLabel("Campaign ID", parent=self)
        self.campaign_id_value = ValueLineEdit(text=str(self.log_file.campaign_id), parent=self)
        self.layout.addRow(self.campaign_id_label, self.campaign_id_value)

        # self.amount_log_records_label = QLabel("Amount Log-Records", parent=self)
        self.amount_log_records_value = ValueLineEdit(text=str(self.log_file.amount_log_records), parent=self)
        self.layout.addRow("Amount Log-Records", self.amount_log_records_value)

        self.mods_label = QLabel("Mods", parent=self)
        self.mods_value = QListView(self)
        model = ModModel(self.log_file.get_mods())
        self.mods_value.setModel(model)

        self.layout.addRow(self.mods_label, self.mods_value)
        self.mods_value.doubleClicked.connect(self.open_mod_link)
        # self.mods_value.doubleClicked.connect(self.add_mod_link)

    def open_mod_link(self, index):

        item = self.mods_value.model().mods[index.row()]
        if item.default is True or item.official is True:
            return
        if item.link:
            QDesktopServices.openUrl(QUrl(str(item.link)))
        else:
            QDesktopServices.openUrl(QUrl(f'https://www.google.com/search?q={item.cleaned_name}'))

    def add_mod_link(self, index):
        item = self.mods_value.model().mods[index.row()]
        link, valid = QInputDialog.getText(self, f"link for {item!s}", f"link for {item!s}")
        if valid and link:
            self.mods_value.model().add_link(index, link)


class LineNumberValueBox(QGroupBox):

    def __init__(self, start_value: int, end_value: int, parent=None):
        super().__init__(parent=parent)
        self.start_value = start_value
        self.end_value = end_value
        self.setLayout(QFormLayout())
        self.start_value_display = ValueLineEdit(text=str(self.start_value))
        self.layout.addRow("Start", self.start_value_display)

        self.end_value_display = ValueLineEdit(text=str(self.end_value))
        self.layout.addRow("End", self.end_value_display)

    @ property
    def layout(self) -> QFormLayout:
        return super().layout()


class BoolLabel(QWidget):

    def __init__(self, value: bool, parent: Optional[PySide6.QtWidgets.QWidget] = None) -> None:
        super().__init__(parent)
        self.value = value
        self.setLayout(QHBoxLayout())
        self._text = "Yes" if self.value else "No"
        self._pixmap = AllResourceItems.check_mark_green.get_as_pixmap() if self.value else AllResourceItems.close_cancel.get_as_pixmap()
        font: QFont = self.font()
        fm = QFontMetrics(font)
        h = fm.height()

        self._pixmap = self._pixmap.scaled(h, h, Qt.KeepAspectRatioByExpanding)

        self.text_item = QLabel(text=self._text)
        self.pixmap_item = QLabel()
        self.pixmap_item.setPixmap(self._pixmap)
        self.layout.addWidget(self.text_item)
        self.layout.addWidget(self.pixmap_item)
        self.layout.setAlignment(Qt.AlignHCenter | Qt.AlignTop)

    @ property
    def layout(self) -> QFormLayout:
        return super().layout()


def _re_pattern_converter(in_data: Union[str, re.Pattern]):
    if isinstance(in_data, str):
        return re.compile(in_data)
    return in_data


class AbstractSyntaxHighlightRule(ABC):
    suffix_remove_pattern = re.compile("HighlightRule", re.IGNORECASE)

    @property
    def name(self) -> str:
        return StringCaseConverter.to_snake_case(self.suffix_remove_pattern.sub("", self.__class__.__name__))

    @property
    def style_format(self) -> QTextFormat:
        return self._style_format

    @property
    def pattern(self) -> re.Pattern:
        return self._pattern

    def apply(self, text: str, highlighter: "MessageHighlighter") -> Generator[tuple[int, int, QTextFormat], None, None]:
        for match in self.pattern.finditer(text):
            start, end = match.span()
            log.debug("%r found match %r", self.name, match)
            yield start, end - start, self.style_format


class SeparatorHighlightRule(AbstractSyntaxHighlightRule):

    def __init__(self) -> None:
        self._pattern = re.compile(r"\-{3,}")
        self._style_format = self._make_style_format()

    def _make_style_format(self) -> QTextCharFormat:
        style_format = QTextCharFormat()
        style_format.setFontWeight(100)
        style_format.setForeground(QColor("red"))
        return style_format


class TitleHighlightRule(AbstractSyntaxHighlightRule):

    def __init__(self) -> None:
        self._pattern = re.compile(r"^[\w ]+")
        self._style_format = self._make_style_format()

    def _make_style_format(self) -> QTextCharFormat:
        style_format = QTextCharFormat()
        style_format.setFontStyleHint(QFont.StyleHint.Monospace, QFont.StyleStrategy.PreferQuality)
        style_format.setFontWeight(QFont.Weight.Black)
        log.debug("before multiplication by 2 style_format.fontPointSize()=%r", style_format.fontPointSize())
        style_format.setFontPointSize(style_format.font().pointSize() * 2)
        log.debug("after multiplication by 2 style_format.fontPointSize()=%r", style_format.fontPointSize())
        style_format.setTextOutline(QColor(0, 0, 0, 255))
        style_format.setForeground(QColor(0, 175, 100, 250))

        return style_format

    def apply(self, text: str, highlighter: "MessageHighlighter") -> Generator[tuple[int, int, QTextFormat], None, None]:
        for match in self.pattern.finditer(text):
            start, end = match.span()

            current_block = highlighter.currentBlock()
            if current_block.firstLineNumber() == 0 and current_block.document().lineCount() > 1:

                log.debug("%r found match %r", self.name, match)
                yield start, end - start, self.style_format


class StringHighlightRule(AbstractSyntaxHighlightRule):

    def __init__(self) -> None:
        self._pattern = re.compile(r'\"[^\"]*\"')
        self._style_format = self._make_style_format()

    def _make_style_format(self) -> QTextCharFormat:
        style_format = QTextCharFormat()
        style_format.setForeground(QColor(45, 90, 150, 255))
        return style_format


class IntegerHighlightRule(AbstractSyntaxHighlightRule):
    def __init__(self) -> None:
        self._pattern = re.compile(r"(?<=[\,\s^\[\(])\d+(?=[\]\)\s\,$])")
        self._style_format = self._make_style_format()

    def _make_style_format(self) -> QTextCharFormat:
        style_format = QTextCharFormat()
        style_format.setForeground(Color.get_color_by_name("darkviolet").qcolor)
        return style_format


class FloatHighlightRule(AbstractSyntaxHighlightRule):
    def __init__(self) -> None:
        self._pattern = re.compile(r"(?<=[\,\s^\[\(])\d+\.\d+(?=[\]\)\s\,$])")
        self._style_format = self._make_style_format()

    def _make_style_format(self) -> QTextCharFormat:
        style_format = QTextCharFormat()
        style_format.setForeground(Color.get_color_by_name("lightcoral").qcolor)
        return style_format


class BracketHighlightRule(AbstractSyntaxHighlightRule):
    def __init__(self) -> None:
        self._pattern = re.compile(r"[" + re.escape("{([])}") + r"]")
        self._style_format = self._make_style_format()

    def _make_style_format(self) -> QTextCharFormat:
        style_format = QTextCharFormat()
        style_format.setForeground(QColor(int(250 * 0.8), int(215 * 0.8), int(120 * 0.8), 255))
        return style_format


class SQFbuiltinsHighlightRule(AbstractSyntaxHighlightRule):

    def __init__(self) -> None:

        self._pattern = SQF_BUILTINS_REGEX
        self._style_format = self._make_style_format()

    def _make_style_format(self) -> QTextCharFormat:
        style_format = QTextCharFormat()
        style_format.setFontUnderline(True)
        style_format.setForeground(QColor(90, 100, 74, 255))
        return style_format


class PunctuationHighlightRule(AbstractSyntaxHighlightRule):
    def __init__(self) -> None:

        self._pattern = re.compile(r"[\;\,(\!\=)\=\:]")
        self._style_format = self._make_style_format()

    def _make_style_format(self) -> QTextCharFormat:
        style_format = QTextCharFormat()

        style_format.setForeground(QColor(50, 111, 67, 255))
        return style_format


class KVHighlightRule(AbstractSyntaxHighlightRule):
    def __init__(self) -> None:

        self._pattern = re.compile(r"^◘.*")
        self._style_format = self._make_style_format()

    def _make_style_format(self) -> QTextCharFormat:
        style_format = QTextCharFormat()

        style_format.setBackground(QColor(25, 75, 25, 100))
        style_format.setForeground(QColor(255, 255, 255, 255))
        return style_format


class MessageHighlighter(QSyntaxHighlighter):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.rules: dict[str:AbstractSyntaxHighlightRule] = {}

    def add_rule(self, rule: AbstractSyntaxHighlightRule):
        self.rules[rule.name] = rule

    def highlightBlock(self, text: str) -> None:
        for rule in self.rules.values():
            for _format in rule.apply(text, self):
                self.setFormat(*_format)


class MessageValue(QTextEdit):

    def __init__(self, record: "AbstractRecord", parent: Optional[PySide6.QtWidgets.QWidget] = None):
        super().__init__(parent)
        self.record = record
        self.setReadOnly(True)
        self.setWordWrapMode(QTextOption.NoWrap)

        self.setFont(self.get_text_font())
        self.highlighter = MessageHighlighter(self)
        self.raw_text = self.record.pretty_message
        self.setPlainText(self.record.pretty_message)
        self.setup_highlighter()

    @property
    def text(self) -> str:
        return self.raw_text

    def get_text_font(self) -> QFont:
        text_font = QFont()
        text_font.setFamily("Lucida Console")
        text_font.setPointSize(int(self.font().pointSize() * 1))
        return text_font

    def setup_highlighter(self):
        self.highlighter.add_rule(SeparatorHighlightRule())
        self.highlighter.add_rule(BracketHighlightRule())
        self.highlighter.add_rule(StringHighlightRule())
        self.highlighter.add_rule(IntegerHighlightRule())
        self.highlighter.add_rule(FloatHighlightRule())
        self.highlighter.add_rule(SQFbuiltinsHighlightRule())
        self.highlighter.add_rule(PunctuationHighlightRule())
        self.highlighter.add_rule(KVHighlightRule())
        self.highlighter.setDocument(self.document())


class LogRecordDetailView(BaseDetailWidget):

    def __init__(self, record: "BaseRecord", parent: Optional[PySide6.QtWidgets.QWidget] = None) -> None:
        super().__init__(parent=parent)
        self.record = record

        self.recorded_at_value = ValueLineEdit(text=self.app.format_datetime(self.record.recorded_at))
        self.layout.addRow("Recorded at", self.recorded_at_value)

        self.log_level_value = ValueLineEdit(text=str(self.record.log_level))
        self.layout.addRow("Log-Level", self.log_level_value)

        self.log_file_value = ValueLineEdit(text=str(self.record.log_file))
        self.layout.addRow("Log-File", self.log_file_value)

        self.line_number_value = LineNumberValueBox(self.record.start, self.record.end)
        self.layout.addRow("Line Number", self.line_number_value)

        self.logged_from_value = ValueLineEdit(text=str(self.record.logged_from))
        self.layout.addRow("Logged from", self.logged_from_value)

        self.called_by_value = ValueLineEdit(text=str(self.record.called_by))
        self.layout.addRow("Called by", self.called_by_value)

        self.is_antistasi_record_value = BoolLabel(self.record.is_antistasi_record)

        self.layout.addRow("Antistasi Record", self.is_antistasi_record_value)

        self.message_value = MessageValue(self.record)
        self.layout.addRow("Message", self.message_value)


# region[Main_Exec]
if __name__ == '__main__':
    pass

# endregion[Main_Exec]
