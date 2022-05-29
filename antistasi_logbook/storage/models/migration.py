"""
WiP.

Soon.
"""

# region [Imports]

# * Standard Library Imports ---------------------------------------------------------------------------->
from typing import TYPE_CHECKING, Callable
from pathlib import Path

# * Third Party Imports --------------------------------------------------------------------------------->
import apsw
from natsort import natsort_key
from sortedcontainers import SortedDict
from playhouse.migrate import SqliteMigrator, migrate

# * Type-Checking Imports --------------------------------------------------------------------------------->
if TYPE_CHECKING:
    from antistasi_logbook.storage.database import GidSqliteApswDatabase

# endregion[Imports]

# region [TODO]


# endregion [TODO]

# region [Logging]


# endregion[Logging]

# region [Constants]

THIS_FILE_DIR = Path(__file__).parent.absolute()

# endregion[Constants]

migrations = SortedDict(natsort_key)


def version_migration(func: Callable):
    version_string = func.__name__.removeprefix("migrate_").strip().replace("_", ".")
    migrations[version_string] = func
    return func


def run_migration(database: "GidSqliteApswDatabase"):
    migrator = SqliteMigrator(database)
    for version, func in migrations.items():
        func(migrator)

# region[Main_Exec]


if __name__ == '__main__':
    pass

# endregion[Main_Exec]
