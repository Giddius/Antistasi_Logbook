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
from typing import TYPE_CHECKING, Union, Callable, Iterable, Optional, Mapping, Any, IO, TextIO, BinaryIO, Hashable, Generator, Literal, TypeVar, TypedDict, AnyStr
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
from peewee import Model, TextField, IntegerField, BooleanField, AutoField, DateTimeField, ForeignKeyField, SQL, BareField, SqliteDatabase, Field
from playhouse.sqlite_ext import SqliteExtDatabase
from playhouse.sqliteq import SqliteQueueDatabase
from playhouse.pool import PooledSqliteExtDatabase
import yarl
from gidapptools.general_helper.timing import time_execution
from gidapptools.gid_signal.interface import get_signal
from gidapptools.meta_data.interface import get_meta_paths, MetaPaths, get_meta_config, get_meta_info
from gidapptools.general_helper.conversion import human2bytes
from antistasi_logbook.utilities.locks import UPDATE_LOCK
from antistasi_logbook.storage.models.models import database, Server, RemoteStorage, LogFile, RecordClass, LogRecord, AntstasiFunction, setup_db
from antistasi_logbook.updating.remote_managers import AbstractRemoteStorageManager, LocalManager, WebdavManager, FakeWebdavManager
from antistasi_logbook.utilities.misc import NoThreadPoolExecutor
from rich.console import Console as RichConsole
import threading
from playhouse.apsw_ext import APSWDatabase
from rich import inspect as rinspect
from dateutil.tz import UTC
from antistasi_logbook.parsing.record_class_manager import RecordClassManager
from gidapptools.gid_logger.fake_logger import fake_logger
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
log = fake_logger
# endregion[Constants]

FIND_INT_REGEX = re.compile(r"\d+")


def make_db_path(in_path: Path) -> str:
    in_path = in_path.as_posix().replace('/', '\\')
    return in_path


class GidSQLiteScriptLoader:
    def __init__(self, script_folder: Path, setup_prefix: str = "setup") -> None:
        self.script_folder = Path(script_folder)
        self.setup_prefix = setup_prefix.casefold()

    @staticmethod
    def modify_key(key: str) -> str:
        return key.casefold().removesuffix('.sql')

    @property
    def scripts(self) -> dict[str, Path]:
        _out = {}
        for dirname, folderlist, filelist in os.walk(self.script_folder):
            for file in filelist:

                file_path = Path(dirname, file)
                if file_path.is_file() is False:
                    continue
                if file_path.suffix.casefold() != '.sql':
                    continue
                _out[self.modify_key(file_path.name)] = file_path
        return _out

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


class GidSqliteQueueDatabase(SqliteQueueDatabase):
    default_pragmas = {
        "cache_size": -1 * 64000,
        "journal_mode": "wal",
        "synchronous": 0,
        "ignore_check_constraints": 0,
        "foreign_keys": 1,

        # "journal_size_limit": human2bytes("250 mb"),
        # "threads": 3,
        # "wal_autocheckpoint": 15000
    }
    default_extensions = {"json_contains": True,
                          "regexp_function": False}

    default_db_name = "storage.db"
    default_db_path = META_PATHS.db_dir if os.getenv('IS_DEV', 'false') == "false" else THIS_FILE_DIR

    default_script_folder = THIS_FILE_DIR.joinpath("sql_scripts")

    def __init__(self,
                 database_path: Path = None,
                 script_folder: Path = None,
                 config: "GidIniConfig" = None,
                 record_class_manager: "RecordClassManager" = None,
                 autoconnect=True,
                 thread_safe=False,
                 queue_max_size=None,
                 results_timeout=None,
                 pragmas=None,
                 extensions=None):
        self.path = self.default_db_path.joinpath(self.default_db_name) if database_path is None else Path(database_path)
        self.script_folder = self.default_script_folder if script_folder is None else Path(script_folder)
        self.config = CONFIG if config is None else config
        self.record_class_manager = RecordClassManager() if record_class_manager is None else record_class_manager
        self.script_provider = GidSQLiteScriptLoader(self.script_folder)
        self.started_up = False
        extensions = self.default_extensions if extensions is None else extensions
        pragmas = self.default_pragmas if pragmas is None else pragmas
        super().__init__(make_db_path(self.path), use_gevent=False, autostart=False, queue_max_size=queue_max_size, results_timeout=results_timeout, thread_safe=thread_safe, autoconnect=autoconnect, pragmas=pragmas, **extensions)

    def start_up_db(self, overwrite: bool = False) -> None:

        if self.started_up is True:
            return
        self.path.parent.mkdir(exist_ok=True, parents=True)
        self.script_folder.mkdir(exist_ok=True, parents=True)
        if overwrite is True:
            self.path.unlink(missing_ok=True)
        self.connect(reuse_if_open=True)
        self.start()
        setup_db()
        # self.optimize()
        # self.vacuum()
        log.info(f"{self.journal_size_limit=}")
        log.info(f"{self.wal_autocheckpoint=}")
        log.info(f"{self.cache_size=}")
        log.info(f"{self.journal_mode=}")
        log.info(f"{self.mmap_size=}")
        log.info(f"{self.page_size=}")
        log.info(f"{self.timeout=}")
        log.info(f"{self.read_uncommitted=}")
        log.info(f"{self.synchronous=}")

        self.stop()
        self.start()
        self.started_up = True

    def optimize(self) -> None:
        log.info("optimizing")

        self.execute_sql("OPTIMIZE")

    def vacuum(self) -> None:
        log.info("vacuuming!")

        self.execute_sql("VACUUM")

    def stop(self):
        # self.pragma("optimize")

        sleep(1)

        _out = super().stop()
        while self.is_stopped() is False:
            log.debug("...")
            sleep(0.25)

        return _out

    def close(self):
        for remote_manager in Server.remote_manager_cache.values():
            log.debug(f"closing remote-manager {remote_manager!r}")
            remote_manager.close()

        return super().close()

    def shutdown(self) -> None:
        self.stop()
        sleep(1)
        self.close()


def get_database(database_path: Path = None, script_folder: Path = None, overwrite_db: bool = False, config: "GidIniConfig" = None, **kwargs) -> GidSqliteQueueDatabase:
    from antistasi_logbook.records.antistasi_records import ALL_ANTISTASI_RECORD_CLASSES

    raw_db = GidSqliteQueueDatabase(database_path=database_path, script_folder=script_folder, config=config, **kwargs)

    database.initialize(raw_db)

    raw_db.start_up_db(overwrite=overwrite_db)
    for record_class in ALL_ANTISTASI_RECORD_CLASSES:
        raw_db.record_class_manager.register_record_class(record_class)

    return raw_db


# region[Main_Exec]
if __name__ == '__main__':
    from antistasi_logbook.updating.updater import get_updater, get_update_thread
    from dotenv import load_dotenv
    from antistasi_logbook.parsing.parser import Parser
    from antistasi_logbook.utilities.misc import frozen_time_giver
    load_dotenv(r"D:\Dropbox\hobby\Modding\Programs\Github\My_Repos\Antistasi_Logbook\antistasi_logbook\nextcloud.env")

    db = get_database(overwrite_db=True, config=CONFIG)
    update_thread = get_update_thread(database=db, use_fake_webdav_manager=False, config=CONFIG)  # , thread_pool_class=NoThreadPoolExecutor), get_now=frozen_time_giver("2021.11.11 0:0:0")

    web_dav_rem = RemoteStorage.get_by_id(1)

    web_dav_rem.set_login_and_password(login=os.getenv("NEXTCLOUD_USERNAME"), password=os.getenv("NEXTCLOUD_PASSWORD"), store_in_db=False)
    log.info("starting")
    duration = 150
    with time_execution(f'must be {duration}', condition=True):
        try:
            update_thread._update()
            # update_thread.start()

            # sleep(duration)
            # update_thread.shutdown()

        finally:
            update_thread.updater.close()
            db.shutdown()
    log.debug(dict(vars(FakeWebdavManager.metrics)))
    with time_execution("selecting log file count", condition=True):
        log.debug(f"{LogFile.select().count()=}")
    with time_execution("selecting log record count", condition=True):
        log.debug(f"{LogRecord.select().count()=}")

        # endregion[Main_Exec]
