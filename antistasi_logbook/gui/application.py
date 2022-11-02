"""
WiP.

Soon.
"""

# region [Imports]

# * Standard Library Imports ---------------------------------------------------------------------------->
import shutil
import argparse
import sys
import os
from time import sleep
from typing import TYPE_CHECKING, Any, Optional, TypedDict, Union
from pathlib import Path
from datetime import datetime
from functools import cached_property
from concurrent.futures import ThreadPoolExecutor
from collections.abc import Iterable, Mapping
# * Qt Imports --------------------------------------------------------------------------------------->
from PySide6.QtGui import QFont, QIcon, QColor, QScreen, QGuiApplication
from PySide6.QtCore import Qt, QRect, QSettings, QObject, Signal
from PySide6.QtWidgets import QMainWindow, QMessageBox, QApplication, QSplashScreen, QStyle
from antistasi_logbook.data import DATA_DIR
# * Third Party Imports --------------------------------------------------------------------------------->
from jinja2 import BaseLoader, Environment, Template

# * Gid Imports ----------------------------------------------------------------------------------------->
from gidapptools import get_logger, get_meta_info, get_meta_paths
from gidapptools.gid_config.interface import get_config, ConfigValueConverter

from gidapptools.gidapptools_qt.basics.application import WindowHolder
from gidapptools.general_helper.string_helper import StringCase, StringCaseConverter
# * Local Imports --------------------------------------------------------------------------------------->
from antistasi_logbook.gui.resources.antistasi_logbook_resources_accessor import AllResourceItems
from antistasi_logbook.errors import ExceptionHandlerManager, MissingLoginAndPasswordError
from antistasi_logbook.records.base_record import BaseRecord, RecordColorCache
import psutil
from antistasi_logbook.data.templates import ABOUT_STYLESHEET_FILE, ABOUT_TEMPLATE_FILE
from antistasi_logbook.data.templates.cli_argument_templates import ARG_DOC_HTML_TEMPLATE, ARG_DOC_MARKDOWN_TEMPLATE
# * Type-Checking Imports --------------------------------------------------------------------------------->
if TYPE_CHECKING:
    from gidapptools.gid_config.interface import GidIniConfig
    from gidapptools.gidapptools_qt.resources.resources_helper import PixmapResourceItem
    from antistasi_logbook.backend import Backend
    from antistasi_logbook.gui.main_window import LogbookSystemTray, AntistasiLogbookMainWindow
    from gidapptools.meta_data.meta_info import MetaInfo
# * Third Party Imports --------------------------------------------------------------------------------->


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


class CommandLineArgDoc:

    suppress_indicators: set[str] = {"==SUPPRESS=="}
    single_line_text_template: str = "{name} - {help_text} - {argument_strings} - default: {default_value} - required: {is_required} - is flag:{is_flag}"
    text_template: str = "{name}\n{help_text}\n{argument_strings}\ndefault: {default_value}\nrequired: {is_required}\nis flag:{is_flag}"
    markdown_template: str = ARG_DOC_MARKDOWN_TEMPLATE
    html_template: Template = Environment(loader=BaseLoader).from_string(ARG_DOC_HTML_TEMPLATE)

    def __init__(self, argument: argparse.Action, app_meta_info: "MetaInfo" = None) -> None:
        self.argument = argument
        self.app_meta_info = app_meta_info or META_INFO

    @property
    def name(self) -> str:
        name = self.argument.metavar or self.argument.dest
        return StringCaseConverter.convert_to(name, StringCase.TITLE)

    @property
    def help_text(self) -> str:
        help_text = self.argument.help.replace("%(prog)r", "{prog}").replace("%(prog)s", "{prog}")
        return help_text

    @property
    def default_value(self) -> Optional[Any]:
        default_value = self.argument.default
        if str(default_value) in self.suppress_indicators:
            return None

        return default_value

    @property
    def is_required(self) -> bool:
        return self.argument.required

    @property
    def is_flag(self) -> bool:
        if isinstance(self.argument, argparse._StoreConstAction):
            return True

        return False

    @property
    def choices(self) -> Optional[Iterable]:
        return self.argument.choices

    @property
    def argument_strings(self) -> tuple[str]:
        return tuple(self.argument.option_strings)

    def get_text(self, single_line: bool = False) -> str:
        bool_values = {True: "Yes", False: "No"}
        help_text = self.help_text.format(prog=self.app_meta_info.pretty_app_name)
        is_required = bool_values[self.is_required]
        is_flag = bool_values[self.is_flag]
        default_value = bool_values.get(self.default_value, self.default_value)

        argument_strings = self.argument_strings
        template = self.single_line_text_template if single_line is True else self.text_template
        return template.format(name=self.name,
                               help_text=help_text,
                               is_required=is_required,
                               is_flag=is_flag,
                               default_value=default_value,
                               argument_strings=argument_strings,
                               prog=self.app_meta_info.pretty_app_name)

    def get_markdown(self) -> str:
        bool_values = {True: "✅", False: "❎"}
        help_text = self.help_text.format(prog="`" + self.app_meta_info.pretty_app_name + "`")
        is_required = bool_values[self.is_required]
        is_flag = bool_values[self.is_flag]
        default_value = bool_values.get(self.default_value, self.default_value)

        argument_strings = '\n'.join(f"- {arg}" for arg in self.argument_strings)

        return self.markdown_template.format(name=self.name,
                                             help_text=help_text,
                                             is_required=is_required,
                                             is_flag=is_flag,
                                             default_value=default_value,
                                             argument_strings=argument_strings,
                                             prog=self.app_meta_info.pretty_app_name)

    def get_html(self) -> str:
        bool_values = {True: '✔️', False: '❌'}
        help_text = self.help_text.format(prog=f'<div class="app_name">{self.app_meta_info.pretty_app_name}</div>')
        is_required = bool_values[self.is_required]
        is_flag = bool_values[self.is_flag]
        default_value = bool_values.get(self.default_value, self.default_value)

        return self.html_template.render(name=self.name,
                                         help_text=help_text,
                                         is_required=is_required,
                                         is_flag=is_flag,
                                         default_value=default_value,
                                         argument_strings=self.argument_strings,
                                         prog=self.app_meta_info.pretty_app_name)

    def __str__(self) -> str:
        return self.get_text(single_line=True)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(action={self.action!r})"


class ErrorSignaler(QObject):
    show_error_signal = Signal(str, BaseException)

    def __repr__(self) -> str:
        """
        Basic Repr
        !REPLACE!
        """
        return f'{self.__class__.__name__}'


class AntistasiLogbookApplication(QApplication):

    def __init__(self, argvs: Iterable[str] = None):
        self.meta_info = get_meta_info()
        self.meta_paths = get_meta_paths()

        super().__init__(argvs)

        self.error_signaler = ErrorSignaler()
        ExceptionHandlerManager.signaler = self.error_signaler
        self.is_setup: bool = False
        self.is_full_gui = True
        self.icon: QIcon = None
        self.main_window: "AntistasiLogbookMainWindow" = None
        self.sys_tray: "LogbookSystemTray" = None
        self.extra_windows = WindowHolder()
        self.current_splash_screen: QSplashScreen = None
        self._gui_thread_pool: ThreadPoolExecutor = None

        self.backend: "Backend" = None
        self.jinja_environment = None
        self.init_app_meta_data()
        self.cli_arguments = self.parse_cli_arguments()
        self.argument_doc_items: list[CommandLineArgDoc] = None
        self.color_config: "GidIniConfig" = None

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

        color_config_file = self.meta_paths.config_dir.joinpath("color_config.ini")
        if self.is_dev is True:
            color_config_file = Path(os.getenv("_MAIN_DIR")).joinpath("dev_temp", "config", color_config_file.name)
        self.color_config = get_config(DATA_DIR.joinpath("color_configspec.json"), color_config_file)
        self.color_config.reload()
        self.backend.color_config = self.color_config
        self.config.reload()
        self.backend.start_up()

        self.setQuitOnLastWindowClosed(False)
        self.setup_app_font()
        BaseRecord._color_cache = RecordColorCache(self.color_config)
        self.is_setup = True

    def get_standard_icon(self, icon_name: Union[str, QStyle.StandardPixmap]) -> QIcon:
        if isinstance(icon_name, QStyle.StandardPixmap):
            return self.style().standardIcon(icon_name)

        all_standard_icons = {i.removeprefix("SP_").casefold(): getattr(QStyle, i) for i in dir(QStyle()) if i.startswith("SP_")}

        corrected_name = all_standard_icons[icon_name.casefold().removeprefix("sp_")]
        return self.style().standardIcon(corrected_name)

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
                      "Python Version": self.meta_info.python_version,
                      "License": self.meta_info.app_license,
                      "Summary": self.meta_info.summary,
                      "Description": self.meta_info.description}

        return self.jinja_environment.from_string(ABOUT_TEMPLATE_FILE.read_text(encoding='utf-8', errors='ignore')).render(data=text_parts, style=ABOUT_STYLESHEET_FILE.read_text(encoding='utf-8', errors='ignore'))

    def show_about(self) -> None:
        title = f"About {self.applicationDisplayName()}"
        text = self._get_about_text()
        QMessageBox.about(self.main_window, title, text)

    def show_about_qt(self) -> None:
        x = self.aboutQt()

    def get_argument_parser(self) -> argparse.ArgumentParser:
        self.argument_doc_items = []
        parser = argparse.ArgumentParser(prog=self.meta_info.app_name, add_help=True)
        self.argument_doc_items.append(CommandLineArgDoc(parser._actions[0]))
        max_action = parser.add_argument("-max", '--maximized', action='store_true', help="Start %(prog)r maximized")
        self.argument_doc_items.append(CommandLineArgDoc(max_action))

        min_action = parser.add_argument("-min", '--minimized', action='store_true', help="Start the %(prog)r minimized")
        self.argument_doc_items.append(CommandLineArgDoc(min_action))

        top_action = parser.add_argument('-t', '--always-on-top', action='store_true', help="Make the main window of the %(prog)r always stay on top")
        self.argument_doc_items.append(CommandLineArgDoc(top_action))

        clear_action = parser.add_argument("-c", "--clear-settings", action="store_true", help="Clear most stored settings (resets the settings). Does not start the %(prog)r")
        self.argument_doc_items.append(CommandLineArgDoc(clear_action))
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
            self.quit()

        return _out

    def create_main_window(self, main_window_class: type[QMainWindow], **kwargs) -> QMainWindow:
        args = self.parse_arguments()

        main_window = main_window_class(self, flags=args["main_window_flags"], ** kwargs)

        main_window.setWindowState(args["main_window_states"])
        self.main_window = main_window
        self.main_window.setup()
        self.current_splash_screen.finish(main_window)

        return main_window

    def show_splash_screen(self, splash_type: str) -> QSplashScreen:
        if splash_type == "start_up":
            pixmap = AllResourceItems.antistasi_logbook_splash_starting_image.get_as_pixmap()

        elif splash_type == "shutdown":
            pixmap = AllResourceItems.antistasi_logbook_splash_shutdown_image.get_as_pixmap()

        self.current_splash_screen = QSplashScreen(pixmap, Qt.WindowStaysOnTopHint)

        self.current_splash_screen.show()
        return self.current_splash_screen

    def quit(self):

        try:
            self.on_quit()

        except Exception as e:
            log.error(e, exc_info=True)

        finally:
            super().quit()

    def on_quit(self):
        if self._gui_thread_pool:
            self._gui_thread_pool.shutdown(wait=True)
        temp_path = self.meta_paths.temp_dir
        log.debug("temp_path: %r", temp_path.as_posix())
        for item in temp_path.iterdir():
            if item.is_file():
                log.debug("deleting file %r", item.as_posix())
                item.unlink(missing_ok=True)
            elif item.is_dir():
                log.debug("deleting folder %r", item.as_posix())
                shutil.rmtree(item)

        log.debug(dict(self.extra_windows.windows))

    def __str__(self) -> str:
        return f"{self.__class__.__name__}(name={self.applicationDisplayName()!r})"

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(argvs={self.arguments()[1:]!r})"


# region[Main_Exec]
if __name__ == '__main__':
    pass

# endregion[Main_Exec]
