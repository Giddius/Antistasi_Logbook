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

from antistasi_logbook.storage.gidsql.phrasers import GidSqliteInserter
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

    phrase_objects = {Insert: GidSqliteInserter, Query: None, Create: None, Drop: None}
    backup_datetime_format = "%Y-%m-%d_%H-%M-%S"
    backup_name_template = "[{date_and_time}_UTC]_{original_name}_backup.{original_file_extension}"

    def __init__(self, db_location, script_location, config=None, log_execution: bool = True):
        self.path = Path(db_location)
        self.name = self.path.name
        self.script_location = Path(script_location)
        self.config = config
        self.pragmas = "PRAGMA cache_size(-250000); PRAGMA journal_mode(OFF);"
        if self.config is not None:
            self.pragmas = self.config.retrieve('general_settings', 'pragmas', typus=List[str], default_fallback=[])
        self.amount_backups_to_keep = self.config.retrieve('general_settings', 'amount_backups_to_keep', typus=int, default_fallback=5) if self.config is not None else 5

        self.writer = GidSQLiteWriter(self.path, self.pragmas, log_execution=log_execution)
        self.reader = GidSqliteReader(self.path, self.pragmas, log_execution=log_execution)
        self.scripter = GidSqliteScriptProvider(self.script_location)

    def limit_backups(self):
        original_name, original_extension = [self.name_format_data.get(i) for i in ["original_name", "original_file_extension"]]
        original_extension = f".{original_extension}"
        all_backups = []
        for file in self.back_up_folder.iterdir():
            if file.is_file() and original_name in file.stem and file.suffix == original_extension:
                creation_time_regex = re.compile(r"""
                                                (?P<year>2\d{3})
                                                [^\d]
                                                (?P<month>[01]?\d)
                                                [^\d]
                                                (?P<day>[0-3]?\d)
                                                [^\d]
                                                (?P<hour>[0-2]?\d)
                                                [^\d]
                                                (?P<minute>[0-6]?\d)
                                                [^\d]
                                                (?P<second>[0-6]?\d)
                                                """, re.VERBOSE)
                all_backups.append((file, datetime(tzinfo=timezone.utc, **{k: int(v) for k, v in creation_time_regex.search(file.stem).groupdict().items()})))
        all_backups = [item[0] for item in sorted(all_backups, key=lambda x: x[1])]
        for file in all_backups[:-self.amount_backups_to_keep]:
            file.unlink(missing_ok=True)

    @property
    def back_up_folder(self) -> Path:
        orig_folder_name = self.path.parent
        backup_folder_name = self.path.stem + '_backups'
        backup_folder = orig_folder_name.joinpath(backup_folder_name).resolve()
        backup_folder.mkdir(exist_ok=True, parents=True)

        return backup_folder

    @property
    def stored_backups(self) -> list[BackUpDbFile]:
        stored_backups = []
        orig_file_extension = self.path.suffix
        for file in os.scandir(self.back_up_folder):
            if file.is_file() and file.name.endswith(f"{orig_file_extension}"):
                stored_backups.append(BackUpDbFile(file.path))
        return sorted(stored_backups, key=lambda x: x.backup_date, reverse=True)

    @property
    def name_format_data(self) -> dict[str, Union[datetime, str]]:
        orig_name, orig_file_extension = self.name.split('.')
        format_data = {"date_and_time": datetime.now(tz=timezone.utc).strftime(self.backup_datetime_format),
                       "original_name": orig_name,
                       "original_file_extension": orig_file_extension}
        return format_data

    @property
    def backup_name(self) -> str:
        return self.backup_name_template.format(**self.name_format_data)

    @property
    def backup_path(self) -> str:
        return self.back_up_folder.joinpath(self.backup_name)

    def startup_db(self, overwrite=False):
        if self.path.exists() is True and overwrite is True:
            self.path.unlink()

        for script in self.scripter.setup_scripts:
            for sql_phrase in script.split(';'):
                if sql_phrase:

                    self.writer.write(sql_phrase=sql_phrase)
        return True

    def new_phrase(self, typus: PhraseType):
        return self.phrase_objects.get(typus)()

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

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.path}, {self.script_location}, {self.config})"

    def __str__(self) -> str:
        return self.__class__.__name__


if __name__ == '__main__':
    pass
