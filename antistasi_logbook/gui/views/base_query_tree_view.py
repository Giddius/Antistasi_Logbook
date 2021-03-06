"""
WiP.

Soon.
"""

# region [Imports]

# * Standard Library Imports ---------------------------------------------------------------------------->
from typing import TYPE_CHECKING, Union, Optional
from pathlib import Path
from concurrent.futures import Future
from functools import cached_property
# * Qt Imports --------------------------------------------------------------------------------------->
import PySide6
from PySide6.QtGui import QIcon, QAction
from PySide6.QtCore import Qt, Slot, QPoint, Signal, QSettings, QModelIndex, QItemSelection, QByteArray
from PySide6.QtWidgets import QMenu, QTreeView, QScrollBar, QHeaderView, QApplication, QAbstractItemView, QToolBar
import pp
# * Gid Imports ----------------------------------------------------------------------------------------->
from gidapptools import get_logger

# * Local Imports --------------------------------------------------------------------------------------->
from antistasi_logbook.gui.views.delegates.universal_delegates import BoolImageDelegate, MarkedImageDelegate
from antistasi_logbook.gui.resources.antistasi_logbook_resources_accessor import AllResourceItems
from antistasi_logbook.gui.widgets.tool_bars import BaseToolBar
# * Type-Checking Imports --------------------------------------------------------------------------------->
if TYPE_CHECKING:
    from antistasi_logbook.backend import Backend
    from antistasi_logbook.gui.application import AntistasiLogbookApplication
    from antistasi_logbook.storage.database import GidSqliteApswDatabase
    from antistasi_logbook.gui.models.base_query_data_model import BaseQueryDataModel

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


class HeaderContextMenuAction(QAction):
    clicked = Signal(int)

    def __init__(self, section: int, icon: QIcon = None, text: str = None, parent=None):
        super().__init__(**{k: v for k, v in dict(icon=icon, text=text, parent=parent).items() if v is not None})
        self.section = section
        self.triggered.connect(self.on_triggered)

    @Slot()
    def on_triggered(self):
        self.clicked.emit(self.section)


class CustomContextMenu(QMenu):

    def __init__(self, title: str = None, parent=None):
        super().__init__(*[i for i in [title, parent] if i is not None])
        self.sub_menus: dict[str, "CustomContextMenu"] = {}

    def get_sub_menu(self, name: str, default=None):
        default = default or self
        return self.sub_menus.get(name.casefold(), default)

    def add_menu(self, name: str, add_to: "CustomContextMenu" = None):
        add_to = add_to or self
        sub_menu = self.__class__(name, add_to)
        self.sub_menus[name.casefold()] = sub_menu
        self.addMenu(sub_menu)
        log.debug("added menu %r to context-menu %r of %r", sub_menu, self, self.parent())

    def add_action(self, action: QAction, sub_menu: Union[str, "CustomContextMenu", QMenu] = None):
        if sub_menu is None:
            sub_menu = self

        elif isinstance(sub_menu, str):
            sub_menu = self.get_sub_menu(sub_menu)
        if not action.parent():
            action.setParent(sub_menu)
        sub_menu.addAction(action)
        log.debug("added action %r to menu %r of context-menu %r of %r", action, sub_menu, self, self.parent())


class BaseQueryTreeView(QTreeView):
    initially_hidden_columns: set[str] = set()
    default_item_size = 150
    _item_size_by_column_name: dict[str, int] = {"id": 75, "marked": 60, "comments": 100}
    default_colum_order = {"marked": 999, "comments": 998}
    single_item_selected = Signal(QModelIndex)
    multiple_items_selected = Signal(list)
    current_items_changed = Signal(list)

    def __init__(self, name: str, icon: QIcon = None, parent=None) -> None:
        super().__init__(parent=parent)
        self.icon = icon

        self.name = "" if name is None else name
        if self.icon is None:
            self.icon = getattr(AllResourceItems, f"{self.name.casefold().replace('-','_').replace(' ','_').replace('.','_')}_tab_icon_image").get_as_icon()
        self.item_size_by_column_name = self._item_size_by_column_name.copy()
        self.original_model: BaseQueryDataModel = None
        self._tool_bar_item: QToolBar = None

    @property
    def app(self) -> "AntistasiLogbookApplication":
        return QApplication.instance()

    @property
    def backend(self) -> "Backend":
        return self.app.backend

    @property
    def database(self) -> "GidSqliteApswDatabase":
        return self.backend.database

    @property
    def header_view(self) -> QHeaderView:
        return self.header()

    @property
    def vertical_scrollbar(self) -> Optional[QScrollBar]:
        return self.verticalScrollBar()

    @property
    def model(self) -> "BaseQueryDataModel":
        return super().model()

    @property
    def column_order(self) -> dict[str, int]:
        settings = QSettings()
        data = settings.value(f"{self.name}_column_order", None)
        if data is None:
            data = {}

        return self.default_colum_order | data

    @property
    def tool_bar_item(self) -> QToolBar:
        if self._tool_bar_item is None:
            self._tool_bar_item = self.create_tool_bar_item()
        return self._tool_bar_item

    def create_tool_bar_item(self) -> QToolBar:
        return BaseToolBar(title=self.name)

    def store_new_column_order(self, logical_index: int, old_visual_index: int, new_visual_index: int):
        column_order = self.column_order
        for idx, column in enumerate(self.model.columns):
            vis_idx = self.header_view.visualIndex(idx)
            column_order[column.name] = vis_idx

        column = self.model.columns[logical_index]
        column_order[column.name] = new_visual_index

        settings = QSettings()
        settings.setValue(f"{self.name}_column_order", column_order)

    @profile
    def setup(self) -> "BaseQueryTreeView":

        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.handle_custom_context_menu)
        self.setSortingEnabled(True)
        self.header_view.setSortIndicatorClearable(True)

        self.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.setup_scrollbars()
        self.setFont(self.app.font())
        self.header_view.setStretchLastSection(False)

        self.extra_setup()
        return self

    def filter(self, use_regex: bool, column_name: str, text: str):
        if self.model:

            self.model.setFilterKeyColumn(self.model.get_column_index(column_name))
            if use_regex is True:
                self.model.setFilterRegularExpression(text)
            else:
                self.model.setFilterFixedString(text)

    def add_free_context_menu_options(self, menu: QMenu):

        return menu

    @Slot(QPoint)
    def handle_custom_context_menu(self, pos: QPoint):
        index = self.indexAt(pos)
        menu = CustomContextMenu(self)
        menu.add_menu("Edit", None)
        if self.app.is_dev is True:
            menu.add_menu("DEBUG")
            force_refresh_view_action = QAction(f"Force Refresh View {self.name!r}")
            force_refresh_view_action.triggered.connect(self.force_refresh)
            menu.add_action(force_refresh_view_action, "debug")
        self.add_free_context_menu_options(menu)
        if self.model is not None:
            self.model.add_context_menu_actions(menu=menu, index=index)

        menu.exec(self.mapToGlobal(pos))

    @profile
    def get_hidden_header_names(self) -> set[str]:
        settings = QSettings()
        hidden_header = settings.value(f"{self.name}_hidden_headers", set())
        return hidden_header

    @profile
    def set_hidden_header_names(self):
        hidden_section_names = []
        for column in self.model.columns:
            index = self.model.get_column_index(column.name)
            if index is not None:
                if self.header_view.isSectionHidden(index) is True:
                    hidden_section_names.append(column.name)
        settings = QSettings()
        settings.setValue(f"{self.name}_hidden_headers", set(hidden_section_names))

    @profile
    def setup_headers(self):
        for column_name in self.initially_hidden_columns:
            index = self.model.get_column_index(column_name)
            if index is not None:
                self.header_view.hideSection(index)
        for column_name in self.get_hidden_header_names():
            index = self.model.get_column_index(column_name)

            if index is not None:
                self.header_view.hideSection(index)
        column_order_map = self.column_order
        original_order = list(self.model.columns)
        new_order = sorted([i.name for i in original_order], key=lambda x: column_order_map.get(x, 0))

        self.header_view.sectionMoved.disconnect(self.store_new_column_order)

        for idx, column in enumerate(original_order):
            new_idx = new_order.index(column.name)
            vis_idx = self.header_view.visualIndex(idx)

            self.header_view.moveSection(vis_idx, new_idx)

        self.header_view.setContextMenuPolicy(Qt.CustomContextMenu)
        self.header_view.customContextMenuRequested.connect(self.handle_header_custom_context_menu)
        self.header_view.sectionMoved.connect(self.store_new_column_order)

    @profile
    def handle_header_custom_context_menu(self, pos: QPoint):
        def get_amount_not_hidden():
            not_hidden = []
            for _column in self.model.columns:
                _idx = self.model.get_column_index(_column.name)
                _hidden = self.header_view.isSectionHidden(_idx)
                if not _hidden:
                    not_hidden.append(_idx)
            return len(not_hidden)

        column_section = self.header_view.logicalIndexAt(pos)
        col = self.model.columns[column_section]

        log.debug("logical index: %r, column from logical index: %r", column_section, col)

        menu = QMenu(self.header_view)

        for column in self.model.columns:
            idx = self.model.get_column_index(column.name)
            hidden = self.header_view.isSectionHidden(idx)
            name = column.verbose_name or column.name

            if hidden is False:
                change_visibility_action = HeaderContextMenuAction(section=idx, icon=AllResourceItems.check_mark_black_image.get_as_icon(), text=name, parent=self.header_view)
                if get_amount_not_hidden() == 1:
                    change_visibility_action.setEnabled(False)
            else:
                change_visibility_action = HeaderContextMenuAction(section=idx, text=name, parent=self.header_view)
            change_visibility_action.clicked.connect(self.toggle_header_section_hidden)
            menu.addAction(change_visibility_action)
        menu.exec(self.header_view.mapToGlobal(pos))

    @profile
    def force_refresh(self):
        log.debug("starting force refreshing %r", self)
        log.debug("repainting %r", self)
        self.repaint()
        log.debug("doing items layout of %r", self)
        self.doItemsLayout()
        log.debug("finished force refreshing %r", self)

    @profile
    def toggle_header_section_hidden(self, section: int):
        is_hidden = self.header_view.isSectionHidden(section)
        if is_hidden:
            log.debug("setting section %r with idx %r to visible", self.model.columns[section], section)
            self.header_view.setSectionHidden(section, False)
        else:
            log.debug("setting section %r with idx %r to hidden", self.model.columns[section], section)
            self.header_view.setSectionHidden(section, True)
        self.set_hidden_header_names()

    def extra_setup(self):
        pass

    @profile
    def setup_scrollbars(self):
        self.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.setHorizontalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.vertical_scrollbar.setSingleStep(3)

    @profile
    def resize_header_sections(self):

        self.header_view.setSectionResizeMode(QHeaderView.Interactive)

        for idx in range(self.header_view.count()):
            section = self.model.columns[idx]
            new_size = int(self.item_size_by_column_name.get(section.name, self.default_item_size))
            self.header_view.resizeSection(idx, new_size)

    @profile
    def pre_set_model(self):
        self.setEnabled(False)
        self.setUniformRowHeights(True)
        self._temp_original_sorting_enabled = self.isSortingEnabled()
        if self._temp_original_sorting_enabled is True:
            self.setSortingEnabled(False)

    @profile
    def post_set_model(self):
        self.setEnabled(True)
        self.setSortingEnabled(self._temp_original_sorting_enabled)

    @profile
    def set_delegates(self):
        marked_col_index = self.model.get_column_index("marked")
        if marked_col_index is not None:
            self.setItemDelegateForColumn(marked_col_index, MarkedImageDelegate(self))

        for column in self.model.columns:
            if column.name == "marked":
                continue
            if column.field_type == "BOOL":
                idx = self.model.get_column_index(column.name)
                self.setItemDelegateForColumn(idx, BoolImageDelegate(self))

    @profile
    def setModel(self, model: PySide6.QtCore.QAbstractItemModel) -> None:
        def _callback(future: Future):
            if future.exception():
                raise future.exception()
            else:
                self.reset()

        try:
            self.pre_set_model()
            super().setModel(model)
            if hasattr(model, "_item_size_by_column_names"):
                self.item_size_by_column_name |= model._item_size_by_column_names.copy()
            self.model.setParent(self)
            self.model.get_columns()
            self.set_delegates()
            self.setup_headers()
            self.resize_header_sections()

            if model.content_items is None:
                self.model.refresh()
                self.reset()
                # task = self.app.gui_thread_pool.submit(self.model.refresh)
                # task.add_done_callback(_callback)

        finally:
            self.post_set_model()

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name={self.name!r}, icon={self.icon}, model={self.model!r})"

    def __str__(self) -> str:
        return f"{self.__class__.__name__}(name={self.name!r})"

    def selectionChanged(self, selected: QItemSelection, deselected: QItemSelection) -> None:

        current_selection = self.selectionModel().selectedRows()
        amount_selection = len(current_selection)

        if amount_selection == 0:

            return

        if amount_selection == 1:

            self.single_item_selected.emit(current_selection[-1])

        else:

            indexes = current_selection

            self.single_item_selected.emit(current_selection[-1])
            self.multiple_items_selected.emit(list(indexes))

        items = [self.model.get(i.row()) for i in current_selection]

        self.current_items_changed.emit(items)
        super().selectionChanged(selected, deselected)


# region[Main_Exec]
if __name__ == '__main__':
    pass

# endregion[Main_Exec]
