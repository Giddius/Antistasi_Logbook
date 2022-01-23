
"""
WiP.

Soon.
"""

# region [Imports]

# * Standard Library Imports ---------------------------------------------------------------------------->
from gidapptools.general_helper.timing import get_dummy_profile_decorator_in_globals
from antistasi_logbook import stream_capturer
import sys
from typing import TYPE_CHECKING
from pathlib import Path
from threading import Thread

# * Third Party Imports --------------------------------------------------------------------------------->


# * Qt Imports --------------------------------------------------------------------------------------->
from PySide6.QtGui import QColor, QCloseEvent, QMouseEvent
from PySide6.QtCore import Qt, Slot, Signal, QObject, QSettings, QByteArray
from PySide6.QtWidgets import QWidget, QMenuBar, QGridLayout, QHeaderView, QMainWindow, QMessageBox, QSizePolicy, QSplashScreen, QToolBar, QTabBar, QPushButton, QDockWidget
import qt_material
# * Gid Imports ----------------------------------------------------------------------------------------->
from gidapptools import get_logger, get_meta_info, get_meta_paths, get_meta_config
from gidapptools.general_helper.string_helper import StringCaseConverter
from gidapptools.gidapptools_qt.widgets.app_log_viewer import AppLogViewer

# * Local Imports --------------------------------------------------------------------------------------->
from antistasi_logbook import setup
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
from antistasi_logbook.gui.models.version_model import VersionModel
from antistasi_logbook.gui.models.game_map_model import GameMapModel
from antistasi_logbook.gui.widgets.debug_widgets import DebugDockWidget
from antistasi_logbook.gui.resources.style_sheets import get_style_sheet_data
from antistasi_logbook.gui.views.base_query_tree_view import BaseQueryTreeView
from antistasi_logbook.gui.models.record_classes_model import RecordClassesModel
from antistasi_logbook.gui.models.base_query_data_model import BaseQueryDataModel
from antistasi_logbook.gui.models.remote_storages_model import RemoteStoragesModel
from antistasi_logbook.gui.models.antistasi_function_model import AntistasiFunctionModel
from antistasi_logbook.gui.widgets.data_view_widget.data_view import DataView
from antistasi_logbook.gui.resources.antistasi_logbook_resources_accessor import AllResourceItems
from gidapptools.gidapptools_qt.widgets.std_stream_widget import StdStreamWidget
from antistasi_logbook.call_tree.call_tree_item import CallTree
from antistasi_logbook.storage.models.models import LogFile
setup()
# * Type-Checking Imports --------------------------------------------------------------------------------->
if TYPE_CHECKING:
    from gidapptools.gid_config.interface import GidIniConfig

    from antistasi_logbook.storage.models.models import BaseModel

# endregion[Imports]

# region [TODO]


# endregion [TODO]

# region [Logging]


# endregion[Logging]

# region [Constants]

get_dummy_profile_decorator_in_globals()
THIS_FILE_DIR = Path(__file__).parent.absolute()
log = get_logger(__name__)
META_CONFIG = get_meta_config()
META_PATHS = get_meta_paths()
META_INFO = get_meta_info()


# endregion[Constants]


class ErrorSignaler(QObject):
    show_error_signal = Signal(str, BaseException)


class AntistasiLogbookMainWindow(QMainWindow):
    update_started = Signal()
    update_finished = Signal()

    def __init__(self, app: "AntistasiLogbookApplication", config: "GidIniConfig") -> None:
        ExceptionHandlerManager.signaler = ErrorSignaler()
        self.config = config
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
        super().__init__()

        self.setup()

    @property
    def backend(self):
        return self.app.backend

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
        qt_material.add_fonts()
        self.set_app_style_sheet(self.current_app_style_sheet)
        settings = QSettings(f"{META_INFO.app_name}_settings", "main_window")
        self.name = StringCaseConverter.convert_to(META_INFO.app_name, StringCaseConverter.TITLE)
        self.title = f"{self.name} {META_INFO.version}"
        self.setWindowTitle(self.title)
        self.addToolBar(Qt.TopToolBarArea, QToolBar(self))
        self.set_menubar(LogbookMenuBar(self))
        self.menubar.show_folder_action.triggered.connect(self.show_folder_window)
        self.menubar.open_credentials_managment_action.triggered.connect(self.show_credentials_managment_window)

        self.setWindowIcon(self.app.icon)
        settings = QSettings()
        geometry = settings.value('main_window_geometry', QByteArray())
        if geometry.size():
            self.restoreGeometry(geometry)
        else:
            self.resize(*self.initial_size)
        self.set_main_widget(MainWidget(self))
        self.main_widget.server_tab.resize_header_sections()
        self.sys_tray = LogbookSystemTray(self, self.app)
        self.app.sys_tray = self.sys_tray
        self.sys_tray.show()

        self.setup_backend()
        self.setup_statusbar()
        ExceptionHandlerManager.signaler.show_error_signal.connect(self.statusbar.show_error)
        ExceptionHandlerManager.signaler.show_error_signal.connect(self.show_error_dialog)
        self.backend.updater.signaler.update_started.connect(self.statusbar.switch_labels)
        self.backend.updater.signaler.update_finished.connect(self.statusbar.switch_labels)

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

        self.development_setup()

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
        self.addDockWidget(Qt.NoDockWidgetArea, self.debug_dock_widget)

        for attr_name in ["desktopFileName",
                          "desktopSettingsAware",
                          "devicePixelRatio",
                          "highDpiScaleFactorRoundingPolicy",
                          "platformName",
                          "applicationState",
                          "font",
                          "applicationDirPath",
                          "applicationFilePath",
                          "applicationPid",
                          "arguments",
                          "isQuitLockEnabled",
                          "isSetuidAllowed",
                          "libraryPaths",
                          "available_font_families"]:
            self.debug_dock_widget.add_show_attr_button(attr_name=attr_name, obj=self.app)

        self.debug_dock_widget.add_show_attr_button(attr_name="colorNames", obj=QColor)

        close_all_db_conn_button = QPushButton("Close All Db Connections")
        close_all_db_conn_button.pressed.connect(self.backend.database.close_all)
        self.debug_dock_widget.add_widget("close_all_db_conn", "Database", close_all_db_conn_button)

    def do_the_call_tree(self):
        c = CallTree(self.backend.database.get_log_files(ordered_by=LogFile.size)[-1])
        c.populate()
        c.save_to_png()

    def show_app_log_window(self):

        log_folder = Path(self.app.meta_paths.log_dir)
        try:
            log_file = sorted([p for p in log_folder.iterdir() if p.is_file() and p.suffix == ".log"], key=lambda x: x.stat().st_ctime, reverse=True)[0]
            self.temp_add_log_window = AppLogViewer(log_file=log_file).setup()
            self.temp_add_log_window.show()
        except IndexError:
            QMessageBox.warning(self, "Error", f"Unable to retrieve the Application Log File from Folder {log_folder.as_posix()!r}")

    def setup_backend(self) -> None:
        self.menubar.single_update_action.triggered.connect(self._single_update)
        self.menubar.reassign_record_classes_action.triggered.connect(self._reassing_record_classes)

    def setup_statusbar(self) -> None:
        self.statusbar = LogbookStatusBar(self)
        self.setStatusBar(self.statusbar)

    def set_menubar(self, menubar: QMenuBar) -> None:
        self.menubar = menubar
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
        config = META_CONFIG.get_config('general')
        db_path = config.get('database', "database_path", default=THIS_FILE_DIR.parent.joinpath("storage"))

        database = GidSqliteApswDatabase(db_path, config=config, thread_safe=True, autoconnect=True)
        backend = Backend(database=database, config=config, update_signaler=UpdaterSignaler())
        backend.start_up()
        self.app.backend = backend
        self.statusbar.setup()

    def show_secondary_model_data(self, db_model: "BaseModel"):
        models = {"AntstasiFunction": AntistasiFunctionModel,
                  "GameMap": GameMapModel,
                  "Version": VersionModel,
                  "Mod": ModsModel,
                  "RemoteStorage": RemoteStoragesModel,
                  "RecordClass": RecordClassesModel,
                  "LogLevel": LogLevelsModel,
                  "RecordOrigin": RecordOriginsModel}
        window = QWidget()
        window.setLayout(QGridLayout())
        view = BaseQueryTreeView(db_model.get_meta().table_name)
        model_class = models.get(db_model.get_meta().table_name, None)
        if model_class is None:
            model = BaseQueryDataModel(db_model=db_model).refresh()
        else:
            model = model_class().refresh()

        view.setModel(model)
        if not isinstance(model, GameMapModel):
            view.header_view.setSectionResizeMode(QHeaderView.ResizeToContents)
        window.layout().addWidget(view)
        view.setup()
        width = 150 * (view.header_view.count() - view.header_view.hiddenSectionCount())

        height = min(800, 50 * model.rowCount())

        self.secondary_model_data_window = window
        self.secondary_model_data_window.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.MinimumExpanding)
        self.secondary_model_data_window.resize(width, height)
        self.secondary_model_data_window.show()

    def show_folder_window(self):
        self._temp_folder_window = DataView()
        self._temp_folder_window.setWindowTitle("Folder")
        self._temp_folder_window.setFixedWidth(1000)
        self._temp_folder_window.setWindowIcon(AllResourceItems.folder_settings_image.get_as_icon())
        self._temp_folder_window.add_row("Database", self.backend.database.database_path.resolve())
        self._temp_folder_window.add_row("Config", self.config.config.file_path.resolve())
        self._temp_folder_window.add_row("Log", self.app.meta_paths.log_dir.resolve())
        self._temp_folder_window.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self._temp_folder_window.setFixedHeight(self.sizeHint().height())
        self._temp_folder_window.show()

    def _reassing_record_classes(self):
        def _run_reassingment():

            self.menubar.single_update_action.setEnabled(False)
            self.menubar.reassign_record_classes_action.setEnabled(False)
            self.update_started.emit()
            try:
                self.backend.updater.update_record_classes(force=True)
            finally:
                self.update_finished.emit()
                self.menubar.single_update_action.setEnabled(True)
                self.menubar.reassign_record_classes_action.setEnabled(True)
                self.backend.database.close()

        self.update_thread = Thread(target=_run_reassingment, name="run_reassignment_Thread")
        self.update_thread.start()

    def _single_update(self) -> None:
        def _run_update():

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
            splash = QSplashScreen(AllResourceItems.app_icon_image.get_as_pixmap(), Qt.WindowStaysOnTopHint)
            settings = QSettings()
            settings.setValue('main_window_geometry', self.saveGeometry())
            self.setVisible(False)
            if self.config.get("database", "backup_database") is True:
                splash.show()
            splash.setPixmap(AllResourceItems.antistasi_logbook_splash_shutdown_backend_image.get_as_pixmap())

            for widget in self.app.allWidgets():
                if widget is not splash:
                    widget.hide()

            log.info("shutting down %r", self.statusbar)
            self.statusbar.shutdown()
            log.info("Starting shutting down %r", self.backend)
            self.backend.shutdown()
            log.info("Finished shutting down %r", self.backend)
            splash.close()

            if self.update_thread is not None:
                self.update_thread.join(10)
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
        return f"{self.__class__.__name__}"


def start_gui():
    qApp = AntistasiLogbookApplication.instance()
    if qApp is None:
        qApp = AntistasiLogbookApplication.with_high_dpi_scaling(argvs=sys.argv)
    start_splash = QSplashScreen(AllResourceItems.app_icon_image.get_as_pixmap(), Qt.WindowStaysOnTopHint)

    start_splash.setPixmap(AllResourceItems.antistasi_logbook_splash_preparing_database_image.get_as_pixmap())

    qApp.processEvents()
    start_splash.show()
    config = META_CONFIG.get_config('general')
    db_path = config.get('database', "database_path", default=None)
    database = GidSqliteApswDatabase(db_path, config=config, thread_safe=True, autoconnect=True)
    start_splash.setPixmap(AllResourceItems.antistasi_logbook_splash_preparing_backend_image.get_as_pixmap())
    backend = Backend(database=database, config=config, update_signaler=UpdaterSignaler())

    start_splash.setPixmap(AllResourceItems.antistasi_logbook_splash_starting_backend_image.get_as_pixmap())
    qApp.setup(backend=backend, icon=AllResourceItems.app_icon_image)

    _main_window = AntistasiLogbookMainWindow(qApp, META_CONFIG.get_config('general'))
    qApp.main_window = _main_window

    _main_window.show()
    _main_window.setWindowState(Qt.WindowActive)
    start_splash.finish(_main_window)
    sys.exit(qApp.exec())


# region[Main_Exec]
if __name__ == '__main__':

    # dotenv.load_dotenv(r"D:\Dropbox\hobby\Modding\Programs\Github\My_Repos\Antistasi_Logbook\antistasi_logbook\nextcloud.env")
    start_gui()


# endregion[Main_Exec]
