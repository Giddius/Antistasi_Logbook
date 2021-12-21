
"""
WiP.

Soon.
"""

# region [Imports]

# * Third Party Imports --------------------------------------------------------------------------------->
from antistasi_logbook.gui.application import AntistasiLogbookApplication
from gidapptools.general_helper.string_helper import StringCaseConverter
from gidapptools import get_logger, get_meta_info, get_meta_paths, get_meta_config
from PySide6.QtWidgets import QWidget, QStyle, QMenuBar, QMainWindow, QMessageBox, QApplication, QStyleFactory, QLabel
from PySide6.QtCore import Slot, QEvent, Signal, QSettings, QByteArray, Qt
from PySide6.QtGui import QCloseEvent, QFont
from antistasi_logbook.gui.resources.antistasi_logbook_resources_accessor import AllResourceItems
from antistasi_logbook.gui.resources.style_sheets import get_style_sheet_data
from antistasi_logbook.storage.models.models import RemoteStorage
from antistasi_logbook.gui.settings_window import SettingsWindow
from antistasi_logbook.gui.main_widget import MainWidget
from antistasi_logbook.gui.status_bar import LogbookStatusBar
from antistasi_logbook.gui.sys_tray import LogbookSystemTray
from antistasi_logbook.gui.menu_bar import LogbookMenuBar
from antistasi_logbook.gui.misc import UpdaterSignaler
from antistasi_logbook.backend import Backend, GidSqliteApswDatabase
from concurrent.futures import ThreadPoolExecutor
from threading import Event, Thread
from weakref import WeakSet
from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable
import sys
import os
from antistasi_logbook import setup

setup()
# * Standard Library Imports ---------------------------------------------------------------------------->

# * Third Party Imports --------------------------------------------------------------------------------->

# * PyQt5 Imports --------------------------------------------------------------------------------------->
# * Gid Imports ----------------------------------------------------------------------------------------->
if TYPE_CHECKING:
    # * Gid Imports ----------------------------------------------------------------------------------------->
    from gidapptools.gid_config.interface import GidIniConfig

# endregion[Imports]

# region [TODO]


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


class SignalCollectingThreadPool(ThreadPoolExecutor):

    def __init__(self, max_workers: int = None, thread_name_prefix: str = None, initializer: Callable = None, initargs: tuple[Any] = None) -> None:
        super().__init__(max_workers=max_workers, thread_name_prefix=thread_name_prefix, initializer=initializer, initargs=initargs)
        self.abort_signals: WeakSet[Event] = WeakSet()

    def add_abort_signal(self, signal: Event) -> None:
        self.abort_signals.add(signal)

    def shutdown(self, wait: bool = None, *, cancel_futures: bool = None) -> None:
        for abort_signal in self.abort_signals:
            abort_signal.set()
        return super().shutdown(wait=wait, cancel_futures=cancel_futures)


class AntistasiLogbookMainWindow(QMainWindow):
    update_started = Signal()
    update_finished = Signal()

    def __init__(self, config: "GidIniConfig") -> None:
        self.config = config
        self.main_widget: MainWidget = None
        self.menubar: QMenuBar = None
        self.statusbar: LogbookStatusBar = None

        self._temp_settings_window: "SettingsWindow" = None

        self.sys_tray: "LogbookSystemTray" = None
        self.name: str = None
        self.title: str = None

        super().__init__()
        self.setup()

    @property
    def app(self) -> AntistasiLogbookApplication:
        return AntistasiLogbookApplication.instance()

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

    def setup(self) -> None:

        self.set_app_style_sheet(self.current_app_style_sheet)
        settings = QSettings(f"{META_INFO.app_name}_settings", "main_window")
        self.name = StringCaseConverter.convert_to(META_INFO.app_name, StringCaseConverter.TITLE)
        self.title = f"{self.name} {META_INFO.version}"
        self.setWindowTitle(self.title)

        self.set_menubar(LogbookMenuBar(self))
        self.setWindowIcon(self.app.icon)
        geometry = settings.value('geometry', QByteArray())
        if geometry.size():
            self.restoreGeometry(geometry)
        else:
            self.resize(*self.initial_size)
        self.set_main_widget(MainWidget(self))
        self.sys_tray = LogbookSystemTray(self, self.app)
        self.sys_tray.show()

        self.setup_backend()
        self.setup_statusbar()
        self.backend.updater.signaler.update_started.connect(self.statusbar.switch_labels)
        self.backend.updater.signaler.update_finished.connect(self.statusbar.switch_labels)

        self.backend.updater.signaler.update_info.connect(self.statusbar.start_progress_bar)
        self.backend.updater.signaler.update_increment.connect(self.statusbar.increment_progress_bar)
        self.main_widget.setup_views()
        self.backend.updater.signaler.update_finished.connect(self.main_widget.server_tab.model().refresh)
        self.backend.updater.signaler.update_finished.connect(self.main_widget.log_files_tab.model().refresh)
        self.backend.updater.signaler.update_finished.connect(self.statusbar.last_updated_label.refresh_text)
        self.menubar.open_settings_window_action.triggered.connect(self.open_settings_window)

    def setup_backend(self) -> None:
        self.backend.start_up()
        self.menubar.single_update_action.triggered.connect(self._single_update)
        self.menubar.reset_database_action.triggered.connect(self._reset_database)

    def setup_statusbar(self) -> None:
        self.statusbar = LogbookStatusBar(self)
        self.setStatusBar(self.statusbar)

    def set_menubar(self, menubar: QMenuBar) -> None:
        self.menubar = menubar
        self.setMenuBar(menubar)

    def set_main_widget(self, main_widget: QWidget) -> None:
        self.main_widget = main_widget
        self.setCentralWidget(main_widget)

    def _reset_database(self) -> None:
        reply = QMessageBox.warning(self, 'THIS IS IRREVERSIBLE', 'Are you sure you want to REMOVE the existing Database and REBUILD it?', QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.menubar.single_update_action.setEnabled(False)
            self.statusbar.last_updated_label.shutdown()
            self.backend.remove_and_reset_database()
            self.statusbar.last_updated_label.start_timer()
            self.menubar.single_update_action.setEnabled(True)

    def _single_update(self) -> None:
        def _run_update():
            self.menubar.single_update_action.setEnabled(False)
            self.update_started.emit()
            self.backend.updater()
            self.update_finished.emit()
            self.menubar.single_update_action.setEnabled(True)

        x = Thread(target=_run_update)
        x.start()

    def close(self) -> bool:
        log.debug("%r executing 'close'", self)
        return super().close()

    def event(self, event: QEvent) -> bool:

        return super().event(event)

    def closeEvent(self, event: QCloseEvent):

        reply = QMessageBox.question(self, 'Message', 'Are you sure you want to quit?', QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.Yes:
            log.info("closing %r", self)
            log.debug("Starting shutting down %r", self.backend)
            self.backend.shutdown()
            log.debug("Finished shutting down %r", self.backend)
            log.debug('%r accepting event %r', self, event.type().name)
            settings = QSettings(f"{META_INFO.app_name}_settings", "main_window")
            settings.setValue('geometry', self.saveGeometry())
            event.accept()
        else:
            event.ignore()

    @Slot()
    def open_settings_window(self):
        self._temp_settings_window = SettingsWindow(general_config=self.config, main_window=self).setup()
        self._temp_settings_window.show()

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}"


def start_gui(nextcloud_username: str = None, nextcloud_password: str = None):
    config = META_CONFIG.get_config('general')
    db_path = config.get('database', "database_path", default=None)
    database = GidSqliteApswDatabase(db_path, config=config, thread_safe=True, autoconnect=True)
    backend = Backend(database=database, config=config, update_signaler=UpdaterSignaler())
    _app = AntistasiLogbookApplication.with_high_dpi_scaling(backend=backend, argvs=sys.argv)
    _app.icon = AllResourceItems.placeholder.get_as_icon()
    m = AntistasiLogbookMainWindow(META_CONFIG.get_config('general'))
    if nextcloud_username is not None and nextcloud_password is not None:
        RemoteStorage.get(name="community_webdav").set_login_and_password(login=nextcloud_username, password=nextcloud_password, store_in_db=False)

    m.show()
    _app.exec()


# region[Main_Exec]
if __name__ == '__main__':

    import dotenv
    dotenv.load_dotenv(r"D:\Dropbox\hobby\Modding\Programs\Github\My_Repos\Antistasi_Logbook\antistasi_logbook\nextcloud.env")
    start_gui(os.getenv("NEXTCLOUD_USERNAME"), os.getenv("NEXTCLOUD_PASSWORD"))


# endregion[Main_Exec]
