"""
WiP.

Soon.
"""

# region [Imports]

# * Standard Library Imports ---------------------------------------------------------------------------->
import random
from math import ceil
from typing import TYPE_CHECKING, Any, Union, Iterable, Optional
from pathlib import Path
from datetime import datetime
from functools import cached_property
from threading import RLock
from statistics import mean, stdev, median
from numpy import average
# * Qt Imports --------------------------------------------------------------------------------------->
import PySide6
import pyqtgraph as pg
from PySide6 import QtCore
from PySide6.QtGui import QPen, QFont, QColor
from PySide6.QtCore import Qt, Slot, QSize, Signal
from PySide6.QtWidgets import QLabel, QWidget, QSpinBox, QGroupBox, QStatusBar, QFormLayout, QGridLayout, QHBoxLayout, QMainWindow, QPushButton, QVBoxLayout, QApplication

# * Gid Imports ----------------------------------------------------------------------------------------->
from gidapptools import get_logger

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
COLORS = ["red", "tan", "blue", "gold", "gray", "lime", "peru", "pink", "plum", "teal", "brown", "coral", "green",
          "olive", "wheat", "white", "bisque", "indigo", "maroon", "orange", "purple", "sienna", "tomato", "yellow"]


class CustomSampleItem(pg.ItemSample):
    changed_vis = Signal(object)

    def mouseClickEvent(self, event):
        """Use the mouseClick event to toggle the visibility of the plotItem
        """
        if event.button() == QtCore.Qt.MouseButton.LeftButton:
            visible = self.item.isVisible()
            self.item.setVisible(not visible)
            self.changed_vis.emit(self.item)
        event.accept()
        self.update()


class ColorSelector(QGroupBox):
    color_changed = Signal(str, QColor)
    color_config_name = "stats"

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setTitle("Colors")
        self.setLayout(QFormLayout())
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
        self.app.color_config.set(self.color_config_name, key.replace(" ", "_"), color)
        self.color_changed.emit(key, color)

    @property
    def layout(self) -> QFormLayout:
        return super().layout()

    @property
    def app(self) -> "AntistasiLogbookApplication":
        return QApplication.instance()


class ControlBox(QGroupBox):
    request_change_extra_lines_hidden = Signal(bool)

    def __init__(self, parent=None):
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

        self.color_box = ColorSelector()
        self.extra_layout.addWidget(self.color_box)

    @property
    def layout(self) -> QVBoxLayout:
        return super().layout()

    @Slot(bool)
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

    @cached_property
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

    @property
    def app(self) -> "AntistasiLogbookApplication":
        return QApplication.instance()

    @Slot(float)
    def set_x_value(self, value: float):

        date_time = datetime.utcfromtimestamp(value)

        text = self.app.format_datetime(date_time)
        # if len(text) < self.x_fixed_num_chars["zero_padding_to"]:
        #     text += "0" * (self.x_fixed_num_chars["zero_padding_to"] - len(text))
        self.x_display.setText(text.center(self.x_fixed_num_chars["center_amount"]))

    @Slot(float)
    def set_y_value(self, value: float):
        rounded_value = round(value, self.y_value_display_sig_places)
        text = str(rounded_value)
        if '.' not in text:
            text += '.0'
        # if len(text) < self.y_fixed_num_chars["zero_padding_to"]:
        #     text += "0" * (self.y_fixed_num_chars["zero_padding_to"] - len(text))
        self.y_display.setText(text.center(self.y_fixed_num_chars["center_amount"]))


class StatsWindow(QMainWindow):
    close_signal = Signal(QMainWindow)
    color_config_name = "stats"
    y_padding_factor = 1.5
    x_padding_factor = 0.125

    mouse_y_pos_changed = Signal(float)
    mouse_x_pos_changed = Signal(float)

    vis_items_lock = RLock()

    def __init__(self, stat_data: list[dict[str, Any]], title: str, parent=None):
        super().__init__(parent=parent)
        self.setCentralWidget(QWidget(self))
        self.centralWidget().setLayout(QHBoxLayout())
        self.plot_widget = pg.PlotWidget(axisItems={'bottom': pg.DateAxisItem(utcOffset=0)}, title=title)
        self.plots: dict[str, pg.PlotItem] = {}
        self.control_box = ControlBox()
        self.stat_data = sorted(stat_data, key=lambda x: x.get("timestamp"), reverse=False)
        self.available_colors = COLORS.copy()
        random.shuffle(self.available_colors)
        self.legend = pg.LegendItem((80, 80), 50, colCount=2, sampleType=CustomSampleItem)
        self.visible_item_names = {"ServerFPS"}
        self.marked_records: dict["BaseRecord", tuple[pg.InfLineLabel, pg.InfiniteLine]] = {}

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

    @cached_property
    def x_padding_seconds(self) -> float:
        seconds_diff = max(self.all_timestamps) - min(self.all_timestamps)

        _out = seconds_diff * self.x_padding_factor
        log.debug("x_padding_seconds = %r from seconds %r and factor %r", _out, seconds_diff, self.x_padding_factor)
        return _out

    @cached_property
    def min_timestamp(self) -> int:
        return min(self.all_timestamps) - self.x_padding_seconds

    @cached_property
    def max_timestamp(self) -> int:
        return max(self.all_timestamps) + self.x_padding_seconds

    @property
    def max_value(self) -> float:
        with self.vis_items_lock:
            data = []
            for item in self.stat_data:
                for k, v in item.items():
                    if k in self.visible_item_names:
                        data.append(v)
            if not data:
                return None
            return ceil(max(data) * self.y_padding_factor)

    @property
    def app(self) -> "AntistasiLogbookApplication":
        return QApplication.instance()

    @cached_property
    def view_box(self) -> pg.ViewBox:
        return self.plot_widget.getPlotItem().getViewBox()

    @property
    def x_axis(self) -> pg.AxisItem:
        return self.plot_widget.getPlotItem().getAxis("bottom")

    @property
    def y_axis(self) -> pg.AxisItem:
        return self.plot_widget.getPlotItem().getAxis("left")

    @cached_property
    def plot_item(self) -> pg.PlotItem:
        return self.plot_widget.getPlotItem()

    def setup(self):
        self.general_setup()
        self.plot_setup()
        self.control_setup()

    def general_setup(self):
        self.resize(1500, 1000)
        self.status_bar = CrosshairDisplayBar(self).setup()
        self.mouse_x_pos_changed.connect(self.status_bar.set_x_value)
        self.mouse_y_pos_changed.connect(self.status_bar.set_y_value)
        self.setStatusBar(self.status_bar)
        self.control_box.setFixedWidth(300)
        self.layout.addWidget(self.control_box, 0)
        self.layout.addWidget(self.plot_widget, 2)

    def plot_setup(self):
        self.vertical_crosshair = pg.InfiniteLine(angle=90, movable=False, pen=pg.mkPen({"style": Qt.DashDotDotLine, "cosmetic": True, "color": (255, 255, 255)}))
        self.horizontal_crosshair = pg.InfiniteLine(angle=0, movable=False, pen=pg.mkPen({"style": Qt.DashDotDotLine, "cosmetic": True, "color": (255, 255, 255)}))
        self.plot_widget.addItem(self.horizontal_crosshair, ignoreBounds=True)
        self.plot_widget.addItem(self.vertical_crosshair, ignoreBounds=True)
        self.vertical_crosshair.setVisible(True)
        self.horizontal_crosshair.setVisible(True)

        self.y_axis.setTickSpacing(10, 1)
        self.plot_widget.setMouseEnabled(True)

        self.view_box.setLimits(xMin=self.min_timestamp, xMax=self.max_timestamp, yMin=0, yMax=self.max_value)
        self.view_box.setXRange(min=self.min_timestamp, max=self.max_timestamp)
        self.view_box.setYRange(min=0, max=self.max_value)

        self.legend.setParentItem(self.plot_widget.getPlotItem())

        for idx, key in enumerate(self.keys):
            data = (self.all_timestamps, [i.get(key) for i in self.stat_data])
            color = self.app.color_config.get(self.color_config_name, key.replace(" ", "_"), default=self.available_colors[idx])

            item = self.plot_widget.plot(*data, pen=pg.mkPen(color, width=1), antialias=False, name=key, autoDownsample=True)
            self.legend.addItem(item, key)
            self.plots[key] = item
            if item.name().casefold() != "serverfps":
                item.setVisible(False)

            for sample, label in self.legend.items:
                sample.changed_vis.connect(self.change_limits)

            self.plot_widget.sceneObj.sigMouseMoved.connect(self.mouse_moved_in_plot)

        self.view_box.setAspectLocked(None)

        self.view_box.setMouseEnabled(x=True, y=False)

    def change_limits(self, item: pg.PlotDataItem):
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

    def control_setup(self):
        self.control_box.line_width_selector.setValue(1)
        self.control_box.line_width_selector.valueChanged.connect(self.change_pen_widths)
        for key in self.keys:
            self.control_box.color_box.add_key(key)
        self.control_box.color_box.color_changed.connect(self.change_pen_color)
        self.control_box.request_change_extra_lines_hidden.connect(self.change_hide_extra_lines)

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
            except:
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

        self.available_colors = COLORS.copy()
        random.shuffle(self.available_colors)
        self.colors = self.available_colors[:len(self.data)]

        tick_dict = {idx * 10: i["game_map"] for idx, i in enumerate(self.data)}
        string_axis = pg.AxisItem(orientation="bottom")
        string_axis.setTicks([tick_dict.items()])
        string_axis.setStyle(tickTextWidth=45)
        super().__init__(parent, background, plotItem, axisItems={"bottom": string_axis}, **kargs)

        self.plot_item = pg.BarGraphItem(x=list(tick_dict.keys()), height=[i["avg_players"] for i in self.data], width=5, brushes=self.colors)
        self.addItem(self.plot_item)

        view_box: pg.ViewBox = self.getPlotItem().getViewBox()
        x_max = max(tick_dict.keys()) * 1.1
        y_max = max([i["avg_players"] for i in self.data]) * 1.1
        view_box.setLimits(xMin=-10, xMax=x_max, yMin=0, yMax=y_max)

    @property
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
