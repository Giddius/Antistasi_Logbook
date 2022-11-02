"""
WiP.

Soon.
"""

# region [Imports]

# * Standard Library Imports ---------------------------------------------------------------------------->
from typing import TYPE_CHECKING, Optional
from pathlib import Path
from datetime import datetime, timezone, timedelta
from operator import and_
from functools import reduce, cached_property

# * Qt Imports --------------------------------------------------------------------------------------->
import PySide6
from PySide6.QtGui import QIcon
from PySide6.QtCore import Qt, QSize, QTimer, Signal, QLocale, QDateTime, QRegularExpression, QSortFilterProxyModel
from PySide6.QtWidgets import QWidget, QToolBox, QCheckBox, QComboBox, QGroupBox, QLineEdit, QCompleter, QFormLayout, QGridLayout, QHBoxLayout, QApplication, QRadioButton, QDateTimeEdit

# * Third Party Imports --------------------------------------------------------------------------------->
from tzlocal import get_localzone
from dateutil.tz import UTC

# * Gid Imports ----------------------------------------------------------------------------------------->
from gidapptools import get_logger

# * Local Imports --------------------------------------------------------------------------------------->
from antistasi_logbook.gui.models import LogLevelsModel, ArmaFunctionModel, RecordClassesModel, RecordOriginsModel
from antistasi_logbook.storage.models.models import Server, LogFile, LogLevel, LogRecord, RecordClass, ArmaFunction
from antistasi_logbook.gui.models.server_model import ServerModel
from antistasi_logbook.gui.models.version_model import VersionModel
from antistasi_logbook.gui.models.game_map_model import GameMapModel
from antistasi_logbook.gui.models.log_records_model import LogRecordsModel
from antistasi_logbook.gui.models.base_query_data_model import EmptyContentItem
from antistasi_logbook.gui.models.remote_storages_model import RemoteStoragesModel
from antistasi_logbook.gui.resources.antistasi_logbook_resources_accessor import AllResourceItems

# * Type-Checking Imports --------------------------------------------------------------------------------->
if TYPE_CHECKING:
    from gidapptools.gid_config.interface import GidIniConfig

    from antistasi_logbook.backend import Backend
    from antistasi_logbook.gui.application import AntistasiLogbookApplication

# endregion[Imports]

# region [TODO]


# endregion [TODO]

# region [Logging]


# endregion[Logging]

# region [Constants]

THIS_FILE_DIR = Path(__file__).parent.absolute()
log = get_logger(__name__)
# endregion[Constants]


def _get_local_utc_offset_string():
    value = int(get_localzone()._zone.utcoffset(datetime.now()).total_seconds() // 3600)
    if value > 0:
        return f"+{value!s}"

    return f"{value!s}"


class BaseDataToolPage(QWidget):
    name: str = None
    icon_name: str = None

    def __init__(self, parent: Optional[PySide6.QtWidgets.QWidget] = None) -> None:
        super().__init__(parent=parent)
        self.setLayout(QFormLayout(self))
        self.layout.setLabelAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        font = self.font()
        font.setPointSizeF(font.pointSizeF() * 0.8)
        self.setFont(font)

    @property
    def app(self) -> "AntistasiLogbookApplication":
        return QApplication.instance()

    @property
    def backend(self) -> "Backend":
        return self.app.backend

    @property
    def config(self) -> "GidIniConfig":
        return self.app.config

    @property
    def layout(self) -> QFormLayout:
        return super().layout()

    @cached_property
    def icon(self) -> Optional[QIcon]:
        if self.icon_name is None:
            return
        return getattr(AllResourceItems, self.icon_name).get_as_icon()


class BaseDataToolWidget(QWidget):
    def __init__(self, parent: Optional[PySide6.QtWidgets.QWidget] = None, ) -> None:

        self.pages: dict[str, BaseDataToolPage] = {}
        super().__init__(parent=parent)
        self.setLayout(QGridLayout(self))
        self.tool_box = QToolBox()
        self.layout.addWidget(self.tool_box)

        font = self.font()
        font.setPointSizeF(font.pointSizeF() * 0.8)
        self.setFont(font)
        self.tool_box.setFont(font)

    def add_page(self, page: BaseDataToolPage):
        if page.name is None or page.icon is None:

            raise AttributeError(f"{page} has to have 'name' and 'icon' set, {page.name=} , {page.icon=}.")

        self.tool_box.addItem(page, page.icon, page.name)
        self.pages[page.name.casefold()] = page
        for idx in range(page.layout.rowCount()):
            child = page.layout.itemAt(idx).widget()
            try:

                child.setFont(self.font())
            except Exception as e:
                log.critical("encountered error %r while setting font for child %r", e, child)
        page.repaint()

    def get_page_by_name(self, name: str) -> BaseDataToolPage:
        return self.pages[name.casefold()]

    @property
    def layout(self) -> QFormLayout:
        return super().layout()

    @property
    def app(self) -> "AntistasiLogbookApplication":
        return AntistasiLogbookApplication.instance()

    @property
    def backend(self) -> "Backend":
        return self.app.backend

    @property
    def config(self) -> "GidIniConfig":
        return self.app.config

    def sizeHint(self) -> QSize:
        widths = [500]
        heights = [250]
        for page in self.pages.values():
            page_size: QSize = page.sizeHint()
            widths.append(page_size.width())
            heights.append(page_size.height())

        max_width = max(widths)

        max_height = max(heights)

        return QSize(max_width, max_height)


class LogFileSearchPage(BaseDataToolPage):
    name: str = "Search"
    icon_name: str = "search_page_symbol_image"
    regex_changed = Signal(str, str)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.column_select_combo = QComboBox(self)
        self.column_select_combo.addItems(list(LogFile.get_meta().columns))
        self.layout.addRow("column", self.column_select_combo)
        self.regex_line_value = QLineEdit(self)
        self.layout.addRow("Regex", self.regex_line_value)
        self.column_select_combo.currentIndexChanged.connect(self.on_change)
        self.regex_line_value.textChanged.connect(self.on_change)

    def on_change(self, *args):
        column_name = self.column_select_combo.currentText()
        regex = self.regex_line_value.text()
        self.regex_changed.emit(column_name, regex)


class TimeSpanFilterWidget(QGroupBox):
    older_than_changed = Signal(datetime)
    newer_than_changed = Signal(datetime)

    def __init__(self, parent=None) -> None:
        super().__init__(parent=parent)
        self.setLayout(QFormLayout(self))
        self.timezone_selector = QComboBox()
        self.timezone_selector.addItems(["UTC", "LOCAL"])
        self.timezone_selector.currentTextChanged.connect(self.on_timezone_change)
        self.layout.addRow("Time-Zone", self.timezone_selector)

        self.use_newer_than_filter = QCheckBox(text='Only newer than')
        self.newer_than_selection = QDateTimeEdit(datetime.now(tz=UTC) - timedelta(days=1))
        self.newer_than_selection.setDisplayFormat(QLocale.system().dateTimeFormat(QLocale.LongFormat) + ' UTC')
        self.newer_than_selection.setCalendarPopup(True)
        self.newer_than_selection.setTimeSpec(Qt.UTC)
        self.newer_than_selection.setEnabled(False)
        self.use_newer_than_filter.toggled.connect(self.on_use_newer_than_filter_checked)
        self.newer_than_selection.dateTimeChanged.connect(self.on_newer_than_date_time_changed)
        self.layout.addRow(self.use_newer_than_filter, self.newer_than_selection)

        self.use_older_than_filter = QCheckBox(text='Only older than')
        self.older_than_selection = QDateTimeEdit(datetime.now(tz=UTC))
        self.older_than_selection.setDisplayFormat(QLocale.system().dateTimeFormat(QLocale.LongFormat) + ' UTC')
        self.older_than_selection.setCalendarPopup(True)
        self.older_than_selection.setTimeSpec(Qt.UTC)
        self.older_than_selection.setEnabled(False)
        self.use_older_than_filter.toggled.connect(self.on_use_older_than_filter_checked)
        self.older_than_selection.dateTimeChanged.connect(self.on_older_than_date_time_changed)
        self.layout.addRow(self.use_older_than_filter, self.older_than_selection)

    @property
    def app(self) -> "AntistasiLogbookApplication":
        return QApplication.instance()

    def on_timezone_change(self, text: str):
        if text == "UTC":
            self.newer_than_selection.setTimeSpec(Qt.UTC)
            self.newer_than_selection.setDisplayFormat(QLocale.system().dateTimeFormat(QLocale.LongFormat) + ' UTC')
            self.older_than_selection.setTimeSpec(Qt.UTC)
            self.older_than_selection.setDisplayFormat(QLocale.system().dateTimeFormat(QLocale.LongFormat) + ' UTC')

        elif text == "LOCAL":
            self.newer_than_selection.setTimeSpec(Qt.TimeZone)
            self.newer_than_selection.setDisplayFormat(QLocale.system().dateTimeFormat(QLocale.LongFormat) + ' ' + _get_local_utc_offset_string())
            self.older_than_selection.setTimeSpec(Qt.TimeZone)
            self.older_than_selection.setDisplayFormat(QLocale.system().dateTimeFormat(QLocale.LongFormat) + ' ' + _get_local_utc_offset_string())

    def on_newer_than_date_time_changed(self, dt: QDateTime):
        py_dt: datetime = dt.toPython()
        log.debug("newer than raw_datetime=%r", py_dt)
        py_dt = py_dt.astimezone(tz=UTC)
        self.newer_than_changed.emit(py_dt)

    def on_older_than_date_time_changed(self, dt: QDateTime):
        py_dt: datetime = dt.toPython()
        log.debug("older than raw_datetime=%r", py_dt)
        py_dt = py_dt.astimezone(tz=UTC)
        self.older_than_changed.emit(py_dt)

    def on_use_newer_than_filter_checked(self, checked: bool):
        self.newer_than_selection.setEnabled(checked)
        if checked:
            self.newer_than_changed.emit(self.newer_than_selection.dateTime())
        else:
            self.newer_than_changed.emit(None)

    def on_use_older_than_filter_checked(self, checked: bool):
        self.older_than_selection.setEnabled(checked)
        if checked:
            self.older_than_changed.emit(self.older_than_selection.dateTime())
        else:
            self.older_than_changed.emit(None)

    @property
    def layout(self) -> QFormLayout:
        return super().layout()


class LogFileFilterPage(BaseDataToolPage):
    name: str = "Filter"
    icon_name: str = "filter_page_symbol_image"
    query_filter_changed = Signal(object)

    def __init__(self, parent: Optional[PySide6.QtWidgets.QWidget] = None) -> None:
        super().__init__(parent=parent)

        self.filter_by_server_combo_box = QComboBox()
        server_model = ServerModel().refresh()
        server_model.add_empty_item()
        self.filter_by_server_combo_box.setModel(server_model)
        self.filter_by_server_combo_box.setModelColumn(self.filter_by_server_combo_box.model().get_column_index("name"))
        self.filter_by_server_combo_box.setCurrentIndex(-1)
        self.layout.addRow("Filter by Server", self.filter_by_server_combo_box)

        self.time_span_filter_box = TimeSpanFilterWidget()
        self.layout.addRow("Filter by Modified at", self.time_span_filter_box)

        self.filter_by_game_map_combo_box = QComboBox()
        game_map_model = GameMapModel().refresh()
        game_map_model.add_empty_item()
        self.filter_by_game_map_combo_box.setModel(game_map_model)
        self.filter_by_game_map_combo_box.setModelColumn(game_map_model.get_column_index("name"))
        self.filter_by_game_map_combo_box.setCurrentIndex(-1)
        self.layout.addRow("Filter by Game Map", self.filter_by_game_map_combo_box)

        self.filter_by_version_combo_box = QComboBox()
        version_model = VersionModel().refresh()
        version_model.add_empty_item()
        self.filter_by_version_combo_box.setModel(version_model)
        self.filter_by_version_combo_box.setModelColumn(version_model.get_column_index("full"))
        self.filter_by_version_combo_box.setCurrentIndex(-1)
        self.layout.addRow("Filter by Version", self.filter_by_version_combo_box)

        self.filter_by_campaign_id_combo_box = QComboBox()
        self.filter_by_campaign_id_combo_box.addItem("")
        self.filter_by_campaign_id_combo_box.addItems([str(i) for i in self.app.backend.database.get_unique_campaign_ids()])
        self.layout.addRow("Filter by Campaign-ID", self.filter_by_campaign_id_combo_box)

        self.filter_by_new_campaign = QCheckBox()

        self.layout.addRow("Show only new campaigns", self.filter_by_new_campaign)

        self.filter_by_marked = QCheckBox()
        self.layout.addRow("Show only Marked", self.filter_by_marked)

        self.show_unparsable_check_box = QCheckBox()
        self.layout.addRow("Show Unparsable", self.show_unparsable_check_box)

    def setup(self) -> "LogFileFilterPage":
        self.setup_signals()

        return self

    def setup_signals(self):
        self.filter_by_server_combo_box.currentTextChanged.connect(self.on_change)
        self.time_span_filter_box.use_newer_than_filter.toggled.connect(self.on_change)
        self.time_span_filter_box.use_older_than_filter.toggled.connect(self.on_change)
        self.time_span_filter_box.newer_than_selection.dateTimeChanged.connect(self.on_change)
        self.time_span_filter_box.older_than_selection.dateTimeChanged.connect(self.on_change)
        self.filter_by_game_map_combo_box.currentTextChanged.connect(self.on_change)
        self.filter_by_new_campaign.toggled.connect(self.on_change)
        self.filter_by_marked.toggled.connect(self.on_change)
        self.filter_by_version_combo_box.currentIndexChanged.connect(self.on_change)
        self.filter_by_campaign_id_combo_box.currentIndexChanged.connect(self.on_change)

    def collect_query_filters(self):
        query_filter = []

        server = self.filter_by_server_combo_box.model().content_items[self.filter_by_server_combo_box.currentIndex()]
        if not isinstance(server, EmptyContentItem):
            query_filter.append((LogFile.server_id == server.id))

        if self.time_span_filter_box.use_newer_than_filter.isChecked():
            date_time: datetime = self.time_span_filter_box.newer_than_selection.dateTime().toPython()
            if self.time_span_filter_box.timezone_selector.currentText() == "UTC":
                date_time = date_time.replace(tzinfo=timezone.utc)
            elif self.time_span_filter_box.timezone_selector.currentText().casefold() == "local":
                date_time = date_time.replace(tzinfo=get_localzone()).astimezone(timezone.utc)
            query_filter.append((LogFile.modified_at > date_time))

        if self.time_span_filter_box.use_older_than_filter.isChecked():
            date_time: datetime = self.time_span_filter_box.older_than_selection.dateTime().toPython()
            if self.time_span_filter_box.timezone_selector.currentText() == "UTC":
                date_time = date_time.replace(tzinfo=timezone.utc)
            elif self.time_span_filter_box.timezone_selector.currentText().casefold() == "local":
                date_time = date_time.replace(tzinfo=get_localzone()).astimezone(timezone.utc)
            query_filter.append((LogFile.modified_at < date_time))

        if self.filter_by_marked.isChecked():
            query_filter.append((LogFile.marked == True))

        game_map = self.filter_by_game_map_combo_box.model().content_items[self.filter_by_game_map_combo_box.currentIndex()]
        if not isinstance(game_map, EmptyContentItem):
            query_filter.append((LogFile.game_map_id == game_map.id))

        campaign_id = self.filter_by_campaign_id_combo_box.currentText()
        if campaign_id != "":
            query_filter.append((LogFile.campaign_id == int(campaign_id)))

        if self.filter_by_new_campaign.isChecked():
            query_filter.append((LogFile.is_new_campaign == True))

        version = self.filter_by_version_combo_box.model().content_items[self.filter_by_version_combo_box.currentIndex()]
        if not isinstance(version, EmptyContentItem):
            query_filter.append((LogFile.version_id == version.id))

        if query_filter:
            return reduce(and_, query_filter)
        return None

    def on_change(self, *args):
        query_filter = self.collect_query_filters()
        self.query_filter_changed.emit(query_filter)


class LogFileDataToolWidget(BaseDataToolWidget):

    def __init__(self, parent: Optional[PySide6.QtWidgets.QWidget] = None) -> None:
        super().__init__(parent=parent)

        self.add_page(LogFileFilterPage(self).setup())


class ServerFilterPage(BaseDataToolPage):
    name: str = "Filter"
    icon_name: str = "filter_page_symbol_image"
    query_filter_changed = Signal(object)

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent=parent)

        self.filter_by_ip_combo_box = QComboBox()
        self.filter_by_ip_combo_box.addItem("")
        self.filter_by_ip_combo_box.addItems(self.app.backend.database.get_unique_server_ips())
        self.layout.addRow("Filter by IP", self.filter_by_ip_combo_box)

        self.filter_by_remote_storage = QComboBox()
        remote_storage_model = RemoteStoragesModel().refresh()
        remote_storage_model.add_empty_item()
        self.filter_by_remote_storage.setModel(remote_storage_model)
        self.filter_by_remote_storage.setModelColumn(remote_storage_model.get_column_index("name"))
        self.filter_by_remote_storage.setCurrentIndex(-1)
        self.layout.addRow("Filter by Remote-Storage", self.filter_by_remote_storage)

        self.filter_by_update_enabled = QCheckBox()
        self.layout.addRow("Show only Update-enabled", self.filter_by_update_enabled)

        self.filter_by_marked = QCheckBox()
        self.layout.addRow("Show only Marked", self.filter_by_marked)

    def setup(self) -> "ServerFilterPage":
        self.setup_signals()

        return self

    def setup_signals(self):
        self.filter_by_ip_combo_box.currentTextChanged.connect(self.on_change)
        self.filter_by_update_enabled.toggled.connect(self.on_change)
        self.filter_by_marked.toggled.connect(self.on_change)
        self.filter_by_remote_storage.currentIndexChanged.connect(self.on_change)

    def collect_query_filters(self):
        query_filter = []
        ip = self.filter_by_ip_combo_box.currentText()
        if ip != "":
            query_filter.append((Server.ip == ip))

        remote_storage = self.filter_by_remote_storage.model().content_items[self.filter_by_remote_storage.currentIndex()]
        if not isinstance(remote_storage, EmptyContentItem):
            query_filter.append((Server.remote_storage_id == remote_storage.id))

        if self.filter_by_update_enabled.isChecked():
            query_filter.append((Server.update_enabled == True))

        if self.filter_by_marked.isChecked():
            query_filter.append((Server.marked == True))

        if query_filter:
            return reduce(and_, query_filter)
        return None

    def on_change(self, *args):
        query_filter = self.collect_query_filters()
        self.query_filter_changed.emit(query_filter)


class ServerDataToolWidget(BaseDataToolWidget):

    def __init__(self, parent: Optional[PySide6.QtWidgets.QWidget] = None) -> None:
        super().__init__(parent=parent)

        self.add_page(ServerFilterPage().setup())


class AntistasiFunctionSelectComboBox(QComboBox):

    def __init__(self, parent: Optional[PySide6.QtWidgets.QWidget] = None) -> None:
        super().__init__(parent)

        self.setEditable(True)
        self.setFocusPolicy(Qt.ClickFocus)
        self.setInsertPolicy(QComboBox.NoInsert)
        self.pFilterModel = QSortFilterProxyModel(self)
        self.pFilterModel.setFilterCaseSensitivity(Qt.CaseInsensitive)
        self.pFilterModel.setSourceModel(self.model())
        self._completer = QCompleter(self.pFilterModel, self)

        self._completer.setCompletionMode(QCompleter.UnfilteredPopupCompletion)
        self.setCompleter(self._completer)
        self.lineEdit().textEdited.connect(self.pFilterModel.setFilterFixedString)
        self.currentIndexChanged.connect(self.on_index_change)

    def on_index_change(self, *args):

        self.setEditText(self.itemData(self.currentIndex(), Qt.DisplayRole))
        self.lineEdit().setPlaceholderText(self.itemData(self.currentIndex(), Qt.DisplayRole))

    def setModel(self, model):
        super().setModel(model)
        self.pFilterModel.setSourceModel(model)
        self._completer.setModel(self.pFilterModel)

    def setModelColumn(self, column):
        self._completer.setCompletionColumn(column)
        self.pFilterModel.setFilterKeyColumn(column)
        super().setModelColumn(column)


class LogRecordSearchPage(BaseDataToolPage):
    name: str = "Search"
    icon_name: str = "search_page_symbol_image"
    search_changed = Signal(bool, str, object)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.column_select_combo = QComboBox(self)
        items = list(LogRecord.get_meta().columns) + [ec.name for ec in LogRecordsModel.extra_columns]
        self.column_select_combo.addItems(items)
        self.column_select_combo.setCurrentIndex(items.index("message"))
        self.layout.addRow("column", self.column_select_combo)

        self.regex_select_box = QGroupBox(self)
        self.regex_select_box.setLayout(QHBoxLayout())
        self.regex_radio_button = QRadioButton("Regex", self.regex_select_box)
        self.plain_text_radio_button = QRadioButton("Plain Text", self.regex_select_box)
        self.plain_text_radio_button.setChecked(True)
        self.regex_select_box.layout().addWidget(self.regex_radio_button)
        self.regex_select_box.layout().addWidget(self.plain_text_radio_button)
        self.layout.addRow("Search Type", self.regex_select_box)

        self.regex_line_value = QLineEdit(self)
        self.regex_line_value.setClearButtonEnabled(True)
        self.layout.addRow("Regex", self.regex_line_value)

        self.column_select_combo.currentIndexChanged.connect(self.on_change)
        self.regex_line_value.textChanged.connect(self.delay_text_execution)
        self.regex_radio_button.toggled.connect(self.on_change)
        self.plain_text_radio_button.toggled.connect(self.on_change)
        self.timer: QTimer = None

    def delay_text_execution(self, *args):
        if self.timer is None or self.timer.isActive() is False:
            log.debug("creating timer for %r", self)
            self.timer = QTimer()
            self.timer.setSingleShot(True)
            self.timer.setTimerType(Qt.CoarseTimer)
            self.timer.timeout.connect(self.on_change)
        self.timer.start(1 * 1000)

    def on_change(self, *args):
        use_regex = self.regex_radio_button.isChecked()
        column_name = self.column_select_combo.currentText()
        text = self.regex_line_value.text()
        if use_regex is True:
            text = QRegularExpression(text, QRegularExpression.PatternOptions() | QRegularExpression.CaseInsensitiveOption)
            if text.isValid() is False:
                log.debug("regex %r is not valid", text)
                return
        self.search_changed.emit(use_regex, column_name, text)

    def setup(self) -> "LogRecordSearchPage":

        return self


class LogRecordFilterPage(BaseDataToolPage):
    name: str = "Filter"
    icon_name: str = "filter_page_symbol_image"
    query_filter_changed = Signal(object)

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.log_file = None
        self.filter_by_log_level_combo_box = QComboBox()
        log_level_model = LogLevelsModel().refresh()
        log_level_model.add_empty_item()
        self.filter_by_log_level_combo_box.setModel(log_level_model)
        self.filter_by_log_level_combo_box.setModelColumn(log_level_model.get_column_index("name"))
        self.filter_by_log_level_combo_box.setCurrentIndex(-1)

        self.layout.addRow("Filter by Log-Level", self.filter_by_log_level_combo_box)

        self.filter_by_logged_from_combo_box = AntistasiFunctionSelectComboBox()
        logged_from_model = ArmaFunctionModel()
        logged_from_model.ordered_by = (ArmaFunction.name,)
        logged_from_model.refresh()
        logged_from_model.add_empty_item()
        self.filter_by_logged_from_combo_box.setModel(logged_from_model)
        self.filter_by_logged_from_combo_box.setModelColumn(logged_from_model.get_column_index("function_name"))
        self.filter_by_logged_from_combo_box.setCurrentIndex(-1)

        self.layout.addRow("Filter by Logged-from", self.filter_by_logged_from_combo_box)

        self.filter_by_called_by_combo_box = AntistasiFunctionSelectComboBox()
        called_by_model = ArmaFunctionModel()
        called_by_model.ordered_by = (ArmaFunction.name,)
        called_by_model.refresh()
        called_by_model.add_empty_item()
        self.filter_by_called_by_combo_box.setModel(called_by_model)
        self.filter_by_called_by_combo_box.setModelColumn(logged_from_model.get_column_index("function_name"))
        self.filter_by_called_by_combo_box.setCurrentIndex(-1)

        self.layout.addRow("Filter by Called-by", self.filter_by_called_by_combo_box)

        self.filter_by_record_origin_combo_box = QComboBox()
        record_origin_model = RecordOriginsModel().refresh()
        record_origin_model.add_empty_item()
        self.filter_by_record_origin_combo_box.setModel(record_origin_model)
        self.filter_by_record_origin_combo_box.setModelColumn(record_origin_model.get_column_index("name"))
        self.filter_by_record_origin_combo_box.setCurrentIndex(-1)

        self.layout.addRow("Filter by Record-Origin", self.filter_by_record_origin_combo_box)

        self.filter_by_record_class_combo_box = QComboBox()
        record_class_model = RecordClassesModel().refresh()
        record_class_model.add_empty_item()
        self.filter_by_record_class_combo_box.setModel(record_class_model)
        self.filter_by_record_class_combo_box.setModelColumn(record_class_model.get_column_index("name"))
        self.filter_by_record_class_combo_box.setCurrentIndex(-1)
        self.layout.addRow("Filter by Record-Class", self.filter_by_record_class_combo_box)

        self.filter_by_marked = QCheckBox()
        self.layout.addRow("Show only Marked", self.filter_by_marked)

    def setup(self) -> "LogRecordFilterPage":
        self.setup_signals()

        return self

    def set_log_file(self, log_file: LogFile):
        self.log_file = log_file
        level_ids = [i.log_level.id for i in LogRecord.select(LogRecord.log_level).where(LogRecord.log_file_id == self.log_file.id).left_outer_join(LogLevel).distinct()]
        self.filter_by_log_level_combo_box.model().filter_item = (LogLevel.id << level_ids)
        self.filter_by_log_level_combo_box.model().refresh()
        self.filter_by_log_level_combo_box.model().add_empty_item()
        self.filter_by_log_level_combo_box.setCurrentIndex(-1)

        logged_from_ids = []
        for item in LogRecord.select(LogRecord.logged_from).where(LogRecord.log_file_id == self.log_file.id).left_outer_join(ArmaFunction, on=LogRecord.logged_from).distinct():
            try:
                logged_from_ids.append(item.logged_from.id)
            except AttributeError:
                continue

        self.filter_by_logged_from_combo_box.model().filter_item = (ArmaFunction.id << logged_from_ids)
        self.filter_by_logged_from_combo_box.model().refresh()
        self.filter_by_logged_from_combo_box.model().add_empty_item()
        self.filter_by_logged_from_combo_box.setCurrentIndex(-1)

        record_class_ids = [i.record_class.id for i in LogRecord.select(LogRecord.record_class).where(LogRecord.log_file_id == self.log_file.id).left_outer_join(RecordClass, on=LogRecord.record_class).distinct()]
        self.filter_by_record_class_combo_box.model().filter_item = (RecordClass.id << record_class_ids)
        self.filter_by_record_class_combo_box.model().refresh()
        self.filter_by_record_class_combo_box.model().add_empty_item()
        self.filter_by_record_class_combo_box.setCurrentIndex(-1)

    def setup_signals(self):
        self.filter_by_log_level_combo_box.currentIndexChanged.connect(self.on_change)
        self.filter_by_logged_from_combo_box.currentIndexChanged.connect(self.on_change)
        self.filter_by_called_by_combo_box.currentIndexChanged.connect(self.on_change)
        self.filter_by_record_origin_combo_box.currentIndexChanged.connect(self.on_change)
        self.filter_by_record_class_combo_box.currentIndexChanged.connect(self.on_change)
        self.filter_by_marked.toggled.connect(self.on_change)

    def collect_query_filters(self):
        query_filter = []

        log_level = self.filter_by_log_level_combo_box.model().content_items[self.filter_by_log_level_combo_box.currentIndex()]
        if not isinstance(log_level, EmptyContentItem):

            query_filter.append((LogRecord.log_level_id == log_level.id))

        logged_from = self.filter_by_logged_from_combo_box.model().content_items[self.filter_by_logged_from_combo_box.currentIndex()]
        if not isinstance(logged_from, EmptyContentItem):
            query_filter.append((LogRecord.logged_from_id == logged_from.id))

        called_by = self.filter_by_called_by_combo_box.model().content_items[self.filter_by_called_by_combo_box.currentIndex()]
        if not isinstance(called_by, EmptyContentItem):
            query_filter.append((LogRecord.called_by_id == called_by.id))

        record_origin = self.filter_by_record_origin_combo_box.model().content_items[self.filter_by_record_origin_combo_box.currentIndex()]
        if not isinstance(record_origin, EmptyContentItem):
            query_filter.append((LogRecord.origin_id == record_origin.id))

        record_class = self.filter_by_record_class_combo_box.model().content_items[self.filter_by_record_class_combo_box.currentIndex()]
        if not isinstance(record_class, EmptyContentItem):
            query_filter.append((LogRecord.record_class_id == record_class.id))

        if self.filter_by_marked.isChecked():
            query_filter.append((LogRecord.marked == True))

        if query_filter:
            return reduce(and_, query_filter)
        return None

    def on_change(self, *args):
        query_filter = self.collect_query_filters()
        self.query_filter_changed.emit(query_filter)


class LogRecordDataToolWidget(BaseDataToolWidget):

    def __init__(self, parent: Optional[PySide6.QtWidgets.QWidget] = None) -> None:
        super().__init__(parent=parent)

        self.add_page(LogRecordFilterPage(self))
        self.add_page(LogRecordSearchPage(self))

    def set_log_file(self, log_file: LogFile):
        log.debug("setting log_file %r", log_file)
        for page in self.pages.values():
            try:
                page.set_log_file(log_file)
            except AttributeError:
                continue
            page.setup()
        self.repaint()
# region[Main_Exec]


if __name__ == '__main__':
    pass

# endregion[Main_Exec]
