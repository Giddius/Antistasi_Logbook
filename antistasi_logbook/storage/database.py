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
from weakref import WeakSet
import logging
import sqlite3
import platform
import importlib
import subprocess
import inspect
from antistasi_logbook import setup
setup()
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
from typing import TYPE_CHECKING, Union, Callable, Iterable, Optional, Mapping, Any, IO, TextIO, BinaryIO, Hashable, Generator, Literal, TypeVar, TypedDict, AnyStr, Protocol, runtime_checkable
from zipfile import ZipFile, ZIP_LZMA
from datetime import datetime, timezone, timedelta
from tempfile import TemporaryDirectory
from textwrap import TextWrapper, fill, wrap, dedent, indent, shorten
from functools import wraps, partial, lru_cache, singledispatch, total_ordering, cached_property
from importlib import import_module, invalidate_caches
from contextlib import contextmanager, asynccontextmanager, nullcontext, closing, ExitStack, suppress
from statistics import mean, mode, stdev, median, variance, pvariance, harmonic_mean, median_grouped
from collections import Counter, ChainMap, deque, namedtuple, defaultdict
from urllib.parse import urlparse
from importlib.util import find_spec, module_from_spec, spec_from_file_location
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from importlib.machinery import SourceFileLoader
from peewee import Model, TextField, IntegerField, BooleanField, AutoField, DateTimeField, ForeignKeyField, SQL, BareField, SqliteDatabase, Field, DatabaseProxy
from playhouse.sqlite_ext import SqliteExtDatabase
from playhouse.sqliteq import SqliteQueueDatabase
from playhouse.pool import PooledSqliteExtDatabase
import yarl
from gidapptools.general_helper.timing import time_execution
from gidapptools.gid_signal.interface import get_signal
from gidapptools.meta_data.interface import get_meta_paths, MetaPaths, get_meta_config, get_meta_info
from gidapptools.general_helper.conversion import human2bytes
from antistasi_logbook.utilities.locks import UPDATE_LOCK
from antistasi_logbook.storage.models.models import Server, RemoteStorage, LogFile, RecordClass, LogRecord, AntstasiFunction, setup_db, DatabaseMetaData, GameMap, LogLevel
from antistasi_logbook.updating.remote_managers import AbstractRemoteStorageManager, LocalManager, WebdavManager, FakeWebdavManager
from antistasi_logbook.utilities.misc import NoThreadPoolExecutor, Version
from rich.console import Console as RichConsole
from threading import Lock
from apsw import Connection
from playhouse.apsw_ext import APSWDatabase
from rich import inspect as rinspect
from dateutil.tz import UTC
from antistasi_logbook.parsing.foreign_key_cache import ForeignKeyCache

from gidapptools import get_main_logger, get_logger
if TYPE_CHECKING:
    from gidapptools.gid_config.interface import GidIniConfig
# endregion[Imports]

# region [TODO]


# endregion [TODO]

# region [Logging]


# endregion[Logging]

# region [Constants]
from gidapptools.general_helper.timing import get_dummy_profile_decorator_in_globals
get_dummy_profile_decorator_in_globals()
THIS_FILE_DIR = Path(__file__).parent.absolute()
META_PATHS: MetaPaths = get_meta_paths()
META_INFO = get_meta_info()
CONFIG: "GidIniConfig" = get_meta_config().get_config('general')
CONFIG.config.load()
log = get_logger(__name__)
# endregion[Constants]

DEFAULT_DB_NAME = "storage.db"

DEFAULT_PRAGMAS = {
    "cache_size": -1 * 64000,
    "journal_mode": 'wal',
    "synchronous": 0,
    "ignore_check_constraints": 0,
    "foreign_keys": 1,
    "temp_store": "MEMORY",
    "threads": 5,
    "mmap_size": human2bytes("1 gb")
}


def make_db_path(in_path: Union[str, os.PathLike, Path]) -> str:
    return Path(in_path).resolve().as_posix().replace('/', '\\')


class GidSqliteDatabase(Protocol):

    def _pre_start_up(self, overwrite: bool = False) -> None:
        ...

    def _post_start_up(self, **kwargs) -> None:
        ...

    def start_up(self, overwrite: bool = False, database_proxy: DatabaseProxy = None) -> "GidSqliteDatabase":
        ...

    def shutdown(self, error: BaseException = None) -> None:
        ...

    def optimize(self) -> "GidSqliteDatabase":
        ...

    def vacuum(self) -> "GidSqliteDatabase":
        ...

    def backup(self, backup_path: Union[str, os.PathLike, Path] = None) -> "GidSqliteDatabase":
        ...


class GidSqliteApswDatabase(APSWDatabase):
    all_connections: WeakSet[Connection] = WeakSet()
    default_extensions = {"json_contains": True,
                          "regexp_function": False}

    default_db_path = META_PATHS.db_dir if os.getenv('IS_DEV', 'false') == "false" else THIS_FILE_DIR

    def __init__(self,
                 database_path: Path = None,
                 config: "GidIniConfig" = None,
                 auto_backup: bool = False,
                 thread_safe=True,
                 autoconnect=True,
                 pragmas=None,
                 extensions=None):
        self.database_path = self.default_db_path.joinpath(DEFAULT_DB_NAME) if database_path is None else Path(database_path)
        self.database_name = self.database_path.name
        self.config = CONFIG if config is None else config
        self.auto_backup = auto_backup
        self.started_up = False
        self.session_meta_data: "DatabaseMetaData" = None
        extensions = self.default_extensions.copy() | (extensions or {})
        pragmas = DEFAULT_PRAGMAS.copy() | (pragmas or {})
        super().__init__(make_db_path(self.database_path), thread_safe=thread_safe, autoconnect=autoconnect, pragmas=pragmas, timeout=30, **extensions)
        self.foreign_key_cache = ForeignKeyCache(self)
        self.write_lock = Lock()

    @property
    def default_backup_folder(self) -> Path:
        return self.database_path.parent.joinpath("backups")

    @cached_property
    def base_record_id(self) -> int:
        return RecordClass.select().where(RecordClass.name == "BaseRecord").scalar()

    # def _add_conn_hooks(self, conn):
    #     super()._add_conn_hooks(conn)
    #     self.all_connections.add(conn)

    def _pre_start_up(self, overwrite: bool = False) -> None:
        self.database_path.parent.mkdir(exist_ok=True, parents=True)
        if overwrite is True:
            self.database_path.unlink(missing_ok=True)

    def _post_start_up(self, **kwargs) -> None:
        self.session_meta_data = DatabaseMetaData.new_session()

    def start_up(self,
                 overwrite: bool = False,
                 force: bool = False) -> "GidSqliteApswDatabase":

        if self.started_up is True and force is False:
            return
        log.info("starting up %r", self)
        self._pre_start_up(overwrite=overwrite)
        self.connect(reuse_if_open=True)
        with self.write_lock:
            setup_db(self)

        self._post_start_up()
        self.started_up = True
        self.foreign_key_cache.reset_all()
        log.info("finished starting up %r", self)
        return self

    def optimize(self) -> "GidSqliteApswDatabase":
        log.info("optimizing %r", self)
        with self.write_lock:
            self.pragma("OPTIMIZE")
        return self

    def vacuum(self) -> "GidSqliteApswDatabase":
        log.info("vacuuming %r", self)
        with self.write_lock:
            self.execute_sql("VACUUM;")
        return self

    def close(self):
        return super().close()

    def shutdown(self,
                 error: BaseException = None,
                 backup_folder: Union[str, os.PathLike, Path] = None) -> None:
        log.debug("shutting down %r", self)
        with self.write_lock:
            self.session_meta_data.save()

        is_closed = self.close()
        for conn in self.all_connections:
            conn.close(True)
        if self.auto_backup is True and error is None:
            # self.backup(backup_folder=backup_folder)
            log.warning("'backup-method' is not written!")
        log.debug("finished shutting down %r", self)
        self.started_up = False

    def get_all_server(self, ordered_by=Server.id) -> tuple[Server]:
        with self:
            return tuple(Server.select().join(RemoteStorage).order_by(ordered_by))

    def get_log_files(self, server: Server = None, ordered_by=LogFile.id) -> tuple[LogFile]:
        with self:
            if server is None:
                return tuple(LogFile.select().join(Server).order_by(ordered_by))
            return tuple(LogFile.select().join(Server).where(LogFile.server_id == server.id).order_by(ordered_by))

    def get_all_log_levels(self, ordered_by=LogLevel.id) -> tuple[LogLevel]:
        with self:
            return tuple(LogLevel.select().order_by(ordered_by))

    def get_all_antistasi_functions(self, ordered_by=AntstasiFunction.id) -> tuple[AntstasiFunction]:
        with self:
            return tuple(AntstasiFunction.select().order_by(ordered_by))

    def get_all_game_maps(self, ordered_by=GameMap.id) -> tuple[GameMap]:
        with self:
            return tuple(GameMap.select().order_by(ordered_by))

    def __repr__(self) -> str:
        repr_attrs = ("database_name", "config", "auto_backup", "thread_safe", "autoconnect")
        _repr = f"{self.__class__.__name__}"
        attr_text = ', '.join(f"{attr_name}={getattr(self, attr_name)}" for attr_name in repr_attrs)
        return f"{_repr}({attr_text})"


# region[Main_Exec]
if __name__ == '__main__':
    pass
    # endregion[Main_Exec]
