"""
WiP.

Soon.
"""

# region [Imports]

# * Standard Library Imports ---------------------------------------------------------------------------->
from typing import TYPE_CHECKING, Any, Union, Callable, Optional
from pathlib import Path

# * Qt Imports --------------------------------------------------------------------------------------->
import PySide6
from PySide6 import QtCore
from PySide6.QtGui import QIcon, QColor, QAction
from PySide6.QtCore import Qt, Slot, QSize, Signal, QModelIndex, QAbstractTableModel, QPersistentModelIndex, QSettings
from PySide6.QtWidgets import QApplication, QColorDialog

# * Third Party Imports --------------------------------------------------------------------------------->
from apsw import SQLError
from peewee import Field, Query, IntegerField
from natsort import natsorted

# * Gid Imports ----------------------------------------------------------------------------------------->
from gidapptools import get_logger, get_meta_config

# * Local Imports --------------------------------------------------------------------------------------->
from antistasi_logbook.gui.misc import CustomRole
from antistasi_logbook.storage.models.models import GameMap, Version, BaseModel
from antistasi_logbook.gui.widgets.markdown_editor import MarkdownEditorDialog
from antistasi_logbook.storage.models.custom_fields import URLField, PathField
from antistasi_logbook.gui.widgets.better_color_dialog import BetterColorDialog
from antistasi_logbook.gui.resources.antistasi_logbook_resources_accessor import AllResourceItems

# * Type-Checking Imports --------------------------------------------------------------------------------->
if TYPE_CHECKING:
    from antistasi_logbook.backend import Backend
    from antistasi_logbook.gui.application import AntistasiLogbookApplication
    from antistasi_logbook.storage.database import GidSqliteApswDatabase
    from antistasi_logbook.records.abstract_record import AbstractRecord
    from antistasi_logbook.gui.widgets.data_tool_widget import BaseDataToolWidget
    from antistasi_logbook.gui.views.base_query_tree_view import CustomContextMenu

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
INDEX_TYPE = Union[QModelIndex, QPersistentModelIndex]

DATA_ROLE_MAP_TYPE = dict[Union[Qt.ItemDataRole, int], Callable[[INDEX_TYPE], Any]]

HEADER_DATA_ROLE_MAP_TYPE = dict[Union[Qt.ItemDataRole, int], Callable[[int, Qt.Orientation], Any]]


class EmptyContentItem:

    def __init__(self, display_text: str = "") -> None:
        self.display_text = display_text

    def get_data(self, column_name: str):
        if column_name == "name":
            return self.display_text

        if column_name == "full":
            return self.display_text

    def __getattr__(self, key: str):
        return None


class ModelContextMenuAction(QAction):
    clicked = Signal(object, object, QModelIndex)

    def __init__(self, item: BaseModel, column: Field, index: QModelIndex, icon: QIcon = None, text: str = None, parent=None):
        super().__init__(**{k: v for k, v in dict(icon=icon, text=text, parent=parent).items() if v is not None})
        self.item = item
        self.column = column
        self.index = index
        self.triggered.connect(self.on_triggered)

    @Slot()
    def on_triggered(self):
        self.clicked.emit(self.item, self.column, self.index)


class BaseQueryDataModel(QAbstractTableModel):
    extra_columns = set()
    strict_exclude_columns = set()

    def __init__(self, db_model: "BaseModel", parent: Optional[QtCore.QObject] = None, name: str = None) -> None:
        self.bool_images = {True: AllResourceItems.check_mark_green_image.get_as_icon(),
                            False: AllResourceItems.close_black_image.get_as_icon()}

        self.mark_images = {"marked": AllResourceItems.mark_image.get_as_icon(),
                            "unmark": AllResourceItems.unmark_image.get_as_icon()}
        self.data_role_table: DATA_ROLE_MAP_TYPE = {Qt.DisplayRole: self._get_display_data,
                                                    Qt.ToolTipRole: self._get_tool_tip_data,
                                                    Qt.TextAlignmentRole: self._get_text_alignment_data,
                                                    Qt.DecorationRole: self._get_decoration_data,
                                                    # Qt.ForegroundRole: self._get_foreground_data,
                                                    Qt.BackgroundRole: self._get_background_data,
                                                    Qt.SizeHintRole: self._get_size_hint_data,
                                                    # Qt.FontRole: self._get_font_data,
                                                    # Qt.EditRole: self._get_edit_data,
                                                    # Qt.InitialSortOrderRole: self._get_initial_sort_order_data,
                                                    # Qt.StatusTipRole: self._get_status_tip_data,
                                                    # Qt.WhatsThisRole: self._get_whats_this_data,
                                                    # Qt.CheckStateRole: self._get_check_state_data,
                                                    # Qt.AccessibleTextRole: self._get_accessible_text_data,
                                                    # Qt.DisplayPropertyRole: self._get_display_property_data,
                                                    # Qt.ToolTipPropertyRole: self._get_tool_tip_property_data,
                                                    # Qt.StatusTipPropertyRole: self._get_status_tip_property_data,
                                                    # Qt.WhatsThisPropertyRole: self._get_whats_this_property_data,
                                                    # Qt.DecorationPropertyRole: self._get_decoration_property_data,
                                                    # Qt.AccessibleDescriptionRole: self._get_accessible_description_data,
                                                    CustomRole.RAW_DATA: self._get_raw_data
                                                    }

        self.header_data_role_table: HEADER_DATA_ROLE_MAP_TYPE = {Qt.DisplayRole: self._get_display_header_data,
                                                                  #   Qt.ToolTipRole: self._get_tool_tip_header_data,
                                                                  #   Qt.ForegroundRole: self._get_foreground_header_data,
                                                                  #   Qt.BackgroundRole: self._get_background_header_data,
                                                                  #   Qt.FontRole: self._get_font_header_data,
                                                                  #   Qt.EditRole: self._get_edit_header_data,
                                                                  #   Qt.InitialSortOrderRole: self._get_initial_sort_order_header_data,
                                                                  #   Qt.UserRole: self._get_user_header_data,
                                                                  #   Qt.SizeHintRole: self._get_size_hint_header_data,
                                                                  #   Qt.StatusTipRole: self._get_status_tip_header_data,
                                                                  #   Qt.WhatsThisRole: self._get_whats_this_header_data,
                                                                  #   Qt.DecorationRole: self._get_decoration_header_data,
                                                                  #   Qt.CheckStateRole: self._get_check_state_header_data,
                                                                  Qt.TextAlignmentRole: self._get_text_alignment_header_data,
                                                                  #   Qt.AccessibleTextRole: self._get_accessible_text_header_data,
                                                                  #   Qt.DisplayPropertyRole: self._get_display_property_header_data,
                                                                  #   Qt.ToolTipPropertyRole: self._get_tool_tip_property_header_data,
                                                                  #   Qt.StatusTipPropertyRole: self._get_status_tip_property_header_data,
                                                                  #   Qt.WhatsThisPropertyRole: self._get_whats_this_property_header_data,
                                                                  #   Qt.DecorationPropertyRole: self._get_decoration_property_header_data,
                                                                  #   Qt.AccessibleDescriptionRole: self._get_accessible_description_header_data
                                                                  }

        self.db_model = db_model
        self.name = name or self.__class__.__name__
        self.ordered_by = (self.db_model.id,)
        self.content_items: list[Union["BaseModel", "AbstractRecord"]] = None
        self.columns: tuple[Field] = tuple(c for c in list(self.db_model.get_meta().sorted_fields) + list(self.extra_columns) if c.name not in self.strict_exclude_columns)
        self.data_tool: "BaseDataToolWidget" = None
        self.original_sort_order: tuple[int] = tuple()
        self.color_config = get_meta_config().get_config("color")
        self.filter_item = None
        self._median_width: int = None
        self._size_hints: dict[tuple[int, int], QSize] = {}

        super().__init__(parent=parent)

    def on_query_filter_changed(self, query_filter):
        self.filter_item = query_filter
        self.refresh()

    @property
    def app(self) -> "AntistasiLogbookApplication":
        return QApplication.instance()

    @property
    def backend(self) -> "Backend":
        return self.app.backend

    @property
    def database(self) -> "GidSqliteApswDatabase":
        return self.backend.database

    def modify_index(self, index: INDEX_TYPE) -> INDEX_TYPE:
        index.row_item = self.content_items[index.row()]
        index.column_item = self.columns[index.column()]
        return index

    def add_empty_item(self, position: int = None):
        empty_item = EmptyContentItem()
        content_items = list(self.content_items)

        if position is None:
            content_items.append(empty_item)
        else:
            content_items.insert(position, empty_item)
        self.original_sort_order = tuple(content_items)
        self.content_items = content_items

    def add_context_menu_actions(self, menu: "CustomContextMenu", index: QModelIndex):
        if self.app.is_dev is True:
            log.debug("%r has attribute %r: %r", self.db_model, "background_color", hasattr(self.db_model, "background_color"))
            force_refresh_model_action = QAction(f"Force Refresh Model {self.name!r}")
            force_refresh_model_action.triggered.connect(self.force_refresh)
            menu.add_action(force_refresh_model_action, "debug")

        item, column = self.get(index)

        if item is None or column is None:
            return
        if self.db_model.has_column_named("marked"):
            mark_text = f"Mark {item.pretty_name}" if item.marked is False else f"Unmark {item.pretty_name}"
            mark_action = ModelContextMenuAction(item, column, index, text=mark_text)
            mark_action.clicked.connect(self.mark_item)

            menu.add_action(mark_action, "edit")

        if self.db_model.has_column_named("comments"):
            edit_comments_action = ModelContextMenuAction(item, column, index, text=f"Edit Comments for {item.pretty_name}")
            edit_comments_action.clicked.connect(self.edit_comments)

            menu.add_action(edit_comments_action, "edit")

        if hasattr(self.db_model, "background_color"):
            change_color_action = ModelContextMenuAction(item, column, index, text=f"Change Color of {item.pretty_name}", icon=AllResourceItems.coloring_icon_1_image.get_as_icon(), parent=menu)
            change_color_action.clicked.connect(self.change_color)
            menu.add_action(change_color_action, "Edit")

    @Slot()
    def force_refresh(self):
        log.debug("starting force refreshing %r", self)
        self.refresh()
        log.debug("finished force refreshing %r", self)

    @Slot(object, object, QModelIndex)
    def edit_comments(self, item: BaseModel, column: Field, index: QModelIndex):
        log.debug("starting comments editor for %r", item)
        accepted, text = MarkdownEditorDialog.show_dialog(text=item.comments)
        log.debug("result of comments editor: (%r, %r)", accepted, text)
        if accepted:
            comments_index = self.index(index.row(), self.get_column_index("comments"), index.parent())
            self.setData(index=comments_index, value=text, role=Qt.DisplayRole)

    @Slot(object, object, QModelIndex)
    def mark_item(self, item: BaseModel, column: Field, index: QModelIndex):
        log.debug("marking %r", item)
        marked_index = self.index(index.row(), self.get_column_index("marked"), index.parent())
        self.setData(index=marked_index, value=not item.marked, role=Qt.DisplayRole)

    def get_query(self) -> "Query":
        query = self.db_model.select()
        if self.filter_item is not None:
            query = query.where(self.filter_item)
        return query.order_by(*self.ordered_by)

    def get_content(self) -> "BaseQueryDataModel":
        """
        [summary]

        Overwrite in subclasses!

        Returns:
            [type]: [description]
        """
        try:
            with self.app.backend.database:

                self.content_items = list(self.get_query().execute())
        except SQLError as e:
            log.error(e, True)
            log.debug(f"{self.get_query()=}")
        return self

    def get_columns(self) -> "BaseQueryDataModel":
        """
        [summary]

        Overwrite in subclasses!

        Returns:
            [type]: [description]
        """
        self.columns = tuple(c for c in list(self.db_model.get_meta().sorted_fields) + list(self.extra_columns) if c.name not in self.strict_exclude_columns)
        return self

    def get_column_index(self, column: Union[str, Field]) -> Optional[int]:

        if isinstance(column, str):
            try:
                return [idx for idx, c in enumerate(self.columns) if c.name == column][0]
            except IndexError:
                return None
        return list(self.columns).index(column)

    @profile
    def on_display_data_bool(self, role: int, item: "BaseModel", column: "Field", value: bool) -> str:
        if role == Qt.DisplayRole:
            if column.name == "marked":
                return ""
            return "Yes" if value is True else "No"
        if role == Qt.DecorationRole:
            if column.name == "marked":
                return self.mark_images.get("marked") if value is True else self.mark_images.get("unmark")

            return self.bool_images[value]

    @profile
    def on_display_data_none(self, role: int, item: "BaseModel", column: "Field") -> str:
        if role == Qt.DisplayRole:
            return '-'

    @profile
    def _modify_display_data(self, data: Any, item: "BaseModel", column: "Field") -> str:
        if isinstance(data, bool):
            return self.on_display_data_bool(Qt.DisplayRole, item, column, data)
        if data is None:
            return self.on_display_data_none(Qt.DisplayRole, item, column)
        return str(data)

    @profile
    def columnCount(self, parent: Union[PySide6.QtCore.QModelIndex, PySide6.QtCore.QPersistentModelIndex] = None) -> int:
        if self.columns is None:
            return 0
        return len(self.columns)

    @profile
    def rowCount(self, parent: Union[PySide6.QtCore.QModelIndex, PySide6.QtCore.QPersistentModelIndex] = None) -> int:
        if self.content_items is None:
            return 0
        return len(self.content_items)

    @profile
    def data(self, index: INDEX_TYPE, role: int = None) -> Any:
        if not index.isValid():
            return
        if not 0 <= index.row() < len(self.content_items):
            return None

        if role not in self.data_role_table:
            return
        if role is not None:
            handler = self.data_role_table.get(role, None)
            if handler is not None:

                return handler(index=self.modify_index(index))

    @profile
    def _get_raw_data(self, index: INDEX_TYPE) -> Any:
        item, column = self.get(index)
        return getattr(item, column.name, None)

    @profile
    def _get_display_data(self, index: INDEX_TYPE) -> Any:
        data = index.row_item.get_data(index.column_item.name)
        return self._modify_display_data(data, index.row_item, index.column_item)

    def _get_foreground_data(self, index: INDEX_TYPE) -> Any:
        pass

    @profile
    def _get_background_data(self, index: INDEX_TYPE) -> Any:
        item, column = self.get(index)
        value = getattr(item, column.name)
        if hasattr(value, "background_color"):
            return value.background_color

        if hasattr(item, "background_color"):
            return item.background_color

    def _get_font_data(self, index: INDEX_TYPE) -> Any:
        pass

    def _get_tool_tip_data(self, index: INDEX_TYPE) -> Any:
        return index.column_item.help_text

    def _get_edit_data(self, index: INDEX_TYPE) -> Any:
        pass

    def _get_user_data(self, index: INDEX_TYPE) -> Any:
        pass

    @profile
    def _get_size_hint_data(self, index: INDEX_TYPE) -> Any:
        return QSize(0, 35)

    @profile
    def _get_decoration_data(self, index: INDEX_TYPE) -> Any:

        data = getattr(index.row_item, index.column_item.name)
        if data is None:
            return self.on_display_data_none(role=Qt.DecorationRole, item=index.row_item, column=index.column_item)
        if isinstance(data, bool):
            return self.on_display_data_bool(role=Qt.DecorationRole, item=index.row_item, column=index.column_item, value=data)

    def _get_status_tip_data(self, index: INDEX_TYPE) -> Any:
        pass

    def _get_whats_this_data(self, index: INDEX_TYPE) -> Any:
        pass

    def _get_check_state_data(self, index: INDEX_TYPE) -> Any:
        pass

    @profile
    def _get_text_alignment_data(self, index: INDEX_TYPE) -> Any:
        return Qt.AlignCenter

    def _get_accessible_text_data(self, index: INDEX_TYPE) -> Any:
        pass

    def _get_display_property_data(self, index: INDEX_TYPE) -> Any:
        pass

    def _get_tool_tip_property_data(self, index: INDEX_TYPE) -> Any:
        pass

    def _get_decoration_property_data(self, index: INDEX_TYPE) -> Any:
        pass

    def _get_status_tip_property_data(self, index: INDEX_TYPE) -> Any:
        pass

    def _get_whats_this_property_data(self, index: INDEX_TYPE) -> Any:
        pass

    def _get_accessible_description_data(self, index: INDEX_TYPE) -> Any:
        pass

    @profile
    def headerData(self, section: int, orientation: Qt.Orientation, role: int = None) -> Any:
        if role not in self.header_data_role_table:
            return
        if role is not None:

            handler = self.header_data_role_table.get(role, None)
            if handler is not None:
                return handler(section, orientation)

    @profile
    def _get_display_header_data(self, section: int, orientation: Qt.Orientation) -> Any:
        if orientation == Qt.Horizontal:
            _out = self.columns[section].verbose_name
            if _out is None:
                _out = self.columns[section].name
            return _out

    def _get_foreground_header_data(self, section: int, orientation: Qt.Orientation) -> Any:
        pass

    def _get_background_header_data(self, section: int, orientation: Qt.Orientation) -> Any:
        pass

    def _get_font_header_data(self, section: int, orientation: Qt.Orientation) -> Any:
        pass

    @profile
    def _get_tool_tip_header_data(self, section: int, orientation: Qt.Orientation) -> Any:
        if orientation == Qt.Horizontal:
            return self.columns[section].help_text

    def _get_edit_header_data(self, section: int, orientation: Qt.Orientation) -> Any:
        pass

    def _get_initial_sort_order_header_data(self, section: int, orientation: Qt.Orientation) -> Any:
        pass

    def _get_user_header_data(self, section: int, orientation: Qt.Orientation) -> Any:
        pass

    def _get_size_hint_header_data(self, section: int, orientation: Qt.Orientation) -> Any:
        pass

    def _get_decoration_header_data(self, section: int, orientation: Qt.Orientation) -> Any:
        pass

    def _get_status_tip_header_data(self, section: int, orientation: Qt.Orientation) -> Any:
        pass

    def _get_whats_this_header_data(self, section: int, orientation: Qt.Orientation) -> Any:
        pass

    def _get_check_state_header_data(self, section: int, orientation: Qt.Orientation) -> Any:
        pass

    def _get_text_alignment_header_data(self, section: int, orientation: Qt.Orientation) -> Any:
        return Qt.AlignCenter

    def _get_accessible_text_header_data(self, section: int, orientation: Qt.Orientation) -> Any:
        pass

    def _get_display_property_header_data(self, section: int, orientation: Qt.Orientation) -> Any:
        pass

    def _get_tool_tip_property_header_data(self, section: int, orientation: Qt.Orientation) -> Any:
        pass

    def _get_decoration_property_header_data(self, section: int, orientation: Qt.Orientation) -> Any:
        pass

    def _get_status_tip_property_header_data(self, section: int, orientation: Qt.Orientation) -> Any:
        pass

    def _get_whats_this_property_header_data(self, section: int, orientation: Qt.Orientation) -> Any:
        pass

    def _get_accessible_description_header_data(self, section: int, orientation: Qt.Orientation) -> Any:
        pass

    def sort(self, column: int, order: PySide6.QtCore.Qt.SortOrder = None) -> None:

        def make_sort_key(in_column: Field):
            def sort_key(item):
                # TODO: Fix this and make everything sortable, find out how!
                if in_column.field_type in {"TIMESTAMP", "TZOFFSET"} or in_column.name in {"size"}:
                    _out = getattr(item, in_column.name)
                else:
                    try:
                        _out = item.get_data(in_column.name, None)
                    except AttributeError:

                        _out = getattr(item, in_column.name, None)

                if isinstance(in_column, PathField):

                    if _out is None:
                        return ""
                    return _out.as_posix()

                if isinstance(in_column, URLField):

                    if _out is None:
                        return ""
                    return str(item.get_data(in_column.name))

                if isinstance(in_column, IntegerField) and _out is None:
                    return 9999999

                if isinstance(_out, GameMap):
                    return str(_out)

                if isinstance(_out, Version):
                    return _out.full

                if _out is None:
                    return ""

                return _out

            return sort_key

        self.layoutAboutToBeChanged.emit()

        if self.columns is None or self.content_items is None:
            return
        new_content = list(self.content_items)
        if column < 0:
            if self.original_sort_order:
                _helper_dict = {i.id: i for i in self.content_items}
                new_content = [_helper_dict.get(i) for i in self.original_sort_order]
        else:
            _column = self.columns[column]

            if order == Qt.AscendingOrder:
                reverse = False
            elif order == Qt.DescendingOrder:
                reverse = True
            try:
                new_content = natsorted(list(self.content_items), key=make_sort_key(in_column=_column), reverse=reverse)
            except TypeError:

                new_content = sorted(list(self.content_items), key=make_sort_key(in_column=_column), reverse=reverse)

        self.content_items = list(new_content)

        self.layoutChanged.emit()

    def refresh(self) -> "BaseQueryDataModel":
        self.beginResetModel()
        self.get_columns().get_content()
        self.endResetModel()

        return self

    def refresh_items(self):
        new_items = []
        with self.database:
            for item in self.content_items:
                new_item = self.db_model.get_by_id(item.id)
                new_items.append(new_item)
        self.content_items = tuple(new_items)
        self.dataChanged.emit(self.index(0, 0, QModelIndex()), self.index(self.rowCount(), self.columnCount(), QModelIndex()))

    def refresh_item(self, index: "INDEX_TYPE"):
        item = self.content_items[index.row()]
        with self.database:
            new_item = self.db_model.get_by_id(item.id)
        self.content_items = tuple([new_item if i is item else i for i in self.content_items])
        self.dataChanged.emit(self.index(index.row(), 0, QModelIndex()), self.index(index.row(), self.columnCount(), QModelIndex()))

    def get(self, key: Union[QModelIndex, int]) -> Union[tuple, BaseModel]:
        if isinstance(key, QModelIndex):
            if not (0 <= key.row() < len(self.content_items)):
                return None, None
            return self.content_items[key.row()], self.columns[key.column()]

        if isinstance(key, int):
            if not (0 <= key < len(self.content_items)):
                return None
            return self.content_items[key]

    def setData(self, index: Union[PySide6.QtCore.QModelIndex, PySide6.QtCore.QPersistentModelIndex], value: Any, role: int = ...) -> bool:
        if not index.isValid():
            return
        if not 0 <= index.row() < len(self.content_items):
            return None

        item, column = self.get(index)
        if role == Qt.DisplayRole:
            log.debug("setting role %r data of %r column %r to %r", Qt.DisplayRole, item, column, value)
            with self.database.write_lock:
                with self.database:
                    self.db_model.update(**{column.name: value}).where(self.db_model.id == item.id).execute()

        self.refresh_item(index)

    @Slot(object, object, QModelIndex)
    def change_color(self, item: BaseModel, column: Field, index: QModelIndex):

        accepted, color = BetterColorDialog.show_dialog(self.color_config.get(self.color_config_name, item.name, default=QColor(255, 255, 255, 0)), True)
        if accepted:
            log.debug("custom color count: %r", QColorDialog.customCount())
            log.debug("custom colors: %r", [(QColorDialog.customColor(i), QColorDialog.customColor(i).name()) for i in range(QColorDialog.customCount())])

            self.color_config.set(self.color_config_name, item.name, color)
            try:
                del item.background_color
            except AttributeError:
                pass

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(backend={self.backend!r}, db_model={self.db_model!r})"

    def __str__(self) -> str:
        return self.name
# region[Main_Exec]


if __name__ == '__main__':
    pass

# endregion[Main_Exec]
