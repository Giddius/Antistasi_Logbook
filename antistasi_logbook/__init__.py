"""Antistasi Logbook"""

__version__ = '0.1.7'

from gidapptools.meta_data import setup_meta_data
from gidapptools import get_main_logger, get_main_logger_with_file_logging
from pathlib import Path
import rich.traceback
from rich.console import Console as RichConsole
import atexit
import os

THIS_FILE_DIR = Path(__file__).parent.absolute()


# _extra_logger = ["peewee"]

_extra_logger = []

# log = get_main_logger("__main__", Path(__file__).resolve(), extra_logger=_extra_logger)
log = get_main_logger_with_file_logging("__main__", log_file_base_name=Path(__file__).resolve().parent.stem, path=Path(__file__).resolve(), extra_logger=_extra_logger)

ERROR_CONSOLE = RichConsole(soft_wrap=True, record=True, width=150)

rich.traceback.install(console=ERROR_CONSOLE, width=150)


def setup():
    setup_meta_data(__file__,
                    configs_to_create=[THIS_FILE_DIR.joinpath("data", "general_config.ini")],
                    spec_to_create=[THIS_FILE_DIR.joinpath("data", "general_configspec.json")],
                    file_changed_parameter="changed_time")


# os.environ["ERRORS_TO_FILE"] = "1"


@ atexit.register
def errors_to_file():
    if os.getenv("ERRORS_TO_FILE", "0") != "1":
        return
    file = THIS_FILE_DIR.joinpath('raised_errors')
    txt_file = file.with_suffix('.txt')
    html_file = file.with_suffix('.html')
    ERROR_CONSOLE.save_text(txt_file, clear=False)
    ERROR_CONSOLE.save_html(html_file, clear=True)
