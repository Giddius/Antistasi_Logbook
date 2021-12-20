"""Antistasi Logbook"""

__version__ = '0.1.10'

from gidapptools.meta_data import setup_meta_data
from gidapptools import get_main_logger, get_main_logger_with_file_logging, get_meta_paths
from pathlib import Path
import rich.traceback
from rich.console import Console as RichConsole
import atexit
import os

THIS_FILE_DIR = Path(__file__).parent.absolute()

# _extra_logger = ["peewee"]
_extra_logger = []

IS_SETUP: bool = False


def setup():
    global IS_SETUP
    if IS_SETUP is True:
        return
    setup_meta_data(__file__,
                    configs_to_create=[THIS_FILE_DIR.joinpath("data", "general_config.ini")],
                    spec_to_create=[THIS_FILE_DIR.joinpath("data", "general_configspec.json")],
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
