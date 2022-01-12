"""Antistasi Logbook"""

__version__ = '0.3.3'

import os
import atexit
from rich.console import Console as RichConsole
from rich.table import Table
from rich.panel import Panel
from rich.containers import Renderables
from rich.align import Align
from rich.box import DOUBLE_EDGE
from rich.text import Text
import rich.traceback
from pathlib import Path
from gidapptools import get_main_logger, get_main_logger_with_file_logging, get_meta_paths
from gidapptools.meta_data import setup_meta_data
import antistasi_logbook.errors
from pyqtgraph.Qt import QT_LIB

import sys

THIS_FILE_DIR = Path(__file__).parent.absolute()

# TODO: Create release-task that auto-updates `INCLUDED_APSW_ENVIRONMENTS`, or find a way to parse the file names (unlikely, can't find UNIX format)
INCLUDED_APSW_ENVIRONMENTS = [{"Platform": "Windows 64bit", "Python-Version": "3.9"},
                              {"Platform": "Windows 64bit", "Python-Version": "3.10"}]


def on_init_error():
    # TODO: create own library for somthing like that and replace 'pynotifier', because it emit deprecation warnings from wintypes
    from pynotifier import Notification
    Notification(title="Error initializing Antistasi-Logbook",
                 description="Please restart Antistasi-Logbook from your Terminal to see the Error description",
                 duration=30,
                 urgency="critical",
                 app_name="Antistasi_Logbook",
                 icon_path=str(THIS_FILE_DIR.joinpath('app_icon.ico'))).send()


def print_apsw_import_error_msg():
    # TODO: Create general functions/classes for something like that in 'gidapptools'
    info_console = RichConsole(soft_wrap=False, markup=True)
    info_console.bell()
    info_console.print()
    info_console.rule(characters=" : ", style="black on yellow")
    info_console.print()
    info_console.rule("[red]ERROR[red]", characters="!-", style="bright_red")
    info_console.print("UNABLE TO IMPORT [blue][b]APSW[/b][/blue] FROM THE INCLUDED COMPILED [blue][b]APSW[/b][/blue]-FILES!", style="bright_red", justify="center")
    info_console.rule("[red]ERROR[red]", characters="!-", style="bright_red")
    info_console.print()

    info_console.print(Panel("Please install [blue][b]apsw[/b][/blue] from [bright_blue][link=https://rogerbinns.github.io/apsw/download.html]clickable-Link🔗[/link][/bright_blue] (https://rogerbinns.github.io/apsw/download.html)",
                       title="Please install [blue][b]apsw[/b][/blue]",
                       border_style="yellow",
                       style="bold",
                       highlight=True), justify="center")

    env_table = Table(title="Included are compiled [blue][b]apsw[/b][/blue]-files only for:", title_justify="center")
    for key in INCLUDED_APSW_ENVIRONMENTS[0]:
        env_table.add_column(key)
    for item in INCLUDED_APSW_ENVIRONMENTS:
        env_table.add_row(*item.values())

    info_console.rule()

    title = "You can help!".title()
    sub_title = "Contact me via Github [bright_blue][link=https://github.com/Giddius/Antistasi_Logbook]clickable-Link🔗[/link][/bright_blue] (https://github.com/Giddius/Antistasi_Logbook)"
    platform_list = {i.get("Platform") for i in INCLUDED_APSW_ENVIRONMENTS}
    platform_list_string = ', '.join(f"[bright_magenta]{p!r}[/bright_magenta]" for p in platform_list)
    text = f"""You can help to include more compiled [blue][b]apsw[/b][/blue]-files in the Future.
As I can only compile [blue][b]apsw[/b][/blue]-files for the environment I have access to, I need people with access to other environments to compile for those.
Especially if you have access to a [b]Platform (Operating System)[/b] that is [b]NOT[/b] one of <{platform_list_string}> it would really help!\n"""
    help_request_panel = Panel(Renderables([Align(env_table, align="center"), text]), title=title, subtitle=sub_title, border_style="green", box=DOUBLE_EDGE, highlight=True)
    info_console.print(help_request_panel, justify="center")

    info_console.print()
    info_console.rule(characters=" : ", style="black on yellow")

    info_console.print("\n" * 3)


if "apsw" not in sys.modules:
    try:
        from . import apsw

        sys.modules["apsw"] = apsw
    except ImportError:
        on_init_error()
        print_apsw_import_error_msg()


os.environ["PYQTGRAPH_QT_LIB"] = "PySide6"
os.environ["PYTHONDEVMODE"] = "1"
# os.environ["ANALYZE_EVENTS"] = "true"


# _extra_logger = ["peewee"]
_extra_logger = []

IS_SETUP: bool = False


def setup():
    global IS_SETUP
    if IS_SETUP is True:
        return
    setup_meta_data(__file__,
                    configs_to_create=[THIS_FILE_DIR.joinpath("data", "general_config.ini"), THIS_FILE_DIR.joinpath("data", "color_config.ini")],
                    spec_to_create=[THIS_FILE_DIR.joinpath("data", "general_configspec.json"), THIS_FILE_DIR.joinpath("data", "color_configspec.json")],
                    file_changed_parameter="changed_time")
    META_PATHS = get_meta_paths()
    # log = get_main_logger("__main__", Path(__file__).resolve(), extra_logger=_extra_logger)
    log = get_main_logger_with_file_logging("__main__",
                                            log_file_base_name=Path(__file__).resolve().parent.stem,
                                            path=Path(__file__).resolve(),
                                            extra_logger=_extra_logger,
                                            log_folder=META_PATHS.log_dir)

    ERROR_CONSOLE = RichConsole(soft_wrap=True, record=False, width=150)
    rich.traceback.install(console=ERROR_CONSOLE, width=150)
    IS_SETUP = True


setup()
