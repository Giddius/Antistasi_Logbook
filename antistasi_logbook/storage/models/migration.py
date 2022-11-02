"""
WiP.

Soon.
"""

# region [Imports]

# * Standard Library Imports ---------------------------------------------------------------------------->
from typing import TYPE_CHECKING, Callable, TypeAlias
from pathlib import Path

# * Third Party Imports --------------------------------------------------------------------------------->
from sortedcontainers import SortedDict
from playhouse.migrate import SqliteMigrator

# * Local Imports --------------------------------------------------------------------------------------->
from antistasi_logbook.utilities.misc import VersionItem

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
MIGRATION_FUNCTION_TYPE: TypeAlias = Callable[[SqliteMigrator], None]

MIGRATIONS: SortedDict[VersionItem, MIGRATION_FUNCTION_TYPE] = SortedDict()


def get_version_from_name(in_name: str) -> VersionItem:
    in_name = in_name.casefold().strip()
    version_text_chars = list(in_name)
    curr_char = version_text_chars.pop(0)
    while curr_char.isnumeric() is False:
        curr_char = version_text_chars.pop(0)
    raw_version_text = "".join([curr_char] + version_text_chars).replace("_", ".")
    return VersionItem.from_string(raw_version_text)


def version_migration(func: MIGRATION_FUNCTION_TYPE) -> MIGRATION_FUNCTION_TYPE:
    version = get_version_from_name(func.__name__)
    print(f"version for func {func!r} is {version!r}", flush=True)
    MIGRATIONS[version] = func
    return func


def run_migration(database: "GidSqliteApswDatabase"):
    migrator = SqliteMigrator(database)
    for version, func in MIGRATIONS.items():
        func(migrator)

# region[Main_Exec]


if __name__ == '__main__':
    pass

# endregion[Main_Exec]
