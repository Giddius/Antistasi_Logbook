"""Antistasi_Serverlog_Statistics"""

__version__ = '0.1.0'

from gidapptools.meta_data import setup_meta_data

from pathlib import Path
import rich.traceback
from rich.console import Console as RichConsole
import atexit

ERROR_CONSOLE = RichConsole(soft_wrap=True, record=True)

rich.traceback.install(console=ERROR_CONSOLE)

THIS_FILE_DIR = Path(__file__).parent.absolute()

import os


def setup():
    setup_meta_data(__file__,
                    configs_to_create=[THIS_FILE_DIR.joinpath("data", "general_config.ini")],
                    spec_to_create=[THIS_FILE_DIR.joinpath("data", "general_configspec.json")],
                    file_changed_parameter="changed_time")


@atexit.register
def errors_to_file():
    file = THIS_FILE_DIR.joinpath('raised_errors')
    txt_file = file.with_suffix('.txt')
    html_file = file.with_suffix('.html')
    ERROR_CONSOLE.save_text(txt_file, clear=False)
    ERROR_CONSOLE.save_html(html_file, clear=False)
