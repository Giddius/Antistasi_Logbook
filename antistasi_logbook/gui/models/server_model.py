"""
WiP.

Soon.
"""

# region [Imports]

# * Standard Library Imports ---------------------------------------------------------------------------->
from typing import TYPE_CHECKING, Optional
from pathlib import Path

# * Third Party Imports --------------------------------------------------------------------------------->
from peewee import Query
from antistasi_logbook.storage.models.models import Server, RemoteStorage
from antistasi_logbook.gui.models.base_query_data_model import BaseQueryDataModel

# * PyQt5 Imports --------------------------------------------------------------------------------------->
from PySide6 import QtCore
from PySide6.QtGui import QColor
from gidapptools import get_logger
if TYPE_CHECKING:
    # * Third Party Imports --------------------------------------------------------------------------------->
    from antistasi_logbook.backend import Backend
    from peewee import ModelIndex
# endregion[Imports]

# region [TODO]


# endregion [TODO]

# region [Logging]


# endregion[Logging]

# region [Constants]

THIS_FILE_DIR = Path(__file__).parent.absolute()
log = get_logger(__name__)
# endregion[Constants]
SERVER_COLOR_ALPHA = 50
SERVER_COLORS = {"no_server": QColor(25, 25, 25, 100),
                 "mainserver_1": QColor(0, 255, 0, SERVER_COLOR_ALPHA),
                 "mainserver_2": QColor(250, 1, 217, SERVER_COLOR_ALPHA),
                 "testserver_1": QColor(0, 127, 255, SERVER_COLOR_ALPHA),
                 "testserver_2": QColor(235, 149, 0, SERVER_COLOR_ALPHA),
                 "testserver_3": QColor(255, 0, 0, SERVER_COLOR_ALPHA),
                 "eventserver": QColor(62, 123, 79, SERVER_COLOR_ALPHA)}


class ServerModel(BaseQueryDataModel):
    strict_exclude_columns: set[str] = {'id', 'remote_storage', "comments"}

    def __init__(self, backend: "Backend", parent: Optional[QtCore.QObject] = None, show_local_files_server: bool = False) -> None:
        self.show_local_files_server = show_local_files_server
        super().__init__(backend, db_model=Server, parent=parent)
        self.ordered_by = (-Server.update_enabled, Server.name, Server.id)

    @property
    def column_names_to_exclude(self) -> set[str]:
        return self._column_names_to_exclude.union({'remote_storage'})

    @property
    def column_ordering(self) -> dict[str, int]:
        return self._column_ordering

    def get_query(self) -> "Query":
        query = Server.select().join(RemoteStorage).switch(Server)
        if self.show_local_files_server is False:
            query = query.where(Server.remote_path != None)
        return query.order_by(*self.ordered_by)

    def get_content(self) -> "BaseQueryDataModel":
        with self.backend.database:
            self.content_items = list(self.get_query().execute())
        return self

    # def get_columns(self) -> "BaseQueryDataModel":
    #     columns = [field for field_name, field in Server._meta.fields.items() if field_name not in self.column_names_to_exclude]
    #     self.columns = sorted(columns, key=lambda x: self.column_ordering.get(x.name.casefold(), 99))

    #     return self


# region[Main_Exec]


if __name__ == '__main__':
    pass

# endregion[Main_Exec]
