"""
WiP.

Soon.
"""

# region [Imports]

# * Standard Library Imports ---------------------------------------------------------------------------->
from typing import TYPE_CHECKING, Optional
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
import PySide6
from PySide6 import (QtCore, QtGui, QtWidgets, Qt3DAnimation, Qt3DCore, Qt3DExtras, Qt3DInput, Qt3DLogic, Qt3DRender, QtAxContainer, QtBluetooth,
                     QtCharts, QtConcurrent, QtDataVisualization, QtDesigner, QtHelp, QtMultimedia, QtMultimediaWidgets, QtNetwork, QtNetworkAuth,
                     QtOpenGL, QtOpenGLWidgets, QtPositioning, QtPrintSupport, QtQml, QtQuick, QtQuickControls2, QtQuickWidgets, QtRemoteObjects,
                     QtScxml, QtSensors, QtSerialPort, QtSql, QtStateMachine, QtSvg, QtSvgWidgets, QtTest, QtUiTools, QtWebChannel, QtWebEngineCore,
                     QtWebEngineQuick, QtWebEngineWidgets, QtWebSockets, QtXml)

from PySide6.QtCore import (QByteArray, QCoreApplication, QDate, QDateTime, QEvent, QLocale, QMetaObject, QModelIndex, QModelRoleData, QMutex,
                            QMutexLocker, QObject, QPoint, QRect, QRecursiveMutex, QRunnable, QSettings, QSize, QThread, QThreadPool, QTime, QUrl,
                            QWaitCondition, Qt, QAbstractItemModel, QAbstractListModel, QAbstractTableModel, Signal, Slot)

from PySide6.QtGui import (QAction, QBrush, QColor, QConicalGradient, QCursor, QFont, QFontDatabase, QFontMetrics, QGradient, QIcon, QImage,
                           QKeySequence, QLinearGradient, QPainter, QPalette, QPixmap, QRadialGradient, QTransform)

from PySide6.QtWidgets import (QApplication, QBoxLayout, QCheckBox, QLCDNumber, QColorDialog, QColumnView, QComboBox, QDateTimeEdit, QDialogButtonBox,
                               QDockWidget, QDoubleSpinBox, QFontComboBox, QFormLayout, QFrame, QGridLayout, QGroupBox, QHBoxLayout, QHeaderView,
                               QLCDNumber, QLabel, QLayout, QLineEdit, QListView, QListWidget, QMainWindow, QMenu, QMenuBar, QMessageBox,
                               QProgressBar, QProgressDialog, QPushButton, QSizePolicy, QSpacerItem, QSpinBox, QStackedLayout, QStackedWidget,
                               QStatusBar, QStyledItemDelegate, QSystemTrayIcon, QTabWidget, QTableView, QTextEdit, QTimeEdit, QToolBox, QTreeView,
                               QVBoxLayout, QWidget, QAbstractItemDelegate, QAbstractItemView, QAbstractScrollArea, QRadioButton, QFileDialog, QButtonGroup)

from matplotlib.cm import ScalarMappable
from matplotlib.colors import Normalize, get_named_colors_mapping
from matplotlib import pyplot as plt
from matplotlib import patheffects
from matplotlib import cm
from io import BytesIO
from threading import Thread
import matplotlib.dates as mdates
# * Gid Imports ----------------------------------------------------------------------------------------->
from gidapptools import get_logger
from antistasi_logbook.gui.widgets.dock_widget import BaseDockWidget
from antistasi_logbook.storage.models.models import Server, LogFile, RecordClass
import pyqtgraph as pg
from antistasi_logbook.gui.widgets.detail_view_widget import ServerDetailWidget, LogFileDetailWidget, LogRecordDetailView
from antistasi_logbook.gui.widgets.data_tool_widget import LogFileDataToolWidget
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
        self.query_widget: BaseDockWidget = None
        self.detail_widget: BaseDockWidget = None
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
        self.query_widget = BaseDockWidget(title="Query", parent=self.parent(), start_floating=True)

        view_action = self.query_widget.toggleViewAction()
        view_action.setText("Query")
        self.main_window.menubar.view_menu.addAction(view_action)
        self.main_window.addDockWidget(Qt.LeftDockWidgetArea, self.query_widget, Qt.Vertical)

    def setup_detail_widget(self) -> None:
        self.detail_widget = BaseDockWidget(title="Details", parent=self.parent(), start_floating=True)

        self.detail_widget.dockLocationChanged.connect(self.detail_widget_resize_on_undock)

        view_action = self.detail_widget.toggleViewAction()
        view_action.setText("Details")
        self.main_window.menubar.view_menu.addAction(view_action)
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

        self.log_files_tab = LogFilesQueryTreeView().setup()
        self.log_files_tab.doubleClicked.connect(self.query_log_file)
        self.main_tabs_widget.addTab(self.log_files_tab, self.log_files_tab.icon, self.log_files_tab.name)

        self.query_result_tab = LogRecordsQueryView(main_window=self.main_window).setup()

        # self.query_result_tab.verticalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.main_tabs_widget.addTab(self.query_result_tab, AllResourceItems.placeholder.get_as_icon(), "Log-Records")

        self.main_layout.addWidget(self.main_tabs_widget, 1, 1, 4, 3)
        self.main_tabs_widget.currentChanged.connect(self.on_tab_changed)

    def on_tab_changed(self, index: int):
        if index == self.main_tabs_widget.indexOf(self.log_files_tab):
            widget = LogFileDataToolWidget()
            self.query_widget.setWidget(widget)
            widget.get_page_by_name("filter").show_unparsable_check_box.toggled.connect(self.log_files_tab.model().change_show_unparsable)
            widget.get_page_by_name("filter").filter_by_server_changed.connect(self.log_files_tab.model().filter_by_server)
            widget.get_page_by_name("filter").time_span_filter_box.older_than_changed.connect(self.log_files_tab.model().on_filter_older_than)
            widget.get_page_by_name("filter").time_span_filter_box.newer_than_changed.connect(self.log_files_tab.model().on_filter_newer_than)
            widget.get_page_by_name("filter").filter_by_game_map_changed.connect(self.log_files_tab.model().filter_by_game_map)
            widget.get_page_by_name("filter").filter_by_new_campaign.toggled.connect(self.log_files_tab.model().on_filter_by_new_campaign)
        else:
            if self.query_widget.widget() is not None:
                self.query_widget.setWidget(QWidget())

    def setup_views(self) -> None:
        server_model = ServerModel(self.main_window.backend)
        server_model.refresh()
        self.server_tab.setModel(server_model)
        self.server_tab.clicked.connect(self.show_server_detail)

        log_file_model = LogFilesModel(self.main_window.backend)
        log_file_model.refresh()
        self.log_files_tab.setModel(log_file_model)
        self.log_files_tab.clicked.connect(self.show_log_file_detail)

    def show_server_detail(self, index):
        item = self.server_tab.model().content_items[index.row()]
        view = ServerDetailWidget(server=item, parent=self.detail_widget)

        self.detail_widget.setWidget(view)
        view.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.MinimumExpanding)

        self.detail_widget.setMinimumSize(300, 100)

        view.repaint()
        self.detail_widget.show_if_first()

    def show_log_file_detail(self, index):
        item = self.log_files_tab.model().content_items[index.row()]
        view = LogFileDetailWidget(log_file=item, parent=self.detail_widget)

        self.detail_widget.setWidget(view)
        view.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Minimum)
        self.detail_widget.setMinimumSize(450, 500)

        view.repaint()
        self.detail_widget.show_if_first()

    def show_log_record_detail(self, index):
        item = self.query_result_tab.model().content_items[index.row()]
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

        log_file = self.log_files_tab.model().content_items[index.row()]
        log_record_model = LogRecordsModel(self.main_window.backend, parent=self.query_result_tab, filter_data={"log_files": (LogRecord.log_file_id == log_file.id)})
        log_record_model.refresh()

        self.query_result_tab.setModel(log_record_model)
        self.main_tabs_widget.setCurrentWidget(self.query_result_tab)
        self.query_result_tab.clicked.connect(self.show_log_record_detail)


# region[Main_Exec]
if __name__ == '__main__':
    pass

# endregion[Main_Exec]
