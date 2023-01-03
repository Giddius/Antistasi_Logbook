"""
WiP.

Soon.
"""

# region [Imports]

# * Standard Library Imports ---------------------------------------------------------------------------->
import re
import sys
import random
from enum import Enum, auto
from typing import TYPE_CHECKING, Optional
from pathlib import Path
from functools import cached_property

# * Qt Imports --------------------------------------------------------------------------------------->
import pyqtgraph as pg
from PySide6.QtCore import Qt, QSize, QTimer, Signal
from PySide6.QtWidgets import QMessageBox

# * Third Party Imports --------------------------------------------------------------------------------->
from numpy.typing import ArrayLike

# * Gid Imports ----------------------------------------------------------------------------------------->
from gidapptools import get_logger

# * Local Imports --------------------------------------------------------------------------------------->
from antistasi_logbook.utilities.local_image import LocalImage
from antistasi_logbook.data.map_images.map_symbols import get_map_symbol_as_np_array

if sys.version_info >= (3, 11):
    from typing import Self
else:
    from typing_extensions import Self
# * Type-Checking Imports --------------------------------------------------------------------------------->
if TYPE_CHECKING:
    pass

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


class ArmaSide(Enum):
    CIV = auto()
    DESTROYED = auto()
    GUER = auto()
    WEST = auto()
    EAST = auto()

    def __str__(self) -> str:
        if self is ArmaSide.CIV:
            return "None"

        return self.name


class BaseMapSymbolImageItem(pg.ImageItem):
    colored_image: dict[ArmaSide:ArrayLike] = {}
    tool_tip_template: str = "x: {x!s} - y: {y!s} -- <b>{name!s}</b> - <u>{side!s}</u> - <i>{description!s}</i>"

    def __init__(self, name: str, x: float, y: float, description: str = None, side: ArmaSide = ArmaSide.CIV, **kwargs):
        self._name = name
        self._arma_x = x
        self._arma_y = y
        self._description = description
        self._side = side
        self._extra_data: dict[str, object] = {}
        self._time_states: dict[float, tuple["ArmaSide", str]] = {}
        super().__init__(**kwargs)

    @property
    def side(self) -> ArmaSide:
        return self._side

    @property
    def name(self) -> str:
        return self._name

    @property
    def description(self) -> Optional[str]:
        return self._description

    @property
    def arma_x(self) -> float:
        return self._arma_x

    @property
    def arma_y(self) -> float:
        return self._arma_y

    @property
    def arma_coordinates(self) -> tuple[float, float]:
        return (self.arma_x, self.arma_y)

    def set_side(self, side: ArmaSide = None):
        if side is not None and side not in self.colored_image:
            raise ValueError(f"'side' can only be one of {list(self.colored_image)!r}, not {side!r}")
        side = side or ArmaSide.CIV
        self._side = side
        self.refresh()

    def set_description(self, description: str = None):
        self._description = description

    def _refresh_image(self):
        self.setImage(self.colored_image[self.side])

    def _refresh_tool_tip(self):
        tool_tip = self.tool_tip_template.format(name=self.name.replace("_", " ").title(), x=self.arma_x, y=self.arma_y, side=self.side, description=self.description or f"Was captured at ??? by ??? ({self.side!s})")
        self.setToolTip(tool_tip)

    def refresh(self):
        self._refresh_image()
        self._refresh_tool_tip()
        self.update()

    def show_message_box(self):
        QMessageBox.information(None, self.name, self.toolTip(), QMessageBox.Ok)

    def mouseClickEvent(self, ev):
        if ev.button() == Qt.MouseButton.LeftButton:
            self.show_message_box()
        return super().mouseClickEvent(ev)


class TownMapSymbolImageItem(BaseMapSymbolImageItem):
    colored_image: dict[ArmaSide: ArrayLike] = {ArmaSide.DESTROYED: get_map_symbol_as_np_array("DESTROYED_TOWN", new_alpha=0.75),
                                                ArmaSide.GUER: get_map_symbol_as_np_array("GUER_TOWN", new_alpha=0.75),
                                                ArmaSide.WEST: get_map_symbol_as_np_array("WEST_TOWN", new_alpha=0.75)}

    def __init__(self, name: str, x: float, y: float, description: str = None, side: ArmaSide = ArmaSide.WEST, **kwargs):
        super().__init__(name.removeprefix("city_").removeprefix("vill_"), x, y, description, side, **kwargs)


class SeaportMapSymbolImageItem(BaseMapSymbolImageItem):
    colored_image: dict[ArmaSide: ArrayLike] = {ArmaSide.GUER: get_map_symbol_as_np_array("GUER_SEAPORT", new_alpha=0.75),
                                                ArmaSide.WEST: get_map_symbol_as_np_array("WEST_SEAPORT", new_alpha=0.75),
                                                ArmaSide.EAST: get_map_symbol_as_np_array("EAST_SEAPORT", new_alpha=0.75)}
    _number_regex: re.Pattern = re.compile(r"seaport_(?P<number>\d+)")

    def __init__(self, name: str, x: float, y: float, description: str = None, side: ArmaSide = ArmaSide.WEST, **kwargs):
        super().__init__(name, x, y, description, side, **kwargs)
        self._extra_data["number"] = self._parse_number()

    def _parse_number(self) -> int:
        match = self._number_regex.match(self.name)
        if match:
            return int(match.group("number"))

        return 0


class AirportMapSymbolImageItem(BaseMapSymbolImageItem):
    colored_image: dict[ArmaSide: ArrayLike] = {ArmaSide.GUER: get_map_symbol_as_np_array("GUER_AIRPORT", new_alpha=0.75),
                                                ArmaSide.WEST: get_map_symbol_as_np_array("WEST_AIRPORT", new_alpha=0.75),
                                                ArmaSide.EAST: get_map_symbol_as_np_array("EAST_AIRPORT", new_alpha=0.75)}

    _number_regex: re.Pattern = re.compile(r"airport_(?P<number>\d+)")

    def __init__(self, name: str, x: float, y: float, description: str = None, side: ArmaSide = ArmaSide.WEST, **kwargs):
        super().__init__(name, x, y, description, side, **kwargs)
        self._extra_data["number"] = self._parse_number()

    def _parse_number(self) -> int:
        match = self._number_regex.match(self.name.casefold())
        if match:
            return int(match.group("number"))

        return 0


class FactoryMapSymbolImageItem(BaseMapSymbolImageItem):
    colored_image: dict[ArmaSide: ArrayLike] = {ArmaSide.GUER: get_map_symbol_as_np_array("GUER_FACTORY", new_alpha=0.75),
                                                ArmaSide.WEST: get_map_symbol_as_np_array("WEST_FACTORY", new_alpha=0.75),
                                                ArmaSide.EAST: get_map_symbol_as_np_array("EAST_FACTORY", new_alpha=0.75)}

    _number_regex: re.Pattern = re.compile(r"factory_(?P<number>\d+)")

    def __init__(self, name: str, x: float, y: float, description: str = None, side: ArmaSide = ArmaSide.WEST, **kwargs):
        super().__init__(name, x, y, description, side, **kwargs)
        self._extra_data["number"] = self._parse_number()

    def _parse_number(self) -> int:
        match = self._number_regex.match(self.name.casefold())
        if match:
            return int(match.group("number"))

        return 0


class ResourceMapSymbolImageItem(BaseMapSymbolImageItem):
    colored_image: dict[ArmaSide: ArrayLike] = {ArmaSide.GUER: get_map_symbol_as_np_array("GUER_RESOURCE", new_alpha=0.75),
                                                ArmaSide.WEST: get_map_symbol_as_np_array("WEST_RESOURCE", new_alpha=0.75),
                                                ArmaSide.EAST: get_map_symbol_as_np_array("EAST_RESOURCE", new_alpha=0.75)}

    _number_regex: re.Pattern = re.compile(r"resource_(?P<number>\d+)")

    def __init__(self, name: str, x: float, y: float, description: str = None, side: ArmaSide = ArmaSide.WEST, **kwargs):
        super().__init__(name, x, y, description, side, **kwargs)
        self._extra_data["number"] = self._parse_number()

    def _parse_number(self) -> int:
        match = self._number_regex.match(self.name.casefold())
        if match:
            return int(match.group("number"))

        return 0


class OutpostMapSymbolImageItem(BaseMapSymbolImageItem):
    colored_image: dict[ArmaSide: ArrayLike] = {ArmaSide.GUER: get_map_symbol_as_np_array("GUER_OUTPOST", new_alpha=0.75),
                                                ArmaSide.WEST: get_map_symbol_as_np_array("WEST_OUTPOST", new_alpha=0.75),
                                                ArmaSide.EAST: get_map_symbol_as_np_array("EAST_OUTPOST", new_alpha=0.75)}
    _number_regex: re.Pattern = re.compile(r"outpost_(?P<number>\d+)")

    def __init__(self, name: str, x: float, y: float, description: str = None, side: ArmaSide = ArmaSide.WEST, **kwargs):
        super().__init__(name, x, y, description, side, **kwargs)
        self._extra_data["number"] = self._parse_number()

    def _parse_number(self) -> int:
        match = self._number_regex.match(self.name.casefold())
        if match:
            return int(match.group("number"))

        return 0


class HighResMapImageWidget(pg.GraphicsLayoutWidget):
    map_symbol_changed = Signal(str)
    finished_run = Signal()

    def __init__(self,
                 high_res_local_image: LocalImage,
                 arma_size: tuple[float, float],
                 name: str = None,
                 parent=None,
                 **kwargs):
        super().__init__(parent=parent, show=False, **kwargs)
        self._high_res_local_image = high_res_local_image
        self._arma_size = arma_size
        self._name = name or self._high_res_local_image.name.title()
        self._view: pg.GraphicsView = None
        self._high_res_image: pg.ImageItem = None
        self._map_symbols: dict[str, BaseMapSymbolImageItem] = {}
        self._last_changed_idx: int = -1
        self.update_timer = QTimer(self)
        self.update_timer.setInterval(1 * 1_000)
        self.update_timer.setTimerType(Qt.CoarseTimer)
        self.update_timer.timeout.connect(self._mix)

    def _setup_view(self):
        self._view: pg.GraphicsView = self.addViewBox()
        self._view.setMenuEnabled(False)
        self._view.setAspectLocked()
        self._high_res_image = pg.ImageItem()
        self._high_res_image.setImage(self._high_res_local_image.to_numpy_array(-90))
        self._view.addItem(self._high_res_image)

    def setup(self) -> Self:
        self._setup_view()
        self.setWindowTitle(self._name)
        return self

    @ cached_property
    def size_multiplier(self) -> float:
        arma_size = QSize(*self._arma_size)
        real_size = QSize(self._high_res_image.width(), self._high_res_image.height())
        multiplier_w = self._high_res_image.width() / self._arma_size[0]
        multiplier_h = self._high_res_image.height() / self._arma_size[1]
        if multiplier_w != multiplier_h:
            log.debug("width multiplier (%r) is not the same as height multiplies (%r)", multiplier_w, multiplier_h)
        multiplier = (multiplier_w + multiplier_h) / 2
        log.debug("arma_size: %r, real_size: %r, multiplier: %r", arma_size, real_size, multiplier)
        return multiplier

    def _set_map_symbol_pos(self, map_symbol: BaseMapSymbolImageItem):
        real_x = (map_symbol.arma_x * self.size_multiplier) - (map_symbol.width() / 2)
        real_y = (map_symbol.arma_y * self.size_multiplier) - (map_symbol.height() / 2)
        map_symbol.setPos(real_x, real_y)

    def set_map_symbol(self, map_symbol: BaseMapSymbolImageItem):
        if map_symbol.name not in self._map_symbols:
            self._view.addItem(map_symbol)
            self._map_symbols[map_symbol.name] = map_symbol
            self._set_map_symbol_pos(map_symbol)

    def _mix(self, *args, **kwargs):
        map_symbols = sorted(list(self._map_symbols.values()), key=lambda x: (x.arma_x, x.arma_y))
        split_idx = len(map_symbols) // 2
        map_symbols = map_symbols[:split_idx] + sorted(map_symbols[split_idx:], key=lambda x: (x.arma_y, x.arma_x))
        try:
            self._last_changed_idx += 1

            map_symbol = map_symbols[self._last_changed_idx]
            if isinstance(map_symbol, TownMapSymbolImageItem):
                new_side = random.choices([ArmaSide.GUER, ArmaSide.DESTROYED], weights=(0.95, 0.05), k=1)[0]
                map_symbol.set_side(new_side)
                self.map_symbol_changed.emit(f"{map_symbol.name}, {new_side.name}, x={map_symbol.arma_x}, y={map_symbol.arma_y}")
            else:
                map_symbol.set_side(ArmaSide.GUER)
                self.map_symbol_changed.emit(f"{map_symbol.name}, {ArmaSide.GUER.name}, x={map_symbol.arma_x}, y={map_symbol.arma_y}")
        except IndexError:
            self.finished_run.emit()
            for map_symbol in map_symbols:
                if isinstance(map_symbol, TownMapSymbolImageItem):
                    map_symbol.set_side(ArmaSide.WEST)
                else:
                    map_symbol.set_side(random.choices([ArmaSide.WEST, ArmaSide.EAST], weights=(0.8, 0.2), k=1)[0])
                self._last_changed_idx = -1

    def show(self):
        self.resize(QSize(self.screen().size().width() * 0.9, self.screen().size().height() * 0.9))
        self.update_timer.start()
        return super().show()

    def close(self):
        self.update_timer.stop()
        return super().close()


# region[Main_Exec]
if __name__ == '__main__':
    pass

# endregion[Main_Exec]
