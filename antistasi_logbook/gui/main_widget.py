"""
WiP.

Soon.
"""

# region [Imports]

# * Standard Library Imports ---------------------------------------------------------------------------->
from typing import TYPE_CHECKING
from pathlib import Path
from threading import Event

# * Third Party Imports --------------------------------------------------------------------------------->
from antistasi_logbook.storage.models.models import LogRecord
from antistasi_logbook.gui.models.server_model import ServerModel
from antistasi_logbook.gui.models.log_files_model import LogFilesModel
from antistasi_logbook.gui.models.log_records_model import LogRecordsModel
from antistasi_logbook.gui.views.base_query_tree_view import ServerQueryTreeView, LogFilesQueryTreeView
from antistasi_logbook.gui.views.log_records_query_view import LogRecordsQueryView
from antistasi_logbook.gui.resources.antistasi_logbook_resources_accessor import AllResourceItems

# * PyQt5 Imports --------------------------------------------------------------------------------------->
from PySide6.QtCore import Qt, QSize, QModelIndex
from PySide6.QtWidgets import QWidget, QGroupBox, QTabWidget, QDockWidget, QGridLayout, QSizePolicy

# * Gid Imports ----------------------------------------------------------------------------------------->
from gidapptools import get_logger

if TYPE_CHECKING:
    # * Third Party Imports --------------------------------------------------------------------------------->
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


class MainWidget(QWidget):
    query_result_finished = Event()

    def __init__(self, main_window: "AntistasiLogbookMainWindow") -> None:
        super().__init__(parent=main_window)
        self.main_window = main_window
        self.info_widget: QGroupBox = None
        self.query_widget: QDockWidget = None
        self.detail_widget: QDockWidget = None
        self.main_tabs_widget: QTabWidget = None
        self.server_tab: ServerQueryTreeView = None
        self.log_files_tab: LogFilesQueryTreeView = None
        self.query_result_tab: LogRecordsQueryView = None
        self.temp_runnable = None
        self.setup()

    def setup(self) -> None:
        self.main_layout = QGridLayout(self)
        self.setLayout(self.main_layout)
        self.setup_info_widget()
        self.setup_query_widget()
        self.setup_detail_widget()
        self.setup_main_tabs_widget()

    def setup_info_widget(self) -> None:
        self.info_widget = QGroupBox(self)
        self.info_widget.setMinimumSize(QSize(0, 50))
        self.info_widget.setMaximumSize(QSize(16777215, 50))
        self.main_layout.addWidget(self.info_widget, 0, 0, 1, 3)

    def setup_query_widget(self) -> None:
        self.query_widget = QDockWidget("Query", self.parent())
        self.query_widget.setMinimumSize(QSize(100, 75))
        self.query_widget.setAllowedAreas(Qt.LeftDockWidgetArea)
        self.query_widget.setFeatures(QDockWidget.DockWidgetMovable | QDockWidget.DockWidgetFloatable | QDockWidget.DockWidgetClosable)
        view_action = self.query_widget.toggleViewAction()
        view_action.setText("Query")
        self.main_window.menubar.view_menu.addAction(view_action)
        self.main_window.addDockWidget(Qt.LeftDockWidgetArea, self.query_widget)
        # self.main_layout.addWidget(self.query_widget, 1, 0, 1, 1)

    def setup_detail_widget(self) -> None:
        self.detail_widget = QDockWidget("Details", self.parent())
        self.detail_widget.setMinimumSize(QSize(175, 100))

        self.detail_widget.setAllowedAreas(Qt.RightDockWidgetArea)
        self.detail_widget.setFeatures(QDockWidget.DockWidgetMovable | QDockWidget.DockWidgetFloatable | QDockWidget.DockWidgetClosable)
        self.detail_widget.setSizePolicy(QSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.MinimumExpanding))
        self.detail_widget.dockLocationChanged.connect(self.detail_widget_resize_on_undock)
        self.detail_widget.featuresChanged.connect(print)
        view_action = self.detail_widget.toggleViewAction()
        view_action.setText("Details")
        self.main_window.menubar.view_menu.addAction(view_action)
        self.main_window.addDockWidget(Qt.RightDockWidgetArea, self.detail_widget)
        self.detail_widget.hide()

    def setup_main_tabs_widget(self) -> None:
        self.main_tabs_widget = QTabWidget(self)
        size_policy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        size_policy.setHorizontalStretch(2)
        size_policy.setVerticalStretch(0)
        self.main_tabs_widget.setSizePolicy(size_policy)
        self.main_tabs_widget.setMinimumSize(QSize(250, 100))

        self.server_tab = ServerQueryTreeView().setup()

        self.main_tabs_widget.addTab(self.server_tab, self.server_tab.icon, self.server_tab.name)

        self.log_files_tab = LogFilesQueryTreeView().setup()
        self.log_files_tab.doubleClicked.connect(self.query_log_file)
        self.main_tabs_widget.addTab(self.log_files_tab, self.log_files_tab.icon, self.log_files_tab.name)

        self.query_result_tab = LogRecordsQueryView(main_window=self.main_window).setup()

        # self.query_result_tab.verticalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.main_tabs_widget.addTab(self.query_result_tab, AllResourceItems.placeholder.get_as_icon(), "Log-Records")

        self.main_layout.addWidget(self.main_tabs_widget, 1, 1, 1, 1)

    def setup_views(self) -> None:
        server_model = ServerModel(self.main_window.backend)
        server_model.generator_refresh()
        self.server_tab.setModel(server_model)

        log_file_model = LogFilesModel(self.main_window.backend)
        log_file_model.generator_refresh()
        self.log_files_tab.setModel(log_file_model)

    def detail_widget_resize_on_undock(self, area: Qt.DockWidgetArea) -> None:
        if area == Qt.NoDockWidgetArea:
            self.detail_widget.adjustSize()

    def query_log_file(self, index: QModelIndex):

        if self.query_result_finished.is_set() is True:
            log.debug("Unable to aquire the lock %r, returning", self.query_result_lock)
            return
        self.query_result_finished.set()
        log_file = self.log_files_tab.model().content_items[index.row()]

        log_record_model = LogRecordsModel(self.main_window.backend, parent=self.query_result_tab, filter_data=(LogRecord.log_file_id == log_file.id,))

        abort_signal = Event()

        def _set_model():
            self.query_result_tab.setModel(log_record_model)
        log_record_model.first_data_available.connect(_set_model)
        thread = log_record_model.generator_refresh(abort_signal=abort_signal)
        thread.finished.connect(self.query_result_finished.clear)

        thread.finished.connect(self.query_result_tab.resize_columns)
        self.main_tabs_widget.setCurrentWidget(self.query_result_tab)
        log.debug("started thread")


# region[Main_Exec]
if __name__ == '__main__':
    pass

# endregion[Main_Exec]
