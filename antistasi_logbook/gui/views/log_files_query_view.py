"""
WiP.

Soon.
"""

# region [Imports]

# * Standard Library Imports ---------------------------------------------------------------------------->
from typing import TYPE_CHECKING
from pathlib import Path

# * Gid Imports ----------------------------------------------------------------------------------------->
from gidapptools import get_logger

# * Local Imports --------------------------------------------------------------------------------------->
from antistasi_logbook.gui.views.base_query_tree_view import BaseQueryTreeView

# * Type-Checking Imports --------------------------------------------------------------------------------->
if TYPE_CHECKING:
    pass

# endregion[Imports]

# region [TODO]


# endregion [TODO]

# region [Logging]


# endregion[Logging]

# region [Constants]

from gidapptools.general_helper.timing import get_dummy_profile_decorator_in_globals
get_dummy_profile_decorator_in_globals()
THIS_FILE_DIR = Path(__file__).parent.absolute()
log = get_logger(__name__)

# endregion[Constants]


class LogFilesQueryTreeView(BaseQueryTreeView):
    initially_hidden_columns: set[str] = {"id", "comments"}

    def __init__(self) -> None:
        super().__init__(name="Log-Files")
        self.item_size_by_column_name = self._item_size_by_column_name.copy() | {"name": 275,
                                                                                 "modified_at": 175,
                                                                                 "created_at": 175,
                                                                                 "size": 75,
                                                                                 "version": 75,
                                                                                 "game_map": 100,
                                                                                 "is_new_campaign": 50,
                                                                                 "campaign_id": 100,
                                                                                 "server": 100,
                                                                                 "max_mem": 100,
                                                                                 "amount_warnings": 75,
                                                                                 "amount_errors": 75,
                                                                                 "amount_log_records": 75,
                                                                                 "utc_offset": 100,
                                                                                 "time_frame": 200,
                                                                                 "unparsable": 100}

        # region[Main_Exec]


if __name__ == '__main__':
    pass

# endregion[Main_Exec]
