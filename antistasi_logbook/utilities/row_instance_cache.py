"""
WiP.

Soon.
"""

# region [Imports]

# * Standard Library Imports ---------------------------------------------------------------------------->
import sys
from typing import TYPE_CHECKING
from pathlib import Path
from functools import lru_cache

if sys.version_info >= (3, 11):
    pass
else:
    pass
# * Third Party Imports --------------------------------------------------------------------------------->
from peewee import Model

# * Gid Imports ----------------------------------------------------------------------------------------->
from gidapptools import get_logger

# * Type-Checking Imports --------------------------------------------------------------------------------->
if TYPE_CHECKING:
    pass

# endregion [Imports]

# region [TODO]


# endregion [TODO]

# region [Logging]


# endregion [Logging]

# region [Constants]

from gidapptools.general_helper.timing import get_dummy_profile_decorator_in_globals
get_dummy_profile_decorator_in_globals()
THIS_FILE_DIR = Path(__file__).parent.absolute()
log = get_logger(__name__)

# endregion [Constants]


class RowInstanceCache:

    def __init__(self, max_size: int = None) -> None:
        self._max_size = max_size
        self._model_class: type[Model] = None

    def log_cache_info(self) -> None:
        log.debug("Cache-Info for RowInstanceCache of %r: %r", self._model_class, self._model_class.get_by_id.cache_info())

    def __call__(self, model_class: type[Model]) -> type[Model]:
        self._model_class = model_class
        self._model_class.row_instance_cache = self
        model_class.get_by_id = lru_cache(maxsize=self._max_size)(super(model_class, model_class).get_by_id)

        return model_class


# region [Main_Exec]

if __name__ == '__main__':
    pass

# endregion [Main_Exec]
