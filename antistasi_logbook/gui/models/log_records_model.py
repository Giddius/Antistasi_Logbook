"""
WiP.

Soon.
"""

# region [Imports]

# * Standard Library Imports ---------------------------------------------------------------------------->
from time import sleep
from typing import TYPE_CHECKING, Any, Union, Iterable, Callable
from pathlib import Path
from operator import or_
from functools import reduce, cache
from threading import Lock, Event
from collections import namedtuple

# * Third Party Imports --------------------------------------------------------------------------------->
from peewee import Field, Query
from antistasi_logbook.storage.models.models import LogRecord, RecordClass
from antistasi_logbook.gui.models.base_query_data_model import BaseQueryDataModel
from antistasi_logbook.gui.resources.antistasi_logbook_resources_accessor import AllResourceItems

# * PyQt5 Imports --------------------------------------------------------------------------------------->
from PySide6 import QtCore
from PySide6.QtGui import QFont, QFontMetrics
from PySide6.QtCore import Qt, QSize, Signal, QObject, QThread
import pp
# * Gid Imports ----------------------------------------------------------------------------------------->
from gidapptools import get_logger
from gidapptools.general_helper.color.color_item import Color
from concurrent.futures import ThreadPoolExecutor
if TYPE_CHECKING:
    # * Third Party Imports --------------------------------------------------------------------------------->
    from antistasi_logbook.backend import Backend
    from antistasi_logbook.records.abstract_record import AbstractRecord
    from antistasi_logbook.records.base_record import BaseRecord
    from antistasi_logbook.gui.models.base_query_data_model import INDEX_TYPE

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


def get_qsize_from_font(font: QFont, text: str) -> QSize:
    fm = QFontMetrics(font)
    return fm.boundingRect(text=text).size()


class RefreshWorker(QThread):
    finished = Signal()

    def __init__(self, model: "LogRecordsModel", **kwargs):
        self.model = model
        self.kwargs = kwargs
        super().__init__()

    def run(self):
        self.model._generator_refresh(**self.kwargs)
        self.finished.emit()
        log.debug("finished refreshing %r", self.model)


RefreshItem = namedtuple("RefreshItem", ["idx", "item"])


class LogRecordsModel(BaseQueryDataModel):
    initialized = Signal()
    default_column_ordering: dict[str, int] = {"marked": 0, "recorded_at": 1, "message": 2, "log_level": 3, "log_file": 4, "logged_from": 5, "called_by": 6}
    bool_images = {True: AllResourceItems.check_mark_green.get_as_icon(),
                   False: AllResourceItems.close_black.get_as_icon()}

    def __init__(self, backend: "Backend", filter_data: dict[str, Any], parent=None) -> None:
        super().__init__(backend, LogRecord, parent=parent)
        self.data_role_table = self.data_role_table | {Qt.BackgroundRole: self._get_background_data, Qt.FontRole: self._get_font_data}
        self.filter_data = {"server_profiling_record": (LogRecord.record_class != RecordClass.get(name="PerfProfilingRecord"))} | filter_data
        self.ordered_by = (LogRecord.start, LogRecord.recorded_at)
        self.generator_refresh_chunk_size = 1
        self.message_column_font = self._make_message_column_font()
        self.content_items = []
        self.columns: tuple[Field] = None
        self._expand: set[int] = set()
        self.expand_all: bool = False

    @property
    def resize_lock(self) -> Lock:
        return self.parent().resize_lock

    def _make_message_column_font(self) -> QFont:
        font = QFont()
        font.setFamily("Cascadia Mono")
        return font

    @property
    def column_names_to_exclude(self) -> set[str]:
        return self._column_names_to_exclude.union({"start", "end", "record_class", "is_antistasi_record"})

    def get_query(self) -> "Query":

        query = LogRecord.select()
        for filter_stmt in self.filter_data.values():
            query = query.where(filter_stmt)

        return query.order_by(*self.ordered_by)

    @profile
    def _get_display_data(self, index: "INDEX_TYPE") -> Any:
        item = self.content_items[index.row()]
        column = self.columns[index.column()]

        data = item.get_data(column.name)
        if column.name == "message":
            return f"{item.message}"
        if data is None:
            return self.on_display_data_none(role=Qt.DisplayRole, item=item, column=column)
        if isinstance(data, bool):
            return self.on_display_data_bool(role=Qt.DisplayRole, item=item, column=column, value=data)
        return str(data)

    @profile
    def _get_background_data(self, index: "INDEX_TYPE") -> Any:
        item = self.content_items[index.row()]
        column = self.columns[index.column()]

        if item.log_level.name == "ERROR":
            return Color(225, 25, 23, 0.5, "error_red").qcolor
        elif item.log_level.name == "WARNING":
            return Color(255, 103, 0, 0.5, "warning_orange").qcolor
        return item.background_color

    @profile
    def _get_font_data(self, index: "INDEX_TYPE") -> Any:
        column = self.columns[index.column()]
        if column.name == "message":
            return self.message_column_font
        return self.parent().font()

    @profile
    def get_content(self) -> None:

        @profile
        def _get_record(_item_data, _all_log_files):
            record_class = self.backend.record_class_manager.get_by_id(_item_data.get('record_class'))
            log_file = _all_log_files[_item_data.get('log_file')]
            record_item = record_class.from_model_dict(_item_data, log_file=log_file)

            return record_item

        log.debug("starting getting content for %r", self)
        all_log_files = {log_file.id: log_file for log_file in self.backend.database.get_log_files()}
        # with self.backend.database:
        with ThreadPoolExecutor() as pool:
            self.content_items = list(pool.map(lambda x: _get_record(_item_data=x, _all_log_files=all_log_files), self.get_query().dicts().iterator()))

        log.debug("finished getting content for %r", self)
        self.initialized.emit()

    @profile
    def get_columns(self) -> "BaseQueryDataModel":
        columns = [field for field_name, field in LogRecord._meta.fields.items() if field_name not in self.column_names_to_exclude]
        self.columns = tuple(sorted(columns, key=lambda x: self.column_ordering.get(x.name.casefold(), 99)))
        return self

    def insertRow(self, row: "BaseRecord") -> bool:
        self.layoutAboutToBeChanged.emit()
        self.content_items.append(row)
        self.layoutChanged.emit()

    def insertRows(self, rows: Iterable["BaseRecord"]) -> bool:
        self.beginInsertRows(QtCore.QModelIndex(), len(self.content_items), len(self.content_items) + len(rows))
        self.content_items += list(rows)
        self.endInsertRows()

    def insertColumns(self, columns: Iterable[Field]) -> bool:
        if self.columns is None:
            self.columns = []

        self.beginInsertColumns(QtCore.QModelIndex(), len(self.columns), len(self.columns) + len(columns))
        self.columns = list(self.columns)
        self.columns += list(columns)
        self.columns = tuple(self.columns)
        self.endInsertColumns()

    def refresh(self) -> "BaseQueryDataModel":
        super().refresh()
        return self


# region[Main_Exec]
if __name__ == '__main__':
    pass

# endregion[Main_Exec]
