"""
WiP.

Soon.
"""

# region [Imports]

# * Standard Library Imports ---------------------------------------------------------------------------->
from time import sleep
from typing import TYPE_CHECKING, Any, Optional
from pathlib import Path
from functools import partial

# * Qt Imports --------------------------------------------------------------------------------------->
from PySide6.QtGui import QFont, QAction, QFontMetrics
from PySide6.QtCore import Qt, Slot, QSize, Signal, QModelIndex, QSettings
from PySide6.QtWidgets import QApplication

# * Third Party Imports --------------------------------------------------------------------------------->
import attr
from peewee import Field, Query
from concurrent.futures import Future
# * Gid Imports ----------------------------------------------------------------------------------------->
from gidapptools import get_logger
from gidapptools.general_helper.color.color_item import Color

# * Local Imports --------------------------------------------------------------------------------------->
from antistasi_logbook.gui.misc import CustomRole
from antistasi_logbook.records.enums import MessageFormat
from antistasi_logbook.storage.models.models import LogRecord, RecordClass, LogFile
from antistasi_logbook.gui.models.base_query_data_model import INDEX_TYPE, BaseQueryDataModel
from antistasi_logbook.gui.models.proxy_models.base_proxy_model import BaseProxyModel
from antistasi_logbook.gui.resources.antistasi_logbook_resources_accessor import AllResourceItems
from gidapptools.general_helper.timing import get_dummy_profile_decorator_in_globals
# * Type-Checking Imports --------------------------------------------------------------------------------->
if TYPE_CHECKING:
    from antistasi_logbook.records.base_record import BaseRecord
    from antistasi_logbook.records.abstract_record import AbstractRecord
    from antistasi_logbook.gui.views.base_query_tree_view import CustomContextMenu
    from antistasi_logbook.gui.models.base_query_data_model import INDEX_TYPE

# endregion[Imports]

# region [TODO]


# endregion [TODO]

# region [Logging]


# endregion[Logging]

# region [Constants]
get_dummy_profile_decorator_in_globals()
THIS_FILE_DIR = Path(__file__).parent.absolute()
log = get_logger(__name__)
# endregion[Constants]


def get_qsize_from_font(font: QFont, text: str) -> QSize:
    fm = QFontMetrics(font)
    return fm.boundingRect(text=text).size()


@attr.s(slots=True, auto_attribs=True, auto_detect=True, weakref_slot=True)
class RefreshItem:
    record: "AbstractRecord" = attr.ib()
    idx: int = attr.ib()


class LogRecordsModel(BaseQueryDataModel):
    request_view_change_visibility = Signal(bool)

    extra_columns = set()
    strict_exclude_columns = {"record_class"}
    bool_images = {True: AllResourceItems.check_mark_green_image.get_as_icon(),
                   False: AllResourceItems.close_black_image.get_as_icon()}

    def __init__(self, parent=None) -> None:
        super().__init__(LogRecord, parent=parent)
        self.data_role_table = self.data_role_table | {Qt.BackgroundRole: self._get_background_data, Qt.FontRole: self._get_font_data, CustomRole.STD_COPY_DATA: self._get_std_copy_data}
        self._base_filter_item = (LogRecord.record_class != RecordClass.get(name="PerfProfilingRecord")) & (LogRecord.record_class != RecordClass.get(name="PerformanceRecord"))
        self.ordered_by = (LogRecord.start, LogRecord.recorded_at)
        self.message_font = self._create_message_font()
        self.proxy_model = BaseProxyModel()
        self.proxy_model.setSourceModel(self)
        self._refresh_task: Future = None
        self.collecting_records = False

    def set_message_font(self, font):
        self.layoutAboutToBeChanged.emit()
        self.message_font = font
        settings = QSettings()
        settings.setValue(f"{self.name}_message_font", font)
        self.layoutChanged.emit()

    @classmethod
    def _create_message_font(cls, reset: bool = False) -> QFont:
        settings = QSettings()
        font = settings.value(f"{cls.__name__}_message_font", None)
        if font is None or reset is True:
            font: QFont = QApplication.instance().font()
            font.setFamily("Lucida Console")

            font.setWeight(QFont.Light)
            font.setStyleHint(QFont.Monospace)
            font.setStyleStrategy(QFont.PreferQuality)

        return font

    def on_query_filter_changed(self, query_filter):
        self.filter_item = query_filter
        try:
            self.last_selection_ids = [i.id for i in self.parent().current_selected_items]

        except AttributeError:
            log.warning("AttributeError in on_query_filter_changed for %r", self)
            self.last_selection_ids = None
        self.refresh()

    def get_query(self) -> "Query":

        query = LogRecord.select().join_from(LogRecord, LogFile)
        if self._base_filter_item is not None:
            query = query.where(self._base_filter_item)
        if self.filter_item is not None:
            query = query.where(self.filter_item)

        return query.order_by(*self.ordered_by)

    def add_context_menu_actions(self, menu: "CustomContextMenu", index: QModelIndex):
        super().add_context_menu_actions(menu, index)
        item, column = self.get(index)

        if item is None or column is None:
            return
        if self.app.is_dev is True:
            reset_all_colors_action = QAction("Reset all Colors")
            reset_all_colors_action.triggered.connect(item.reset_colors)
            menu.add_action(reset_all_colors_action, "debug")

    @Slot(object, object, QModelIndex)
    def on_copy(self, item: "BaseRecord", column: Field, index: QModelIndex):
        text = item.get_formated_message(msg_format=MessageFormat.ORIGINAL)
        clipboard = self.app.clipboard()
        clipboard.setText(text)

    def _get_std_copy_data(self, index: "INDEX_TYPE"):
        item, column = self.get(index)
        return item.get_formated_message(msg_format=MessageFormat.ORIGINAL)

    def _get_display_data(self, index: "INDEX_TYPE") -> Any:
        item = self.content_items[index.row()]
        column = self.columns[index.column()]

        if column.name == "message":
            return str(item.message)
        data = item.get_data(column.name)
        if data is None:
            return self.on_display_data_none(role=Qt.DisplayRole, item=item, column=column)
        if isinstance(data, bool):
            return self.on_display_data_bool(role=Qt.DisplayRole, item=item, column=column, value=data)
        return str(data)

    def _get_background_data(self, index: "INDEX_TYPE") -> Any:
        item = self.content_items[index.row()]
        column = self.columns[index.column()]

        if item.log_level.name == "ERROR":
            return Color(value=(225, 25, 23, 0.5), typus=Color.color_typus.RGB, name="error_red").qcolor
        elif item.log_level.name == "WARNING":
            return Color(value=(255, 103, 0, 0.5), typus=Color.color_typus.RGB, name="warning_orange").qcolor

        if column.name == "log_level":
            return getattr(item, column.name).background_color

        try:
            return item.background_color
        except AttributeError:
            pass
        return super()._get_background_data(index)

    def _get_text_alignment_data(self, index: INDEX_TYPE) -> Any:
        if index.column_item.name in {"message"}:
            return None
        return super()._get_text_alignment_data(index)

    def _get_size_hint_data(self, index: INDEX_TYPE) -> Any:
        return QSize(0, self.message_font.pointSize() * 2)

    def _get_font_data(self, index: "INDEX_TYPE") -> Any:
        if index.column_item.name in {"message"}:
            return self.message_font
        return self.message_font

    def _get_record(self, _item_data, _all_log_files):
        record_class = self.backend.record_class_manager.get_by_id(_item_data.get('record_class'))
        log_file = _all_log_files[_item_data.get('log_file')]
        record_item = record_class.from_model_dict(_item_data, foreign_key_cache=self.backend.foreign_key_cache, log_file=log_file)

        return record_item

    def get_content(self) -> "LogRecordsModel":

        log.debug("starting getting content for %r", self)
        self.collecting_records = True
        all_log_files = {log_file.id: log_file for log_file in self.backend.database.get_log_files()}

        self.content_items = []
        records_getter = partial(self._get_record, _all_log_files=all_log_files)
        num_collected = 0
        for record_item in self.app.backend.thread_pool.map(records_getter, self.get_query().dicts().iterator()):

            self.content_items.append(record_item)
            # num_collected += 1
            # if num_collected % 1_000 == 0:
            #     sleep(0.0001)
        log.debug("finished getting content for %r", self)
        self.collecting_records = False
        return self

    def refresh(self) -> "BaseQueryDataModel":
        # self.request_view_change_visibility.emit(False)

        self.beginResetModel()
        self.get_columns().get_content()
        self.endResetModel()
        # self.request_view_change_visibility.emit(True)

        return self

    def refresh_item(self, index: "INDEX_TYPE"):
        item, column = self.get(index)

        setattr(item, column.name, getattr(self.db_model.get_by_id(item.id), column.name))


# region[Main_Exec]
if __name__ == '__main__':
    pass

# endregion[Main_Exec]
