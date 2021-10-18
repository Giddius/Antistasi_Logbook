"""
WiP.

Soon.
"""

# region [Imports]

import os
import re
import sys
import json
import queue
import math
import base64
import pickle
import random
import shelve
import dataclasses
import shutil
import asyncio
import logging
import sqlite3
import platform
import importlib
import subprocess
import inspect
import sqlite3
from time import sleep, process_time, process_time_ns, perf_counter, perf_counter_ns
from io import BytesIO, StringIO
from abc import ABC, ABCMeta, abstractmethod
from copy import copy, deepcopy
from enum import Enum, Flag, auto, unique
from time import time, sleep
from pprint import pprint, pformat
from pathlib import Path
from string import Formatter, digits, printable, whitespace, punctuation, ascii_letters, ascii_lowercase, ascii_uppercase
from timeit import Timer
from typing import TYPE_CHECKING, Union, Callable, Iterable, Optional, Mapping, Any, IO, TextIO, BinaryIO, Hashable, Generator, Literal, TypeVar, TypedDict, AnyStr, ContextManager
import atexit
from zipfile import ZipFile, ZIP_LZMA
from datetime import datetime, timezone, timedelta
from tempfile import TemporaryDirectory
from textwrap import TextWrapper, fill, wrap, dedent, indent, shorten
from functools import wraps, partial, lru_cache, singledispatch, total_ordering, cached_property
from importlib import import_module, invalidate_caches
from contextlib import contextmanager, asynccontextmanager, nullcontext, closing, ExitStack, suppress, AbstractContextManager
from statistics import mean, mode, stdev, median, variance, pvariance, harmonic_mean, median_grouped
from collections import Counter, ChainMap, deque, namedtuple, defaultdict
from urllib.parse import urlparse
from importlib.util import find_spec, module_from_spec, spec_from_file_location
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from importlib.machinery import SourceFileLoader
from antistasi_logbook.items.base_item import AbstractBaseItem
from antistasi_logbook.items.server import Server
from threading import Thread, Lock, RLock, Event, Condition, Barrier, Semaphore
from gidapptools.gid_signal.interface import get_signal
from antistasi_logbook.storage.table import GidSQLTable
# endregion[Imports]

# region [TODO]


# endregion [TODO]

# region [Logging]


# endregion[Logging]

# region [Constants]

THIS_FILE_DIR = Path(__file__).parent.absolute()

# endregion[Constants]


# some pragmas:
#   PRAGMA cache_size(-250000)
#   PRAGMA journal_mode(OFF)
#   PRAGMA synchronous=OFF

FIND_INT_REGEX = re.compile(r"\d+")
DEFAULT_AMOUNT_BACKUPS_TO_KEEP = 5
DEFAULT_BACKUP_DATETIME_FORMAT = "%Y-%m-%d_%H-%M-%S"
DEFAULT_BACKUP_NAME_TEMPLATE = "[{date_and_time}_UTC]_{original_name}_backup.{original_file_extension}"


class BackupManager:

    def __init__(self, db_path: Path, backup_datetime_format: str = None, backup_name_template: str = None, backup_folder: Path = None) -> None:
        self.db_path = Path(db_path)
        self.backup_datetime_format = DEFAULT_BACKUP_DATETIME_FORMAT if backup_datetime_format is None else backup_datetime_format
        self.backup_name_template = DEFAULT_BACKUP_NAME_TEMPLATE if backup_name_template is None else backup_name_template
        self.backup_folder = self.db_path.parent.joinpath('backups') if backup_folder is None else Path(backup_folder)

    @property
    def amount_backups_to_keep(self) -> int:

        return DEFAULT_AMOUNT_BACKUPS_TO_KEEP

    @property
    def all_backup_files(self) -> tuple[Path]:
        _out = []
        for file in self.backup_folder.iterdir():
            if file.is_file() and self.db_path.stem.casefold() in file.stem.casefold() and file.suffix == self.db_path.suffix:
                _out.append(file)
        return sorted(_out, key=lambda x: x.stat().st_ctime)

    def _make_backup_name(self) -> str:
        original_file_extension = self.db_path.suffix.removeprefix('.')
        original_name = self.db_path.stem
        date_and_time = datetime.now(tz=timezone.utc).strftime(self.backup_datetime_format)
        return self.backup_name_template.format(date_and_time=date_and_time, original_name=original_name, original_file_extension=original_file_extension)

    def _copy_db(self) -> None:
        src = self.db_path
        tgt = self.backup_folder.joinpath(self._make_backup_name())
        shutil.copy(src=src, dst=tgt)

    def _delete_excess_backups(self) -> None:
        for backup in self.all_backup_files[:-self.amount_backups_to_keep]:
            backup.unlink(missing_ok=True)

    def backup(self) -> None:
        self.backup_folder.mkdir(parents=True, exist_ok=True)
        self._copy_db()
        self._delete_excess_backups()


class GidSQLiteScriptLoader:
    def __init__(self, script_folder: Path, setup_prefix: str = "setup") -> None:
        self.script_folder = Path(script_folder)
        self.setup_prefix = setup_prefix.casefold()

    @staticmethod
    def modify_key(key: str) -> str:
        return key.casefold().removesuffix('.sql')

    @property
    def scripts(self) -> dict[str, Path]:
        return {self.modify_key(file.name): file for file in self.script_folder.iterdir() if file.is_file() and file.suffix.casefold() == '.sql'}

    def get_setup_scripts(self) -> list[str]:
        _out = []
        for name, file in ((k, v) for k, v in self.scripts.items() if k.startswith(self.setup_prefix)):
            if name == self.setup_prefix:
                _out.append((file, 0))
            elif name.endswith("base"):
                _out.append((file, 0))
            elif name.endswith('items'):
                _out.append((file, 99))
            else:
                match = FIND_INT_REGEX.search(name)
                if match:
                    pos = int(match.group())
                    _out.append((file, pos))
                else:
                    raise NameError(f"Cannot determine setup position of script file {name!r}.")
        return [item.read_text(encoding='utf-8', errors='ignore') for item, pos in sorted(_out, key=lambda x:x[1])]

    def __getitem__(self, key) -> Path:
        key = self.modify_key(key)
        return self.scripts[key]

    def __contains__(self, key) -> bool:
        key = self.modify_key(key)
        return key in self.scripts

    def __len__(self) -> int:
        return len(self.scripts)

    def __setitem__(self, key, value) -> None:
        key = self.modify_key(key)
        _path = self.script_folder.joinpath(key).with_suffix('.sql')
        _path.write_text(value, encoding='utf-8', errors='ignore')

    def __iter__(self):
        return (self.get_phrase(key) for key in self.scripts)

    def get(self, key, default=None):
        key = self.modify_key(key)
        return self.scripts.get(key, default)

    def get_phrase(self, key: str, default: str = None) -> str:
        key = self.modify_key(key)
        try:
            file = self.scripts[key]
            return file.read_text(encoding='utf-8', errors='ignore')
        except KeyError:
            return default

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(script_folder={self.script_folder.as_posix()!r}, setup_prefix={self.setup_prefix!r})"


class GidSQLiteConnector:
    trace_callback_signal = get_signal('db_connection_trace_callback')
    progress_signal = get_signal("db_connection_progress")

    def __init__(self, path: Path,
                 pragmas: tuple[str],
                 lock: RLock = None,
                 progress_handler: tuple[Callable, int] = None,
                 trace_callback: Callable[[str], None] = None,
                 ** connection_kwargs) -> None:
        self.path = path
        self.pragmas = pragmas
        self.lock = lock
        self.progress_handler = (self.default_progress_handler, 1) if progress_handler is None else progress_handler
        self.trace_callback = self.default_trace_callback if trace_callback is None else trace_callback
        self.connection_kwargs = connection_kwargs
        self._open_connection: sqlite3.Connection = None
        self._progress_counter = 0
        self._last_total_changes = None

    def default_trace_callback(self, *args, **kwargs):
        self.trace_callback_signal.emit(*args, **kwargs)

    def default_progress_handler(self) -> None:
        total_changes = self._open_connection.total_changes
        if self._last_total_changes is None or self._last_total_changes != total_changes:
            self._last_total_changes = total_changes
            self._progress_counter += self._open_connection.total_changes
        self.progress_signal.emit(self._progress_counter)

    @property
    def is_connected(self) -> bool:
        return self._open_connection is not None

    def _execute_pragmas(self, ) -> None:
        cursor = self._open_connection.cursor()
        for pragma in self.pragmas:
            cursor.execute(pragma)
        cursor.close()

    def _make_connection(self) -> None:
        self._open_connection = sqlite3.connect(self.path, **self.connection_kwargs)
        self._execute_pragmas()
        if self.progress_handler is not None:
            self._open_connection.set_progress_handler(*self.progress_handler)
        else:
            self._open_connection.set_progress_handler(self.default_progress_handler, 1)

        if self.trace_callback is not None:
            self._open_connection.set_trace_callback(self.trace_callback)
        else:
            self._open_connection.set_trace_callback(self.default_trace_callback)

    def _close_connection(self) -> None:
        self._open_connection.close()
        self._open_connection = None

    def __enter__(self) -> sqlite3.Connection:
        if self.lock is not None:
            self.lock.acquire()
        self._make_connection()
        return self._open_connection

    def __exit__(self, t: type = None, exc: BaseException = None, tb: Any = None) -> None:
        self._close_connection()
        if self.lock is not None:
            self.lock.release()


class GidSQLiteWriter:

    def __init__(self, connector: GidSQLiteConnector) -> None:
        self.connector = connector
        self.parameter_type_dispatch_table = {type(None): self._execute_script,
                                              tuple: self._execute,
                                              list: self._execute_many}

    def _execute_script(self, phrase: str, parameter: None, connection: sqlite3.Connection = None):
        if connection is not None:
            connection.executescript(phrase)
        else:
            with self.connector as connection:
                connection.executescript(phrase)

    def _execute(self, phrase: str, parameter: tuple[Any] = None, connection: sqlite3.Connection = None):
        if connection is not None:
            connection.execute(phrase, parameter)
        else:
            with self.connector as connection:
                connection.execute(phrase, parameter)

    def _execute_many(self, phrase: str, parameter: list[tuple[Any]], connection: sqlite3.Connection = None):
        if connection is not None:
            connection.executemany(phrase, parameter)
        else:
            with self.connector as connection:
                connection.executemany(phrase, parameter)

    def write(self, phrase: str, parameter: Union[list[tuple[Any]], tuple[Any]] = None, connection: sqlite3.Connection = None):
        meth = self.parameter_type_dispatch_table.get(type(parameter), None)
        if meth is None:
            # TODO: Custom Error!
            raise RuntimeError(f"'parameter' has an invalid type of {type(parameter)!r}.")
        meth(phrase, parameter, connection=connection)

    def __call__(self, phrase: str, parameter: Union[list[tuple[Any]], tuple[Any]] = None, connection: sqlite3.Connection = None):
        self.write(phrase=phrase, parameter=parameter, connection=connection)


class GidSQLiteReader:

    def __init__(self, connector: GidSQLiteConnector) -> None:
        self.connector = connector

    def iter_read(self, phrase: str, parameter: tuple[Any] = None, row_factory: Callable[[sqlite3.Cursor, tuple[Any]], Any] = None, connection: sqlite3.Connection = None) -> Generator[Any, None, None]:
        cm = self.connector if connection is None else nullcontext(connection)
        with cm as _connection:
            if row_factory is not None:
                _connection.row_factory = row_factory
            cursor = _connection.execute(phrase, parameter)
            data = cursor.fetchone()
            while data is not None:
                yield data
                data = cursor.fetchone()

    def read(self, phrase: str, parameter: tuple[Any] = None, fetch: Union[Literal['one'], Literal['all'], int] = 'all', row_factory: Callable[[sqlite3.Cursor, tuple[Any]], Any] = None, connection: sqlite3.Connection = None) -> Any:
        cm = self.connector if connection is None else nullcontext(connection)
        with cm as _connection:
            if row_factory is not None:
                _connection.row_factory = row_factory

            cursor = _connection.execute(*[i for i in (phrase, parameter) if i is not None])
            if isinstance(fetch, int):
                return cursor.fetchmany(fetch)
            if fetch == 'all':
                return cursor.fetchall()
            elif fetch == 'one':
                return cursor.fetchone()

    def __call__(self, phrase: str, parameter: tuple[Any] = None, fetch: Union[Literal['one'], Literal['all'], int] = 'all', row_factory: Callable[[sqlite3.Cursor, tuple[Any]], Any] = None, connection: sqlite3.Connection = None) -> Any:
        return self.read(phrase=phrase, parameter=parameter, fetch=fetch, row_factory=row_factory, connection=connection)


class GidSQLClassRegistry:

    def __init__(self) -> None:
        self.registry: dict[str:type] = {}
        self.tables: dict[str, GidSQLTable] = {}

    def register(self, klass: type) -> None:
        if inspect.isabstract(klass) is False:
            name = klass.__name__.casefold()
            if name not in self.registry:
                self.registry[name] = klass
                klass.___db_table___ = self.tables.get(name)

    def register_with_subclasses(self, top_klass: type, recursive: bool = True) -> None:
        self.register(top_klass)
        for sub_class in top_klass.__subclasses__():
            if recursive is True:
                self.register_with_subclasses(sub_class, recursive=recursive)
            else:
                self.register(sub_class)

    def get_tables(self, db: "GidSQLiteDatabase") -> None:
        with db.connect() as con_db:
            for item in con_db.connection.iterdump():
                if item.casefold().startswith('create table'):
                    table = GidSQLTable.from_create_sql_string(item)
                    self.tables[table.name.casefold().removesuffix('_tbl')] = table


class GidSQLiteDatabase:
    write_locks: dict[Path, RLock] = {}
    read_locks: dict[Path, RLock] = {}
    base_locks: dict[Path, RLock] = {}
    default_connection_kwargs = {"detect_types": sqlite3.PARSE_DECLTYPES, "isolation_level": None}
    registry = GidSQLClassRegistry()

    def __init__(self, db_location: Union[str, os.PathLike, Path],
                 script_location: Union[str, os.PathLike, Path],
                 pragmas: Iterable[str] = None,
                 progress_handler: tuple[Callable, int] = None,
                 trace_callback: Callable[[str], None] = None,
                 **connection_kwargs) -> None:
        self.path = Path(db_location)
        self.name = self.path.name
        self.pragmas = tuple() if pragmas is None else tuple(pragmas)

        self.connection_kwargs = self.default_connection_kwargs | connection_kwargs
        self.base_connector = GidSQLiteConnector(self.path, self.pragmas, self.base_lock, progress_handler=progress_handler, trace_callback=trace_callback, **self.connection_kwargs)

        self.backup_manager = BackupManager(self.path)
        self.scripter = GidSQLiteScriptLoader(Path(script_location))
        self.writer = GidSQLiteWriter(GidSQLiteConnector(self.path, self.pragmas, self.write_lock, progress_handler=progress_handler, trace_callback=trace_callback, **self.connection_kwargs))
        self.reader = GidSQLiteReader(GidSQLiteConnector(self.path, self.pragmas, self.read_lock, progress_handler=progress_handler, trace_callback=trace_callback, **self.connection_kwargs))

        self.startup_db()

    @property
    def connection(self) -> sqlite3.Connection:
        if self.base_connector.is_connected is True:
            return self.base_connector._open_connection
        # TODO: Custom Error!
        raise RuntimeError(f"{self} is currently not connected, this attribute can only be used inside the 'connect'-contextmanager.")

    @property
    def base_lock(self) -> RLock:
        try:
            return self.base_locks[self.path]
        except KeyError:
            lock = RLock()
            self.base_locks[self.path] = lock
            return lock

    @property
    def write_lock(self) -> RLock:
        try:
            return self.write_locks[self.path]
        except KeyError:
            lock = RLock()
            self.write_locks[self.path] = lock
            return lock

    @property
    def read_lock(self) -> RLock:
        try:
            return self.read_locks[self.path]
        except KeyError:
            lock = RLock()
            self.read_locks[self.path] = lock
            return lock

    def register_atexit_close(self) -> None:
        atexit.register(self.close)

    def unregister_atexit_close(self) -> None:
        atexit.unregister(self.close)

    def startup_db(self, overwrite=False):
        if self.path.exists() is True and overwrite is True:
            self.path.unlink()

        for script in self.scripter.get_setup_scripts():
            self.writer(script)
        self.registry.get_tables(self)

    def write(self, phrase: str, parameter: Union[list[tuple[Any]], tuple[Any]] = None):
        phrase = self.scripter.get_phrase(phrase, phrase)
        connection = None if self.base_connector.is_connected is False else self.connection
        self.writer(phrase=phrase, parameter=parameter, connection=connection)

    def read(self, phrase: str, parameter: tuple[Any] = None, fetch: Union[Literal['one'], Literal['all'], int] = 'all', row_factory: Callable[[sqlite3.Cursor, tuple[Any]], Any] = None):
        phrase = self.scripter.get_phrase(phrase, phrase)
        connection = None if self.base_connector.is_connected is False else self.connection

        return self.reader(phrase=phrase, parameter=parameter, fetch=fetch, row_factory=row_factory, connection=connection)

    def iter_read(self, phrase: str, parameter: tuple[Any] = None, row_factory: Callable[[sqlite3.Cursor, tuple[Any]], Any] = None) -> Generator[Any, None, None]:
        phrase = self.scripter.get_phrase(phrase, phrase)
        connection = None if self.base_connector.is_connected is False else self.connection
        yield from self.reader.iter_read(phrase=phrase, parameter=parameter, row_factory=row_factory, connection=connection)

    def vacuum(self):
        self.write('VACUUM')

    def backup(self) -> None:
        with self.base_lock:
            with self.write_lock:
                with self.read_lock:
                    self.backup_manager.backup()

    def close(self) -> None:
        self.vacuum()
        self.backup()

    @contextmanager
    def connect(self):
        with self.base_connector as connection:
            yield self

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(db_location={self.path.as_posix()!r}, script_location={self.scripter.script_folder.as_posix()!r}, pragmas={self.pragmas!r})"

    def __str__(self) -> str:
        return f"{self.__class__.__name__}({self.name!r})"


# region[Main_Exec]
if __name__ == '__main__':

    x = GidSQLiteDatabase(Path.cwd().joinpath('check.db'), Path.cwd().joinpath("sql_phrases"), ("PRAGMA cache_size(-250000)", "PRAGMA journal_mode(OFF)", "PRAGMA synchronous=OFF"))
    x.registry.register_with_subclasses(AbstractBaseItem)
    x.register_atexit_close()
    x.write("insert_game_map.sql", (None, 'blah', 'blah_blah', True, None, Path.cwd().as_posix(), None))

    y = x.read("get_server.sql")
    print(Server.___db_table___.get_all())

# endregion[Main_Exec]
