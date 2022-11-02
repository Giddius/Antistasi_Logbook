"""
WiP.

Soon.
"""

# region [Imports]

from antistasi_logbook import setup
setup()

# * Standard Library Imports ---------------------------------------------------------------------------->

from typing import TYPE_CHECKING, TypeVar, Generic
from pathlib import Path
import sys

# * Gid Imports ----------------------------------------------------------------------------------------->
from antistasi_logbook.errors import setup_exception_handler
setup_exception_handler()
from gidapptools import get_logger
from gidapptools.meta_data import get_meta_info, get_meta_paths

from gidapptools.general_helper.meta_helper.single_running_instance import SingleRunningInstanceRestrictor

# * Local Imports --------------------------------------------------------------------------------------->

from antistasi_logbook.gui.main_window import start_gui

# * Type-Checking Imports --------------------------------------------------------------------------------->


# endregion[Imports]


# region [TODO]


# endregion [TODO]

# region [Logging]


# endregion[Logging]

# region [Constants]


THIS_FILE_DIR = Path(__file__).parent.absolute()
META_PATHS = get_meta_paths()
META_INFO = get_meta_info()


log = get_logger(__name__)

# endregion[Constants]


def main():
    with SingleRunningInstanceRestrictor(storage_folder=META_PATHS.data_dir, app_name=META_INFO.app_name):
        exit_code = start_gui()
    sys.exit(exit_code)


# region[Main_Exec]
if __name__ == '__main__':

    main()

# endregion[Main_Exec]
