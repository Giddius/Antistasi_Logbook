# region [Imports]


import os
import asyncio
import logging
from enum import Enum, auto
import re
from typing import List, Union, Callable, Any
from threading import Lock

import sqlite3
from datetime import datetime, timedelta, timezone


from antistasi_logbook.storage.gidsql.backup_manager import BackupManager
from antistasi_logbook.storage.gidsql.db_reader import Fetch, GidSqliteReader
from antistasi_logbook.storage.gidsql.db_writer import GidSQLiteWriter
from antistasi_logbook.storage.gidsql.script_handling import GidSqliteScriptProvider
from pathlib import Path
from sortedcontainers import SortedList
# endregion[Imports]

__updated__ = '2020-11-28 03:29:05'

# region [AppUserData]

# endregion [AppUserData]

# region [Logging]

log = logging.getLogger('gidsql')


# endregion[Logging]

# region [Constants]
THIS_FILE_DIR = os.path.abspath(os.path.dirname(__file__))
# endregion[Constants]


class BackUpDbFile:
    backup_date_regex = re.compile(r"""
        \[
        (?P<year>\d+)
        [^\d]
        (?P<month>\d+)
        [^\d]
        (?P<day>\d+)
        [^\d]
        (?P<hour>\d+)
        [^\d]
        (?P<minute>\d+)
        [^\d]
        (?P<second>\d+)
        \_UTC
        \]
        \_
        .*
        """, re.VERBOSE | re.IGNORECASE)

    def __init__(self, path: Union[str, os.PathLike]) -> None:
        self.path = Path(path)
        self.name = self.path.name
        self.backup_date = self._parse_backup_date()

    def _parse_backup_date(self) -> datetime:
        cleaned_name = self.name.split('.')[0].casefold()
        date_and_time_match = self.backup_date_regex.match(cleaned_name)
        back_up_date = datetime(**date_and_time_match.groupdict(), microsecond=0, tzinfo=timezone.utc)
        return back_up_date

    def delete(self):
        os.remove(self.path)
        log.info("removed backup DB file '%s'", self.name)


class PhraseType(Enum):
    Insert = auto()
    Query = auto()
    Create = auto()
    Drop = auto()


class GidSqliteDatabase:
    Insert = PhraseType.Insert
    Query = PhraseType.Query
    Create = PhraseType.Create
    Drop = PhraseType.Drop

    All = Fetch.All
    One = Fetch.One

    def __init__(self, db_location, script_location, config=None, log_execution: bool = True):
        self.path = Path(db_location)
        self.name = self.path.name
        self.script_location = Path(script_location)
        self.config = config
        self.pragmas = "PRAGMA cache_size(-250000);PRAGMA journal_mode(OFF);PRAGMA synchronous=OFF"
        if self.config is not None:
            self.pragmas = self.config.retrieve('general_settings', 'pragmas', typus=List[str], default_fallback=[])
        self.amount_backups_to_keep = self.config.retrieve('general_settings', 'amount_backups_to_keep', typus=int, default_fallback=5) if self.config is not None else 5

        self.writer = GidSQLiteWriter(self.path, self.pragmas, log_execution=log_execution)
        self.reader = GidSqliteReader(self.path, self.pragmas, log_execution=log_execution)
        self.scripter = GidSqliteScriptProvider(self.script_location)
        self.backup_manager = BackupManager(self.path, self.config)
        with sqlite3.connect(self.path, isolation_level=None, detect_types=sqlite3.PARSE_DECLTYPES) as conn:
            self.writer._execute_pragmas(conn)

    def startup_db(self, overwrite=False):
        if self.path.exists() is True and overwrite is True:
            self.path.unlink()

        for idx, script in enumerate(self.scripter.setup_scripts):
            print(f"writing setup script number {idx}")
            for sql_phrase in script.split(';'):
                if sql_phrase:

                    self.writer.write(sql_phrase=sql_phrase)
        return True

    def write(self, phrase, variables=None) -> bool:
        if isinstance(phrase, str):
            phrase = phrase.removesuffix('.sql')
            sql_phrase = self.scripter.get(phrase, phrase)

            outcome = self.writer.write(sql_phrase, variables)
            return outcome
        raise TypeError(f"Phrase has to be of type 'str', not {type(phrase)!r}.")

    def query(self, phrase, variables=None, fetch: Fetch = Fetch.All, row_factory: Union[Callable[[sqlite3.Cursor, tuple[Any]], Any], bool] = None):

        phrase = phrase.removesuffix('.sql')
        sql_phrase = self.scripter.get(phrase, phrase)

        _out = self.reader.query(sql_phrase, variables=variables, fetch=fetch, row_factory=row_factory)

        return _out

    def vacuum(self):
        self.write('VACUUM')

    def close(self) -> None:
        self.vacuum()
        self.backup_manager.backup()

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.path}, {self.script_location}, {self.config})"

    def __str__(self) -> str:
        return self.__class__.__name__


if __name__ == '__main__':
    pass
