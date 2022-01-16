"""
WiP.

Soon.
"""

# region [Imports]

# * Standard Library Imports ---------------------------------------------------------------------------->
from typing import TYPE_CHECKING, Union, Optional
from pathlib import Path

# * Qt Imports --------------------------------------------------------------------------------------->
import PySide6
from PySide6.QtGui import QIcon, QAction
from PySide6.QtCore import Qt, Slot, QPoint, Signal, QItemSelection, QModelIndex, QSettings, QByteArray
from PySide6.QtWidgets import QMenu, QTreeView, QScrollBar, QHeaderView, QApplication, QAbstractItemView

# * Gid Imports ----------------------------------------------------------------------------------------->
from gidapptools import get_logger

# * Local Imports --------------------------------------------------------------------------------------->
from antistasi_logbook.gui.resources.antistasi_logbook_resources_accessor import AllResourceItems

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
    single_item_selected = Signal(QModelIndex)
    multiple_items_selected = Signal(list)

    def __init__(self, name: str, icon: QIcon = None, parent=None) -> None:
        super().__init__(parent=parent)
        self.icon = icon

        self.name = "" if name is None else name
        if self.icon is None:
            self.icon = getattr(AllResourceItems, f"{self.name.casefold().replace('-','_').replace(' ','_').replace('.','_')}_tab_icon_image").get_as_icon()

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

    def setup(self) -> "BaseQueryTreeView":
        # self.setRootIsDecorated(False)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.handle_custom_context_menu)
        self.setSortingEnabled(True)
        self.header_view.setSortIndicatorClearable(True)

        self.setUniformRowHeights(True)
        self.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.setup_scrollbars()
        self.setFont(self.app.font())
        self.extra_setup()
        return self

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
        log.debug("actions of menu %r : %r", menu, menu.actions())
        menu.exec_(self.mapToGlobal(pos))

    def get_hidden_header_names(self) -> set[str]:
        settings = QSettings()
        hidden_header = settings.value(f"{self.name}_hidden_headers", set())
        return hidden_header

    def set_hidden_header_names(self):
        hidden_section_names = []
        for column in self.model.columns:
            index = self.model.get_column_index(column.name)
            if index is not None:
                if self.header_view.isSectionHidden(index) is True:
                    hidden_section_names.append(column.name)
        settings = QSettings()
        settings.setValue(f"{self.name}_hidden_headers", set(hidden_section_names))

    def setup_headers(self):
        for column_name in self.initially_hidden_columns:
            index = self.model.get_column_index(column_name)
            if index is not None:
                self.header_view.hideSection(index)
        for column_name in self.get_hidden_header_names():
            index = self.model.get_column_index(column_name)
            if index is not None:
                self.header_view.hideSection(index)
        self.header_view.setContextMenuPolicy(Qt.CustomContextMenu)
        self.header_view.customContextMenuRequested.connect(self.handle_header_custom_context_menu)

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

    def pre_set_model(self):
        self.setEnabled(False)
        self._temp_original_sorting_enabled = self.isSortingEnabled()
        if self._temp_original_sorting_enabled is True:
            self.setSortingEnabled(False)

    def post_set_model(self):
        self.setEnabled(True)

        self.setSortingEnabled(self._temp_original_sorting_enabled)

    def setModel(self, model: PySide6.QtCore.QAbstractItemModel) -> None:
        try:
            self.pre_set_model()

            super().setModel(model)
            model.setParent(self)
            self.app.gui_thread_pool.submit(model.refresh)
            log.debug("after set model, parent of model: %r", model.parent())
            self.setup_headers()
            self.reset()
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
        super().selectionChanged(selected, deselected)


class LogFilesQueryTreeView(BaseQueryTreeView):
    initially_hidden_columns: set[str] = {"id", "comments"}

    def __init__(self) -> None:
        super().__init__(name="Log-Files")


# region[Main_Exec]

if __name__ == '__main__':
    pass

# endregion[Main_Exec]
