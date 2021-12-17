"""
WiP.

Soon.
"""

# region [Imports]

# * Standard Library Imports ---------------------------------------------------------------------------->
import queue
from typing import TYPE_CHECKING, Any, Union, Callable, Optional
from pathlib import Path
from functools import partial
from threading import Event

# * Third Party Imports --------------------------------------------------------------------------------->
from peewee import Field, Query
from antistasi_logbook.storage.models.models import BaseModel
from antistasi_logbook.gui.resources.antistasi_logbook_resources_accessor import AllResourceItems

# * PyQt5 Imports --------------------------------------------------------------------------------------->
import PySide6
from PySide6 import QtCore
from PySide6.QtCore import Qt, QAbstractTableModel

if TYPE_CHECKING:
    # * Third Party Imports --------------------------------------------------------------------------------->
    from antistasi_logbook.backend import Backend
    from antistasi_logbook.records.abstract_record import AbstractRecord

# endregion[Imports]

# region [TODO]


# endregion [TODO]

# region [Logging]


# endregion[Logging]

# region [Constants]

THIS_FILE_DIR = Path(__file__).parent.absolute()

# endregion[Constants]
INDEX_TYPE = Union[QtCore.QModelIndex, QtCore.QPersistentModelIndex]

DATA_ROLE_MAP_TYPE = dict[Union[Qt.ItemDataRole, int], Callable[[INDEX_TYPE], Any]]

HEADER_DATA_ROLE_MAP_TYPE = dict[Union[Qt.ItemDataRole, int], Callable[[int, Qt.Orientation], Any]]


class BaseQueryDataModel(QAbstractTableModel):
    always_exclude_column_names: set[str] = {"id", "comments"}
    default_column_ordering: dict[str, int] = {"marked": 0, "name": 1}
    bool_images = {True: AllResourceItems.check_mark_green.get_as_icon(),
                   False: AllResourceItems.close_black.get_as_icon()}

    def __init__(self, backend: "Backend", db_model: "BaseModel", parent: Optional[QtCore.QObject] = None) -> None:
        self.data_role_table: DATA_ROLE_MAP_TYPE = {Qt.DisplayRole: self._get_display_data,
                                                    Qt.ForegroundRole: self._get_foreground_data,
                                                    Qt.BackgroundRole: self._get_background_data,
                                                    Qt.FontRole: self._get_font_data,
                                                    Qt.ToolTipRole: self._get_tool_tip_data,
                                                    Qt.EditRole: self._get_edit_data,
                                                    Qt.InitialSortOrderRole: self._get_initial_sort_order_data,
                                                    Qt.UserRole: self._get_user_data,
                                                    Qt.SizeHintRole: self._get_size_hint_data,
                                                    Qt.StatusTipRole: self._get_status_tip_data,
                                                    Qt.WhatsThisRole: self._get_whats_this_data,
                                                    Qt.DecorationRole: self._get_decoration_data,
                                                    Qt.CheckStateRole: self._get_check_state_data,
                                                    Qt.TextAlignmentRole: self._get_text_alignment_data,
                                                    Qt.AccessibleTextRole: self._get_accessible_text_data,
                                                    Qt.DisplayPropertyRole: self._get_display_property_data,
                                                    Qt.ToolTipPropertyRole: self._get_tool_tip_property_data,
                                                    Qt.StatusTipPropertyRole: self._get_status_tip_property_data,
                                                    Qt.WhatsThisPropertyRole: self._get_whats_this_property_data,
                                                    Qt.DecorationPropertyRole: self._get_decoration_property_data,
                                                    Qt.AccessibleDescriptionRole: self._get_accessible_description_data}

        self.header_data_role_table: HEADER_DATA_ROLE_MAP_TYPE = {Qt.DisplayRole: self._get_display_header_data,
                                                                  Qt.ForegroundRole: self._get_foreground_header_data,
                                                                  Qt.BackgroundRole: self._get_background_header_data,
                                                                  Qt.FontRole: self._get_font_header_data,
                                                                  Qt.ToolTipRole: self._get_tool_tip_header_data,
                                                                  Qt.EditRole: self._get_edit_header_data,
                                                                  Qt.InitialSortOrderRole: self._get_initial_sort_order_header_data,
                                                                  Qt.UserRole: self._get_user_header_data,
                                                                  Qt.SizeHintRole: self._get_size_hint_header_data,
                                                                  Qt.StatusTipRole: self._get_status_tip_header_data,
                                                                  Qt.WhatsThisRole: self._get_whats_this_header_data,
                                                                  Qt.DecorationRole: self._get_decoration_header_data,
                                                                  Qt.CheckStateRole: self._get_check_state_header_data,
                                                                  Qt.TextAlignmentRole: self._get_text_alignment_header_data,
                                                                  Qt.AccessibleTextRole: self._get_accessible_text_header_data,
                                                                  Qt.DisplayPropertyRole: self._get_display_property_header_data,
                                                                  Qt.ToolTipPropertyRole: self._get_tool_tip_property_header_data,
                                                                  Qt.StatusTipPropertyRole: self._get_status_tip_property_header_data,
                                                                  Qt.WhatsThisPropertyRole: self._get_whats_this_property_header_data,
                                                                  Qt.DecorationPropertyRole: self._get_decoration_property_header_data,
                                                                  Qt.AccessibleDescriptionRole: self._get_accessible_description_header_data}
        self.backend = backend
        self._column_names_to_exclude: set[str] = self.always_exclude_column_names.copy()
        self._column_ordering: dict[str, int] = self.default_column_ordering.copy()

        self.db_model = db_model
        self.ordered_by = (self.db_model.id,)
        self.content_items: list[Union["BaseModel", "AbstractRecord"]] = None
        self.columns: tuple[Field] = None
        self.generator_refresh_chunk_size: int = 250

        super().__init__(parent=parent)

    def get_query(self) -> "Query":
        return self.db_model.select().order_by(self.ordered_by)

    def get_content(self) -> "BaseQueryDataModel":
        """
        [summary]

        Overwrite in subclasses!

        Returns:
            [type]: [description]
        """
        return self

    def get_columns(self) -> "BaseQueryDataModel":
        """
        [summary]

        Overwrite in subclasses!

        Returns:
            [type]: [description]
        """
        return self

    @ property
    def column_names_to_exclude(self) -> set[str]:
        return self._column_names_to_exclude

    @ property
    def column_ordering(self) -> dict[str, int]:
        return self._column_ordering

    def add_column_name_to_exclude(self, name) -> "BaseQueryDataModel":
        self._column_names_to_exclude.add(name)
        self.refresh()
        return self

    def on_display_data_bool(self, role: int, item: "BaseModel", column: "Field", value: bool) -> str:
        if role == Qt.DisplayRole:
            if column.name == "marked":
                return ""
            return "Yes" if value is True else "No"
        if role == Qt.DecorationRole:
            if column.name == "marked":
                return self.bool_images[True] if value is True else None

            return self.bool_images[value]

    def on_display_data_none(self, role: int, item: "BaseModel", column: "Field") -> str:
        if role == Qt.DisplayRole:
            return '-'

    def columnCount(self, parent: Union[PySide6.QtCore.QModelIndex, PySide6.QtCore.QPersistentModelIndex] = None) -> int:
        if self.columns is None:
            return 0
        return len(self.columns)

    def rowCount(self, parent: Union[PySide6.QtCore.QModelIndex, PySide6.QtCore.QPersistentModelIndex] = None) -> int:
        if self.content_items is None:
            return 0
        return len(self.content_items)

    def data(self, index: INDEX_TYPE, role: int = None) -> Any:
        if not index.isValid():
            return
        if not 0 <= index.row() < len(self.content_items):
            return None
        if role is not None:
            return self.data_role_table[role](index=index)

    def _get_display_data(self, index: INDEX_TYPE) -> Any:
        item = self.content_items[index.row()]
        column = self.columns[index.column()]
        data = item.get_data(column.name)
        if data is None:
            return self.on_display_data_none(role=Qt.DisplayRole, item=item, column=column)
        if isinstance(data, bool):
            return self.on_display_data_bool(role=Qt.DisplayRole, item=item, column=column, value=data)
        return str(data)

    def _get_foreground_data(self, index: INDEX_TYPE) -> Any:
        pass

    def _get_background_data(self, index: INDEX_TYPE) -> Any:
        pass

    def _get_font_data(self, index: INDEX_TYPE) -> Any:
        pass

    def _get_tool_tip_data(self, index: INDEX_TYPE) -> Any:
        pass

    def _get_edit_data(self, index: INDEX_TYPE) -> Any:
        pass

    def _get_initial_sort_order_data(self, index: INDEX_TYPE) -> Any:
        pass

    def _get_user_data(self, index: INDEX_TYPE) -> Any:
        pass

    def _get_size_hint_data(self, index: INDEX_TYPE) -> Any:
        pass

    def _get_decoration_data(self, index: INDEX_TYPE) -> Any:

        item = self.content_items[index.row()]
        column = self.columns[index.column()]
        data = getattr(item, column.name)
        if data is None:
            return self.on_display_data_none(role=Qt.DecorationRole, item=item, column=column)
        if isinstance(data, bool):
            return self.on_display_data_bool(role=Qt.DecorationRole, item=item, column=column, value=data)

    def _get_status_tip_data(self, index: INDEX_TYPE) -> Any:
        pass

    def _get_whats_this_data(self, index: INDEX_TYPE) -> Any:
        pass

    def _get_check_state_data(self, index: INDEX_TYPE) -> Any:
        pass

    def _get_text_alignment_data(self, index: INDEX_TYPE) -> Any:
        return Qt.AlignVCenter | Qt.AlignLeft

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

    def headerData(self, section: int, orientation: Qt.Orientation, role: int = None) -> Any:
        if role is not None:
            return self.header_data_role_table[role](section, orientation)

    def _get_display_header_data(self, section: int, orientation: Qt.Orientation) -> Any:
        if orientation == Qt.Horizontal:
            return self.columns[section].verbose_name

    def _get_foreground_header_data(self, section: int, orientation: Qt.Orientation) -> Any:
        pass

    def _get_background_header_data(self, section: int, orientation: Qt.Orientation) -> Any:
        pass

    def _get_font_header_data(self, section: int, orientation: Qt.Orientation) -> Any:
        pass

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
        pass

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

    @staticmethod
    def _sort_helper(item: Any, column: Field):
        value = getattr(item, column.name)
        if isinstance(value, BaseModel):
            return str(value)
        return value

    def sort(self, column: int, order: PySide6.QtCore.Qt.SortOrder = ...) -> None:
        self.layoutAboutToBeChanged.emit()
        if self.columns is None or self.content_items is None:
            return

        try:
            _column = self.columns[column]
        except IndexError:
            return
        as_reversed = True if order == Qt.DescendingOrder else False
        non_none_items = (item for item in self.content_items if getattr(item, _column.name, None))
        none_items = (item for item in self.content_items if not getattr(item, _column.name, None))

        new_content = sorted(list(non_none_items), key=partial(self._sort_helper, column=_column))

        new_content += list(none_items)
        if as_reversed is True:
            new_content = list(reversed(new_content))
        self.content_items = new_content
        self.layoutChanged.emit()

    def event(self, event: PySide6.QtCore.QEvent) -> bool:
        # log.debug("%s received event %r", self, event.type().name)
        return super().event(event)

    def refresh(self) -> "BaseQueryDataModel":
        self.beginResetModel()
        if self.columns is None:
            self.get_columns()

        self.get_content()

        self.endResetModel()

        return self

    def generator_refresh(self, abort_signal: Event = None) -> tuple["BaseQueryDataModel", Event]:
        self.layoutAboutToBeChanged.emit()
        self.get_columns()
        idx_queue = queue.Queue(self.generator_refresh_chunk_size)
        if abort_signal is not None and abort_signal.is_set() is True:
            return self, abort_signal

        if self.content_items is None:
            self.content_items = []
        else:
            self.content_items.clear()

        for idx, item in enumerate(self.get_query().iterator()):
            if abort_signal is None or abort_signal.is_set() is False:
                self.content_items.append(item)
                try:
                    idx_queue.put_nowait(idx)
                except queue.Full:
                    self.layoutChanged.emit()

                    with idx_queue.mutex:
                        idx_queue.queue.clear()
        if abort_signal is None or abort_signal.is_set() is False:
            self.modelReset.emit()

        return self, abort_signal

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(backend={self.backend!r}, db_model={self.db_model!r}, parent={self.parent!r})"
# region[Main_Exec]


if __name__ == '__main__':
    pass

# endregion[Main_Exec]
