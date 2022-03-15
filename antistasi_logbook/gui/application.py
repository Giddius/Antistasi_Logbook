"""
WiP.

Soon.
"""

# region [Imports]

# * Standard Library Imports ---------------------------------------------------------------------------->
import shutil
import argparse
from typing import TYPE_CHECKING, Any, Iterable
from pathlib import Path
from datetime import datetime
from functools import cached_property
from concurrent.futures import ThreadPoolExecutor

# * Qt Imports --------------------------------------------------------------------------------------->
from PySide6.QtGui import QFont, QIcon, QColor, QScreen, QGuiApplication
from PySide6.QtCore import Qt, QRect, QSettings
from PySide6.QtWidgets import QMainWindow, QMessageBox, QApplication, QSplashScreen

# * Third Party Imports --------------------------------------------------------------------------------->
from jinja2 import BaseLoader, Environment

# * Gid Imports ----------------------------------------------------------------------------------------->
from gidapptools import get_logger, get_meta_info, get_meta_paths, get_meta_config
from gidapptools.gid_config.interface import EntryTypus
from gidapptools.gidapptools_qt.basics.application import WindowHolder

# * Local Imports --------------------------------------------------------------------------------------->
from antistasi_logbook.gui.resources.antistasi_logbook_resources_accessor import AllResourceItems

# * Type-Checking Imports --------------------------------------------------------------------------------->
if TYPE_CHECKING:
    from gidapptools.gid_config.interface import GidIniConfig
    from gidapptools.gidapptools_qt.resources.resources_helper import PixmapResourceItem
    from antistasi_logbook.backend import Backend
    from antistasi_logbook.gui.main_window import LogbookSystemTray, AntistasiLogbookMainWindow

# * Third Party Imports --------------------------------------------------------------------------------->
import pp

# endregion[Imports]

# region [TODO]


# endregion [TODO]

# region [Logging]


# endregion[Logging]

# region [Constants]

THIS_FILE_DIR = Path(__file__).parent.absolute()
log = get_logger(__name__)
META_INFO = get_meta_info()
META_PATHS = get_meta_paths()

# endregion[Constants]


ABOUT_TEMPLATE = """
<dl>
    {% for key, value in data.items() %}
    <dt><b><u>{{key}}:</u></b></dt>
    <dd>{{value}}</dd>
    {% endfor %}
</dl>"""


def _qcolor(value: str, mode: str = 'decode', **named_arguments) -> float:
    if mode == "decode":
        if value:
            r, g, b, a = (int(i.strip()) for i in value.split(',') if i.strip())
            return QColor(r, g, b, a)

    elif mode == "encode":
        if value:
            return ', '.join(str(i) for i in value.getRgb())


def _handle_qcolor(value: Any, sub_arguments: dict[str, str]) -> EntryTypus:
    return EntryTypus(original_value=value, base_typus=QColor)


META_CONFIG = get_meta_config()
META_CONFIG.add_spec_value_handler("qcolor", _handle_qcolor)
META_CONFIG.add_converter_function(QColor, _qcolor)

COLOR_CONFIG = META_CONFIG.get_config("color")


COLOR_CONFIG.reload()


class AntistasiLogbookApplication(QApplication):

    def __init__(self, argvs: Iterable[str] = None):
        super().__init__(argvs)
        self.is_setup: bool = False
        self.is_full_gui = True
        self.icon: QIcon = None
        self.main_window: "AntistasiLogbookMainWindow" = None
        self.sys_tray: "LogbookSystemTray" = None
        self.extra_windows = WindowHolder()
        self.current_splash_screen: QSplashScreen = None
        self._gui_thread_pool: ThreadPoolExecutor = None
        self.meta_info = get_meta_info()
        self.meta_paths = get_meta_paths()

        self.backend: "Backend" = None
        self.jinja_environment = None
        self.init_app_meta_data()
        self.cli_arguments = self.parse_cli_arguments()

    @cached_property
    def screen_points(self) -> dict[str, int]:
        screen: QScreen = self.primaryScreen()
        screen_rect: QRect = screen.geometry()
        return {"top": screen_rect.top(), "bottom": screen_rect.bottom(), "left": screen_rect.left(), "right": screen_rect.right()}

    def del_extra_window(self, name: str):
        del self.extra_windows[name]

    def init_app_meta_data(self):
        self.setApplicationName(self.meta_info.app_name)
        self.setApplicationDisplayName(self.meta_info.pretty_app_name)
        self.setApplicationVersion(str(self.meta_info.version))
        self.setOrganizationName(self.meta_info.pretty_app_author)
        self.setOrganizationDomain(str(self.meta_info.url))

    def parse_cli_arguments(self):
        return self.parse_arguments()

    def setup(self, backend: "Backend", icon: "PixmapResourceItem") -> None:
        if self.is_setup is True:
            return

        self.backend = backend
        self.icon = icon.get_as_icon() if icon is not None else icon

        self.jinja_environment = Environment(loader=BaseLoader)

        self.color_config = get_meta_config().get_config("color")
        self.backend.start_up()

        self.setQuitOnLastWindowClosed(False)
        self.setup_app_font()
        self.is_setup = True

    @ classmethod
    def with_high_dpi_scaling(cls, argvs: Iterable[str] = None):
        cls.setAttribute(Qt.AA_EnableHighDpiScaling, True)
        cls.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
        QGuiApplication.setDesktopSettingsAware(True)
        return cls(argvs=argvs)

    def setup_app_font(self):
        font: QFont = self.font()

        font_family = "Roboto"
        font_size = 11
        font.setFamily(font_family)
        font.setPointSize(font_size)
        font.setStyleStrategy(QFont.PreferAntialias)
        font.setHintingPreference(QFont.PreferNoHinting)

        self.setFont(font)

    @property
    def gui_thread_pool(self) -> ThreadPoolExecutor:
        if self._gui_thread_pool is None:
            self._gui_thread_pool = ThreadPoolExecutor(5, thread_name_prefix="gui")
        return self._gui_thread_pool

    @property
    def config(self) -> "GidIniConfig":
        return self.backend.config

    @property
    def settings(self) -> QSettings:
        return QSettings()

    @property
    def is_dev(self) -> bool:
        dev_mode = self.config.get("debug", "dev_mode")
        return any(value is True for value in [dev_mode, self.meta_info.is_dev])

    def format_datetime(self, date_time: datetime) -> str:
        if self.config.get("time", "use_local_timezone", default=False) is True:
            date_time = date_time.astimezone(tz=self.meta_info.local_tz)
        time_format = self.config.get("time", "time_format", default='c')
        if time_format == "iso":
            return date_time.isoformat()
        if time_format == "local":
            time_format = "%x %X"

        _out = date_time.strftime(time_format)
        if "%f" in time_format:
            _out = _out[:-3]
        return _out

    def _get_about_text(self) -> str:
        text_parts = {"Name": self.applicationDisplayName(),
                      "Author": self.organizationName(),
                      "Link": f'<a href="{self.organizationDomain()}">{self.organizationDomain()}</a>',
                      "Version": self.applicationVersion(),
                      "Dev Mode": "Yes" if self.is_dev is True else "No",
                      "Operating System": self.meta_info.os,
                      "Python Version": self.meta_info.python_version}

        return self.jinja_environment.from_string(ABOUT_TEMPLATE).render(data=text_parts)

    def show_about(self) -> None:
        title = f"About {self.applicationDisplayName()}"
        text = self._get_about_text()
        QMessageBox.about(self.main_window, title, text)

    def show_about_qt(self) -> None:
        self.aboutQt()

    def get_argument_parser(self) -> argparse.ArgumentParser:
        parser = argparse.ArgumentParser(prog=self.applicationDisplayName(), add_help=True)
        parser.add_argument("-max", '--maximized', action='store_true')
        parser.add_argument("-min", '--minimized', action='store_true')
        parser.add_argument('-t', '--always-on-top', action='store_true')
        parser.add_argument("-c", "--clear-settings", action="store_true")
        return parser

    def parse_arguments(self):
        parser = self.get_argument_parser()
        raw_args = self.arguments()[1:]
        if "-h" in raw_args or '--help' in raw_args:
            self.is_full_gui = False
        result = parser.parse_args()
        _out = {"main_window_flags": Qt.WindowFlags(), "main_window_states": Qt.WindowActive}
        if result.maximized:
            _out["main_window_states"] |= Qt.WindowMaximized
        if result.minimized:
            _out["main_window_states"] |= Qt.WindowMinimized
        if result.always_on_top:
            _out["main_window_flags"] |= Qt.WindowStaysOnTopHint
        if result.clear_settings:
            QSettings().clear()

        return _out

    def create_main_window(self, main_window_class: type[QMainWindow], **kwargs) -> QMainWindow:
        args = self.parse_arguments()

        main_window = main_window_class(self, flags=args["main_window_flags"], ** kwargs)
        self.current_splash_screen.finish(main_window)
        main_window.setWindowState(args["main_window_states"])
        self.main_window = main_window
        self.main_window.setup()
        return main_window

    def show_splash_screen(self, splash_type: str) -> QSplashScreen:
        if splash_type == "start_up":
            pixmap = AllResourceItems.antistasi_logbook_splash_starting_backend_image.get_as_pixmap()
        elif splash_type == "shutdown":
            pixmap = AllResourceItems.antistasi_logbook_splash_shutdown_backend_image.get_as_pixmap()

        self.current_splash_screen = QSplashScreen(pixmap, Qt.WindowStaysOnTopHint)
        self.current_splash_screen.show()
        return self.current_splash_screen

    def quit(self):
        self.on_quit()
        super().quit()

    def on_quit(self):
        if self._gui_thread_pool:
            self._gui_thread_pool.shutdown(wait=True)
        temp_path = self.meta_paths.temp_dir
        log.debug("temp_path: %r", temp_path.as_posix())
        for item in temp_path.iterdir():
            if item.is_file():
                log.debug(f"deleting file {item.as_posix()!r}")
                item.unlink(missing_ok=True)
            elif item.is_dir():
                log.debug(f"deleting folder {item.as_posix()!r}")
                shutil.rmtree(item)

        log.debug(pp.fmt(self.extra_windows.windows))

    def __str__(self) -> str:
        return f"{self.__class__.__name__}(name={self.applicationDisplayName()!r})"

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(argvs={self.arguments()[1:]!r})"


# region[Main_Exec]
if __name__ == '__main__':
    pass

# endregion[Main_Exec]
