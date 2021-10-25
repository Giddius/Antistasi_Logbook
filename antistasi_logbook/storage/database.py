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
from gidapptools.gid_signal.interface import get_signal
from antistasi_logbook.storage.models.models import database, Server
# endregion[Imports]

# region [TODO]


# endregion [TODO]

# region [Logging]


# endregion[Logging]

# region [Constants]

THIS_FILE_DIR = Path(__file__).parent.absolute()

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
        "cache_size": -1024 * 64,
        "journal_mode": "wal",
        "synchronous": 0,
        "ignore_check_constraints": 0,
        "foreign_keys": 1
    }
    default_extensions = {"json_contains": True,
                          "regexp_function": True}

    def __init__(self,
                 database_path: Path,
                 script_folder: Path,
                 use_gevent=False,
                 autostart=True,
                 queue_max_size=None,
                 results_timeout=None,
                 pragmas=None,
                 extensions=None):
        self.path = Path(database_path)
        self.script_folder = Path(script_folder)
        self.script_provider = GidSQLiteScriptLoader(self.script_folder)
        self.started_up = False
        extensions = self.default_extensions if extensions is None else extensions
        super().__init__(make_db_path(self.path), use_gevent=use_gevent, autostart=autostart, queue_max_size=queue_max_size, results_timeout=results_timeout, pragmas=pragmas or self.default_pragmas, **extensions)

    def start_up_db(self) -> None:
        if self.start_up_db is False:
            for script in self.script_provider.get_setup_scripts():
                self.execute_sql(script)
        self.started_up = True


class GidSQLiteDatabase(SqliteExtDatabase):
    default_pragmas = {
        "cache_size": -1024 * 64,
        "journal_mode": "wal",
        "synchronous": 0,
        "ignore_check_constraints": 0,
        "foreign_keys": 1
    }

    default_extensions = {"json_contains": True,
                          "regexp_function": True}

    def __init__(self,
                 database_path: Path,
                 script_folder: Path,
                 pragmas=None,
                 extensions=None):
        self.path = Path(database_path)
        self.script_folder = Path(script_folder)
        self.script_provider = GidSQLiteScriptLoader(self.script_folder)
        extensions = self.default_extensions if extensions is None else extensions
        pragmas = self.default_pragmas if pragmas is None else pragmas

        super().__init__(make_db_path(self.path), pragmas=pragmas, autoconnect=True, ** extensions)

    def start_up_db(self) -> None:
        conn = sqlite3.connect(self.path)
        for script in self.script_provider.get_setup_scripts():

            conn.executescript(script)
        conn.close()


# region[Main_Exec]
if __name__ == '__main__':
    from rich import inspect as rinspect
    db = GidSQLiteDatabase(THIS_FILE_DIR.joinpath('storage.db'), THIS_FILE_DIR.joinpath("sql_scripts"))
    db.start_up_db()
    database.initialize(db)
    for i in Server.select():
        if i.remote_type.name != "local":
            print(i.get_log_files())

# endregion[Main_Exec]
