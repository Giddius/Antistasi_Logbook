"""
WiP.

Soon.
"""

# region [Imports]

# * Standard Library Imports ---------------------------------------------------------------------------->
from typing import TYPE_CHECKING, Any, Optional
from pathlib import Path
from concurrent.futures import Future

# * Qt Imports --------------------------------------------------------------------------------------->
from PySide6 import QtCore
from PySide6.QtCore import Qt, QUrl, Slot, QMimeData, QModelIndex

# * Third Party Imports --------------------------------------------------------------------------------->
from peewee import Field, Query

# * Gid Imports ----------------------------------------------------------------------------------------->
from gidapptools import get_logger

# * Local Imports --------------------------------------------------------------------------------------->
from antistasi_logbook.storage.models.models import ModSet, Server, LogFile, Version
from antistasi_logbook.storage.models.custom_fields import FakeField
from antistasi_logbook.gui.models.base_query_data_model import INDEX_TYPE, BaseQueryDataModel, ModelContextMenuAction

# * Type-Checking Imports --------------------------------------------------------------------------------->
if TYPE_CHECKING:
    from antistasi_logbook.storage.models.models import BaseModel
    from antistasi_logbook.gui.views.base_query_tree_view import CustomContextMenu

# endregion[Imports]

# region [TODO]


# endregion [TODO]

# region [Logging]


# endregion[Logging]

# region [Constants]

THIS_FILE_DIR = Path(__file__).parent.absolute()
log = get_logger(__name__)
# endregion[Constants]


class LogFilesModel(BaseQueryDataModel):
    extra_columns = {
        FakeField("time_frame", "Time Frame")
    }
    strict_exclude_columns = {"startup_text", "remote_path", "header_text", "original_file"}

    def __init__(self, parent: Optional[QtCore.QObject] = None) -> None:
        self.show_unparsable = False
        super().__init__(LogFile, parent=parent)
        self.ordered_by = (-LogFile.modified_at,)
        self.filter_item = None
        self.currently_reparsing: bool = False
        self.refresh_future: Future = None

    def add_context_menu_actions(self, menu: "CustomContextMenu", index: QModelIndex):
        super().add_context_menu_actions(menu, index)
        item, column = self.get(index)

        if item is None or column is None:
            return
        force_reparse_action = ModelContextMenuAction(item, column, index, text=f"Force Reparse {item.pretty_name}", parent=menu)
        force_reparse_action.clicked.connect(self.reparse_log_file)
        if self.currently_reparsing is True:
            force_reparse_action.setEnabled(False)
        menu.add_action(force_reparse_action)

        copy_action = ModelContextMenuAction(item, column, index, text=f"Copy {item.pretty_name} to Clipboard", parent=menu)
        copy_action.clicked.connect(self.copy_file_to_clipboard)
        menu.add_action(copy_action)

    @Slot(object, object, QModelIndex)
    def copy_file_to_clipboard(self, item: LogFile, column: Field, index: QModelIndex):
        clipboard = self.app.clipboard()
        data = QMimeData()
        original_file: Path = item.original_file.to_file()
        data.setUrls([QUrl.fromLocalFile(original_file)])
        clipboard.setMimeData(data)

    @Slot(object, object, QModelIndex)
    def reparse_log_file(self, item: LogFile, column: Field, index: QModelIndex):
        def _actual_reparse(log_file: LogFile):
            self.backend.updater.process_log_file(log_file=log_file, force=True)
            self.backend.updater._update_record_classes(log_file=log_file, force=True)
            self.refresh()

        def _callback(future):
            if future.exception():
                raise future.exception()
            self.layoutChanged.emit()
            self.currently_reparsing = False

        self.currently_reparsing = True
        self.layoutAboutToBeChanged.emit()
        task = self.backend.thread_pool.submit(_actual_reparse, item)
        task.add_done_callback(_callback)

    def change_show_unparsable(self, show_unparsable):
        if show_unparsable and self.show_unparsable is False:
            self.show_unparsable = True
            self.refresh()

        elif not show_unparsable and self.show_unparsable is True:
            self.show_unparsable = False
            self.refresh()

    def on_display_data_bool(self, role: int, item: "BaseModel", column: "Field", value: bool) -> str:
        if role == Qt.DisplayRole:
            if column.name in {"is_new_campaign"}:
                return ''

            return super().on_display_data_bool(role=role, item=item, column=column, value=value)
        if role == Qt.DecorationRole:
            if column.name in {"is_new_campaign"}:
                return self.bool_images[True] if value is True else None

            return super().on_display_data_bool(role=role, item=item, column=column, value=value)

    def get_query(self) -> "Query":
        query = LogFile.select(LogFile)
        if self.show_unparsable is False:
            query = query.where(LogFile.unparsable == False)
        if self.filter_item is not None:
            query = query.where(self.filter_item)
        return query.order_by(*self.ordered_by)

    def get_content(self) -> "BaseQueryDataModel":
        def load_up_log_file(in_log_file: LogFile):
            in_log_file.server = Server.get_by_id_cached(in_log_file.server_id)
            in_log_file.game_map = self.backend.database.foreign_key_cache.get_game_map_by_id(in_log_file.game_map_id)
            if in_log_file.version_id is not None:
                in_log_file.version = Version.get_by_id_cached(in_log_file.version_id)
            if in_log_file.mod_set_id is not None:
                in_log_file.mod_set = ModSet.get_by_id_cached(in_log_file.mod_set_id)
            in_log_file.ensure_dynamic_columns()

            return in_log_file

        # self.database.foreign_key_cache.reset_all()
        self.database.foreign_key_cache.preload_all()

        self.content_items = []
        self.database.connect(True)
        for log_file in self.backend.thread_pool.map(load_up_log_file, self.get_query().iterator()):

            self.content_items.append(log_file)
        self.content_items = tuple(self.content_items)
        return self

    def _get_tool_tip_data(self, index: INDEX_TYPE) -> Any:
        item = self.content_items[index.row()]
        column = self.columns[index.column()]

        if column.name == "marked":
            if item.marked is True:
                return "This Log-File is marked"
            else:
                return "This Log-File is not marked"

        elif column.name == "amount_headless_clients":
            return f"connected: {item.amount_headless_clients_connected}\ndisconnected: {item.amount_headless_clients_disconnected}"
        elif column.name == "game_map" and item.game_map.has_low_res_image() is True:
            return f'<b>{item.game_map.pretty_name!s}</b><br><img src="{item.game_map.map_image_low_resolution.image_path!s}">'

        return super()._get_tool_tip_data(index)
# region[Main_Exec]


if __name__ == '__main__':
    pass

# endregion[Main_Exec]
