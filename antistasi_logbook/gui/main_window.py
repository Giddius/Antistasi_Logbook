
"""
WiP.

Soon.
"""


# region [Imports]

# * Standard Library Imports ---------------------------------------------------------------------------->
import sys
from typing import TYPE_CHECKING, Union, Optional
from pathlib import Path
from datetime import timedelta, datetime
from threading import Thread
from antistasi_logbook.utilities.date_time_utilities import DateTimeFrame
# * Qt Imports --------------------------------------------------------------------------------------->
from PySide6.QtGui import QColor, QCloseEvent
from PySide6.QtCore import Qt, Slot, QSize, QPoint, QTimer, Signal, QObject, QSysInfo, QSettings, QByteArray, QTimerEvent
from PySide6.QtWidgets import (QLabel, QWidget, QPushButton, QMenuBar, QToolBar, QDockWidget, QGridLayout, QHBoxLayout, QMainWindow,
                               QMessageBox, QSizePolicy, QVBoxLayout, QTableWidget, QSplashScreen, QTableWidgetItem)

# * Third Party Imports --------------------------------------------------------------------------------->
import qt_material

# * Gid Imports ----------------------------------------------------------------------------------------->
from gidapptools import get_logger, get_meta_info, get_meta_paths, get_meta_config
from gidapptools.gid_logger.misc import QtMessageHandler

from gidapptools.general_helper.string_helper import StringCaseConverter
from gidapptools.gidapptools_qt.widgets.app_log_viewer import StoredAppLogViewer
from gidapptools.gidapptools_qt.widgets.spinner_widget import BusyPushButton
from gidapptools.gidapptools_qt.widgets.std_stream_widget import StdStreamWidget

# * Local Imports --------------------------------------------------------------------------------------->
from antistasi_logbook import stream_capturer
from antistasi_logbook.errors import ExceptionHandlerManager, MissingLoginAndPasswordError
from antistasi_logbook.backend import Backend, GidSqliteApswDatabase
from antistasi_logbook.gui.misc import UpdaterSignaler
from antistasi_logbook.gui.models import LogLevelsModel, RecordOriginsModel
from antistasi_logbook.gui.menu_bar import LogbookMenuBar
from antistasi_logbook.gui.sys_tray import LogbookSystemTray
from antistasi_logbook.gui.status_bar import LogbookStatusBar
from antistasi_logbook.gui.application import AntistasiLogbookApplication
from antistasi_logbook.gui.main_widget import MainWidget
from antistasi_logbook.gui.settings_window import SettingsWindow, CredentialsManagmentWindow
from antistasi_logbook.gui.models.mods_model import ModsModel
from antistasi_logbook.gui.widgets.tool_bars import BaseToolBar
from antistasi_logbook.storage.models.models import GameMap, LogRecord
from antistasi_logbook.gui.models.version_model import VersionModel
from antistasi_logbook.gui.widgets.stats_viewer import AvgMapPlayersPlotWidget
from antistasi_logbook.gui.models.game_map_model import GameMapModel
from antistasi_logbook.gui.widgets.debug_widgets import DebugDockWidget
from antistasi_logbook.gui.resources.style_sheets import get_style_sheet_data
from antistasi_logbook.gui.models.arma_function_model import ArmaFunctionModel
from antistasi_logbook.gui.views.base_query_tree_view import BaseQueryTreeView
from antistasi_logbook.gui.models.record_classes_model import RecordClassesModel
from antistasi_logbook.gui.models.base_query_data_model import BaseQueryDataModel
from antistasi_logbook.gui.models.remote_storages_model import RemoteStoragesModel
from antistasi_logbook.gui.widgets.data_view_widget.data_view import DataView
from antistasi_logbook.gui.resources.antistasi_logbook_resources_accessor import AllResourceItems

# * Type-Checking Imports --------------------------------------------------------------------------------->
if TYPE_CHECKING:
    from gidapptools.gid_config.interface import GidIniConfig

    from antistasi_logbook.storage.models.models import BaseModel

# endregion[Imports]

# region [TODO]

# TODO: Refractor the Hell out of this and split it into classes and functions!

# endregion [TODO]

# region [Logging]


# endregion[Logging]

# region [Constants]


THIS_FILE_DIR = Path(__file__).parent.absolute()
log = get_logger(__name__)
META_CONFIG = get_meta_config()
META_PATHS = get_meta_paths()
META_INFO = get_meta_info()


# endregion[Constants]


class ErrorSignaler(QObject):
    show_error_signal = Signal(str, BaseException)

    def __repr__(self) -> str:
        """
        Basic Repr
        !REPLACE!
        """
        return f'{self.__class__.__name__}'


class SecondaryWindow(QWidget):
    close_signal = Signal(QWidget)

    def __init__(self, parent: QWidget = None, f: Qt.WindowFlags = None, name: str = None) -> None:
        super().__init__(*[i for i in [parent, f] if i is not None])
        if name is not None:
            self.setObjectName(name)

    @property
    def app(self) -> "AntistasiLogbookApplication":
        return AntistasiLogbookApplication.instance()

    def show(self) -> None:
        self.app.extra_windows.add_window(self)

        return super().show()

    def closeEvent(self, event: QCloseEvent) -> None:
        self.close_signal.emit(self)
        return super().closeEvent(event)

    def __repr__(self) -> str:
        """
        Basic Repr
        !REPLACE!
        """
        return f'{self.__class__.__name__}'


class AntistasiLogbookMainWindow(QMainWindow):
    update_started = Signal()
    update_finished = Signal()
    calculated_average_players = Signal(list)

    def __init__(self, app: "AntistasiLogbookApplication", flags=None) -> None:
        ExceptionHandlerManager.signaler = ErrorSignaler()

        self.app = app
        self.main_widget: MainWidget = None
        self.menubar: LogbookMenuBar = None
        self.statusbar: LogbookStatusBar = None

        self._temp_settings_window: "SettingsWindow" = None
        self._temp_folder_window = None
        self._temp_credentials_managment_window = None

        self.sys_tray: "LogbookSystemTray" = None
        self.name: str = None
        self.title: str = None
        self.update_thread: Thread = None
        self.dock_widgets: list[QDockWidget] = []
        self.update_timer: QTimer = None
        flags = flags or Qt.WindowFlags()
        super().__init__(None, flags)

    @property
    def backend(self):
        return self.app.backend

    @property
    def config(self) -> "GidIniConfig":
        return self.app.config

    @property
    def initial_size(self) -> list[int, int]:
        return self.config.get("main_window", "initial_size", default=[1600, 1000])

    @property
    def current_app_style_sheet(self) -> str:
        return self.config.get("gui", "style")

    def set_app_style_sheet(self, styleSheet: str) -> None:

        data = get_style_sheet_data(styleSheet)

        if data is None:
            data = styleSheet
        self.app.setStyleSheet(data)

    def addDockWidget(self, area: Qt.DockWidgetArea, dockwidget: QDockWidget, orientation: Qt.Orientation = None):
        args = [area, dockwidget]
        if orientation is not None:
            args.append(orientation)
        super().addDockWidget(*args)
        self.dock_widgets.append(dockwidget)

    def setup(self) -> None:
        self.setContextMenuPolicy(Qt.NoContextMenu)
        qt_material.add_fonts()
        self.set_app_style_sheet(self.current_app_style_sheet)

        self.name = StringCaseConverter.convert_to(META_INFO.app_name, StringCaseConverter.TITLE)
        self.title = f"{self.name} {META_INFO.version}"
        self.setWindowTitle(self.title)

        self.set_menubar(LogbookMenuBar(self))
        self.menubar.show_folder_action.triggered.connect(self.show_folder_window)
        self.menubar.open_credentials_managment_action.triggered.connect(self.show_credentials_managment_window)
        log.debug("finished setting up %r", self.menubar)
        self.setWindowIcon(self.app.icon)
        settings = QSettings()
        geometry = settings.value('main_window_geometry', QByteArray())
        if geometry.size():
            self.restoreGeometry(geometry)
        else:
            self.resize(*self.initial_size)
        self.tool_bar = BaseToolBar(self)
        self.addToolBar(Qt.TopToolBarArea, self.tool_bar)
        log.debug("starting to set main widget")
        self.set_main_widget(MainWidget(self))
        log.debug("finished setting up main widget %r", self.main_widget)
        self.main_widget.server_tab.resize_header_sections()
        self.sys_tray = LogbookSystemTray()
        self.app.sys_tray = self.sys_tray
        self.sys_tray.show()

        self.setup_statusbar()
        self.setup_backend()
        self.update_started.connect(self.statusbar.last_updated_label.shutdown)
        self.update_finished.connect(self.statusbar.last_updated_label.start)
        ExceptionHandlerManager.signaler.show_error_signal.connect(self.statusbar.show_error)
        ExceptionHandlerManager.signaler.show_error_signal.connect(self.show_error_dialog)
        self.backend.updater.signaler.update_started.connect(self.statusbar.switch_labels)
        self.backend.updater.signaler.update_finished.connect(self.statusbar.switch_labels)
        self.backend.update_signaler.change_update_text.connect(self.statusbar.set_update_text)

        self.backend.updater.signaler.update_info.connect(self.statusbar.start_progress_bar)
        self.backend.updater.signaler.update_increment.connect(self.statusbar.increment_progress_bar)
        self.main_widget.setup_views()
        self.backend.updater.signaler.update_finished.connect(self.main_widget.server_tab.model.refresh)

        self.backend.updater.signaler.update_finished.connect(self.main_widget.log_files_tab.model.refresh)
        self.backend.updater.signaler.update_finished.connect(self.statusbar.last_updated_label.refresh_text)
        self.menubar.open_settings_window_action.triggered.connect(self.open_settings_window)

        self.menubar.data_menu_actions_group.triggered.connect(self.show_secondary_model_data)
        self.menubar.show_app_log_action.triggered.connect(self.show_app_log_window)
        self.menubar.show_errors_action.triggered.connect(self.show_errors_window)
        self.menubar.cyclic_update_action.triggered.connect(self.start_update_timer)
        self.development_setup()

    def start_update_timer(self):
        interval: timedelta = self.config.get("updating", "update_interval")
        interval_msec = int(interval.total_seconds() * 1000)
        if self.update_timer is not None:
            log.debug("killing timer with id %r", self.update_timer.timerId())
            self.update_timer.stop()

        self.update_timer = QTimer(self)
        self.update_timer.setInterval(interval_msec)
        self.update_timer.setTimerType(Qt.CoarseTimer)
        self.update_timer.timeout.connect(self._single_update)
        self.update_timer.start()
        self.menubar.cyclic_update_remaining.start(self.update_timer)
        log.debug("started timer with id %r and interval of %r s", self.update_timer.timerId(), self.update_timer.interval() / 1000)
        try:
            self.menubar.cyclic_update_action.triggered.disconnect(self.start_update_timer)
            self.menubar.cyclic_update_action.triggered.connect(self.stop_update_timer)
        except Exception as e:
            log.critical("Ecountered exception %r", e)
        self.menubar.cyclic_update_action.setText("Stop Cyclic Update")
        self._single_update()

    def stop_update_timer(self):
        if self.update_timer is not None:
            log.debug("killing timer with id %r", self.update_timer.timerId())
            self.update_timer.stop()
            self.menubar.cyclic_update_remaining.stop()
            self.update_timer = None
            try:
                self.menubar.cyclic_update_action.triggered.disconnect(self.stop_update_timer)
                self.menubar.cyclic_update_action.triggered.connect(self.start_update_timer)
            except Exception as e:
                log.critical("Ecountered exception %r", e)
            self.menubar.cyclic_update_action.setText("Start Cyclic Update")

    def timerEvent(self, event: QTimerEvent) -> None:
        if event.timerId() == self.update_timer_id:
            log.debug("starting single update")
            self._single_update()

    def show_error_dialog(self, text: str, exception: BaseException):
        QMessageBox.critical(None, "Error", text)

        if isinstance(exception, MissingLoginAndPasswordError):
            self.show_credentials_managment_window()

    def show_errors_window(self):
        self.errors_window = StdStreamWidget(stream_capturer=stream_capturer).setup()
        self.errors_window.show()

    def development_setup(self):
        if self.app.is_dev is False:
            return

        self.debug_dock_widget = DebugDockWidget(parent=self, add_to_menu=self.menubar.windows_menu)
        self.addDockWidget(Qt.TopDockWidgetArea, self.debug_dock_widget)

        for attr_name in ["applicationVersion",
                          "organizationName",
                          "applicationDisplayName",
                          "desktopFileName",
                          "desktopSettingsAware",
                          "font",
                          "applicationDirPath",
                          "applicationFilePath",
                          "applicationPid",
                          "arguments",
                          "libraryPaths"]:
            self.debug_dock_widget.add_show_attr_button(attr_name=attr_name, obj=self.app)

        self.debug_dock_widget.add_show_attr_button(attr_name="colorNames", obj=QColor)

        self.debug_dock_widget.add_show_attr_button(attr_name="amount_log_records", obj=LogRecord)

    def set_tool_bar(self, tool_bar: QToolBar):
        if self.tool_bar:
            self.removeToolBar(self.tool_bar)
            self.tool_bar = tool_bar
            tool_bar.setParent(self)
            self.addToolBar(Qt.TopToolBarArea, tool_bar)
            self.tool_bar.setVisible(True)

    def show_app_log_window(self):
        # log_folder = Path(self.app.meta_paths.log_dir)
        # try:
        #     log_file = sorted([p for p in log_folder.iterdir() if p.is_file() and p.suffix == ".log"], key=lambda x: x.stat().st_ctime, reverse=True)[0]
        #     self.temp_add_log_window = FileAppLogViewer(log_file=log_file).setup()
        #     self.temp_add_log_window.show()
        # except IndexError:
        #     QMessageBox.warning(self, "Error", f"Unable to retrieve the Application Log File from Folder {log_folder.as_posix()!r}")
        return
        viewer = StoredAppLogViewer()
        viewer.setup()
        self.temp_app_log_window = viewer
        viewer.show()

    def setup_backend(self) -> None:
        self.menubar.single_update_action.triggered.connect(self._single_update)
        self.menubar.reassign_record_classes_action.triggered.connect(self._reassing_record_classes)

    def setup_statusbar(self) -> None:
        self.statusbar = LogbookStatusBar(self)
        log.debug("setting up %r", self.statusbar)
        self.statusbar.setup()
        self.setStatusBar(self.statusbar)

    def set_menubar(self, menubar: QMenuBar) -> None:
        self.menubar = menubar
        self.menubar.setParent(self)
        self.menubar.setup()
        self.setMenuBar(menubar)

    def set_main_widget(self, main_widget: QWidget) -> None:
        self.main_widget = main_widget
        self.setCentralWidget(main_widget)

    def shutdown_backend(self):
        self.statusbar.shutdown()
        self.backend.shutdown()

    def delete_db(self):
        path = self.backend.database.database_path

        log.debug("deleting DB at %r", path.as_posix())

        try:
            path.unlink(missing_ok=True)
        except Exception as e:
            log.error(e, True)
            log.critical("Unable to delete DB at %r", path.as_posix())

    def start_backend(self):

        log.debug("starting backend")
        config = META_CONFIG.get_config('general')
        db_path = config.get('database', "database_path", default=THIS_FILE_DIR.parent.joinpath("storage"))

        database = GidSqliteApswDatabase(db_path, config=config, thread_safe=True, autoconnect=True)
        backend = Backend(database=database, config=config, update_signaler=UpdaterSignaler())
        backend.start_up()
        self.app.backend = backend

    def show_secondary_model_data(self, db_model: "BaseModel"):
        models = {"ArmaFunction": ArmaFunctionModel,
                  "GameMap": GameMapModel,
                  "Version": VersionModel,
                  "Mod": ModsModel,
                  "RemoteStorage": RemoteStoragesModel,
                  "RecordClass": RecordClassesModel,
                  "LogLevel": LogLevelsModel,
                  "RecordOrigin": RecordOriginsModel}
        window = SecondaryWindow()

        window.setLayout(QGridLayout())
        view = BaseQueryTreeView(db_model.get_meta().table_name)

        model_class = models.get(db_model.get_meta().table_name, None)
        if model_class is None:
            model = BaseQueryDataModel(db_model=db_model).refresh()
        else:
            model = model_class().refresh()

        name = view.name
        window.setObjectName(name)
        view.setModel(model)
        icon_label = QLabel(window)
        icon_label.setPixmap(view.icon.pixmap(QSize(100, 100)))
        icon_label.setAlignment(Qt.AlignCenter)
        window.layout().addWidget(icon_label)
        window.layout().addWidget(view)
        if isinstance(model, GameMapModel):
            self.get_average_players_button = BusyPushButton(text="Get Average Player per Hour", parent=view, spinner_gif="busy_spinner_cat.gif", spinner_size=QSize(100, 100))
            self.get_average_players_button.pressed.connect(self.show_avg_player_window)
            window.layout().addWidget(self.get_average_players_button)
        view.setup()
        width = 150 * (view.header_view.count() - view.header_view.hiddenSectionCount())

        height = min(800, 50 * model.rowCount())

        window.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.MinimumExpanding)
        window.resize(width, height)
        window.setWindowIcon(view.icon)

        window.show()

    def show_avg_player_window(self):

        def _get_item_data(in_game_map: "GameMap") -> Optional[dict[str, Union[float, int, datetime]]]:
            data = in_game_map.get_avg_players_per_hour()

            return data | {"game_map": in_game_map.full_name}

        def _get_all_data():
            data = []
            for item_data in self.backend.thread_pool.map(_get_item_data, self.backend.database.foreign_key_cache.all_game_map_objects.values()):
                if any(i is None for i in [item_data.get("avg_players"), item_data.get("sample_size")]):
                    continue
                data.append(item_data)
            data = sorted(data, key=lambda x: (x.get("avg_players"), x.get("sample_size")), reverse=True)
            self.calculated_average_players.emit(data)
            self.backend.database.close()

        self.calculated_average_players.connect(self.show_avg_player_window_helper)

        self.get_average_players_button.start_spinner_while_future(self.backend.thread_pool.submit(_get_all_data))

    def show_avg_player_window_helper(self, data: list):
        time_frame = DateTimeFrame(start=min(i.get("min_timestamp") for i in data), end=max(i.get("max_timestamp") for i in data))

        plot_widget = AvgMapPlayersPlotWidget(data)
        icon = AllResourceItems.average_players_icon_image.get_as_pixmap(75, 75)
        window = SecondaryWindow(name="avg_player_window")
        window.setWindowTitle("Average Players per Hour")
        window.setWindowIcon(icon)
        sub_layout = QVBoxLayout()
        sub_layout.setAlignment(Qt.AlignCenter)

        window.setLayout(sub_layout)

        image_widget = QLabel(window)
        image_widget.setPixmap(icon)
        image_widget.setAlignment(Qt.AlignCenter)

        sub_layout.addWidget(image_widget)
        sub_sub_layout = QHBoxLayout()
        sub_layout.addLayout(sub_sub_layout)
        plot_widget.setMinimumSize(QSize(1250, 600))
        sub_sub_layout.addWidget(plot_widget)
        data_widget = QTableWidget(window)
        row_count = (len(data))
        columns = ["game_map", "avg_players", "sample_size"]
        column_count = (len(columns))
        data_widget.setColumnCount(column_count)
        data_widget.setRowCount(row_count)
        data_widget.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)

        data_widget.setHorizontalHeaderLabels(["Map", "Average Players per Hour", "Sample Size (Hours)"])

        for row in range(row_count):  # add items from array to QTableWidget
            for col_idx, column in enumerate(columns):
                item = str(data[row][column])
                table_item = QTableWidgetItem(item)
                table_item.setData(Qt.InitialSortOrderRole, data[row][column])
                data_widget.setItem(row, col_idx, table_item)
        data_widget.horizontalHeader().setMinimumSectionSize(175)
        data_widget.setEditTriggers(QTableWidget.NoEditTriggers)
        data_widget.setMinimumSize(QSize(600, 600))
        sub_sub_sub_layout = QVBoxLayout()

        sub_sub_sub_layout.addWidget(data_widget)
        overall_hours = QLabel("<b>Sum Hours:</b><br><i>" + str(sum(i["sample_size"] for i in data)) + "</i>")
        overall_hours.setAlignment(Qt.AlignCenter)
        overall_days = QLabel("<b>Amount Days:</b><br><i>" + str(int(time_frame.delta.days)) + "</i>")
        overall_days.setAlignment(Qt.AlignCenter)
        overall_time_frame = QLabel("<b>Time-Frame:</b><br><i>" + str(time_frame.to_pretty_string()) + "</i>")
        overall_time_frame.setAlignment(Qt.AlignCenter)
        sub_sub_sub_layout.addWidget(overall_hours)
        sub_sub_sub_layout.addWidget(overall_days)
        sub_sub_sub_layout.addWidget(overall_time_frame)
        sub_sub_layout.addLayout(sub_sub_sub_layout)
        screen_center_pos = self.app.screenAt(self.pos()).availableGeometry().center()
        fg = window.frameGeometry()
        new_center_pos = QPoint(screen_center_pos.x() - fg.width(), screen_center_pos.y() - fg.height())
        window.move(new_center_pos)
        window.show()

    def show_folder_window(self):
        self._temp_folder_window = DataView()
        self._temp_folder_window.setWindowTitle("Folder")
        self._temp_folder_window.setFixedWidth(1000)
        self._temp_folder_window.setWindowIcon(AllResourceItems.folder_settings_image.get_as_icon())
        self._temp_folder_window.add_row("Database", self.backend.database.database_path.resolve())
        self._temp_folder_window.add_row("Config", self.config.config.file_path.resolve())
        self._temp_folder_window.add_row("Log", self.app.meta_paths.log_dir.resolve())
        self._temp_folder_window.add_row("Cache", self.app.meta_paths.cache_dir.resolve())
        self._temp_folder_window.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self._temp_folder_window.setFixedHeight(self.sizeHint().height())
        self._temp_folder_window.show()

    def _reassing_record_classes(self):

        def _run_reassingment():

            self.menubar.single_update_action.setEnabled(False)
            self.menubar.reassign_record_classes_action.setEnabled(False)
            self.update_started.emit()
            self.backend.database.close()
            self.backend.database.connect(True)
            try:
                self.backend.updater.update_all_record_classes()
            finally:
                self.update_finished.emit()
                self.menubar.single_update_action.setEnabled(True)
                self.menubar.reassign_record_classes_action.setEnabled(True)
                self.backend.database.close()
                self.update_thread = None

        self.update_thread = Thread(target=_run_reassingment, name="run_reassignment_Thread")
        self.update_thread.start()

    def _single_update(self) -> None:
        def _run_update():
            # TODO: Connect update_action to the Stausbar label and shut it down while updating and start it up afterwards
            self.menubar.single_update_action.setEnabled(False)
            self.update_started.emit()
            try:
                self.backend.updater()
            finally:
                self.update_finished.emit()
                self.menubar.single_update_action.setEnabled(True)
                self.backend.database.close()

        self.update_thread = Thread(target=_run_update, name="run_update_Thread")

        self.update_thread.start()

    def close(self) -> bool:
        log.debug("%r executing 'close'", self)
        return super().close()

    def closeEvent(self, event: QCloseEvent):

        reply = QMessageBox.question(self, 'Message', 'Are you sure you want to quit?', QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.Yes:
            try:
                self.sys_tray.hide()
            except AttributeError:
                pass
            log.info("closing %r", self)
            self.stop_update_timer()
            splash = QSplashScreen(AllResourceItems.app_icon_image.get_as_pixmap(), Qt.WindowStaysOnTopHint)
            settings = QSettings()
            log.debug("saving main window geometry")
            settings.setValue('main_window_geometry', self.saveGeometry())
            self.setVisible(False)
            if self.config.get("database", "backup_database") is True:
                splash.show()
            splash.setPixmap(AllResourceItems.antistasi_logbook_splash_shutdown_backend_image.get_as_pixmap())

            for widget in self.app.allWidgets():
                if widget is not splash:
                    widget.hide()
            if self.update_thread is not None:
                self.update_thread.join(5)
            log.info("shutting down %r", self.statusbar)
            self.statusbar.shutdown()
            log.info("Starting shutting down %r", self.backend)
            self.backend.shutdown()

            log.info("Finished shutting down %r", self.backend)
            splash.close()

            log.info("closing all windows of %r", self.app)
            self.app.closeAllWindows()
            log.info("Quiting %r", self.app)

            self.app.quit()
            log.info('%r accepting event %r', self, event.type().name)
            event.accept()

        else:
            event.ignore()

    @ Slot()
    def open_settings_window(self):
        self._temp_settings_window = SettingsWindow(general_config=self.config, main_window=self).setup()
        self._temp_settings_window.show()

    def show_credentials_managment_window(self):
        self._temp_credentials_managment_window = CredentialsManagmentWindow()
        self._temp_credentials_managment_window.show()

    def __repr__(self) -> str:
        """
        Basic Repr
        !REPLACE!
        """
        return f'{self.__class__.__name__}'


def start_gui():

    # TODO: Rewrite so everything starts through the app

    app = AntistasiLogbookApplication.with_high_dpi_scaling(argvs=sys.argv)
    app.message_handler = QtMessageHandler().install()

    if app.is_full_gui is False:
        return

    config = META_CONFIG.get_config('general')

    if config.get("general", "is_first_start", default=True) is True:
        temp_db_path = config.get('database', "database_path", default=None)
        config.set("general", "is_first_start", False, create_missing_section=True)
    start_splash = app.show_splash_screen("start_up")
    db_path = config.get('database', "database_path", default=None)
    database = GidSqliteApswDatabase(db_path, config=config, thread_safe=True, autoconnect=True)

    backend = Backend(database=database, config=config, update_signaler=UpdaterSignaler())

    app.setup(backend=backend, icon=AllResourceItems.app_icon_image)

    _main_window = app.create_main_window(AntistasiLogbookMainWindow)

    _main_window.show()

    sys.exit(app.exec())


# region[Main_Exec]
if __name__ == '__main__':

    # dotenv.load_dotenv(r"D:\Dropbox\hobby\Modding\Programs\Github\My_Repos\Antistasi_Logbook\antistasi_logbook\nextcloud.env")
    start_gui()


# endregion[Main_Exec]
