"""
WiP.

Soon.
"""

# region [Imports]

# * Standard Library Imports ---------------------------------------------------------------------------->
import re
from abc import ABC
from typing import TYPE_CHECKING, Any, Union, Optional, Generator
from pathlib import Path

# * Qt Imports --------------------------------------------------------------------------------------->
import PySide6
from PySide6.QtGui import QFont, QColor, QAction, QPixmap, QMouseEvent, QDrag, QTextFormat, QTextOption, QFontMetrics, QTextDocument, QTextCharFormat, QDesktopServices, QSyntaxHighlighter
from PySide6.QtCore import Qt, QUrl, QAbstractTableModel, QSize, QMimeData
from PySide6.QtWidgets import (QMenu, QLabel, QWidget, QGroupBox, QLineEdit, QListView, QTextEdit, QLCDNumber, QFormLayout,
                               QHBoxLayout, QPushButton, QVBoxLayout, QApplication, QInputDialog, QTextBrowser)

# * Third Party Imports --------------------------------------------------------------------------------->
from peewee import Field, DoesNotExist, IntegrityError

# * Gid Imports ----------------------------------------------------------------------------------------->
from gidapptools import get_logger
from gidapptools.general_helper.conversion import seconds2human
from gidapptools.general_helper.string_helper import StringCase, StringCaseConverter
from gidapptools.general_helper.color.color_item import Color

# * Local Imports --------------------------------------------------------------------------------------->
from antistasi_logbook.errors import InsufficientDataPointsError
from antistasi_logbook.data.sqf_syntax_data import SQF_BUILTINS_REGEX
from antistasi_logbook.storage.models.models import Mod, Server, GameMap, LogFile, ModLink, LogRecord, RecordClass
from antistasi_logbook.gui.widgets.stats_viewer import StatsWindow
from antistasi_logbook.gui.widgets.collapsible_widget import CollapsibleGroupBox
from antistasi_logbook.gui.widgets.data_view_widget.data_view import DataView
from antistasi_logbook.gui.resources.antistasi_logbook_resources_accessor import AllResourceItems

# * Type-Checking Imports --------------------------------------------------------------------------------->
if TYPE_CHECKING:
    from gidapptools.gid_config.interface import GidIniConfig

    from antistasi_logbook.backend import Backend
    from antistasi_logbook.gui.application import AntistasiLogbookApplication
    from antistasi_logbook.records.base_record import BaseRecord
    from antistasi_logbook.records.abstract_record import AbstractRecord

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


class ModDataView(DataView):
    def __init__(self, mod: Mod, parent: Optional[PySide6.QtWidgets.QWidget] = None, show_none: bool = False) -> None:
        super().__init__(parent=parent, show_none=show_none, title=mod.pretty_name)
        self.mod = mod

        for column in sorted(list(self.mod.get_meta().sorted_fields), key=self.column_sorter):
            self.add_row(column.verbose_name or column.name, getattr(self.mod, column.name))
        for extra_name in ["cleaned_name", "link"]:
            self.add_row(extra_name, getattr(self.mod, extra_name))
        self.add_row("log_files", [f"{i.server.name}/{i}" for i in sorted(self.mod.get_log_files(), key=lambda x: (-x.server_id, x.modified_at), reverse=True)])

    def column_sorter(self, column: Field) -> int:
        if column.name.casefold() == "marked":
            return -1
        return len(column.verbose_name or column.name)


class ModView(QListView):

    def __init__(self, parent: Optional[PySide6.QtWidgets.QWidget] = None) -> None:
        super().__init__(parent=parent)

        self.open_link_action: QAction = None
        self.set_link_action: QAction = None
        self.all_actions: set[QAction] = set()
        self.mod_data_view: ModDataView = None
        self.setup_actions()

    @property
    def app(self) -> "AntistasiLogbookApplication":
        return QApplication.instance()

    @property
    def backend(self) -> "Backend":
        return self.app.backend

    def setup_actions(self):
        self.open_link_action = QAction(text="open link")
        self.open_link_action.triggered.connect(self.open_link)
        self.all_actions.add(self.open_link_action)

        self.set_link_action = QAction(text="set link")
        self.set_link_action.triggered.connect(self.set_link)
        self.all_actions.add(self.set_link_action)

        self.open_mod_data_view_action = QAction(text="Details")
        self.open_mod_data_view_action.triggered.connect(self.open_mod_data_view)
        self.all_actions.add(self.open_mod_data_view_action)

    def set_link(self):
        index = self.currentIndex()
        item = self.model().mods[index.row()]
        if item.default is True or item.official is True:
            return
        link, accepted = QInputDialog.getText(self, f'New link for Mod {item.cleaned_name!r}', f"please enter an valid link for {item.cleaned_name!r}", QLineEdit.EchoMode.Normal)
        if accepted and link:
            try:
                mod_link = ModLink.get(cleaned_mod_name=item.cleaned_name)
                with self.backend.database.write_lock:
                    ModLink.update(link=link).where(ModLink.id == mod_link.id)
            except DoesNotExist:
                with self.backend.database.write_lock:
                    mod_link = ModLink(cleaned_mod_name=item.cleaned_name, link=link)
                    mod_link.save()

    def open_link(self):
        index = self.currentIndex()
        item = self.model().mods[index.row()]
        if item.default is True or item.official is True:
            return
        if item.link:
            QDesktopServices.openUrl(QUrl(str(item.link)))
        else:
            QDesktopServices.openUrl(QUrl(f'https://www.google.com/search?q={item.cleaned_name}'))

    def open_mod_data_view(self):
        mod = self.model().mods[self.currentIndex().row()]
        self.mod_data_view = ModDataView(mod=mod)
        self.mod_data_view.show()

    def contextMenuEvent(self, event: PySide6.QtGui.QContextMenuEvent) -> None:
        index = self.indexAt(event.pos())
        self.setCurrentIndex(index)
        item = self.model().mods[index.row()]
        if index.isValid():
            menu = QMenu(self)
            if item.default is True or item.official is True:
                pass
            else:
                menu.addAction(self.open_link_action)
                menu.addAction(self.set_link_action)
            menu.addAction(self.open_mod_data_view_action)
            menu.exec(event.globalPos())


class ValueLineEdit(QLineEdit):
    style_sheet_data = """
    """

    def __init__(self, text: str = None, parent=None):
        super().__init__(text, parent=parent)
        self.setReadOnly(True)
        self.setAlignment(Qt.AlignCenter)
        self.setProperty("display_only", True)
        self.setStyleSheet(self.style_sheet_data)


class GameMapValue(QWidget):

    def __init__(self, game_map=GameMap, parent=None):
        super().__init__(parent=parent)
        self.setLayout(QVBoxLayout())
        self.game_map = game_map
        self.game_map_label = ValueLineEdit(self.game_map.full_name)
        self.layout.addWidget(self.game_map_label)
        self.game_map_thumbnail = QLabel()
        self.game_map_pixmap = self._get_game_map_pixmap()
        if self.game_map_pixmap is not None:
            self.game_map_thumbnail.setPixmap(self.game_map_pixmap)
            self.collapsible_box = CollapsibleGroupBox(text="Thumbnail", content=self.game_map_thumbnail, parent=self)
            self.collapsible_box.set_expanded(False)
            self.layout.addWidget(self.collapsible_box)

    def _get_game_map_pixmap(self) -> Optional[QPixmap]:
        game_map_bytes = self.game_map.map_image_low_resolution
        if game_map_bytes is None:
            return
        pixmap = QPixmap()
        pixmap.loadFromData(game_map_bytes)
        return pixmap

    @ property
    def layout(self) -> QVBoxLayout:
        return super().layout()


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

    def __init__(self, server: Server, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent=parent)
        self.server = server

        self.name_label = QLabel(text="Name")
        self.name_value = ValueLineEdit(self.server.name, parent=self)

        self.layout.addRow(self.name_label, self.name_value)

        self.amount_log_files_label = QLabel(text="Amount Log-Files")
        self.amount_log_files_value = QLCDNumber(3, self)
        self.amount_log_files_value.setSegmentStyle(QLCDNumber.Flat)
        self.amount_log_files_value.display(self.server.get_amount_log_files())
        self.layout.addRow(self.amount_log_files_label, self.amount_log_files_value)

        self.remote_path_label = QLabel(text="Remote Path")
        self.remote_path_value = ValueLineEdit(self.server.remote_path.as_posix(), parent=self)

        self.layout.addRow(self.remote_path_label, self.remote_path_value)

        self.comments_value = QTextBrowser(self)
        self.comments_value.setOpenExternalLinks(True)
        self.comments_value.setOpenLinks(True)
        self.comments_value.setReadOnly(True)

        self.comments_value.setStyleSheet("""background-color: rgba(255,255,255,150)""")
        self.comments_value.setMarkdown(self.server.comments)
        document: QTextDocument = self.comments_value.document()

        self.layout.addWidget(QLabel("Comments"))
        self.layout.addWidget(self.comments_value)

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

        time_frame_string = f"{self.app.format_datetime(self.log_file.time_frame.start)} until {self.app.format_datetime(self.log_file.time_frame.end)}"

        self.time_frame_value = ValueLineEdit(text=time_frame_string)
        self.layout.addRow("Time-Frame", self.time_frame_value)

        time_frame_duration_string = seconds2human(self.log_file.time_frame.delta.total_seconds(), min_unit="second")

        self.duration_value = ValueLineEdit(text=time_frame_duration_string)
        self.layout.addRow("Duration", self.duration_value)

        self.server_label = QLabel(text="Server")
        self.server_value = ValueLineEdit(text=self.log_file.server.name, parent=self)
        self.layout.addRow(self.server_label, self.server_value)

        self.game_map_label = QLabel("Game Map", parent=self)
        self.game_map_value = GameMapValue(self.log_file.game_map, self)
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
        self.mods_value = ModView(self)
        model = ModModel(self.log_file.get_mods())
        self.mods_value.setModel(model)

        self.layout.addRow(self.mods_label, self.mods_value)

        self.mods_value.doubleClicked.connect(self.open_mod_link)
        self.header_text_value = QTextEdit()
        self.header_text_value.setReadOnly(True)
        self.header_text_value.setLineWrapMode(QTextEdit.NoWrap)
        self.header_text_value.setPlainText(self.log_file.header_text)
        self.header_text_box = CollapsibleGroupBox("Show Header Text", self.header_text_value, self)
        self.header_text_box.set_expanded(False)
        self.layout.addRow('Header Text', self.header_text_box)

        self.get_stats_button = QPushButton(AllResourceItems.stats_icon_2_image.get_as_icon(), "Get Stats")
        self.layout.addWidget(self.get_stats_button)
        self.get_stats_button.pressed.connect(self.show_stats)
        self.temp_plot_widget = None

    def show_stats(self):
        all_stats = self.log_file.get_stats()
        if len(all_stats) < 2:
            raise InsufficientDataPointsError(len(all_stats), 2)

        self.temp_plot_widget = StatsWindow(all_stats, title=self.log_file.name.upper)
        self.temp_plot_widget.add_marked_records(self.log_file.get_marked_records())
        self.temp_plot_widget.show()

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
        self._pixmap = AllResourceItems.check_mark_green_image.get_as_pixmap() if self.value else AllResourceItems.close_cancel_image.get_as_pixmap()
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
        return StringCaseConverter.convert_to(self.suffix_remove_pattern.sub("", self.__class__.__name__), StringCase.SNAKE)

    @property
    def style_format(self) -> QTextFormat:
        return self._style_format

    @property
    def pattern(self) -> re.Pattern:
        return self._pattern

    def apply(self, text: str, highlighter: "MessageHighlighter") -> Generator[tuple[int, int, QTextFormat], None, None]:
        for match in self.pattern.finditer(text):
            start, end = match.span()

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

        style_format.setFontPointSize(style_format.font().pointSize() * 2)

        style_format.setTextOutline(QColor(0, 0, 0, 255))
        style_format.setForeground(QColor(0, 175, 100, 250))

        return style_format

    def apply(self, text: str, highlighter: "MessageHighlighter") -> Generator[tuple[int, int, QTextFormat], None, None]:
        for match in self.pattern.finditer(text):
            start, end = match.span()

            current_block = highlighter.currentBlock()
            if current_block.firstLineNumber() == 0 and current_block.document().lineCount() > 1:

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

        self._pattern = re.compile(r"^???.*")
        self._style_format = self._make_style_format()

    def _make_style_format(self) -> QTextCharFormat:
        style_format = QTextCharFormat()

        style_format.setBackground(QColor(25, 75, 25, 35))

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

    def __init__(self, record: "AbstractRecord" = None, parent: Optional[PySide6.QtWidgets.QWidget] = None):
        super().__init__(parent)
        self.record = record
        self.setReadOnly(True)
        self.setLineWrapMode(QTextEdit.WidgetWidth)
        self.setWordWrapMode(QTextOption.WrapAtWordBoundaryOrAnywhere)

        self.setFont(self.get_text_font())
        self.highlighter = MessageHighlighter(self)
        self.setup_highlighter()
        if self.record is not None:
            self.raw_text = self.record.pretty_message
            self.setPlainText(self.record.pretty_message)

    def set_record(self, record: "AbstractRecord"):
        self.record = record
        self.raw_text = record.pretty_message
        self.setPlainText(self.raw_text)

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

        self.origin_value = ValueLineEdit(self.record.origin.name)

        self.layout.addRow("Origin", self.origin_value)
        if self.record.extra_detail_views:
            extra_view_content = DataView(border=True)

            for extra in self.record.extra_detail_views:

                extra_view_content.add_row(StringCaseConverter.convert_to(extra, StringCase.TITLE), self.record.get_data(extra))

            self.extra_view = CollapsibleGroupBox("Extra Data", extra_view_content.build(), start_expanded=False, parent=self)
            self.layout.addWidget(self.extra_view)

        self.message_value = MessageValue(self.record)
        self.layout.addRow("Message", self.message_value)

        self.get_stats_button = QPushButton(AllResourceItems.stats_icon_2_image.get_as_icon(), "Stats for this Record")
        self.layout.addWidget(self.get_stats_button)
        self.get_stats_button.pressed.connect(self.get_stats)

    def get_stats(self):
        all_stats = self.record.log_file.get_stats()
        if len(all_stats) < 2:
            raise InsufficientDataPointsError(len(all_stats), 2)

        self.temp_plot_widget = StatsWindow(all_stats, title=self.record.log_file.name.upper)
        self.temp_plot_widget.add_current_record(self.record)

        self.temp_plot_widget.add_marked_records(self.record.log_file.get_marked_records())
        self.temp_plot_widget.show()


# region[Main_Exec]
if __name__ == '__main__':
    pass

# endregion[Main_Exec]
