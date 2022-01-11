"""
WiP.

Soon.
"""

# region [Imports]
import os
from typing import TYPE_CHECKING
from pathlib import Path
import click
from dotenv import load_dotenv
from antistasi_logbook.backend import Backend, GidSqliteApswDatabase
from antistasi_logbook.gui.main_window import start_gui
from antistasi_logbook.storage.models.models import RemoteStorage
from antistasi_logbook.storage.models.models import database_proxy
from gidapptools import get_logger
from gidapptools.meta_data import get_meta_info, get_meta_paths
from gidapptools.meta_data.interface import get_meta_config
import antistasi_logbook
from antistasi_logbook import setup

setup()
# * Third Party Imports --------------------------------------------------------------------------------->


# * Standard Library Imports ---------------------------------------------------------------------------->

# * Third Party Imports --------------------------------------------------------------------------------->

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

META_PATHS = get_meta_paths()
META_INFO = get_meta_info()
CONFIG: "GidIniConfig" = get_meta_config().get_config('general')
CONFIG.config.load()
log = get_logger(__name__)
# endregion[Constants]


def main():
    start_gui()


# region[Main_Exec]
if __name__ == '__main__':
    main()
# endregion[Main_Exec]
