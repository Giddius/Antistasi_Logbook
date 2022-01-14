"""
WiP.

Soon.
"""

# region [Imports]

# * Standard Library Imports ---------------------------------------------------------------------------->
from typing import TYPE_CHECKING, Any, Optional
from pathlib import Path
from datetime import datetime

# * Third Party Imports --------------------------------------------------------------------------------->
from peewee import JOIN, Field, Query

# * Qt Imports --------------------------------------------------------------------------------------->
from PySide6 import QtCore
from PySide6.QtGui import Qt
from PySide6.QtCore import Qt

# * Gid Imports ----------------------------------------------------------------------------------------->
from gidapptools import get_logger

# * Local Imports --------------------------------------------------------------------------------------->
from antistasi_logbook.storage.models.models import Server, GameMap, LogFile
from antistasi_logbook.storage.models.custom_fields import FakeField
from antistasi_logbook.gui.models.base_query_data_model import INDEX_TYPE, BaseQueryDataModel

# * Type-Checking Imports --------------------------------------------------------------------------------->
if TYPE_CHECKING:
    from antistasi_logbook.storage.models.models import BaseModel

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
    extra_columns = {FakeField(name="amount_log_records", verbose_name="Amount Log Records"),
                     FakeField("time_frame", "Time Frame"),
                     FakeField(name="amount_errors", verbose_name="Amount Errors"),
                     FakeField(name="amount_warnings", verbose_name="Amount Warnings")}
    strict_exclude_columns = {"startup_text", "header_text", "remote_path"}

    def __init__(self, parent: Optional[QtCore.QObject] = None, show_unparsable: bool = False) -> None:
        self.show_unparsable = show_unparsable
        super().__init__(LogFile, parent=parent)
        self.ordered_by = (-LogFile.modified_at, LogFile.server)
        self.filter_item = None

    def on_filter_newer_than(self, dt: datetime):
        if not isinstance(dt, datetime):
            dt = None
        if dt is None and "newer_than" in self.filters:
            del self.filters["newer_than"]
            self.refresh()

        if dt is not None:
            self.filters["newer_than"] = (LogFile.modified_at >= dt)
            self.refresh()

    def on_filter_by_new_campaign(self, checked):
        if not checked and "new_campaign" in self.filters:
            del self.filters["new_campaign"]
            self.refresh()

        elif checked:
            self.filters["new_campaign"] = (LogFile.is_new_campaign == True)
            self.refresh()

    def on_filter_older_than(self, dt: datetime):
        if not isinstance(dt, datetime):
            dt = None
        if dt is None and "older_than" in self.filters:
            del self.filters["older_than"]
            self.refresh()

        if dt is not None:
            self.filters["older_than"] = (LogFile.modified_at <= dt)
            self.refresh()

    def on_filter_by_marked(self, checked):
        if not checked and "marked" in self.filters:
            del self.filters["marked"]
            self.refresh()
        elif checked:
            self.filters["marked"] = (LogFile.marked == True)
            self.refresh()

    def filter_by_server(self, server_id: int):

        if server_id == -1 and "server" in self.filters:
            del self.filters["server"]
            self.refresh()

        elif server_id != -1:
            self.filters["server"] = (LogFile.server_id == server_id)
            self.refresh()

    def filter_by_game_map(self, game_map_id: int):

        if game_map_id == -1 and "game_map" in self.filters:
            del self.filters["game_map"]
            self.refresh()

        elif game_map_id != -1:
            self.filters["game_map"] = (LogFile.game_map_id == game_map_id)
            self.refresh()

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
        query = LogFile.select().join(GameMap, join_type=JOIN.LEFT_OUTER).switch(LogFile).join(Server).switch(LogFile)
        if self.show_unparsable is False:
            query = query.where(LogFile.unparsable == False)
        if self.filter_item is not None:
            query = query.where(self.filter_item)
        return query.order_by(*self.ordered_by)

    def get_content(self) -> "BaseQueryDataModel":
        with self.backend.database:
            self.content_items = list(self.get_query().execute())

        return self

    def _get_tool_tip_data(self, index: INDEX_TYPE) -> Any:
        item = self.content_items[index.row()]
        column = self.columns[index.column()]
        if column.name == "marked":
            if item.marked is True:
                return "This Log-File is marked"
            else:
                return "This Log-File is not marked"

        return super()._get_tool_tip_data(index)
# region[Main_Exec]


if __name__ == '__main__':
    pass

# endregion[Main_Exec]
