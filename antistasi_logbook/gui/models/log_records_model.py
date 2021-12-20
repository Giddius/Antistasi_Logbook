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
from antistasi_logbook.gui.models.base_query_data_model import BaseQueryDataModel, handler_for_header_role, handler_for_role, get_handlers
from antistasi_logbook.gui.resources.antistasi_logbook_resources_accessor import AllResourceItems

# * PyQt5 Imports --------------------------------------------------------------------------------------->
from PySide6 import QtCore
from PySide6.QtGui import QFont, QFontMetrics
from PySide6.QtCore import Qt, QSize, Signal, QObject, QThread

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


@cache
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


@get_handlers
class LogRecordsModel(BaseQueryDataModel):
    initialized = Signal()
    default_column_ordering: dict[str, int] = {"marked": 0, "recorded_at": 1, "message": 2, "log_level": 3, "log_file": 4, "logged_from": 5, "called_by": 6}
    bool_images = {True: AllResourceItems.check_mark_green.get_as_icon(),
                   False: AllResourceItems.close_black.get_as_icon()}

    def __init__(self, backend: "Backend", filter_data: Iterable, parent=None) -> None:
        super().__init__(backend, LogRecord, parent=parent)
        self.filter_data = filter_data
        self.ordered_by = (LogRecord.start, LogRecord.recorded_at)
        self.generator_refresh_chunk_size = 1
        self.message_column_font = self._make_message_column_font()
        self.content_items = []
        self.columns = self.get_columns()
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

        query = LogRecord.select().where(reduce(or_, self.filter_data)).where(LogRecord.record_class != RecordClass.get(name="PerfProfilingRecord")).order_by(*self.ordered_by)
        return query

    @handler_for_role(Qt.DisplayRole)
    def _get_display_data(self, index: "INDEX_TYPE") -> Any:
        item = self.content_items[index.row()]
        column = self.columns[index.column()]

        data = item.get_data(column.name)
        if column.name == "message":
            if index.row() in self._expand or self.expand_all is True:
                return item.pretty_message
            else:
                return item.single_line_message
        if data is None:
            return self.on_display_data_none(role=Qt.DisplayRole, item=item, column=column)
        if isinstance(data, bool):
            return self.on_display_data_bool(role=Qt.DisplayRole, item=item, column=column, value=data)
        return str(data)

    @handler_for_role(Qt.BackgroundRole)
    def _get_background_data(self, index: "INDEX_TYPE") -> Any:
        item = self.content_items[index.row()]
        column = self.columns[index.column()]

        if item.log_level.name == "ERROR":
            return Color(225, 25, 23, 0.5, "error_red").qcolor
        elif item.log_level.name == "WARNING":
            return Color(255, 103, 0, 0.5, "warning_orange").qcolor
        return item.background_color

    def _make_size(self, item: Union["AbstractRecord", "LogRecord"]) -> Union["AbstractRecord", "LogRecord"]:
        message = item.pretty_message.strip()
        # metrics = QFontMetrics(self.message_column_font)
        # b_rect = metrics.boundingRect(message)
        # width = b_rect.width()
        # height = 0
        # for line in message.splitlines():
        #     height += metrics.boundingRect(line).height()
        # item.message_size_hint = QSize(width, height)
        item.message_size_hint = get_qsize_from_font(font=self.message_column_font, text=message)
        return item

    # def _get_size_hint_data(self, index: "INDEX_TYPE") -> Any:
    #     if index.row() in self._expand or self.expand_all is True:
    #         item = self.content_items[index.row()]
    #         column = self.columns[index.column()]
    #         if column.name == "message":
    #             # if item.message_size_hint is None:

    #             #     message = item.pretty_message.strip()
    #             #     metrics = QFontMetrics(self.message_column_font)
    #             #     b_rect = metrics.boundingRect(message)
    #             #     width = b_rect.width()
    #             #     height = 0
    #             #     for line in message.splitlines():
    #             #         height += metrics.boundingRect(line).height()
    #             #     item.message_size_hint = QSize(width, height)

    #             return item.message_size_hint
    @handler_for_role(Qt.FontRole)
    def _get_font_data(self, index: "INDEX_TYPE") -> Any:
        column = self.columns[index.column()]
        if column.name == "message":
            return self.message_column_font
        return self.parent().font()

    def get_content(self) -> None:

        def _get_record(_item_data, _all_log_files):
            record_class = self.backend.record_class_manager.get_by_id(_item_data.get('record_class'))
            log_file = _all_log_files[_item_data.get('log_file')]
            record_item = record_class.from_model_dict(_item_data, log_file=log_file)
            return record_item
        log.debug("starting getting content for %r", self)
        all_log_files = {log_file.id: log_file for log_file in self.backend.database.get_log_files()}
        with self.backend.database:
            with ThreadPoolExecutor() as pool:
                self.content_items = list(pool.map(lambda x: _get_record(_item_data=x, _all_log_files=all_log_files), self.get_query().dicts().iterator()))

        log.debug("finished getting content for %r", self)
        self.initialized.emit()

    def get_columns(self) -> tuple["Field"]:
        columns = [field for field_name, field in LogRecord._meta.fields.items() if field_name not in self.column_names_to_exclude]
        return tuple(sorted(columns, key=lambda x: self.column_ordering.get(x.name.casefold(), 99)))

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

    def refresh(self, abort_signal: Event = None) -> "BaseQueryDataModel":
        super().refresh()
        return self, abort_signal

    def _generator_refresh(self, abort_signal: Event = None) -> "LogRecordsModel":
        def _get_record_item(_item_data, _all_log_files):

            record_class = self.backend.record_class_manager.get_by_id(_item_data.get('record_class'))
            log_file = _all_log_files.get(_item_data.get("log_file"))

            return record_class.from_model_dict(_item_data, log_file)
        log.debug("starting generator_refresh of %r", self)
        self.modelAboutToBeReset.emit()
        self.content_items = []
        items = []
        idx = 0
        all_log_files = {log_file.id: log_file for log_file in self.backend.database.get_log_files()}
        xlock = Lock()
        with self.backend.database:
            with ThreadPoolExecutor() as pool:
                for record_item in pool.map(lambda x: _get_record_item(_item_data=x, _all_log_files=all_log_files), self.get_query().dicts().iterator()):
                    with xlock:
                        idx += 1

                        items.append(RefreshItem(idx, record_item))
                        if len(items) == self.generator_refresh_chunk_size:

                            self.content_items += [i.item for i in items]
                            self.dataChanged.emit(self.index(min([i.idx for i in items]), 0, QtCore.QModelIndex()), self.index(max([i.idx for i in items]), len(self.columns) - 1, QtCore.QModelIndex()))
                            items.clear()
                            sleep(0.00001)

        with xlock:
            if len(items) > 0:

                self.content_items += [i.item for i in items]

                min_index = min([i.idx for i in items]) if len(items) >= 2 else items[0].idx
                max_index = max([i.idx for i in items]) if len(items) >= 2 else items[0].idx
                self.dataChanged.emit(self.index(min_index, 0, QtCore.QModelIndex()), self.index(max_index, len(self.columns) - 1, QtCore.QModelIndex()))
                items.clear()
        self.modelReset.emit()
        log.debug("finished generator_refresh of %r", self)
        return self, abort_signal

    def generator_refresh(self, abort_signal: Event = None, callback: Callable = None) -> RefreshWorker:

        thread = RefreshWorker(self, abort_signal=abort_signal)
        thread.finished.connect(callback)
        thread.start()
        return thread


# region[Main_Exec]
if __name__ == '__main__':
    pass

# endregion[Main_Exec]
