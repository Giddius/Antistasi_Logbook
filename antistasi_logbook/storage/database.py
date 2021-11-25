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
from antistasi_logbook.storage.models.models import database, Server, RemoteStorage, LogFile, RecordClass, LogRecord, AntstasiFunction, setup_db, DatabaseMetaData
from antistasi_logbook.updating.remote_managers import AbstractRemoteStorageManager, LocalManager, WebdavManager, FakeWebdavManager
from antistasi_logbook.utilities.misc import NoThreadPoolExecutor, Version
from rich.console import Console as RichConsole
import threading
from playhouse.apsw_ext import APSWDatabase
from rich import inspect as rinspect
from dateutil.tz import UTC


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
    "wal_autocheckpoint": "1"
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


class GidSqliteQueueDatabase(SqliteQueueDatabase):

    default_extensions = {"json_contains": True,
                          "regexp_function": False}

    default_db_path = META_PATHS.db_dir if os.getenv('IS_DEV', 'false') == "false" else THIS_FILE_DIR

    def __init__(self,
                 database_path: Path = None,

                 config: "GidIniConfig" = None,
                 auto_backup: bool = True,
                 autoconnect=True,
                 thread_safe=True,
                 queue_max_size=None,
                 results_timeout=None,
                 pragmas=None,
                 extensions=None):
        self.database_path = self.default_db_path.joinpath(DEFAULT_DB_NAME) if database_path is None else Path(database_path)
        self.config = CONFIG if config is None else config
        self.auto_backup = auto_backup
        self.started_up = False
        self.session_meta_data: "DatabaseMetaData" = None
        extensions = self.default_extensions if extensions is None else extensions
        pragmas = DEFAULT_PRAGMAS.copy() if pragmas is None else pragmas
        super().__init__(make_db_path(self.database_path), use_gevent=False, autostart=False, queue_max_size=queue_max_size, results_timeout=results_timeout, thread_safe=thread_safe, autoconnect=autoconnect, pragmas=pragmas, **extensions)

    @property
    def default_backup_path(self) -> Path:
        return self.default_db_path.joinpath("backups")

    def _pre_start_up(self, **kwargs) -> None:
        self.database_path.parent.mkdir(exist_ok=True, parents=True)
        if kwargs.get("overwrite", False) is True:
            self.database_path.unlink(missing_ok=True)

    def _post_start_up(self, **kwargs) -> None:
        self.session_meta_data = DatabaseMetaData.new_session(started_at=kwargs.get("started_at", None), app_version=kwargs.get("app_version", None))

    def start_up(self,
                 overwrite: bool = False,
                 force: bool = False,
                 database_proxy: DatabaseProxy = None,
                 started_at: datetime = None,
                 app_version: "Version" = None) -> "GidSqliteQueueDatabase":
        if self.started_up is True and force is False:
            return
        log.info("starting up %r", self)
        self._pre_start_up(overwrite=overwrite)
        if database_proxy:
            database_proxy.initialize(self)
        self.connect(reuse_if_open=True)
        self.start()
        setup_db()

        self.stop()
        self.start()
        self._post_start_up(started_at=started_at, app_version=app_version)
        self.started_up = True
        log.info("finished starting up %r", self)
        return self

    def restart(self) -> "GidSqliteQueueDatabase":
        log.info("restarting %r", self)
        self.stop()
        self.start()
        return self

    def optimize(self) -> "GidSqliteQueueDatabase":
        log.info("optimizing %r", self)
        self.execute_sql("OPTIMIZE")
        return self

    def vacuum(self) -> "GidSqliteQueueDatabase":
        log.info("vacuuming %r", self)
        self.execute_sql("VACUUM")
        return self

    def backup(self, backup_path: Union[str, os.PathLike, Path] = None) -> "GidSqliteQueueDatabase":
        log.info("backing up %r", self)
        backup_path = self.default_backup_path if backup_path is None else Path(backup_path).resolve()
        if backup_path.is_dir():
            backup_path = backup_path.joinpath(self.database_path.name)
        backup_path.parent.mkdir(exist_ok=True, parents=True)
        shutil.copy(self.database_path, backup_path)
        print(backup_path.with_suffix('.zip'))
        with ZipFile(backup_path.with_suffix('.zip'), mode='w') as zippy:
            zippy.write(backup_path.name, backup_path)
        log.info("finished backing up %r", self)

    def shutdown(self,
                 error: BaseException = None,
                 backup_path: Union[str, os.PathLike, Path] = None) -> None:
        log.debug("shutting down %r", self)
        self.session_meta_data.save()
        self.stop()
        sleep(1)
        self.close()
        if self.auto_backup is True and error is None:
            self.backup(backup_path=backup_path)
        log.debug("finished shutting down %r", self)


class GidSqliteApswDatabase(APSWDatabase):
    default_extensions = {"json_contains": True,
                          "regexp_function": False}

    default_db_path = META_PATHS.db_dir if os.getenv('IS_DEV', 'false') == "false" else THIS_FILE_DIR

    def __init__(self,
                 database_path: Path = None,
                 config: "GidIniConfig" = None,
                 auto_backup: bool = False,
                 thread_safe=False,
                 autoconnect=True,
                 pragmas=None,
                 extensions=None):
        self.database_path = self.default_db_path.joinpath(DEFAULT_DB_NAME) if database_path is None else Path(database_path)
        self.database_name = self.database_path.name
        self.config = CONFIG if config is None else config
        self.auto_backup = auto_backup
        self.started_up = False
        self.session_meta_data: "DatabaseMetaData" = None
        extensions = self.default_extensions if extensions is None else extensions
        pragmas = DEFAULT_PRAGMAS.copy() if pragmas is None else pragmas
        super().__init__(make_db_path(self.database_path), thread_safe=thread_safe, autoconnect=autoconnect, pragmas=pragmas, **extensions)

    @property
    def default_backup_folder(self) -> Path:
        return self.database_path.parent.joinpath("backups")

    def reconnect(self) -> None:
        self.close()
        self.connect(True)

    def _pre_start_up(self, overwrite: bool = False) -> None:
        self.database_path.parent.mkdir(exist_ok=True, parents=True)
        if overwrite is True:
            self.database_path.unlink(missing_ok=True)

    def _post_start_up(self, **kwargs) -> None:
        self.session_meta_data = DatabaseMetaData.new_session()

    def start_up(self,
                 overwrite: bool = False,
                 force: bool = False,
                 database_proxy: DatabaseProxy = None) -> "GidSqliteQueueDatabase":
        if self.started_up is True and force is False:
            return
        log.info("starting up %r", self)
        self._pre_start_up(overwrite=overwrite)
        if database_proxy:
            database_proxy.initialize(self)
        self.connect(reuse_if_open=True)

        setup_db()

        self._post_start_up()
        self.started_up = True
        log.info("finished starting up %r", self)
        return self

    def optimize(self) -> "GidSqliteQueueDatabase":
        log.info("optimizing %r", self)
        self.pragma("OPTIMIZE")
        return self

    def vacuum(self) -> "GidSqliteQueueDatabase":
        log.info("vacuuming %r", self)
        self.execute_sql("VACUUM;")
        return self

    # TODO: make class or something, think about how it should work

    def backup(self, backup_folder: Union[str, os.PathLike, Path] = None) -> "GidSqliteQueueDatabase":
        def _get_backup_name(_backup_folder: Path) -> str:
            _backup_folder.mkdir(exist_ok=True, parents=True)
            number = 1
            name = f"{self.database_path.stem}_backup_{number}"

            while name in {item.stem for item in _backup_folder.iterdir() if item.is_file()}:
                number += 1
                name = f"{self.database_path.stem}_backup_{number}"
            return name

        def _limit_backups(_backup_folder: Path) -> None:
            backups = [item for item in _backup_folder.iterdir() if item.is_file()]
            backups = sorted(backups, key=lambda x: x.stat().st_ctime, reverse=True)
            to_delete = backups[self.config.get("backup", "max_backups", default=3):]
            for item in to_delete:
                item.unlink(missing_ok=True)
        log.info("backing up %r", self)
        backup_folder = Path(backup_folder) if backup_folder is not None else self.default_backup_folder

        backup_path = backup_folder.joinpath(_get_backup_name(backup_folder)).with_suffix(self.database_path.suffix)

        shutil.copy(self.database_path, backup_path)

        with ZipFile(backup_path.with_suffix('.zip'), mode='w', compression=ZIP_LZMA) as zippy:
            zippy.write(backup_path, backup_path.name)
        backup_path.unlink(missing_ok=True)
        _limit_backups(backup_folder)
        log.info("finished backing up %r", self)

    def shutdown(self,
                 error: BaseException = None,
                 backup_folder: Union[str, os.PathLike, Path] = None) -> None:
        log.debug("shutting down %r", self)
        self.session_meta_data.save()

        self.close()
        if self.auto_backup is True and error is None:
            self.backup(backup_folder=backup_folder)
        log.debug("finished shutting down %r", self)

    def __repr__(self) -> str:
        repr_attrs = ("database_name", "config", "auto_backup", "thread_safe", "autoconnect")
        _repr = f"{self.__class__.__name__}"
        attr_text = ', '.join(f"{attr_name}={getattr(self, attr_name)}" for attr_name in repr_attrs)
        return f"{_repr}({attr_text})"


# region[Main_Exec]
if __name__ == '__main__':
    pass
    # endregion[Main_Exec]
