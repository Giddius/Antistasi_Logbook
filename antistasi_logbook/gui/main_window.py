
"""
WiP.

Soon.
"""


# region [Imports]

# * Standard Library Imports ---------------------------------------------------------------------------->
import sys
import os
from time import sleep
from typing import TYPE_CHECKING, Union, Optional
from pathlib import Path
from datetime import timedelta, datetime
from threading import Thread
from concurrent.futures import Future
from antistasi_logbook.utilities.date_time_utilities import DateTimeFrame
from antistasi_logbook.data import DATA_DIR
# * Qt Imports --------------------------------------------------------------------------------------->
from PySide6.QtGui import QColor, QCloseEvent, QScreen, QDesktopServices
from PySide6.QtHelp import QHelpEngineCore, QHelpContentWidget, QHelpEngine
from PySide6.QtCore import Qt, Slot, QSize, QPoint, QTimer, Signal, QObject, QSysInfo, QSettings, QByteArray, QTimerEvent, QRect
from PySide6.QtWidgets import (QLabel, QWidget, QPushButton, QMenuBar, QToolBar, QDockWidget, QGridLayout, QHBoxLayout, QMainWindow,
                               QMessageBox, QSizePolicy, QVBoxLayout, QTableWidget, QSplashScreen, QTableWidgetItem)

from PySide6.QtWebEngineWidgets import QWebEngineView
from tempfile import TemporaryDirectory
# * Third Party Imports --------------------------------------------------------------------------------->
import qt_material

# * Gid Imports ----------------------------------------------------------------------------------------->
from gidapptools import get_logger, get_meta_info, get_meta_paths
from gidapptools.gid_logger.misc import QtMessageHandler

from gidapptools.general_helper.string_helper import StringCaseConverter
from gidapptools.gidapptools_qt.widgets.app_log_viewer import StoredAppLogViewer
from gidapptools.gidapptools_qt.widgets.spinner_widget import BusyPushButton
from gidapptools.gidapptools_qt.widgets.std_stream_widget import StdStreamWidget

# * Local Imports --------------------------------------------------------------------------------------->
# from antistasi_logbook import stream_capturer
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
from antistasi_logbook.storage.models.models import GameMap, LogRecord, DatabaseMetaData
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
from antistasi_logbook.gui.debug import setup_debug_widget
from gidapptools.gidapptools_qt.helper.misc import center_window
from gidapptools.gidapptools_qt.helper.window_geometry_helper import move_to_center_of_screen
from gidapptools.general_helper.conversion import bytes2human
from gidapptools.gidapptools_qt.widgets.spinner_widget import BusySpinnerWidget
import pp
from gidapptools.gid_config.interface import GidIniConfig, get_config
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

META_PATHS = get_meta_paths()
META_INFO = get_meta_info()


# endregion[Constants]


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


class CLIHelpWindow(QWebEngineView):

    def __init__(self, html: str, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.html = html
        self.setHtml(self.html)


class AntistasiLogbookMainWindow(QMainWindow):
    update_started = Signal()
    update_finished = Signal()
    calculated_average_players = Signal(list)

    def __init__(self, app: "AntistasiLogbookApplication", flags=None) -> None:
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
        self.temp_help_dir = None
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
        return [1600, 1000]

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

        move_to_center_of_screen(self)
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
        self.backend.updater.signaler.update_record_classes_started.connect(self.statusbar.switch_labels)
        self.backend.updater.signaler.update_finished.connect(self.statusbar.finish_progress_bar)
        self.backend.updater.signaler.update_finished.connect(self.statusbar.switch_labels)
        self.backend.updater.signaler.update_record_classes_finished.connect(self.statusbar.switch_labels)
        self.backend.update_signaler.change_update_text.connect(self.statusbar.set_update_text)

        self.backend.updater.signaler.update_info.connect(self.statusbar.start_progress_bar)
        self.backend.updater.signaler.update_increment.connect(self.statusbar.increment_progress_bar)
        self.backend.updater.signaler.update_log_file_finished.connect(self.statusbar.increment_log_file_finished)
        self.main_widget.setup_views()
        self.backend.updater.signaler.update_finished.connect(self.main_widget.server_tab.model.refresh)

        self.backend.updater.signaler.update_finished.connect(self.main_widget.log_files_tab.model.refresh)
        self.backend.updater.signaler.update_finished.connect(self.statusbar.last_updated_label.refresh_text)
        self.menubar.open_settings_window_action.triggered.connect(self.open_settings_window)

        self.menubar.data_menu_actions_group.triggered.connect(self.show_secondary_model_data)
        self.menubar.show_app_log_action.triggered.connect(self.show_app_log_window)
        self.menubar.show_errors_action.triggered.connect(self.show_errors_window)
        self.menubar.cyclic_update_action.triggered.connect(self.start_update_timer)
        self.menubar.show_cli_arguments.triggered.connect(self.show_cli_arguments_page)
        self.menubar.show_help.setEnabled(False)
        self.menubar.run_full_vaccum_action.triggered.connect(self.run_full_vacuum)
        self.development_setup()
        self.ensure_fully_visible()
        self.raise_()

    def run_full_vacuum(self):

        def _do_full_vacuum():
            self.backend.database.checkpoint()
            self.backend.database.connection().execute("VACUUM").fetchall()
            self.backend.database.checkpoint()

        value = QMessageBox.warning(self,
                                    "Full Vacuum",
                                    '\n'.join(i.strip() for i in f"""Running a full Database Vacuum can take some time.
                                     It will also require at least {bytes2human(self.backend.database.database_file_size)} of extra Disk Space!

                                     The Application will shut down after it is done vacuuming!

                                     Do you really want to do a Full Vacuum?""".splitlines()),
                                    QMessageBox.StandardButton.Yes,
                                    QMessageBox.StandardButton.Cancel)

        if value == QMessageBox.StandardButton.Yes.value:
            log.info("starting full_vaccum")
            s = min([self.size().width() // 2, self.size().height() // 2])
            self._vacuum_spinner_widget = BusySpinnerWidget(spinner_gif="busy_spinner_cat.gif", spinner_size=QSize(s, s))
            self._vacuum_spinner_widget.setWindowModality(Qt.WindowModality.ApplicationModal)
            self._vacuum_spinner_widget.setWindowFlags(Qt.FramelessWindowHint)
            self._vacuum_spinner_widget.setStyleSheet("""background-color: rgba(200, 200, 200,0); """)
            self._vacuum_spinner_widget.setAttribute(Qt.WA_TranslucentBackground)
            center_window(self._vacuum_spinner_widget, allow_window_resize=False)
            self._vacuum_spinner_widget._stop_signal.connect(lambda x: self._vacuum_spinner_widget.close())
            self._vacuum_spinner_widget._stop_signal.connect(lambda x: self.app.exit())
            future: Future = self.backend.thread_pool.submit(_do_full_vacuum)
            future.add_done_callback(self._vacuum_spinner_widget._stop_signal.emit)

            self._vacuum_spinner_widget.start()
            self._vacuum_spinner_widget.show()

    def ensure_fully_visible(self) -> None:
        screen_geometry = self.app.screens()[0].availableGeometry()
        window_geometry = self.geometry()

        if window_geometry.height() > int(screen_geometry.height() * 0.8):
            window_geometry.setHeight(int(screen_geometry.height() * 0.8))
        if window_geometry.width() > int(screen_geometry.width() * 0.8):
            window_geometry.setHeight(int(screen_geometry.width() * 0.8))

        if screen_geometry.contains(window_geometry) is False:
            new_size_height = min(window_geometry.height(), int(screen_geometry.height() * 0.8))
            new_size_width = min(window_geometry.width(), int(screen_geometry.width() * 0.8))

            window_geometry.setSize(QSize(new_size_width, new_size_height))
            window_geometry.moveCenter(screen_geometry.center())
        if screen_geometry.contains(window_geometry) is False:
            move_x = 0
            move_y = 0

            if window_geometry.bottom() > screen_geometry.bottom():
                move_y = min(screen_geometry.bottom(), window_geometry.bottom()) - max(screen_geometry.bottom(), window_geometry.bottom())
                move_y = int(move_y * 0.8)
            elif window_geometry.top() < screen_geometry.top():
                move_y = max(screen_geometry.top(), window_geometry.top()) - min(screen_geometry.top(), window_geometry.top())
                move_y = int(move_y * 1.2)
            if window_geometry.right() > screen_geometry.right():
                move_x = min(screen_geometry.right(), window_geometry.right()) - max(screen_geometry.right(), window_geometry.right())
                move_x = int(move_x * 0.8)
            elif window_geometry.left() < screen_geometry.left():
                move_x = max(screen_geometry.left(), window_geometry.left()) - min(screen_geometry.left(), window_geometry.left())
                move_x = int(move_x * 1.2)
            window_geometry.translate(move_x, move_y)
        self.setGeometry(window_geometry)

    def show_cli_arguments_page(self):
        css_file = DATA_DIR.joinpath("cli_help_view.css")
        all_ids_text = '<a href="#usage">♦️ Usage</a>'
        for item in self.app.argument_doc_items:
            _id = item.name
            all_ids_text += f'<a href="#{_id}">♦️ {_id}</a>'

        all_ids_text = f"""<div class="toc">{all_ids_text}</div>"""
        usage_text = self.app.get_argument_parser().format_usage().removeprefix("usage:").strip()
        usage_text = f"""<div class="usage"><h1><a id="usage">Usage</a></h1><pre><code>{usage_text}</code></pre></div><br><hr><hr><br>"""
        html = f"""<!DOCTYPE html>
<html>
<head>
<title>Command Line Arguments</title>

    <style>
    {css_file.read_text(encoding='utf-8', errors='ignore')}
    </style>
</head>
<body>
{usage_text}
{all_ids_text}"""

        for doc_item in self.app.argument_doc_items:
            html += doc_item.get_html() + "<br><hr><br>"

        html += """</body>
</html>"""
        self.temp_help_dir = TemporaryDirectory()
        help_file = Path(self.temp_help_dir.name).joinpath("help.html")
        help_file.write_text(html, encoding='utf-8', errors='ignore')
        QDesktopServices.openUrl(help_file.as_uri())

    @property
    def config(self):
        return self.app.config

    @property
    def cyclic_update_running(self) -> bool:
        if self.update_timer is None:
            return False

        return self.update_timer.isActive()

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
        pass
        # self.errors_window = StdStreamWidget(stream_capturer=stream_capturer).setup()
        # self.errors_window.show()

    def development_setup(self):
        if self.app.is_dev is False:
            return

        self.debug_dock_widget = DebugDockWidget(parent=self, add_to_menu=self.menubar.windows_menu)
        self.addDockWidget(Qt.TopDockWidgetArea, self.debug_dock_widget)
        setup_debug_widget(self.debug_dock_widget)

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

    def start_backend(self):

        log.debug("starting backend")
        config = self.config.get_config('general')
        db_path = config.get('database', "database_path", default=THIS_FILE_DIR.parent.joinpath("storage"))

        database = GidSqliteApswDatabase(db_path, config=config, thread_safe=True, autoconnect=True)
        backend = Backend(database=database, config=config, update_signaler=UpdaterSignaler())
        backend.start_up()
        self.app.backend = backend

    def show_secondary_model_data(self, db_model: "BaseModel"):
        log.debug("show requested for %r", db_model)
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
            spinner_gif = "busy_spinner_cat.gif" if self.config.get("gui", "use_cat_busy_spinner", default=True) is True else "busy_spinner_7.gif"
            self.get_average_players_button = BusyPushButton(text="Get Average Player per Hour", parent=view, spinner_gif=spinner_gif, spinner_size=QSize(100, 100))
            self.get_average_players_button.pressed.connect(self.show_avg_player_window)
            window.layout().addWidget(self.get_average_players_button)
        view.setup()
        width = 150 * (view.header_view.count() - view.header_view.hiddenSectionCount())

        height = min(800, 50 * model.rowCount())

        window.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.MinimumExpanding)
        window.resize(width, height)
        window.setWindowIcon(view.icon)

        window = center_window(window, False)

        window.show()

    def show_avg_player_window(self):

        def _get_item_data(in_game_map: "GameMap") -> Optional[dict[str, Union[float, int, datetime]]]:
            try:

                data = in_game_map.get_avg_players_per_hour()

                return data | {"game_map": in_game_map.full_name}
            except Exception as e:
                log.error(e, exc_info=True)
                return None

        def _get_all_data():
            data = []
            for item_data in self.backend.thread_pool.map(_get_item_data, self.backend.database.foreign_key_cache.all_game_map_objects.values()):
                if item_data is None or any(i is None for i in [item_data.get("avg_players"), item_data.get("sample_size_hours"), item_data.get("sample_size_data_points")]):
                    continue
                data.append(item_data)
            data = sorted(data, key=lambda x: (x.get("avg_players"), x.get("sample_size_data_points"), x.get("sample_size_hours")), reverse=True)
            self.calculated_average_players.emit(data)
            self.backend.database.close()

        self.calculated_average_players.connect(self.show_avg_player_window_helper)

        self.get_average_players_button.start_spinner_while_future(self.backend.thread_pool.submit(_get_all_data))

    def show_avg_player_window_helper(self, data: list):

        time_frame = DateTimeFrame(start=min(i.get("date_time_frame").start for i in data), end=max(i.get("date_time_frame").end for i in data))

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
        data_widget.setSortingEnabled(True)
        data_widget.verticalHeader().setVisible(False)
        row_count = (len(data))
        columns = ["#", "game_map", "avg_players", "sample_size_hours", "sample_size_data_points"]
        column_count = (len(columns))
        data_widget.setColumnCount(column_count)
        data_widget.setRowCount(row_count)
        data_widget.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)

        data_widget.setHorizontalHeaderLabels(["#", "Map", "Average Players per Hour", "Sample Size (Hours)", "Sample Size (Data-Points)"])

        red_background = QColor(255, 0, 0, 50)
        yellow_background = QColor(255, 255, 0, 50)
        green_background = QColor(0, 255, 0, 50)

        for row in range(row_count):  # add items from array to QTableWidget
            for col_idx, column in enumerate(columns):
                if column == "#":
                    table_item = QTableWidgetItem()
                    table_item.setData(Qt.DisplayRole, row + 1)
                    table_item.setData(Qt.InitialSortOrderRole, row + 1)

                else:
                    item = data[row][column]
                    table_item = QTableWidgetItem()
                    table_item.setData(Qt.DisplayRole, item)
                    table_item.setData(Qt.InitialSortOrderRole, item)
                avg_players = data[row]["avg_players"]
                color = None
                if avg_players < 5:
                    color = red_background
                elif avg_players < 10:
                    color = yellow_background
                elif avg_players >= 10:
                    color = green_background

                if color:
                    table_item.setData(Qt.BackgroundRole, color)
                data_widget.setItem(row, col_idx, table_item)

        data_widget.horizontalHeader().setDefaultAlignment(Qt.AlignCenter)
        data_widget.horizontalHeader().setStretchLastSection(True)

        data_widget.horizontalHeader().setSectionResizeMode(data_widget.horizontalHeader().ResizeMode.Interactive)
        data_widget.horizontalHeader().setSectionResizeMode(0, data_widget.horizontalHeader().ResizeMode.Fixed)

        data_widget.horizontalHeader().resizeSections(data_widget.horizontalHeader().ResizeMode.ResizeToContents)
        data_widget.horizontalHeader().setStretchLastSection(True)
        data_widget.setAlternatingRowColors(True)
        data_widget.setEditTriggers(QTableWidget.NoEditTriggers)
        data_widget.setMinimumSize(QSize(800, 600))
        sub_sub_sub_layout = QVBoxLayout()

        sub_sub_sub_layout.addWidget(data_widget)
        overall_hours = QLabel("<b>Sum Hours:</b><br><i>" + str(sum(i["sample_size_hours"] for i in data)) + "</i>")
        overall_hours.setAlignment(Qt.AlignCenter)
        overall_data_points = QLabel("<b>Sum Data-Points:</b><br><i>" + str(sum(i["sample_size_data_points"] for i in data)) + "</i>")
        overall_data_points.setAlignment(Qt.AlignCenter)
        overall_days = QLabel("<b>Amount Days:</b><br><i>" + str(int(time_frame.days)) + "</i>")
        overall_days.setAlignment(Qt.AlignCenter)
        overall_time_frame = QLabel("<b>Time-Frame:</b><br><i>" + str(time_frame.to_pretty_string()) + "</i>")
        overall_time_frame.setAlignment(Qt.AlignCenter)
        sub_sub_sub_layout.addWidget(overall_hours)
        sub_sub_sub_layout.addWidget(overall_data_points)

        sub_sub_sub_layout.addWidget(overall_days)
        sub_sub_sub_layout.addWidget(overall_time_frame)
        sub_sub_layout.addLayout(sub_sub_sub_layout)
        move_to_center_of_screen(self, self.app.screens()[0])

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

            try:
                amount_update, amount_deleted = self.backend.updater()
                if amount_update is not None and amount_deleted is not None:
                    if self.config.get("gui", "notify_on_update_finished") is True and any(i > 0 for i in [amount_update, amount_deleted]):
                        self.sys_tray.send_update_finished_message(msg=f"Updated {amount_update!r} Log-files\nDeleted {amount_deleted!r} old Log-Files.")

            finally:

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
                self.backend.events.stop.set()
                self.update_thread.join(5.0)
            log.info("shutting down %r", self.statusbar)
            self.statusbar.shutdown()
            self.menubar.close()
            self.menubar.destroy(True, True)
            log.info("Starting shutting down %r", self.backend)
            self.backend.shutdown()

            log.info("Finished shutting down %r", self.backend)
            splash.close()

            log.info("closing all windows of %r", self.app)
            self.app.closeAllWindows()
            for widget in self.app.allWidgets():
                try:
                    widget.close()
                    widget.destroy(True, True)
                except RuntimeError:
                    continue
            log.info("Quiting %r", self.app)

            self.app.quit()
            if self.temp_help_dir is not None:
                self.temp_help_dir.cleanup()
            log.info('%r accepting event %r', self, event.type().name)
            self.deleteLater()
            event.accept()
        else:
            event.ignore()

    def open_settings_window(self):
        x = self.config
        self._temp_settings_window = SettingsWindow(general_config=x, main_window=self).setup()
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


def start_gui() -> int:

    # TODO: Rewrite so everything starts through the app

    app = AntistasiLogbookApplication(sys.argv)
    app.message_handler = QtMessageHandler().install()

    if app.is_full_gui is False:
        return

    config_path = META_PATHS.config_dir.joinpath("general_config.ini")
    if os.getenv("is_dev", "false") != "false":
        config_path = Path(os.getenv("_MAIN_DIR")).joinpath("dev_temp", "config", config_path.name)
    config = get_config(spec_path=DATA_DIR.joinpath("general_configspec.json"), config_path=config_path)
    config.reload()
    if config.get("general", "is_first_start", default=True) is True:
        temp_db_path = config.get('database', "database_path", default=None)
        config.set("general", "is_first_start", False, create_missing_section=True)
    start_splash = app.show_splash_screen("start_up")
    db_path = config.get('database', "database_path", default=None)
    database = GidSqliteApswDatabase(db_path, config=config, thread_safe=True, autoconnect=True, autorollback=not META_INFO.is_dev)
    config.set('database', "database_path", Path(database.database_path))
    backend = Backend(database=database, config=config, update_signaler=UpdaterSignaler())

    app.setup(backend=backend, icon=AllResourceItems.app_icon_image)

    _main_window = app.create_main_window(AntistasiLogbookMainWindow)

    _main_window.show()
    return app.exec()


# region[Main_Exec]
if __name__ == '__main__':

    # dotenv.load_dotenv(r"D:\Dropbox\hobby\Modding\Programs\Github\My_Repos\Antistasi_Logbook\antistasi_logbook\nextcloud.env")
    start_gui()


# endregion[Main_Exec]
