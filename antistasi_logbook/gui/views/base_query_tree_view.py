"""
WiP.

Soon.
"""

# region [Imports]

# * Standard Library Imports ---------------------------------------------------------------------------->
import sys
from time import sleep
from typing import TYPE_CHECKING, Union, Optional
from pathlib import Path

# * Qt Imports --------------------------------------------------------------------------------------->
from PySide6.QtGui import QIcon, QAction, QMouseEvent
from PySide6.QtCore import Qt, Slot, QPoint, Signal, QSettings, QModelIndex, QItemSelection, QAbstractItemModel, QAbstractTableModel, QItemSelectionModel, QItemSelectionRange
from PySide6.QtWidgets import QMenu, QToolBar, QTreeView, QScrollBar, QHeaderView, QApplication, QAbstractItemView
from gidapptools.general_helper.string_helper import StringCaseConverter, StringCase
# * Gid Imports ----------------------------------------------------------------------------------------->
from gidapptools import get_logger
from gidapptools.general_helper.timing import get_dummy_profile_decorator_in_globals

# * Local Imports --------------------------------------------------------------------------------------->
from antistasi_logbook.gui.views.delegates.universal_delegates import BoolImageDelegate, MarkedImageDelegate
from antistasi_logbook.gui.resources.antistasi_logbook_resources_accessor import AllResourceItems
from antistasi_logbook.gui.misc import write_settings, read_settings
# * Type-Checking Imports --------------------------------------------------------------------------------->
if TYPE_CHECKING:
    from antistasi_logbook.backend import Backend
    from antistasi_logbook.gui.application import AntistasiLogbookApplication
    from antistasi_logbook.storage.database import GidSqliteApswDatabase
    from antistasi_logbook.storage.models.models import BaseModel
    from antistasi_logbook.gui.models.base_query_data_model import BaseQueryDataModel

# endregion[Imports]

# region [TODO]


# endregion [TODO]

# region [Logging]


# endregion[Logging]

# region [Constants]
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

    def __repr__(self) -> str:
        """
        Basic Repr
        !REPLACE!
        """
        return f'{self.__class__.__name__}'


class CustomContextMenu(QMenu):

    def __init__(self, title: str = None, parent=None):
        super().__init__(*[i for i in [title, parent] if i is not None])
        self.sub_menus: dict[str, "CustomContextMenu"] = {}

    def get_sub_menu(self, name: str, default=None):
        default = default or self
        return self.sub_menus.get(name.casefold(), default)

    def add_menu(self, name: str, add_to: "CustomContextMenu" = None) -> "CustomContextMenu":
        add_to = add_to or self
        sub_menu = self.__class__(name, add_to)
        self.sub_menus[name.casefold()] = sub_menu
        self.addMenu(sub_menu)
        return sub_menu

    def add_action(self, action: QAction, sub_menu: Union[str, "CustomContextMenu", QMenu] = None):
        if sub_menu is None:
            sub_menu = self

        elif isinstance(sub_menu, str):
            sub_menu = self.get_sub_menu(sub_menu)
        if not action.parent():
            action.setParent(sub_menu)
        sub_menu.addAction(action)

    def __repr__(self) -> str:
        """
        Basic Repr
        !REPLACE!
        """
        return f'{self.__class__.__name__}'


class BaseQueryTreeView(QTreeView):
    initially_hidden_columns: set[str] = set()
    default_item_size = 150
    _item_size_by_column_name: dict[str, int] = {"id": 75, "marked": 60, "comments": 100}
    default_colum_order = {"marked": 999, "comments": 998}
    single_item_selected = Signal(QModelIndex)
    multiple_items_selected = Signal(list)
    current_items_changed = Signal(list)
    model_was_set = Signal(QAbstractTableModel)

    def __init__(self, name: str, icon: QIcon = None, parent=None) -> None:
        super().__init__(parent=parent)
        self.icon = icon

        self.name = "" if name is None else name
        if self.icon is None:
            self.icon = getattr(AllResourceItems, f"{self.name.casefold().replace('-','_').replace(' ','_').replace('.','_')}_tab_icon_image").get_as_icon()
        self.item_size_by_column_name = self._item_size_by_column_name.copy()
        self.original_model: BaseQueryDataModel = None
        self._tool_bar_item: QToolBar = None
        self._last_selection_ids: list[int] = None

    @property
    def settings_prefix(self) -> str:
        return StringCaseConverter.convert_to(self.name, StringCase.SNAKE) + '_view'

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
        data = read_settings(self.app.settings, ["views", self.settings_prefix, "column_order"], None)

        if data is None:
            data = {}

        _out = self.default_colum_order | data

        return _out

    @property
    def tool_bar_item(self) -> QToolBar:
        if self._tool_bar_item is None:
            self._tool_bar_item = self.create_tool_bar_item()
        return self._tool_bar_item

    def create_tool_bar_item(self) -> QToolBar:
        return QToolBar()

    def store_new_column_order(self, logical_index: int, old_visual_index: int, new_visual_index: int):
        column_order = self.column_order
        column = self.model.columns[logical_index]

        column_order[column.name] = new_visual_index

        # column = self.model.columns[logical_index]
        # column_order[column.name] = new_visual_index
        write_settings(self.app.settings, ["views", self.settings_prefix, "column_order"], column_order)

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

    def add_free_context_menu_options(self, menu: CustomContextMenu):

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

    def get_hidden_header_names(self) -> set[str]:

        hidden_header = read_settings(self.app.settings, ["views", self.settings_prefix, "hidden_headers"], set())

        return hidden_header

    def set_hidden_header_names(self):
        hidden_section_names = []
        for column in self.model.columns:
            index = self.model.get_column_index(column.name)
            if index is not None:
                if self.header_view.isSectionHidden(index) is True:
                    hidden_section_names.append(column.name)

        write_settings(self.app.settings, ["views", self.settings_prefix, "hidden_headers"], set(hidden_section_names))

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
        self.header_view.sectionMoved.disconnect(self.store_new_column_order)
        for idx, column in enumerate(self.model.columns):
            pos = column_order_map.get(column.name, None)

            orig_vis_index = self.header_view.visualIndex(idx)
            if pos is None:
                pos = orig_vis_index
            self.header_view.moveSection(orig_vis_index, pos)

        self.header_view.setContextMenuPolicy(Qt.CustomContextMenu)
        self.header_view.customContextMenuRequested.connect(self.handle_header_custom_context_menu)
        self.header_view.sectionMoved.connect(self.store_new_column_order)

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

    def force_refresh(self):
        log.debug("starting force refreshing %r", self)
        log.debug("repainting %r", self)
        self.repaint()
        log.debug("doing items layout of %r", self)
        self.doItemsLayout()
        log.debug("finished force refreshing %r", self)

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

    def setup_scrollbars(self):
        self.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.setHorizontalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.vertical_scrollbar.setSingleStep(3)

    def resize_header_sections(self):

        self.header_view.setSectionResizeMode(QHeaderView.Interactive)

        for idx in range(self.header_view.count()):
            section = self.model.columns[idx]
            new_size = int(self.item_size_by_column_name.get(section.name, self.default_item_size))
            self.header_view.resizeSection(idx, new_size)

    def pre_set_model(self):
        self.setEnabled(False)
        self.setUniformRowHeights(True)
        self._temp_original_sorting_enabled = self.isSortingEnabled()
        if self._temp_original_sorting_enabled is True:
            self.setSortingEnabled(False)

    def post_set_model(self):
        self.model._last_selection_ids = None
        self.setEnabled(True)
        self.setSortingEnabled(self._temp_original_sorting_enabled)
        self.model_was_set.emit(self.model)

        self.model.modelReset.connect(self.on_model_reset)

    def on_model_reset(self):
        log.debug("on_model_reset was triggered for %r", self)
        co = sys._getframe(3).f_code
        log.debug("called_by %r of %r", co.co_name, co.co_filename)

        if self.model.last_selection_ids is None or len(self.model.last_selection_ids) <= 0:
            log.debug("model.last_selection_ids is either None or empty (%r)", self.model.last_selection_ids)
            return

        all_indexes = []
        for item_id in self.model.last_selection_ids:
            try:
                row_num = [(idx, item) for idx, item in enumerate(self.model.content_items) if item.id == item_id][0][0]
                log.debug("adding row_num %r", row_num)
                index_first = self.model.index(row_num, 0, QModelIndex())
                # index_last = self.model.index(row_num, self.model.columnCount())
                all_indexes.append(index_first)
            except IndexError:

                continue
        selection = QItemSelection()
        selection.append([QItemSelectionRange(i) for i in all_indexes])
        flags = QItemSelectionModel.SelectionFlags() | QItemSelectionModel.Rows | QItemSelectionModel.Select

        self.selectionModel().clear()
        self.selectionModel().select(selection, flags)
        self.selectionModel().setCurrentIndex(all_indexes[0], QItemSelectionModel.SelectionFlags() | QItemSelectionModel.Rows | QItemSelectionModel.NoUpdate)
        log.debug("current_selected_indexes %r", self.selectionModel().selectedIndexes())
        hidden_header_names = self.get_hidden_header_names()
        for idx, column in enumerate(self.model.columns):
            if idx == 0:
                continue
            if column.name not in hidden_header_names:
                column_idx = idx
                break
        scroll_to_index = self.original_model.index(all_indexes[0].row(), column_idx, QModelIndex())
        try:
            scroll_to_index = self.model.mapFromSource(scroll_to_index)
        except AttributeError:
            pass
        log.debug("scrolling to %r", scroll_to_index)
        self.scrollTo(scroll_to_index, self.ScrollHint.PositionAtCenter)

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

    def setModel(self, model: QAbstractItemModel) -> None:
        try:
            self.pre_set_model()
            super().setModel(model)
            try:
                self.item_size_by_column_name |= model._item_size_by_column_names.copy()
            except AttributeError:
                pass
            self.model.setParent(self)
            self.model.get_columns()
            self.set_delegates()
            self.setup_headers()
            self.resize_header_sections()
            if not self.model.content_items:
                self.model.refresh()
            # self.reset()
            # task = self.app.gui_thread_pool.submit(self.model.refresh)
            # task.add_done_callback(_callback)
            try:
                while self.model.collecting_records is True:
                    sleep(0.25)
            except AttributeError:
                pass
        finally:

            self.post_set_model()

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name={self.name!r}, icon={self.icon}, model={self.model!r})"

    def __str__(self) -> str:
        return f"{self.__class__.__name__}(name={self.name!r})"

    @property
    def current_selection(self) -> tuple[QModelIndex]:
        raw_current_selection = self.selectionModel().selectedRows()
        try:
            return tuple(self.model.mapToSource(idx) for idx in raw_current_selection)
        except AttributeError:
            return tuple(raw_current_selection)

    @property
    def current_selected_items(self) -> tuple["BaseModel"]:
        current_selection = self.current_selection
        if len(current_selection) <= 0:
            return tuple()
        if self.model is None:
            return tuple()
        return tuple(self.model.get(i.row()) for i in current_selection)

    def selectionChanged(self, selected: QItemSelection, deselected: QItemSelection) -> None:

        current_selection = self.current_selection
        amount_selection = len(current_selection)

        if amount_selection == 0:
            return super().selectionChanged(selected, deselected)

        if amount_selection == 1:

            self.single_item_selected.emit(current_selection[-1])

        else:

            indexes = current_selection

            self.single_item_selected.emit(current_selection[-1])
            self.multiple_items_selected.emit(list(indexes))

        items = [self.model.get(i.row()) for i in current_selection]

        self.current_items_changed.emit(items)
        return super().selectionChanged(selected, deselected)

    def mouseDoubleClickEvent(self, event: QMouseEvent) -> None:
        idx = self.indexAt(event.position().toPoint())
        idx = self.model.modify_index(idx)

        if idx.isValid() and event.button() == Qt.MouseButton.LeftButton and idx.column_item.name == "marked":
            self.model.mark_item(idx.row_item, idx.column_item, idx)
        else:
            return super().mouseDoubleClickEvent(event)


# region[Main_Exec]
if __name__ == '__main__':
    pass

# endregion[Main_Exec]
