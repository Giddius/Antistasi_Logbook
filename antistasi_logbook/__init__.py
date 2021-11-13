"""Antistasi_Serverlog_Statistics"""

__version__ = '0.1.0'

from gidapptools.meta_data import setup_meta_data

from pathlib import Path
import rich.traceback
from rich.console import Console as RichConsole

CONSOLE = RichConsole(soft_wrap=True)

rich.traceback.install(console=CONSOLE)

THIS_FILE_DIR = Path(__file__).parent.absolute()

import os


def setup():
    setup_meta_data(__file__,
                    configs_to_create=[THIS_FILE_DIR.joinpath("data", "general_config.ini")],
                    spec_to_create=[THIS_FILE_DIR.joinpath("data", "general_configspec.json")],
                    file_changed_parameter="changed_time")
