"""
WiP.

Soon.
"""

# region [Imports]

# * Standard Library Imports ---------------------------------------------------------------------------->
from typing import TYPE_CHECKING
from pathlib import Path
import sys
# * Gid Imports ----------------------------------------------------------------------------------------->
from gidapptools import get_logger
from gidapptools.meta_data import get_meta_info, get_meta_paths
from gidapptools.meta_data.interface import get_meta_config

# * Local Imports --------------------------------------------------------------------------------------->
from antistasi_logbook import setup
from antistasi_logbook.gui.main_window import start_gui
import atexit
from time import sleep
setup()
# * Type-Checking Imports --------------------------------------------------------------------------------->
if TYPE_CHECKING:
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
