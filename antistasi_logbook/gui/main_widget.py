"""
WiP.

Soon.
"""

# region [Imports]

# * Standard Library Imports ---------------------------------------------------------------------------->
from typing import TYPE_CHECKING, Optional
from pathlib import Path
from threading import Event

# * Qt Imports --------------------------------------------------------------------------------------->
import PySide6
from PySide6.QtGui import QMovie
from PySide6.QtCore import Qt, QSize, Signal, QThread, QByteArray, QModelIndex
from PySide6.QtWidgets import QLabel, QDialog, QWidget, QGroupBox, QTabWidget, QGridLayout, QSizePolicy, QVBoxLayout, QApplication

# * Gid Imports ----------------------------------------------------------------------------------------->
from gidapptools import get_logger

# * Local Imports --------------------------------------------------------------------------------------->
from antistasi_logbook.storage.models.models import LogRecord
from antistasi_logbook.gui.models.server_model import ServerModel
from antistasi_logbook.gui.widgets.dock_widget import QueryWidget, BaseDockWidget
from antistasi_logbook.gui.models.log_files_model import LogFilesModel
from antistasi_logbook.gui.views.server_query_view import ServerQueryTreeView
from antistasi_logbook.gui.models.log_records_model import LogRecordsModel
from antistasi_logbook.gui.widgets.data_tool_widget import ServerDataToolWidget, LogFileDataToolWidget, LogRecordDataToolWidget
from antistasi_logbook.gui.views.log_files_query_view import LogFilesQueryTreeView
from antistasi_logbook.gui.widgets.detail_view_widget import ServerDetailWidget, LogFileDetailWidget, LogRecordDetailView
from antistasi_logbook.gui.views.log_records_query_view import LogRecordsQueryView
from antistasi_logbook.gui.resources.antistasi_logbook_resources_accessor import AllResourceItems

# * Type-Checking Imports --------------------------------------------------------------------------------->
if TYPE_CHECKING:
    from antistasi_logbook.gui.application import AntistasiLogbookApplication
    from antistasi_logbook.gui.main_window import AntistasiLogbookMainWindow

# endregion[Imports]

# region [TODO]


# endregion [TODO]

# region [Logging]


# endregion[Logging]

# region [Constants]

THIS_FILE_DIR = Path(__file__).parent.absolute()
log = get_logger(__name__)
# endregion[Constants]


class SpinnerWidget(QDialog):

    def __init__(self, parent=None) -> None:
        super().__init__(parent, Qt.WindowStaysOnTopHint)
        self.setLayout(QVBoxLayout(self))
        self.setModal(True)

    def setup_movie(self):
        self.spinner_screen = QLabel()
        self.spinner_movie = QMovie(AllResourceItems.spinner_gif.qt_path, QByteArray(), self)
        self.spinner_movie.setCacheMode(QMovie.CacheAll)
        self.spinner_movie.setSpeed(100)
        self.spinner_screen.setAlignment(Qt.AlignCenter)
        self.spinner_screen.setMovie(self.spinner_movie)
        self.layout().addWidget(self.spinner_screen)
        self.spinner_movie.start()

    def close(self) -> bool:
        self.spinner_movie.stop()
        return super().close()


class Spinner(QThread):

    def __init__(self, parent: Optional[PySide6.QtCore.QObject] = None) -> None:
        super().__init__(parent=parent)
        self.term_requested = False

    def run(self) -> None:
        while self.term_requested is False:
            self.sleep(5)

    def request_term(self):
        self.term_requested = True


class MainWidget(QWidget):
    query_result_finished = Event()
    stop_spinner = Signal()

    def __init__(self, main_window: "AntistasiLogbookMainWindow") -> None:
        super().__init__(parent=main_window)
        self.main_window = main_window

        self.query_widget: QueryWidget = None
        self.detail_widget: BaseDockWidget = None
        self.main_tabs_widget: QTabWidget = None
        self.server_tab: ServerQueryTreeView = None
        self.log_files_tab: LogFilesQueryTreeView = None
        self.query_result_tab: LogRecordsQueryView = None

        self.temp_runnable = None
        self.setup()

    @property
    def app(self) -> "AntistasiLogbookApplication":
        return QApplication.instance()

    def setup(self) -> None:
        self.main_layout = QGridLayout(self)

        self.setLayout(self.main_layout)

        self.setup_query_widget()
        self.setup_detail_widget()
        self.setup_main_tabs_widget()

    def _clear_temp_runnable(self):
        self.temp_runnable = None

    def setup_query_widget(self) -> None:
        self.query_widget = QueryWidget(parent=self.parent(), add_to_menu=self.main_window.menubar.windows_menu, start_floating=False)
        main_window_size: QSize = self.main_window.size()
        self.query_widget.move(150, main_window_size.height() // 2)

        self.main_window.addDockWidget(Qt.LeftDockWidgetArea, self.query_widget, Qt.Vertical)

    def setup_detail_widget(self) -> None:
        self.detail_widget = BaseDockWidget(title="Details", parent=self.parent(), start_floating=False, add_to_menu=self.main_window.menubar.windows_menu)
        main_window_size: QSize = self.main_window.size()
        self.detail_widget.move(main_window_size.width() + (main_window_size.width() // 8), main_window_size.height() // 2)
        self.detail_widget.dockLocationChanged.connect(self.detail_widget_resize_on_undock)

        self.main_window.addDockWidget(Qt.RightDockWidgetArea, self.detail_widget, Qt.Vertical)

    def setup_main_tabs_widget(self) -> None:
        self.main_tabs_widget = QTabWidget(self)
        size_policy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        size_policy.setHorizontalStretch(2)
        size_policy.setVerticalStretch(0)
        self.main_tabs_widget.setSizePolicy(size_policy)
        self.main_tabs_widget.setMinimumSize(QSize(250, 100))

        self.server_tab = ServerQueryTreeView().setup()

        self.main_tabs_widget.addTab(self.server_tab, self.server_tab.icon, self.server_tab.name)
        old_icon_size = self.main_tabs_widget.iconSize()
        new_icon_size = QSize(old_icon_size.width() * 1.25, old_icon_size.height() * 1.25)
        self.main_tabs_widget.setIconSize(new_icon_size)
        self.log_files_tab = LogFilesQueryTreeView().setup()
        self.log_files_tab.doubleClicked.connect(self.query_log_file)
        self.main_tabs_widget.addTab(self.log_files_tab, self.log_files_tab.icon, self.log_files_tab.name)

        self.query_result_tab = LogRecordsQueryView().setup()
        self.query_result_tab.about_to_screenshot.connect(self.hide_dock_widgets)
        self.query_result_tab.screenshot_finished.connect(self.unhide_dock_widgets)

        # self.query_result_tab.verticalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.main_tabs_widget.addTab(self.query_result_tab, self.query_result_tab.icon, "Log-Records")

        self.main_layout.addWidget(self.main_tabs_widget, 1, 1, 4, 3)
        self.main_tabs_widget.currentChanged.connect(self.on_tab_changed)

    def unhide_dock_widgets(self):
        self.detail_widget.setVisible(True)
        self.query_widget.setVisible(True)

    def hide_dock_widgets(self):
        self.detail_widget.setVisible(False)
        self.query_widget.setVisible(False)

    def on_tab_changed(self, index: int):

        if index == self.main_tabs_widget.indexOf(self.log_files_tab):
            if self.log_files_tab.model is None:

                return
            if self.log_files_tab.model.data_tool is None:

                widget = LogFileDataToolWidget()
                self.query_widget.add_page(widget, name="log_file")
                self.log_files_tab.model.data_tool = widget
                widget.pages["filter"].query_filter_changed.connect(self.log_files_tab.model.on_query_filter_changed)

            self.query_widget.set_current_index(self.log_files_tab.model.data_tool)
            self.query_widget.resize(self.query_widget.sizeHint())
            self.log_files_tab.resize_header_sections()

        elif index == self.main_tabs_widget.indexOf(self.server_tab):
            if self.server_tab.model is None:

                return
            if self.server_tab.model.data_tool is None:

                widget = ServerDataToolWidget()
                self.query_widget.add_page(widget, name="server")
                self.server_tab.model.data_tool = widget
                widget.pages["filter"].query_filter_changed.connect(self.server_tab.model.on_query_filter_changed)
            self.query_widget.set_current_index(self.server_tab.model.data_tool)
            self.query_widget.resize(self.query_widget.sizeHint())
            self.server_tab.resize_header_sections()
        elif index == self.main_tabs_widget.indexOf(self.query_result_tab):
            if self.query_result_tab.model is None:
                self.query_widget.resize(self.query_widget.sizeHint())
                return
            if self.query_result_tab.model.data_tool is None:
                widget = LogRecordDataToolWidget()
                self.query_widget.add_page(widget, name="log_record")
                self.query_result_tab.model.data_tool = widget
                for page in widget.pages.values():

                    self.query_result_tab.model.request_view_change_visibility.connect(page.setEnabled)

                widget.pages["filter"].query_filter_changed.connect(self.query_result_tab.model.on_query_filter_changed)
                widget.pages["search"].search_changed.connect(self.query_result_tab.filter)
            self.query_widget.set_current_index(self.query_result_tab.model.data_tool)
            self.query_widget.resize(self.query_widget.sizeHint())
            self.query_result_tab.resize_header_sections()
        self.query_widget.resize(self.query_widget.sizeHint())

    def setup_views(self) -> None:
        server_model = ServerModel()

        self.server_tab.setModel(server_model)

        self.server_tab.single_item_selected.connect(self.show_server_detail)
        self.on_tab_changed(0)
        log_file_model = LogFilesModel()

        self.log_files_tab.setModel(log_file_model)

        self.log_files_tab.resize_header_sections()
        self.log_files_tab.single_item_selected.connect(self.show_log_file_detail)

        self.log_files_tab.model.refresh()
        self.server_tab.model.refresh()

    def show_server_detail(self, index):
        item = self.server_tab.model.content_items[index.row()]
        view = ServerDetailWidget(server=item, parent=self.detail_widget)

        self.detail_widget.setWidget(view)
        view.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.MinimumExpanding)

        self.detail_widget.setMinimumSize(300, 100)

        view.repaint()
        self.detail_widget.show_if_first()

    def show_log_file_detail(self, index):
        item = self.log_files_tab.model.content_items[index.row()]
        view = LogFileDetailWidget(log_file=item, parent=self.detail_widget)

        self.detail_widget.setWidget(view)
        view.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Minimum)
        self.detail_widget.setMinimumSize(450, 500)

        view.repaint()
        self.detail_widget.show_if_first()

    def show_log_record_detail(self, index):
        item = self.query_result_tab.model.content_items[index.row()]

        view = LogRecordDetailView(record=item, parent=self.detail_widget)
        self.detail_widget.setWidget(view)
        view.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.MinimumExpanding)

        self.detail_widget.setMinimumSize(300, 100)

        view.repaint()
        self.detail_widget.show_if_first()

    def detail_widget_resize_on_undock(self, area: Qt.DockWidgetArea) -> None:
        if area == Qt.NoDockWidgetArea:
            self.detail_widget.adjustSize()

    def query_log_file(self, index: QModelIndex):

        log_file = self.log_files_tab.model.content_items[index.row()]
        log_record_model = LogRecordsModel(parent=self.query_result_tab)
        log_record_model._base_filter_item = log_record_model._base_filter_item & (LogRecord.log_file_id == log_file.id)
        log_record_model.request_view_change_visibility.connect(self.query_result_tab.setEnabled)
        log_record_model.request_view_change_visibility.connect(self.query_result_tab.setVisible)
        self.main_tabs_widget.setCurrentWidget(self.query_result_tab)

        self.query_result_tab.setModel(log_record_model)
        self.on_tab_changed(self.main_tabs_widget.currentIndex())

        self.query_result_tab.single_item_selected.connect(self.show_log_record_detail)


# region[Main_Exec]
if __name__ == '__main__':
    pass

# endregion[Main_Exec]
