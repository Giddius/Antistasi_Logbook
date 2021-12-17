"""
WiP.

Soon.
"""

# region [Imports]

# * Standard Library Imports ---------------------------------------------------------------------------->
from time import sleep
from typing import TYPE_CHECKING, Any, Union, Iterable
from pathlib import Path
from operator import or_
from functools import reduce
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
from PySide6.QtCore import Qt, QSize, Signal, QThread

# * Gid Imports ----------------------------------------------------------------------------------------->
from gidapptools import get_logger
from gidapptools.general_helper.color.color_item import Color

if TYPE_CHECKING:
    # * Third Party Imports --------------------------------------------------------------------------------->
    from antistasi_logbook.backend import Backend
    from antistasi_logbook.records.abstract_record import AbstractRecord
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


class RefreshWorker(QThread):
    finished = Signal()

    def __init__(self, model: "LogRecordsModel", **kwargs):
        self.model = model
        self.kwargs = kwargs
        super().__init__(self.model)

    def run(self):
        self.model._generator_refresh(**self.kwargs)
        self.finished.emit()
        log.debug("finished refreshing %r", self.model)


RefreshItem = namedtuple("RefreshItem", ["idx", "item"])


class LogRecordsModel(BaseQueryDataModel):
    first_data_available = Signal()
    default_column_ordering: dict[str, int] = {"marked": 0, "recorded_at": 1, "message": 2, "log_level": 3, "log_file": 4, "logged_from": 5, "called_by": 6}
    bool_images = {True: AllResourceItems.check_mark_green.get_as_icon(),
                   False: AllResourceItems.close_black.get_as_icon()}

    def __init__(self, backend: "Backend", filter_data: Iterable, parent=None) -> None:
        super().__init__(backend, LogRecord, parent=parent)
        self.filter_data = filter_data
        self.ordered_by = (LogRecord.start, LogRecord.recorded_at)
        self.generator_refresh_chunk_size = 50
        self.message_column_font = self._make_message_column_font()
        self.header_font = self._make_header_font()
        self.content_items = []
        self.columns = self.get_columns()

    @property
    def resize_lock(self) -> Lock:
        return self.parent().resize_lock

    def _make_header_font(self) -> QFont:
        font = QFont()
        return font

    def _make_message_column_font(self) -> QFont:
        font = QFont()
        font.setFamily("Cascadia Mono")
        return font

    @property
    def column_names_to_exclude(self) -> set[str]:
        return self._column_names_to_exclude.union({"start", "end", "record_class", "is_antistasi_record"})

    def get_query(self) -> "Query":

        query = LogRecord.select().where(reduce(or_, self.filter_data)).where(LogRecord.record_class != RecordClass.get(name="PerfProfilingRecord")).order_by(*self.ordered_by)
        return query

    def _get_display_data(self, index: "INDEX_TYPE") -> Any:
        item = self.content_items[index.row()]
        column = self.columns[index.column()]

        data = item.get_data(column.name)
        if column.name == "message" and len(data.strip().splitlines()[0]) > 100:
            return data[:97] + "..."
        if data is None:
            return self.on_display_data_none(role=Qt.DisplayRole, item=item, column=column)
        if isinstance(data, bool):
            return self.on_display_data_bool(role=Qt.DisplayRole, item=item, column=column, value=data)
        return str(data)

    def _get_background_data(self, index: "INDEX_TYPE") -> Any:
        item = self.content_items[index.row()]
        column = self.columns[index.column()]
        if item.log_level is None:
            log.critical("log_level is None for %r", item)
        elif item.log_level.name == "ERROR":
            return Color(225, 25, 23, 0.5, "error_red").qcolor

        return item.background_color

    def _make_size(self, item: Union["AbstractRecord", "LogRecord"]) -> Union["AbstractRecord", "LogRecord"]:
        message = item.pretty_message.strip()
        metrics = QFontMetrics(self.message_column_font)
        b_rect = metrics.boundingRect(message)
        width = b_rect.width()
        height = 0
        for line in message.splitlines():
            height += metrics.boundingRect(line).height()
        item.message_size_hint = QSize(width, height)
        return item

    def _get_size_hint_data(self, index: "INDEX_TYPE") -> Any:
        item = self.content_items[index.row()]
        column = self.columns[index.column()]
        if column.name == "message":
            # if item.message_size_hint is None:

            #     message = item.pretty_message.strip()
            #     metrics = QFontMetrics(self.message_column_font)
            #     b_rect = metrics.boundingRect(message)
            #     width = b_rect.width()
            #     height = 0
            #     for line in message.splitlines():
            #         height += metrics.boundingRect(line).height()
            #     item.message_size_hint = QSize(width, height)

            return item.message_size_hint

    def _get_font_header_data(self, section: int, orientation: Qt.Orientation) -> Any:
        if orientation == Qt.Horizontal:
            return self.header_font

    def _get_font_data(self, index: "INDEX_TYPE") -> Any:
        column = self.columns[index.column()]
        if column.name == "message":
            return self.message_column_font
        return self.parent().font()

    def get_content(self) -> "BaseQueryDataModel":
        all_log_files = {log_file.id: log_file for log_file in self.backend.database.get_log_files()}

        def _get_record(in_data):
            record_class = self.backend.record_class_manager.get_by_id(in_data.get('record_class'))
            log_file = all_log_files.get(in_data.get('log_file'))
            record_item = record_class.from_model_dict(in_data, log_file=log_file)
            return record_item

        with self.backend.database:

            self.content_items = [_get_record(i) for i in self.get_query().dicts().iterator()]
        return self

    def get_columns(self) -> tuple["Field"]:
        columns = [field for field_name, field in LogRecord._meta.fields.items() if field_name not in self.column_names_to_exclude]
        return tuple(sorted(columns, key=lambda x: self.column_ordering.get(x.name.casefold(), 99)))

    def refresh(self, abort_signal: Event = None) -> "BaseQueryDataModel":
        super().refresh()
        return self, abort_signal

    def _generator_refresh(self, abort_signal: Event = None) -> "LogRecordsModel":

        items = []
        is_first = True
        idx = 0
        all_log_files = {log_file.id: log_file for log_file in self.backend.database.get_log_files()}
        with self.backend.database:
            for item_data in self.get_query().dicts():

                idx += 1
                record_class = self.backend.record_class_manager.get_by_id(item_data.get('record_class'))
                log_file = all_log_files.get(item_data.get("log_file"))
                record_item = record_class.from_model_dict(item_data, log_file)
                items.append(RefreshItem(idx, record_item))
                if len(items) == self.generator_refresh_chunk_size:

                    self.beginInsertRows(QtCore.QModelIndex(), min(i.idx for i in items), max(i.idx for i in items))

                    self.content_items += [i.item for i in items]

                    self.endInsertRows()

                    items.clear()
                    if is_first is True:
                        self.first_data_available.emit()
                        is_first = False

                sleep(0.0)

        if len(items) != 0:
            self.beginInsertRows(QtCore.QModelIndex(), min(i.idx for i in items), max(i.idx for i in items))

            self.content_items += [i.item for i in items]
            self.endInsertRows()
            items.clear()

        return self, abort_signal

    def generator_refresh(self, abort_signal: Event = None) -> RefreshWorker:
        thread = RefreshWorker(self, abort_signal=abort_signal)
        thread.start()
        return thread


# region[Main_Exec]
if __name__ == '__main__':
    pass

# endregion[Main_Exec]
