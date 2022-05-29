"""
WiP.

Soon.
"""

# region [Imports]

# * Standard Library Imports ---------------------------------------------------------------------------->
import random
from gidapptools.general_helper.enums import MiscEnum
from math import ceil, log as math_log, sqrt, exp
from typing import TYPE_CHECKING, Any, Union, Iterable, Optional
from pathlib import Path
from datetime import datetime
from statistics import mean, median
from functools import cached_property
from threading import RLock
from enum import Enum, auto, unique, Flag
# * Qt Imports --------------------------------------------------------------------------------------->
import PySide6
import pyqtgraph as pg
from types import MethodType
from PySide6 import QtCore
from PySide6.QtGui import QPen, QFont, QColor, QAction
from PySide6.QtCore import Qt, Slot, QSize, Signal
from PySide6.QtWidgets import QLabel, QWidget, QSpinBox, QMenu, QSizePolicy, QGroupBox, QStatusBar, QFormLayout, QScrollArea, QGridLayout, QHBoxLayout, QMainWindow, QPushButton, QVBoxLayout, QApplication, QDoubleSpinBox
from PySide6.QtSvg import QSvgRenderer
# * Gid Imports ----------------------------------------------------------------------------------------->
from gidapptools import get_logger
from antistasi_logbook.gui.diagram.abstract_stats_model import PerformanceStatsModel
from gidapptools.gidapptools_qt.helper.misc import center_window
# * Local Imports --------------------------------------------------------------------------------------->
from antistasi_logbook.records.enums import MessageFormat

# * Type-Checking Imports --------------------------------------------------------------------------------->
if TYPE_CHECKING:
    from antistasi_logbook.gui.application import AntistasiLogbookApplication
    from antistasi_logbook.records.base_record import BaseRecord

# endregion[Imports]

# region [TODO]


# endregion [TODO]

# region [Logging]


# endregion[Logging]

# region [Constants]

THIS_FILE_DIR = Path(__file__).parent.absolute()
log = get_logger(__name__)
# endregion[Constants]
# "white"
COLORS = ["red", "tan", "blue", "gold", "gray", "lime", "peru", "pink", "plum", "teal", "brown", "coral", "green",
          "olive", "wheat", "bisque", "indigo", "maroon", "orange", "purple", "sienna", "tomato", "yellow"] * 10

# 'arrow_up', 'arrow_right', 'arrow_down', 'arrow_left','crosshair'
SYMBOLS = ['s', 't', "o", "t1", 't2', 't3', 'd', '+', "p", 'h', 'star'
           ]
random.shuffle(SYMBOLS)
SYMBOLS = tuple((['x'] + SYMBOLS) * 10)


class CustomSampleItem(pg.ItemSample):
    changed_vis = Signal(object)

    def set_visibility(self, value: bool):
        self.item.setVisible(value)

        self.changed_vis.emit(self.item)

    def mouseClickEvent(self, event):
        """Use the mouseClick event to toggle the visibility of the plotItem
        """
        if event.button() == QtCore.Qt.MouseButton.LeftButton:
            visible = self.item.isVisible()
            self.set_visibility(not visible)

        event.accept()
        self.update()


class ColorSelector(QGroupBox):
    color_changed = Signal(str, QColor)

    def __init__(self, color_config_name: str, parent=None):
        super().__init__(parent=parent)
        self.color_config_name = color_config_name
        self.setTitle("Colors")
        self.setLayout(QFormLayout())
        self.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Preferred)
        self.layout.setVerticalSpacing(3)
        self.key_map: dict[pg.ColorButton, str] = {}

    def add_key(self, key: str):
        color_selector = pg.ColorButton(padding=5)
        color_selector.setMinimumSize(QSize(25, 25))
        self.layout.addRow(key, color_selector)
        color = self.app.color_config.get(self.color_config_name, key.replace(" ", "_"), default=None)
        if color is not None:
            color_selector.setColor(color)
        color_selector.sigColorChanged.connect(self.color_change_proxy)
        self.key_map[color_selector] = key

    @Slot(object)
    def color_change_proxy(self, button: pg.ColorButton):
        key = self.key_map[button]
        color = button.color()
        self.app.color_config.set(self.color_config_name, key.replace(" ", "_"), color, create_missing_section=True)
        self.color_changed.emit(key, color)

    @property
    def layout(self) -> QFormLayout:
        return super().layout()

    @property
    def app(self) -> "AntistasiLogbookApplication":
        return QApplication.instance()


class PaddingOptionsBox(QGroupBox):
    y_padding_factor_changed = Signal(float)
    x_padding_factor_changed = Signal(float)

    default_y_padding_factor: float = 0.35
    default_x_padding_factor: float = 0.10

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setLayout(QFormLayout())
        self.y_padding_factor_selector = QDoubleSpinBox(self)
        self.y_padding_factor_selector.setDecimals(2)
        self.y_padding_factor_selector.setValue(self.default_y_padding_factor)

        self.y_padding_factor_selector.setSingleStep(0.05)
        self.y_padding_factor_selector.valueChanged.connect(self.y_padding_factor_changed.emit)
        self.layout.addRow("Y", self.y_padding_factor_selector)

        self.x_padding_factor_selector = QDoubleSpinBox(self)
        self.x_padding_factor_selector.setDecimals(2)
        self.x_padding_factor_selector.setValue(self.default_x_padding_factor)
        self.x_padding_factor_selector.setSingleStep(0.05)
        self.x_padding_factor_selector.valueChanged.connect(self.x_padding_factor_changed.emit)
        self.layout.addRow("X", self.x_padding_factor_selector)

    @property
    def layout(self) -> QFormLayout:
        return super().layout()

    @property
    def y_padding_factor(self) -> float:
        return round(self.y_padding_factor_selector.value(), 2)

    @property
    def x_padding_factor(self) -> float:
        return round(self.x_padding_factor_selector.value(), 2)


class ControlBox(QGroupBox):
    request_change_extra_lines_hidden = Signal(bool)

    def __init__(self, color_config_name: str, parent=None):
        super().__init__(parent=parent)
        self.setLayout(QVBoxLayout())
        self.form_layout = QFormLayout()
        self.extra_layout = QGridLayout()
        self.extra_layout.setAlignment(Qt.AlignHCenter | Qt.AlignTop)
        self.layout.addLayout(self.form_layout)
        self.layout.addLayout(self.extra_layout)
        self.layout.addStretch(2)
        self.line_width_selector = QSpinBox()
        self.line_width_selector.setMinimum(1)
        self.line_width_selector.setMaximum(99)

        self.form_layout.addRow("Line width", self.line_width_selector)

        self.hide_extra_lines_toggle = QPushButton()
        self.hide_extra_lines_toggle.setText("Hide")

        self.hide_extra_lines_toggle.active = False

        self.hide_extra_lines_toggle.clicked.connect(self.on_hide_extra_lines_pressed)
        self.form_layout.addRow("Hide extra Lines", self.hide_extra_lines_toggle)

        self.hide_symbols_button = QPushButton("Hide")
        self.hide_symbols_button.active = False
        self.hide_symbols_button.clicked.connect(self.on_hide_symbols_pressed)
        self.form_layout.addRow("Hide Symbols", self.hide_symbols_button)

        self.hide_legend_button = QPushButton("Hide")
        self.hide_legend_button.active = True
        self.hide_legend_button.clicked.connect(self.on_hide_legend_pressed)
        self.form_layout.addRow("Hide Legend", self.hide_legend_button)
        self.on_hide_symbols_pressed()

        self.show_all_button = QPushButton("Show all Items")
        self.hide_all_button = QPushButton("Hide all Items")

        self.form_layout.addWidget(self.show_all_button)
        self.form_layout.addWidget(self.hide_all_button)

        self.padding_factor_select_box = PaddingOptionsBox(self)
        self.form_layout.addRow("Axis Padding Factors", self.padding_factor_select_box)
        self.color_box = ColorSelector(color_config_name=color_config_name)
        self.color_box_scroll_area = QScrollArea()
        self.color_box_scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self.color_box_scroll_area.setWidget(self.color_box)
        self.color_box_scroll_area.setWidgetResizable(True)
        self.color_box_scroll_area.resize(self.color_box.sizeHint())

        self.extra_layout.addWidget(self.color_box_scroll_area)

    def sizeHint(self) -> QSize:
        return self.layout.totalSizeHint()

    @ property
    def layout(self) -> QVBoxLayout:
        return super().layout()

    def on_hide_symbols_pressed(self, checked: bool = None):
        log.debug("%r was clicked", self.hide_symbols_button)

        if self.hide_symbols_button.active is False:
            log.debug("switching active state from %r to %r", self.hide_symbols_button.active, True)
            self.hide_symbols_button.active = True
            self.hide_symbols_button.setStyleSheet("background-color: grey")

            self.hide_symbols_button.setText("Show")

        else:
            log.debug("switching active state from %r to %r", self.hide_symbols_button.active, False)
            self.hide_symbols_button.active = False
            self.hide_symbols_button.setDown(False)
            self.hide_symbols_button.setText("Hide")
            self.hide_symbols_button.setStyleSheet("")

    @ Slot(bool)
    def on_hide_legend_pressed(self, checked: bool = None):
        log.debug("%r was clicked", self.hide_legend_button)

        if self.hide_legend_button.active is False:
            log.debug("switching active state from %r to %r", self.hide_legend_button.active, True)
            self.hide_legend_button.active = True
            self.hide_legend_button.setStyleSheet("background-color: grey")

            self.hide_legend_button.setText("Show")

        else:
            log.debug("switching active state from %r to %r", self.hide_legend_button.active, False)
            self.hide_legend_button.active = False
            self.hide_legend_button.setDown(False)
            self.hide_legend_button.setText("Hide")
            self.hide_legend_button.setStyleSheet("")

    @ Slot(bool)
    def on_hide_extra_lines_pressed(self, checked: bool = None):
        log.debug("%r was clicked", self.hide_extra_lines_toggle)

        if self.hide_extra_lines_toggle.active is False:
            log.debug("switching active state from %r to %r", self.hide_extra_lines_toggle.active, True)
            self.hide_extra_lines_toggle.active = True
            self.hide_extra_lines_toggle.setStyleSheet("background-color: grey")

            self.hide_extra_lines_toggle.setText("Show")

        else:
            log.debug("switching active state from %r to %r", self.hide_extra_lines_toggle.active, False)
            self.hide_extra_lines_toggle.active = False
            self.hide_extra_lines_toggle.setDown(False)
            self.hide_extra_lines_toggle.setText("Hide")
            self.hide_extra_lines_toggle.setStyleSheet("")
        log.debug("emiting %r with value %r", self.request_change_extra_lines_hidden, self.hide_extra_lines_toggle.active)
        self.request_change_extra_lines_hidden.emit(self.hide_extra_lines_toggle.active)


class CrosshairDisplayBar(QStatusBar):
    y_value_display_sig_places = 2
    x_fixed_num_chars = {"zero_padding_to": 23, "center_amount": 25}
    y_fixed_num_chars = {"zero_padding_to": 2, "center_amount": 10}

    def __init__(self, parent: Optional[PySide6.QtWidgets.QWidget] = None) -> None:
        super().__init__(parent=parent)
        # self.setLayoutDirection(Qt.LeftToRight)
        self.x_display = QLabel()
        self.x_display.setText(" " * self.x_fixed_num_chars["center_amount"])

        self.y_display = QLabel()
        self.y_display.setText(" " * self.y_fixed_num_chars["center_amount"])
        self.x_widget = QWidget()
        self.x_widget.setLayout(QFormLayout())
        self.x_widget.layout().addRow("Time: ", self.x_display)

        self.y_widget = QWidget()
        self.y_widget.setLayout(QFormLayout())
        self.y_widget.layout().addRow("Value: ", self.y_display)

    @ cached_property
    def display_font(self) -> QFont:
        font = QFont()
        font.setFamily("Lucida Console")
        font.setStyleHint(QFont.Monospace)
        return font

    def setup(self) -> "CrosshairDisplayBar":
        self.addWidget(self.x_widget)
        self.addWidget(self.y_widget)
        for display in [self.x_display, self.y_display]:
            display.setFont(self.display_font)

        return self

    @ property
    def app(self) -> "AntistasiLogbookApplication":
        return QApplication.instance()

    @ Slot(float)
    def set_x_value(self, value: float):

        date_time = datetime.utcfromtimestamp(value)

        text = self.app.format_datetime(date_time)
        # if len(text) < self.x_fixed_num_chars["zero_padding_to"]:
        #     text += "0" * (self.x_fixed_num_chars["zero_padding_to"] - len(text))
        self.x_display.setText(text.center(self.x_fixed_num_chars["center_amount"]))

    @ Slot(float)
    def set_y_value(self, value: float):
        rounded_value = round(value, self.y_value_display_sig_places)
        text = str(rounded_value)
        if '.' not in text:
            text += '.0'
        # if len(text) < self.y_fixed_num_chars["zero_padding_to"]:
        #     text += "0" * (self.y_fixed_num_chars["zero_padding_to"] - len(text))
        self.y_display.setText(text.center(self.y_fixed_num_chars["center_amount"]))


class StatType(Enum):
    def __new__(cls, color_config_name):
        obj = object.__new__(cls)
        obj.color_config_name = color_config_name
        return obj
    PERFORMANCE = ("stats",)


class StatsLegend(pg.LegendItem):
    def __init__(self, size=None, offset=None, horSpacing=25, verSpacing=0, pen=None, brush=None, labelTextColor=None, frame=True, labelTextSize='9pt', colCount=1, sampleType=None, **kwargs):
        super().__init__(size, offset, horSpacing, verSpacing, pen, brush, labelTextColor, frame, labelTextSize, colCount, sampleType, **kwargs)
        self._visible = True

    def show_all(self):
        for item, label in self.items:
            item.set_visibility(True)

    def hide_all(self):
        for item, label in self.items:
            item.set_visibility(False)

    def change_visibility(self):
        if self._visible is True:
            for item in self.items:
                item[0].setVisible(False)
                item[1].setVisible(False)

            self._visible = False

        else:
            for item in self.items:
                item[0].setVisible(True)
                item[1].setVisible(True)
            self._visible = True


class StatsWindow(QMainWindow):
    close_signal = Signal(QMainWindow)
    color_config_name = "stats"

    grid_alpha: int = int(255 / 5)

    mouse_y_pos_changed = Signal(float)
    mouse_x_pos_changed = Signal(float)

    vis_items_lock = RLock()

    def __init__(self, stat_type: StatType, stat_data: list[dict[str, Any]], title: str, visible_item_names: Iterable[str] = None, parent=None):
        super().__init__(parent=parent)
        self.stat_type = StatType(stat_type)
        self.setCentralWidget(QWidget(self))
        self.centralWidget().setLayout(QHBoxLayout())
        self.plot_widget = pg.PlotWidget(axisItems={'bottom': pg.DateAxisItem(utcOffset=0)}, title=title)
        self.plots: dict[str, pg.PlotItem] = {}
        self.control_box = ControlBox(color_config_name=self.stat_type.color_config_name)
        self.stat_data = sorted(stat_data, key=lambda x: x.get("timestamp"), reverse=False)
        self.available_colors = COLORS.copy()
        random.shuffle(self.available_colors)
        self.legend = StatsLegend((80, 80), 50, colCount=ceil(len(self.keys) / 10), sampleType=CustomSampleItem, labelTextSize="8pt")

        self.visible_item_names = set(visible_item_names) if visible_item_names is not None else set()

        self.marked_records: dict["BaseRecord", tuple[pg.InfLineLabel, pg.InfiniteLine]] = {}

        self.setup()

    @ property
    def layout(self) -> QHBoxLayout:
        return self.centralWidget().layout()

    @ cached_property
    def keys(self) -> list[str]:
        keys = []
        items = self.stat_data
        if "side" in items[0]:
            items = sorted(self.stat_data, key=lambda x: x.get("side"))
        for item in items:
            for k in sorted(item.keys(), key=lambda x: (x == "ServerFPS", x.casefold()), reverse=True):
                if k not in {"timestamp", "side"} and k not in keys:
                    keys.append(k)
        return keys

    @ cached_property
    def all_timestamps(self) -> list[float]:
        return [i.get("timestamp").timestamp() for i in self.stat_data]

    @ cached_property
    def x_padding_seconds(self) -> float:
        seconds_diff = max(self.all_timestamps) - min(self.all_timestamps)

        _out = seconds_diff * self.control_box.padding_factor_select_box.x_padding_factor
        return _out

    @ cached_property
    def min_timestamp(self) -> int:
        return min(self.all_timestamps) - self.x_padding_seconds

    @ cached_property
    def max_timestamp(self) -> int:
        return max(self.all_timestamps) + self.x_padding_seconds

    @ property
    def max_value(self) -> float:
        with self.vis_items_lock:
            data = []
            for item in self.stat_data:
                for k, v in item.items():
                    if k in self.visible_item_names and v is not None:
                        data.append(v)
            if not data:
                max_data = 10
            else:
                max_data = max(data)
            return ceil(max_data + (max_data * self.control_box.padding_factor_select_box.y_padding_factor))

    @ property
    def app(self) -> "AntistasiLogbookApplication":
        return QApplication.instance()

    @ cached_property
    def view_box(self) -> pg.ViewBox:
        return self.plot_widget.getPlotItem().getViewBox()

    @ property
    def x_axis(self) -> pg.AxisItem:
        return self.plot_widget.getPlotItem().getAxis("bottom")

    @ property
    def y_axis(self) -> pg.AxisItem:
        return self.plot_widget.getPlotItem().getAxis("left")

    @ cached_property
    def plot_item(self) -> pg.PlotItem:
        return self.plot_widget.getPlotItem()

    def setup(self):
        self.general_setup()
        self.plot_setup()
        self.control_setup()
        self.resize(QSize(self.size().width() * 1.5, self.size().height()))

    def general_setup(self):
        self.resize(1500, 1000)
        self.status_bar = CrosshairDisplayBar(self).setup()
        self.mouse_x_pos_changed.connect(self.status_bar.set_x_value)
        self.mouse_y_pos_changed.connect(self.status_bar.set_y_value)
        self.setStatusBar(self.status_bar)
        self.control_box.setFixedWidth(450)
        self.layout.addWidget(self.control_box, 0)
        self.layout.addWidget(self.plot_widget, 2)
        self.tick_font = self._create_tick_font()

    def _create_tick_font(self) -> QFont:
        font: QFont = self.app.font()
        font.setFamily("Lucida Console")

        font.setWeight(QFont.Light)
        font.setStyleHint(QFont.Monospace)
        font.setStyleStrategy(QFont.PreferQuality)

        return font

    def plot_setup(self):
        self.vertical_crosshair = pg.InfiniteLine(angle=90, movable=False, pen=pg.mkPen({"style": Qt.DashDotDotLine, "cosmetic": True, "color": (255, 255, 255)}))
        self.horizontal_crosshair = pg.InfiniteLine(angle=0, movable=False, pen=pg.mkPen({"style": Qt.DashDotDotLine, "cosmetic": True, "color": (255, 255, 255)}))
        self.plot_widget.addItem(self.horizontal_crosshair, ignoreBounds=True)
        self.plot_widget.addItem(self.vertical_crosshair, ignoreBounds=True)
        self.vertical_crosshair.setVisible(True)
        self.horizontal_crosshair.setVisible(True)

        self.y_axis.setTickSpacing(10, 1)
        self.y_axis.setGrid(self.grid_alpha)
        self.y_axis.setTickFont(self.tick_font)
        self.x_axis.setGrid(self.grid_alpha)
        self.x_axis.setTickFont(self.tick_font)
        self.plot_widget.setMouseEnabled(True)

        self.view_box.setLimits(xMin=self.min_timestamp, xMax=self.max_timestamp, yMin=0, yMax=self.max_value)
        self.view_box.setXRange(min=self.min_timestamp, max=self.max_timestamp)
        self.view_box.setYRange(min=0, max=self.max_value)

        self.legend.setParentItem(self.plot_widget.getPlotItem())
        self._symbols_visible = True
        self._symbol_size = 8

        for idx, key in enumerate(self.keys):
            indexes_and_values = [(idx, i.get(key)) for idx, i in enumerate(self.stat_data) if i.get(key) is not None]
            data = ([self.all_timestamps[i[0]] for i in indexes_and_values], [i[1] for i in indexes_and_values])
            color = self.app.color_config.get(self.color_config_name, key.replace(" ", "_"), default=self.available_colors[idx])
            symbol_brush = pg.mkBrush(color)
            symbol_brush_color = symbol_brush.color()
            symbol_brush_color.setAlpha(155)
            symbol_brush.setColor(symbol_brush_color)

            item = self.plot_widget.plot(*data, pen=pg.mkPen(color, width=1), antialias=False, name=key, autoDownsample=True, symbol=SYMBOLS[idx], symbolSize=self._symbol_size, symbolBrush=symbol_brush, symbolPen=pg.mkPen((255, 255, 255, 155), width=1))
            item.idx = idx
            self.legend.addItem(item, key)
            self.plots[key] = item
            if item.name().casefold() != "serverfps":
                item.setVisible(False)

            for sample, label in self.legend.items:
                sample.changed_vis.connect(self.change_limits)

            self.plot_widget.sceneObj.sigMouseMoved.connect(self.mouse_moved_in_plot)

        self.view_box.setAspectLocked(None)

        self.view_box.setMouseEnabled(x=True, y=False)
        self.change_symbol_vis()

    #     self.view_box.sigRangeChangedManually.connect(self.on_scroll)

    # def on_scroll(self, *args):
    #     orig_time = self.max_timestamp - self.min_timestamp
    #     new_min, new_max = self.view_box.viewRange()[0]
    #     new_time = new_max - new_min

    #     _factor = math_log(orig_time, new_time)
    #     log.debug("orig_time: %r, new_time:%r, factor:%r", orig_time, new_time, _factor)
    #     new_symbol_size = ceil(self._symbol_size * _factor)
    #     for plot in self.plots.values():
    #         plot.setSymbolSize(new_symbol_size)

    def change_limits(self, item: pg.PlotDataItem = None):
        if item is not None:
            name = item.name()
            is_visible = item.isVisible()
            if is_visible is True:
                with self.vis_items_lock:
                    self.visible_item_names.add(name)
            elif name in self.visible_item_names:
                with self.vis_items_lock:
                    self.visible_item_names.remove(name)
        max_y = self.max_value
        if max_y is None:
            return

        if max_y >= 300_000:
            self.y_axis.setTickSpacing(100_000, 10_000)

        elif max_y >= 30_000:
            self.y_axis.setTickSpacing(10_000, 1000)

        elif max_y >= 3000:
            self.y_axis.setTickSpacing(1000, 100)
        elif max_y >= 300:
            self.y_axis.setTickSpacing(100, 10)
        else:
            self.y_axis.setTickSpacing(10, 1)
        self.view_box.setLimits(xMin=self.min_timestamp, xMax=self.max_timestamp, yMin=0, yMax=max_y)
        self.view_box.setYRange(min=0, max=max_y)
        self.view_box.setXRange(min=self.min_timestamp, max=self.max_timestamp)
        for label, line in self.marked_records.values():
            line.viewTransformChanged()
            label.viewTransformChanged()

    def mouse_moved_in_plot(self, pos) -> None:

        if self.plot_widget.sceneBoundingRect().contains(pos):
            mousePoint = self.view_box.mapSceneToView(pos)
            x = mousePoint.x()
            y = mousePoint.y()
            self.vertical_crosshair.setPos(x)
            self.horizontal_crosshair.setPos(y)
            self.mouse_x_pos_changed.emit(x)
            self.mouse_y_pos_changed.emit(y)

            record_box_found = False

            for record, items in self.marked_records.items():
                if items[0].boundingRect().contains(items[0].mapFromView(mousePoint)):

                    self.status_bar.showMessage(record.message)
                    record_box_found = True
                    break
            if record_box_found is False:
                self.status_bar.clearMessage()

    def y_factor_changed(self, factor: float):
        self.change_limits()

    def x_factor_changed(self, factor: float):
        del self.x_padding_seconds
        del self.min_timestamp
        del self.max_timestamp

        self.change_limits()

    def control_setup(self):
        self.control_box.line_width_selector.setValue(1)
        self.control_box.line_width_selector.valueChanged.connect(self.change_pen_widths)
        for key in self.keys:
            self.control_box.color_box.add_key(key)
        self.control_box.color_box.color_changed.connect(self.change_pen_color)
        self.control_box.request_change_extra_lines_hidden.connect(self.change_hide_extra_lines)
        self.control_box.padding_factor_select_box.y_padding_factor_changed.connect(self.y_factor_changed)
        self.control_box.padding_factor_select_box.x_padding_factor_changed.connect(self.x_factor_changed)
        self.control_box.hide_legend_button.pressed.connect(self.legend.change_visibility)
        self.control_box.show_all_button.pressed.connect(self.legend.show_all)
        self.control_box.hide_all_button.pressed.connect(self.legend.hide_all)
        self.control_box.hide_symbols_button.pressed.connect(self.change_symbol_vis)

    def change_symbol_vis(self):
        if self._symbols_visible is True:
            for plot in self.plots.values():
                plot.setSymbol(None)
                self._symbols_visible = False

        else:
            for plot in self.plots.values():
                plot.setSymbol(SYMBOLS[plot.idx])
                self._symbols_visible = True

    @ Slot(bool)
    def change_hide_extra_lines(self, hide: bool):
        log.debug("change_hide_extra_lines was requested with parameter hide: %r", hide)
        for label, line in self.marked_records.values():

            label.setVisible(not hide)

            line.setVisible(not hide)

    @ Slot(float)
    def change_pen_widths(self, new_width: float):
        for item in self.plots.values():
            new_pen = item.opts["pen"]
            if not isinstance(new_pen, QPen):
                continue
            new_pen.setWidth(new_width)
            item.setPen(new_pen)

    @ Slot(str, QColor)
    def change_pen_color(self, key: str, color: QColor):
        item = self.plots[key]
        new_pen = item.opts["pen"]
        new_pen.setColor(color)
        item.setPen(new_pen)

    def add_record_label_line(self,
                              record: "BaseRecord",
                              line_color: tuple[int] = (255, 255, 255, 255),
                              line_width: int = 3,
                              text: str = "",
                              html: str = None,
                              text_color: Union[tuple[int], QColor] = (200, 200, 200, 255),
                              border: Union[str, QPen] = None,
                              fill: tuple[int] = None,
                              moveable: bool = False,
                              position: float = 0.5,
                              anchors: list[tuple[int]] = None,
                              text_anchor: tuple[int] = (0, 0),
                              text_angle: int = 0,
                              rotateAxis=None) -> tuple[pg.InfLineLabel, pg.InfiniteLine]:

        line = pg.InfiniteLine(pos=record.recorded_at.timestamp(), angle=90, pen=pg.mkPen({"color": line_color, "width": line_width}), movable=False)

        self.plot_widget.addItem(line)
        if text_color is None:
            text_color = text_color

        label = pg.InfLineLabel(line=line, text=text, movable=moveable, angle=text_angle, position=position, html=html, color=text_color, border=border, fill=fill, anchors=anchors, anchor=text_anchor, rotateAxis=rotateAxis)

        return label, line

    def add_marked_records(self, marked_records: Iterable["BaseRecord"]):
        for record in marked_records:
            try:
                text = record.get_formated_message(MessageFormat.SHORT) + '\n' + record.pretty_recorded_at
            except Exception as e:
                log.error(e, exc_info=True)
                text = "-"
            label, line = self.add_record_label_line(record,
                                                     line_color=(255, 255, 0, 255),
                                                     text_color=(25, 25, 25, 255),
                                                     line_width=1,
                                                     text=text,
                                                     border='w',
                                                     fill=(200, 200, 0, 200),
                                                     position=0.8,
                                                     text_angle=-45,
                                                     text_anchor=(1, 0),
                                                     anchors=[(0, 0), (0, 0)])

            self.marked_records[record] = (label, line)

    def add_current_record(self, record: "BaseRecord"):
        label, line = self.add_record_label_line(record,
                                                 line_color=(255, 0, 0, 255),
                                                 text_color=(25, 25, 25, 255),
                                                 line_width=3,
                                                 text=f"Current Record\n{record.pretty_recorded_at}",
                                                 border="w",
                                                 fill=(200, 0, 0, 200),
                                                 position=0.85,
                                                 text_angle=-45,
                                                 text_anchor=(1, 0),
                                                 anchors=[(0, 0), (0, 0)])

        self.marked_records[record] = (label, line)

    def show(self) -> None:
        self.app.extra_windows.add_window(self)
        center_window(self, allow_window_resize=False)
        return super().show()

    def closeEvent(self, event: PySide6.QtGui.QCloseEvent) -> None:
        self.close_signal.emit(self)
        return super().closeEvent(event)


class LabeledAxisItem(pg.AxisItem):

    def __init__(self, names: list[str], **kwargs):
        self.names = names
        super().__init__(**kwargs)

    def tickStrings(self, values, scale, spacing):
        return self.names


class AvgMapPlayersPlotWidget(pg.PlotWidget):
    close_signal = Signal(pg.PlotWidget)

    def __init__(self, data: list[dict[str, float]], parent=None, background='default', plotItem=None, **kargs):
        self.data = data
        self.tick_font = self._create_tick_font()
        self.x_axis_tick_font = self._create_tick_font()
        self.x_axis_tick_font.setPointSize(int(self.x_axis_tick_font.pointSize() * 0.75))
        self.available_colors = COLORS.copy()
        random.shuffle(self.available_colors)
        self.colors = [QColor(*i, 200) for i in [
            (112, 112, 168),
            (114, 255, 110),
            (254, 167, 110),
            (112, 214, 255),
            (238, 110, 255),
            (225, 254, 120),
            (165, 191, 162),
            (212, 185, 254),
            (195, 109, 119),
            (136, 140, 255),
            (177, 253, 209),
            (113, 160, 110),
            (252, 210, 183),
            (219, 146, 184),
            (110, 233, 181),
        ]]

        tick_dict = {idx * 10: i["game_map"] for idx, i in enumerate(self.data)}
        y_axis = pg.AxisItem(orientation="left")
        y_axis.setTickSpacing(levels=[(1, 0), (0.1, 0)])
        y_axis.setGrid(255 // 5)
        y_axis.setTickFont(self.tick_font)
        x_axis = pg.AxisItem(orientation="bottom")
        x_axis.setTicks([tick_dict.items()])
        x_axis.setTickFont(self.x_axis_tick_font)
        x_axis.setStyle(tickTextWidth=45)
        super().__init__(parent, background, plotItem, axisItems={"bottom": x_axis, "left": y_axis}, **kargs)

        self.plot_item = pg.BarGraphItem(x=list(tick_dict.keys()), height=[i["avg_players"] for i in self.data], width=5, brushes=self.colors)
        self.addItem(self.plot_item)

        view_box: pg.ViewBox = self.getPlotItem().getViewBox()
        x_max = max(tick_dict.keys()) * 1.1
        y_max = max([i["avg_players"] for i in self.data]) * 1.1
        view_box.setLimits(xMin=-10, xMax=x_max, yMin=0, yMax=y_max)

        # mean_y = mean(i["avg_players"] for i in self.data)
        # self.mean_line = pg.InfiniteLine(mean_y, angle=0, movable=False, pen=pg.mkPen({"style": Qt.DashDotDotLine, "cosmetic": True, "color": (255, 255, 255)}),label="mean")
        # self.addItem(self.mean_line)
        # median_y = median(i["avg_players"] for i in self.data)
        # self.median_line = pg.InfiniteLine(median_y, angle=0, movable=False, pen=pg.mkPen({"style": Qt.DashLine, "cosmetic": True, "color": (100, 255, 100)}), label="median")
        # self.addItem(self.median_line)

    def _create_tick_font(self) -> QFont:
        font: QFont = self.app.font()
        font.setFamily("Lucida Console")

        font.setWeight(QFont.Light)
        font.setStyleHint(QFont.Monospace)
        font.setStyleStrategy(QFont.PreferQuality)

        return font

    @ property
    def app(self) -> "AntistasiLogbookApplication":
        return QApplication.instance()

    def show(self) -> None:
        self.app.extra_windows.add_window(self)
        return super().show()

    def closeEvent(self, event: PySide6.QtGui.QCloseEvent) -> None:
        self.close_signal.emit(self)
        return super().closeEvent(event)


# region[Main_Exec]
if __name__ == '__main__':
    pass

# endregion[Main_Exec]
