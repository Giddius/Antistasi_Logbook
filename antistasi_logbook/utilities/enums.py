"""
WiP.

Soon.
"""

# region [Imports]

# * Standard Library Imports ---------------------------------------------------------------------------->
from pathlib import Path

# * Gid Imports ----------------------------------------------------------------------------------------->
from gidapptools import get_logger
from gidapptools.meta_data import app_meta, get_meta_info, get_meta_paths
from gidapptools.general_helper.enums import BaseGidEnum

# endregion[Imports]

# region [TODO]


# endregion [TODO]

# region [Logging]


from gidapptools.general_helper.timing import get_dummy_profile_decorator_in_globals

log = get_logger(__name__)
# endregion[Logging]

# region [Constants]
if app_meta.is_setup is False:
    pass
THIS_FILE_DIR = Path(__file__).parent.absolute()
META_PATHS = get_meta_paths()
META_INFO = get_meta_info()


# endregion[Constants]


class RemoteItemType(BaseGidEnum):
    DIRECTORY = "directory"
    FILE = "file"

# region[Main_Exec]


if __name__ == '__main__':
    pass

# endregion[Main_Exec]
