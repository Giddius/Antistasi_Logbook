"""
WiP.

Soon.
"""

# region [Imports]

# * Standard Library Imports ---------------------------------------------------------------------------->
import re
import random
from abc import ABC
from typing import TYPE_CHECKING, Any, Union, Literal, Optional, Sequence, Generator
from pathlib import Path
from datetime import datetime, timedelta, timezone
from functools import partial
from collections.abc import Iterable
from pprint import pprint
# * Qt Imports --------------------------------------------------------------------------------------->
import PySide6
import pyqtgraph as pg
from PySide6.QtGui import QFont, QColor, QPaintEvent, QPainter, QTextItem, QAction, QPixmap, QTextFormat, QTextOption, QFontMetrics, QTextDocument, QTextCharFormat, QDesktopServices, QSyntaxHighlighter
from PySide6.QtCore import Qt, QUrl, QAbstractTableModel, QPoint, QSize
from PySide6.QtWidgets import (QMenu, QFrame, QLabel, QStyle, QWidget, QSizePolicy, QScrollArea, QGroupBox, QLineEdit, QListView, QGraphicsSimpleTextItem, QTextEdit, QLCDNumber, QSlider, QFormLayout, QHBoxLayout,
                               QMessageBox, QPushButton, QVBoxLayout, QApplication, QInputDialog, QProgressBar, QTextBrowser)

# * Third Party Imports --------------------------------------------------------------------------------->
from peewee import Field, DoesNotExist, IntegrityError, prefetch

# * Gid Imports ----------------------------------------------------------------------------------------->
from gidapptools import get_logger
from gidapptools.general_helper.conversion import seconds2human
from gidapptools.general_helper.string_helper import StringCase, StringCaseConverter
from gidapptools.general_helper.color.color_item import Color

# * Local Imports --------------------------------------------------------------------------------------->
from antistasi_logbook.errors import InsufficientDataPointsError
from antistasi_logbook.data.sqf_syntax_data import SQF_BUILTINS_REGEX
from antistasi_logbook.storage.models.models import Mod, Server, GameMap, LogFile, ModLink, LogRecord, RecordClass, Version, Message, LogLevel, ArmaFunction, ArmaFunctionAuthorPrefix
from antistasi_logbook.utilities.gui_utilities import make_line
from antistasi_logbook.gui.widgets.image_viewer import (ArmaSide, HighResMapImageWidget, TownMapSymbolImageItem, AirportMapSymbolImageItem,
                                                        FactoryMapSymbolImageItem, OutpostMapSymbolImageItem, SeaportMapSymbolImageItem, ResourceMapSymbolImageItem)
from antistasi_logbook.gui.widgets.stats_viewer import StatType, StatsWindow
from antistasi_logbook.gui.widgets.collapsible_widget import CollapsibleGroupBox
from antistasi_logbook.gui.widgets.data_view_widget.data_view import DataView
from antistasi_logbook.gui.resources.antistasi_logbook_resources_accessor import AllResourceItems

# * Type-Checking Imports --------------------------------------------------------------------------------->
if TYPE_CHECKING:
    from gidapptools.gid_config.interface import GidIniConfig
    from antistasi_logbook.records.antistasi_records import ChangingSidesRecord
    from antistasi_logbook.backend import Backend
    from antistasi_logbook.gui.application import AntistasiLogbookApplication
    from antistasi_logbook.records.base_record import BaseRecord

# endregion [Imports]

# region [TODO]


# endregion [TODO]

# region [Logging]


# endregion [Logging]

# region [Constants]

THIS_FILE_DIR = Path(__file__).parent.absolute()
log = get_logger(__name__)
# endregion [Constants]

VIEW_ABLE_ITEMS_TYPE = Union["AbstractRecord", "LogRecord", "LogFile", "Server"]


class ModModel(QAbstractTableModel):
    ace_compat_regex = re.compile(r"ace.*compat", re.IGNORECASE)
    column_names_to_exclude = {"id", "full_path", "mod_hash_short", "mod_hash", "marked", "comments", "link", "mod_dir"}

    def __init__(self, mods: Iterable[Mod], parent: Optional[PySide6.QtCore.QObject] = None) -> None:
        super().__init__(parent=parent)
        if not mods:
            self.mods = []
        else:
            self.mods = sorted(mods, key=self._sort_func)
        self.columns: tuple[Field] = self.get_columns()

    def _sort_func(self, in_mod: Mod):
        return (in_mod.cleaned_name == "utility",
                in_mod.official is True,
                in_mod.default is True,
                self.ace_compat_regex.search(in_mod.name) is not None,
                "rhs" in in_mod.name.casefold(),
                "3cb" in in_mod.name.casefold(),
                "cup" in in_mod.name.casefold(),
                in_mod.cleaned_name
                )

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

        if role == Qt.ItemDataRole.FontRole:
            font = QFont()
            font.setPointSizeF(font.pointSizeF() * 0.8)
            return font

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

    def __repr__(self) -> str:
        """
        Basic Repr
        !REPLACE!
        """
        return f'{self.__class__.__name__}'


class ModDataView(DataView):
    def __init__(self, mod: Mod, parent: Optional[PySide6.QtWidgets.QWidget] = None, show_none: bool = False) -> None:
        super().__init__(parent=parent, show_none=show_none, title=mod.get_data("name"))
        self.mod = mod

        for column in sorted(list(self.mod.get_meta().sorted_fields), key=self.column_sorter):
            self.add_row(column.verbose_name or column.name, getattr(self.mod, column.name))
        for extra_name in ["cleaned_name", "link"]:
            self.add_row(extra_name, getattr(self.mod, extra_name))

        all_log_files_values = self.get_all_log_file_values()
        if all_log_files_values is not None:
            self.add_row("log_files", all_log_files_values)

    def get_all_log_file_values(self) -> Optional[tuple["LogFile"]]:
        all_log_files = self.mod.get_log_files()
        if all_log_files is None:
            return None

        sorted_log_files = sorted(all_log_files, key=lambda x: (-x.server_id, x.modified_at), reverse=True)

        return [f"{i.server.name}/{i}" for i in sorted_log_files]

    def column_sorter(self, column: Field) -> int:
        if column.name.casefold() == "marked":
            return -1
        return len(column.verbose_name or column.name)

    def __repr__(self) -> str:
        """
        Basic Repr
        !REPLACE!
        """
        return f'{self.__class__.__name__}'


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

    def __repr__(self) -> str:
        """
        Basic Repr
        !REPLACE!
        """
        return f'{self.__class__.__name__}'


class ValueLineEdit(QLineEdit):
    style_sheet_data = """
    """

    def __init__(self, text: str = None, parent=None):
        super().__init__(text, parent)
        self.setReadOnly(True)
        self.setAlignment(Qt.AlignCenter)
        self.setProperty("display_only", True)
        # self.setStyleSheet(self.style_sheet_data)

    def sizeHint(self) -> PySide6.QtCore.QSize:
        font_metrics = self.fontMetrics()
        return font_metrics.size(Qt.TextSingleLine, self.text())

    def __repr__(self) -> str:
        """
        Basic Repr
        !REPLACE!
        """
        return f'{self.__class__.__name__}'


class MapSymbolImageItem(pg.ImageItem):

    def __init__(self, other_image=None, image=None, **kargs):
        super().__init__(image, **kargs)
        self.other_image = other_image
        self.setToolTip("A House")

    def mouseClickEvent(self, ev):
        if ev.button() == Qt.MouseButton.LeftButton:

            pop_up = QMessageBox.information(None, "Housy", str((self.scenePos().x(), self.scenePos().y())), QMessageBox.Ok)
        return super().mouseClickEvent(ev)


class LabeledSlider(QSlider):

    def get_px_of_secondary_slider_pos(self):
        return [
            QStyle.sliderPositionFromValue(self.minimum(), self.maximum(), idx, self.width())
            for idx in range(self.minimum(), self.maximum() + 1, self.tickInterval())
        ]

    def paintEvent(self, ev: QPaintEvent) -> None:
        super().paintEvent(ev)
        pix_secondary_slider_pos = self.get_px_of_secondary_slider_pos()

        if len(pix_secondary_slider_pos) > 0:
            painter = QPainter(self)
            orig_font_size = font = painter.font().pointSize()
            font = painter.font()
            font.setPointSize(int(font.pointSize() * 0.90))
            painter.setFont(font)
            for x_pos in pix_secondary_slider_pos:
                text = datetime.fromtimestamp(QStyle.sliderValueFromPosition(self.minimum(), self.maximum(), x_pos, self.width()), tz=timezone.utc).isoformat(sep=" ", timespec="seconds").split("+")[0]

                text_height = painter.fontMetrics().boundingRect(text).height()

                text_width = painter.fontMetrics().boundingRect(text).width()

                painter.drawText(QPoint(x_pos, 0), text)

            font.setPointSize(orig_font_size)
            painter.setFont(font)

    def sizeHint(self) -> QSize:
        orig_size_hint = super().sizeHint()
        return QSize(orig_size_hint.width(), int(orig_size_hint.height() * 1.25))


class GameMapThumbnail(QLabel):

    def __init__(self, game_map: GameMap, campaign_id: int = None, parent=None):
        super().__init__(parent=parent)
        self.game_map = game_map
        self.campaign_id = campaign_id
        self.has_low_res_image = self.game_map.has_low_res_image()
        self.has_high_res_image = self.game_map.has_high_res_image()
        self.original_cursor = self.cursor()

        if self.has_low_res_image is True:
            pixmap = self.game_map.map_image_low_resolution.to_qpixmap()
            self.setPixmap(pixmap)

        if self.has_high_res_image is True:
            self.setToolTip("Click to open High-Res Map image")
        self.high_res_game_map_window: QWidget = None

    @ property
    def has_content(self) -> bool:
        return self.has_low_res_image

    def collect_states(self) -> None:
        record_class = RecordClass.get(name="ChangingSidesRecord")

        query = prefetch(LogRecord.select(LogRecord).join_from(LogRecord, LogFile).where((LogFile.campaign_id == self.campaign_id)).where((LogRecord.record_class_id == record_class.id)).order_by(LogRecord.recorded_at), LogFile, RecordClass, Message, LogLevel)

        data = [i.to_record_class() for i in query]
        try:
            start = min(i.recorded_at for i in data)
            end = max(i.recorded_at for i in data)
        except ValueError:
            start = data[0].recorded_at
            end = data[-1].recorded_at

        for item in data:
            item: "ChangingSidesRecord"
            time = item.recorded_at.timestamp()
            side = ArmaSide(item.side.upper())

            name = item.location_name
            desc = ""
            self.high_res_game_map_window._map_symbols[name]._time_states[time] = (side, desc)
        return start, end

    def mousePressEvent(self, event: PySide6.QtGui.QMouseEvent) -> None:

        if event.button() == Qt.LeftButton:
            if self.game_map.coordinates is not None and self.campaign_id is not None:
                data = self.game_map.coordinates
                self.high_res_game_map_window = HighResMapImageWidget(self.game_map.map_image_high_resolution, (data["world_size"], data["world_size"]), name=self.game_map.full_name).setup()

                for item in data["map_marker"]:
                    name = item["name"]
                    if name.casefold().startswith("outpost"):
                        klass = OutpostMapSymbolImageItem
                        side = ArmaSide.WEST
                    elif name.casefold().startswith("resource"):
                        klass = ResourceMapSymbolImageItem
                        side = ArmaSide.WEST
                    elif name.casefold().startswith("factory"):
                        klass = FactoryMapSymbolImageItem
                        side = ArmaSide.WEST
                    elif name.casefold().startswith("airport"):
                        klass = AirportMapSymbolImageItem
                        side = ArmaSide.WEST
                    elif name.casefold().startswith("seaport"):
                        klass = SeaportMapSymbolImageItem
                        side = ArmaSide.WEST
                    else:
                        klass = TownMapSymbolImageItem
                        side = ArmaSide.WEST
                    marker_item = klass(item["name"], item["x"], item["y"], side=side)
                    marker_item.refresh()
                    self.high_res_game_map_window.set_map_symbol(marker_item)
                    marker_item.refresh()

                start, end = self.collect_states()
                self.high_res_game_map_window.show()
                self._comb_window = QWidget()
                self._comb_window.setLayout(QVBoxLayout())
                comb_label = QLabel()
                comb_label.setAlignment(Qt.AlignHCenter)
                self.high_res_game_map_window.map_symbol_changed.connect(comb_label.setText, type=Qt.ConnectionType.UniqueConnection)
                self._comb_window.layout().addWidget(comb_label)
                self._comb_window.layout().addWidget(self.high_res_game_map_window)
                current_time_label = QLabel()
                current_time_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                comb_slider = LabeledSlider(Qt.Orientation.Horizontal)
                comb_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
                comb_slider.setTickInterval(int((end - start).total_seconds() / 20))
                comb_slider.setTracking(True)

                comb_slider.setMinimum(int(start.timestamp()))

                comb_slider.setMaximum(int(end.timestamp()))
                comb_slider.valueChanged.connect(lambda x: current_time_label.setText(datetime.fromtimestamp(x, tz=timezone.utc).isoformat(sep=" ", timespec="seconds").split("+")[0]))
                comb_slider.valueChanged.connect(lambda x: comb_slider.setToolTip(datetime.fromtimestamp(x, tz=timezone.utc).isoformat(sep=" ", timespec="seconds").split("+")[0]))
                comb_slider.valueChanged.connect(self.high_res_game_map_window.state_to_timestamp)
                self._comb_window.layout().addWidget(current_time_label)
                self._comb_window.layout().addWidget(comb_slider)

                self._comb_window.show()

        return super().mousePressEvent(event)

    def enterEvent(self, event: PySide6.QtGui.QEnterEvent) -> None:
        if self.has_high_res_image is True:
            self.setCursor(Qt.PointingHandCursor)
        return super().enterEvent(event)

    def leaveEvent(self, event: PySide6.QtCore.QEvent) -> None:
        if self.has_high_res_image is True:
            self.setCursor(self.original_cursor)
        return super().leaveEvent(event)


class GameMapValue(QWidget):

    def __init__(self, game_map=GameMap, campaign_id: int = None, parent=None):
        super().__init__(parent=parent)
        self.setLayout(QVBoxLayout())
        self.game_map = game_map
        self.game_map_label = ValueLineEdit(self.game_map.full_name)
        self.layout.addWidget(self.game_map_label)
        self.game_map_thumbnail = GameMapThumbnail(self.game_map, campaign_id=campaign_id)

        self.collapsible_box = CollapsibleGroupBox(text="Thumbnail", content=self.game_map_thumbnail, parent=self)
        self.collapsible_box.no_content_text = "NO THUMBNAIL"
        self.collapsible_box.set_expanded(False)
        self.layout.addWidget(self.collapsible_box)
        self.game_map_thumbnail.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)

    def _get_game_map_pixmap(self) -> Optional[QPixmap]:
        game_map_bytes = self.game_map.map_image_low_resolution
        if game_map_bytes is None:
            return
        pixmap = QPixmap()
        pixmap.loadFromData(game_map_bytes)
        return pixmap

    def setFont(self, arg__1: Union[PySide6.QtGui.QFont, str, Sequence[str]]) -> None:
        super().setFont(arg__1)
        self.game_map_label.setFont(arg__1)
        self.collapsible_box.setFont(arg__1)

    @ property
    def layout(self) -> QVBoxLayout:
        return super().layout()

    def __repr__(self) -> str:
        """
        Basic Repr
        !REPLACE!
        """
        return f'{self.__class__.__name__}'


class ListFormLabel(QLabel):

    def __init__(self, text: str):
        super().__init__(text)
        font = self.font()
        font.setBold(True)

        self._original_font_size: int = int(font.pointSize())
        self._font_size_factor: float = 1.0
        self.setFont(font)

    def set_font_size_factor(self, factor: float) -> None:
        font = self.font()
        font.setPointSize(int(self._original_font_size * factor))
        self.setFont(font)
        self.repaint()

    def sizeHint(self) -> PySide6.QtCore.QSize:
        font_metrics = self.fontMetrics()
        return font_metrics.size(Qt.TextSingleLine, self.text())


class ListFormLayout(QVBoxLayout):

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self._font_size_factor: float = 0.85

    def set_font_size_factor(self, factor: float):
        self._font_size_factor = factor
        for i in range(self.count()):
            item = self.itemAt(i).widget()
            log.info("type: %r, name: %r, %r", type(item), item.objectName(), item)
            if isinstance(item, ListFormLabel):
                item.set_font_size_factor(self.font_size_factor)

    @ property
    def font_size_factor(self) -> float:
        return self._font_size_factor

    def addRow(self, label: Union[str, QLabel], value: QWidget):
        _label = self.make_label(label)
        _value = self.modify_value(value)
        self.addWidget(_label)
        self.addWidget(_value)

    def modify_value(self, in_value: QWidget) -> QWidget:
        font = in_value.font()

        font.setPointSizeF(font.pointSizeF() * self.font_size_factor)
        in_value.setFont(font)
        in_value.repaint()

        return in_value

    def make_label(self, label: Union[str, QLabel]) -> QLabel:
        if isinstance(label, str):
            label = ListFormLabel(label)
        elif not isinstance(label, ListFormLabel):
            log.debug(type(label))
            log.debug(label.text())
            label = ListFormLabel(text=label.text())

        label.setAlignment(Qt.AlignCenter)

        label.set_font_size_factor(self.font_size_factor)
        return label

    def add_line(self):
        self.addWidget(make_line("horizontal"))

    def sizeHint(self) -> QSize:
        orig_size_hint = super().sizeHint()

        heights = []
        widths = []
        for i in range(self.count()):
            item = self.itemAt(i)
            item_size_hint = item.sizeHint()
            heights.append(item_size_hint.height())
            widths.append(item_size_hint.width())

        height = sum(heights) if heights else orig_size_hint.height()
        width = max(widths) if widths else orig_size_hint.width()

        return QSize(width, height)


class BaseDetailWidget(QScrollArea):

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setWidgetResizable(True)
        self.setLayout(ListFormLayout())

    @ property
    def layout(self) -> ListFormLayout:
        return super().layout()

    @ property
    def app(self) -> "AntistasiLogbookApplication":
        return QApplication.instance()

    @ property
    def backend(self) -> "Backend":
        return self.app.backend

    @ property
    def config(self) -> "GidIniConfig":
        return self.backend.config

    def __repr__(self) -> str:
        """
        Basic Repr
        !REPLACE!
        """
        return f'{self.__class__.__name__}'


class ServerDetailWidget(BaseDetailWidget):

    def __init__(self, server: Server, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent=parent)
        self.server = server

        self.name_value = ValueLineEdit(self.server.name, parent=self)

        self.layout.addRow("Name", self.name_value)

        self.amount_log_files_value = QLCDNumber(3, self)
        self.amount_log_files_value.setSegmentStyle(QLCDNumber.Flat)
        self.amount_log_files_value.display(self.server.get_amount_log_files())
        self.layout.addRow("Amount Log-Files", self.amount_log_files_value)

        self.remote_path_value = ValueLineEdit(self.server.remote_path.as_posix(), parent=self)

        self.layout.addRow("Remote Path", self.remote_path_value)

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
            item = conc_record_class.from_model_dict(record, foreign_key_cache=self.backend.foreign_key_cache, log_file=log_file)
            x.append(item.recorded_at.timestamp())
            y.append(item.stats.get("Players"))

        return x, y

    def __repr__(self) -> str:
        """
        Basic Repr
        !REPLACE!
        """
        return f'{self.__class__.__name__}'


class LogFileDetailWidget(BaseDetailWidget):

    def __init__(self, log_file: LogFile, parent: Optional[PySide6.QtWidgets.QWidget] = None) -> None:
        super().__init__(parent=parent)
        self.log_file = log_file

        self.name_value = ValueLineEdit(self.log_file.name, parent=self)

        self.layout.addRow("Name", self.name_value)

        self.modified_at_value = ValueLineEdit(text=self.app.format_datetime(self.log_file.modified_at))
        self.layout.addRow("Modified at", self.modified_at_value)
        if self.log_file.time_frame is None:
            time_frame_string = "-"
        else:
            time_frame_string = f"{self.app.format_datetime(self.log_file.time_frame.start)} until {self.app.format_datetime(self.log_file.time_frame.end)}"

        self.time_frame_value = ValueLineEdit(text=time_frame_string)
        self.layout.addRow("Time-Frame", self.time_frame_value)

        if self.log_file.time_frame is not None:
            time_frame_duration_string = seconds2human(self.log_file.time_frame.delta.total_seconds(), min_unit="second")
        else:
            time_frame_duration_string = None
        self.duration_value = ValueLineEdit(text=time_frame_duration_string)
        self.layout.addRow("Duration", self.duration_value)

        self.server_value = ValueLineEdit(text=self.log_file.server.name, parent=self)
        self.layout.addRow("Server", self.server_value)
        if self.log_file.game_map is not None:
            self.game_map_value = GameMapValue(self.log_file.game_map, self.log_file.campaign_id, self)
            self.layout.addRow("Game Map", self.game_map_value)

        try:
            version_string = str(self.log_file.version)

        except DoesNotExist:
            log.debug("failing version id is %r for log_file %r", self.log_file.version_id, self.log_file)
            log.debug("result of querying by id: %r", Version.get_by_id(self.log_file.version_id))
            version_string = ""

        self.version_value = ValueLineEdit(text=version_string, parent=self)
        self.layout.addRow("Version", self.version_value)

        self.campaign_id_value = ValueLineEdit(text=str(self.log_file.campaign_id), parent=self)
        self.layout.addRow("Campaign ID", self.campaign_id_value)

        self.amount_log_records_value = ValueLineEdit(text=str(self.log_file.amount_log_records), parent=self)
        self.layout.addRow("Amount Log-Records", self.amount_log_records_value)

        amount_average_players = self.log_file.average_players_per_hour[0]
        self.amount_average_players_value = ValueLineEdit(text=str(amount_average_players), parent=self)
        if amount_average_players < 10:
            self.amount_average_players_value.setStyleSheet("background-color: rgba(255, 0, 0, 100)")
        elif amount_average_players < 15:
            self.amount_average_players_value.setStyleSheet("background-color: rgba(242, 169, 0 ,100)")
        elif amount_average_players >= 15:
            self.amount_average_players_value.setStyleSheet("background-color: rgba(0, 255, 0, 100)")
        self.layout.addRow("Amount average Players per Hour", self.amount_average_players_value)

        self.amount_headless_clients_value = ValueLineEdit(text=str(self.log_file.amount_headless_clients), parent=self)
        self.layout.addRow("Amount Headless Clients", self.amount_headless_clients_value)

        self.mod_set_value = ValueLineEdit(text=str(log_file.mod_set), parent=self)
        self.layout.addRow("Mod-Set", self.mod_set_value)

        self.mods_value = ModView(self)

        model = ModModel(self.log_file.get_mods())
        self.mods_value.setModel(model)

        self.layout.addRow("Mods", self.mods_value)

        self.mods_value.doubleClicked.connect(self.open_mod_link, type=Qt.ConnectionType.UniqueConnection)
        self.header_text_value = QTextEdit()
        self.header_text_value.setReadOnly(True)
        self.header_text_value.setLineWrapMode(QTextEdit.NoWrap)
        self.header_text_value.setPlainText(self.log_file.header_text)
        self.header_text_value.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Maximum)
        self.header_text_box = CollapsibleGroupBox("Show Header Text", self.header_text_value, self)
        self.header_text_box.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        self.header_text_box.set_expanded(False)
        self.layout.addRow('Header Text', self.header_text_box)

        self.get_stats_button = QPushButton(AllResourceItems.stats_icon_2_image.get_as_icon(), "Get Stats")
        self.layout.addWidget(self.get_stats_button)
        self.get_stats_button.pressed.connect(partial(self.show_stats, "log_file"), type=Qt.ConnectionType.UniqueConnection)

        self.get_campaign_stats_button = QPushButton(AllResourceItems.stats_icon_2_image.get_as_icon(), "Get Campaign Stats")
        self.layout.addWidget(self.get_campaign_stats_button)
        self.get_campaign_stats_button.pressed.connect(partial(self.show_stats, "campaign"), type=Qt.ConnectionType.UniqueConnection)
        if self.log_file.campaign_id is None:
            self.get_campaign_stats_button.setEnabled(False)

        self.repaint()

    def show_stats(self, scope: Literal["log_file", "campaign", "ressource_check"]):

        if scope == "log_file":
            all_stats = self.log_file.get_stats()
            all_log_files = (self.log_file,)
            name = f"Log File: {self.log_file.name.upper()}"
            obj_name = f"{self.log_file.name}_stats_window"
            visible_item_names = {"ServerFPS"}
        elif scope == "campaign":
            all_stats, all_log_files = self.log_file.get_campaign_stats()
            name = f"Campaign {self.log_file.campaign_id}"
            obj_name = f"{self.log_file.campaign_id}_stats_window"
            visible_item_names = {"ServerFPS"}

        if len(all_stats) < 2:
            raise InsufficientDataPointsError(len(all_stats), 2)

        temp_plot_widget = StatsWindow(stat_type=StatType.PERFORMANCE, stat_data=all_stats, title=name, visible_item_names=visible_item_names)
        for _log_file in all_log_files:
            temp_plot_widget.add_marked_records(_log_file.get_marked_records())
        temp_plot_widget.setObjectName(obj_name)
        self.app.extra_windows.add_window(temp_plot_widget)
        temp_plot_widget.show()

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

    def __repr__(self) -> str:
        """
        Basic Repr
        !REPLACE!
        """
        return f'{self.__class__.__name__}'


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

    def __repr__(self) -> str:
        """
        Basic Repr
        !REPLACE!
        """
        return f'{self.__class__.__name__}'


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

    def __repr__(self) -> str:
        """
        Basic Repr
        !REPLACE!
        """
        return f'{self.__class__.__name__}'


def _re_pattern_converter(in_data: Union[str, re.Pattern]):
    if isinstance(in_data, str):
        return re.compile(in_data)
    return in_data


class AbstractSyntaxHighlightRule(ABC):
    suffix_remove_pattern = re.compile("HighlightRule", re.IGNORECASE)

    @ property
    def name(self) -> str:
        return StringCaseConverter.convert_to(self.suffix_remove_pattern.sub("", self.__class__.__name__), StringCase.SNAKE)

    @ property
    def style_format(self) -> QTextFormat:
        return self._style_format

    @ property
    def pattern(self) -> re.Pattern:
        return self._pattern

    def apply(self, text: str, highlighter: "MessageHighlighter") -> Generator[tuple[int, int, QTextFormat], None, None]:
        for match in self.pattern.finditer(text):
            start, end = match.span()

            yield start, end - start, self.style_format

    def __repr__(self) -> str:
        """
        Basic Repr
        !REPLACE!
        """
        return f'{self.__class__.__name__}'


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

        self._pattern = re.compile(r"^◘.*")
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
            self.raw_text = self.record.get_data("message")
            self.setPlainText(self.record.get_data("message"))

    def set_record(self, record: "AbstractRecord"):
        self.record = record
        self.raw_text = record.get_data("message")
        self.setPlainText(self.raw_text)

    @ property
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

    def __repr__(self) -> str:
        """
        Basic Repr
        !REPLACE!
        """
        return f'{self.__class__.__name__}'


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
        self.get_stats_button.pressed.connect(self.get_stats, type=Qt.ConnectionType.UniqueConnection)

        self.amount_selected = 1
        self.amount_selected_value = ValueLineEdit(str(self.amount_selected))
        self.layout.addRow("amount items selected", self.amount_selected_value)

    def on_multiple_items_selected(self, indexes: list):
        self.set_amount_selected(len(indexes))

    def on_single_item_selected(self, item):
        self.set_amount_selected(1)

    def set_amount_selected(self, amount: int = 1):
        self.amount_selected = amount
        self.amount_selected_value.setText(str(self.amount_selected))

    def get_stats(self):
        all_stats = self.record.log_file.get_stats()
        if len(all_stats) < 2:
            raise InsufficientDataPointsError(len(all_stats), 2)

        self.temp_plot_widget = StatsWindow(stat_type=StatType.PERFORMANCE, stat_data=all_stats, title=self.record.log_file.name.upper, visible_item_names={"ServerFPS"})
        self.temp_plot_widget.add_current_record(self.record)

        self.temp_plot_widget.add_marked_records(self.record.log_file.get_marked_records())
        self.temp_plot_widget.show()

    def sizeHint(self) -> PySide6.QtCore.QSize:
        return self.layout.sizeHint()

    def __repr__(self) -> str:
        """
        Basic Repr
        !REPLACE!
        """
        return f'{self.__class__.__name__}'


# region [Main_Exec]
if __name__ == '__main__':
    pass

# endregion [Main_Exec]
