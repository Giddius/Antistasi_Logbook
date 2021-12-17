"""
WiP.

Soon.
"""

# region [Imports]

# * Standard Library Imports ---------------------------------------------------------------------------->
from typing import TYPE_CHECKING, Optional
from pathlib import Path

# * Third Party Imports --------------------------------------------------------------------------------->
from peewee import Field, Query
from antistasi_logbook.storage.models.models import Server, GameMap, LogFile
from antistasi_logbook.gui.models.base_query_data_model import BaseQueryDataModel

# * PyQt5 Imports --------------------------------------------------------------------------------------->
from PySide6 import QtCore
from PySide6.QtCore import Qt

# * Gid Imports ----------------------------------------------------------------------------------------->
from gidapptools import get_logger

if TYPE_CHECKING:
    # * Third Party Imports --------------------------------------------------------------------------------->
    from antistasi_logbook.backend import Backend
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


class FakeField:

    def __init__(self, name: str, verbose_name: str) -> None:
        self.name = name
        self.verbose_name = verbose_name
        self.help_text = None


class LogFilesModel(BaseQueryDataModel):

    def __init__(self, backend: "Backend", parent: Optional[QtCore.QObject] = None, show_unparsable: bool = False) -> None:
        self.show_unparsable = show_unparsable
        super().__init__(backend, LogFile, parent=parent)
        self.ordered_by = (-LogFile.modified_at, LogFile.server)

    @property
    def column_names_to_exclude(self) -> set[str]:
        _out = self._column_names_to_exclude.union({'header_text', 'startup_text', 'utc_offset', 'last_parsed_datetime', 'last_parsed_line_number'})
        if self.show_unparsable is False:
            _out.add("unparsable")
        return _out

    @property
    def column_ordering(self) -> dict[str, int]:
        return self._column_ordering | {"server": 2, "remote_path": 100}

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
        query = LogFile.select().join(GameMap).switch(LogFile).join(Server).switch(LogFile)
        if self.show_unparsable is False:
            query = query.where(LogFile.unparsable != True)
        return query.order_by(*self.ordered_by)

    def get_content(self) -> "BaseQueryDataModel":

        self.content_items = list(self.get_query().execute())

        return self

    def get_columns(self) -> "BaseQueryDataModel":
        columns = [field for field_name, field in LogFile._meta.fields.items() if field_name not in self.column_names_to_exclude]
        columns.append(FakeField(name="amount_log_records", verbose_name="Amount Log Records"))
        self.columns = tuple(sorted(columns, key=lambda x: self.column_ordering.get(x.name.casefold(), 99)))
        return self
# region[Main_Exec]


if __name__ == '__main__':
    pass

# endregion[Main_Exec]
