"""
WiP.

Soon.
"""

# region [Imports]

# * Standard Library Imports ---------------------------------------------------------------------------->
import sys
from typing import TYPE_CHECKING, Union, Optional
from pathlib import Path

# * Qt Imports --------------------------------------------------------------------------------------->
from PySide6.QtGui import QPixmap, QIcon
from PySide6.QtWidgets import QTabBar, QWidget, QTabWidget

# * Gid Imports ----------------------------------------------------------------------------------------->
from gidapptools.gid_logger.logger import get_logger
from gidapptools.general_helper.enums import MiscEnum

if sys.version_info >= (3, 11):
    pass
else:
    pass
# * Type-Checking Imports --------------------------------------------------------------------------------->
if TYPE_CHECKING:
    pass

# endregion[Imports]

# region [TODO]


# endregion [TODO]

# region [Logging]


# endregion[Logging]

# region [Constants]

THIS_FILE_DIR = Path(__file__).parent.absolute()
log = get_logger(__name__)
# endregion[Constants]


class MainTabWidgetTabBar(QTabBar):
    ...


class MainTabWidget(QTabWidget):

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setTabBar(MainTabWidgetTabBar())
        self.setTabsClosable(True)
        self.setUpdatesEnabled(True)
        self.tabCloseRequested.connect(self.on_close_request)

        self._fixed_tabs: list[QWidget] = []
        self._normal_tabs: list[QWidget] = []

    @property
    def fixed_tabs(self) -> dict[int:QWidget]:
        return {self.indexOf(i): i for i in self._fixed_tabs}

    @property
    def normal_tabs(self) -> dict[int:QWidget]:
        return {self.indexOf(i): i for i in self._normal_tabs}

    @property
    def all_indexes(self) -> tuple[int]:
        return tuple(list(self.fixed_tabs) + list(self.normal_tabs))

    def _auto_label(self, widget: QWidget) -> str:
        return str(widget)

    def _auto_icon(self, widget: QWidget) -> Optional[Union[QIcon, QPixmap]]:
        return None

    def add_tab(self, widget: QWidget, label: str = MiscEnum.AUTO, icon: Union[QIcon, QPixmap] = MiscEnum.AUTO, fixed: bool = False) -> int:
        if fixed is True:
            return self.add_fixed_tab(widget=widget, label=label, icon=icon)
        else:
            return self.add_normal_tab(widget=widget, label=label, icon=icon)

    def add_normal_tab(self, widget: QWidget, label: str = MiscEnum.AUTO, icon: Union[QIcon, QPixmap] = MiscEnum.AUTO) -> int:
        if label is MiscEnum.AUTO:
            label = self._auto_label(widget=widget)

        if icon is MiscEnum.AUTO:
            icon = self._auto_icon(widget=widget)

        tab_id = self.addTab(*[v for v in (widget, icon, label) if v is not None])
        self._normal_tabs.append(widget)

        self._reorder_tabs()

        return self.indexOf(widget)

    def add_fixed_tab(self, widget: QWidget, label: str = MiscEnum.AUTO, icon: Union[QIcon, QPixmap] = MiscEnum.AUTO) -> int:
        if label is MiscEnum.AUTO:
            label = self._auto_label(widget=widget)

        if icon is MiscEnum.AUTO:
            icon = self._auto_icon(widget=widget)

        tab_id = self.addTab(*[v for v in (widget, icon, label) if v is not None])
        self.tabBar().setTabButton(tab_id, QTabBar.RightSide, None)
        self._fixed_tabs.append(widget)

        self._reorder_tabs()

        return self.indexOf(widget)

    def _reorder_tabs(self) -> None:

        fixed_widgets = tuple(self._fixed_tabs)
        normal_widgets = tuple(self._normal_tabs)

        tab_bar = self.tabBar()
        available_idx = 0
        for fixed_widget in fixed_widgets:
            tab_bar.moveTab(self.indexOf(fixed_widget), available_idx)
            available_idx += 1

        for normal_widget in normal_widgets:
            tab_bar.moveTab(self.indexOf(normal_widget), available_idx)
            available_idx += 1

    def on_close_request(self, tab_index: int):
        if tab_index not in self._fixed_tabs:
            self.removeTab(tab_index)
        self._reorder_tabs()

    def removeTab(self, index: int) -> None:
        self._normal_tabs.remove(self.widget(index))
        super().removeTab(index)

    def __len__(self) -> int:
        return self.tabBar().count()
# region[Main_Exec]


if __name__ == '__main__':
    pass

# endregion[Main_Exec]
