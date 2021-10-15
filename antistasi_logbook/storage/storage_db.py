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
from rich.console import Console as RichConsole, ConsoleOptions
from rich import inspect as rinspect
from antistasi_serverlog_statistic.storage.gidsql.facade import GidSqliteDatabase
from gidapptools.general_helper.dict_helper import replace_dict_keys
from gidapptools.general_helper.timing import time_func
from threading import Lock, RLock
from functools import lru_cache
from string import printable, ascii_letters, digits
from antistasi_serverlog_statistic.storage.gidsql.db_reader import Fetch
from antistasi_serverlog_statistic.items.enums import DBItemAction
import sqlparse
import atexit
from antistasi_serverlog_statistic.utilities.path_utilities import RemotePath
from antistasi_serverlog_statistic.items.enums import LogLevel, PunishmentAction
if TYPE_CHECKING:
    from antistasi_serverlog_statistic.items.base_item import AbstractBaseItem
    from antistasi_serverlog_statistic.storage.gidsql.script_handling import GidSqliteScriptProvider

# endregion[Imports]

# region [TODO]


# endregion [TODO]

# region [Logging]


# endregion[Logging]

# region [Constants]

THIS_FILE_DIR = Path(__file__).parent.absolute()
CONSOLE = RichConsole(soft_wrap=True, record=True)
# endregion[Constants]


def adapt_remotepath(remote_path: RemotePath) -> str:
    return remote_path._path.as_posix()


def convert_remotepath(s: bytes) -> RemotePath:
    path_string = s.decode('utf-8', errors='ignore')
    return RemotePath(Path(path_string))


def adapt_path(path: Path) -> str:
    return path.as_posix()


def convert_path(s: bytes) -> Path:
    path_string = s.decode('utf-8', errors='ignore')
    return Path(path_string)


def adapt_log_level(log_level: LogLevel) -> int:
    return log_level.value


def adapt_punishment_action(punishment_action: PunishmentAction) -> int:
    return punishment_action.value


# Register adapters
sqlite3.register_adapter(RemotePath, adapt_remotepath)
sqlite3.register_adapter(Path, adapt_path)
sqlite3.register_adapter(LogLevel, adapt_log_level)
sqlite3.register_adapter(PunishmentAction, adapt_punishment_action)
# Register converters
sqlite3.register_converter("REMOTEPATH", convert_remotepath)
sqlite3.register_converter("PATH", convert_path)


def dict_row_factory(cursor: sqlite3.Cursor, row: tuple[Any]) -> dict[str, Any]:
    return {desc[0]: row[idx] for idx, desc in enumerate(cursor.description)}


class InsertParameterConverter:

    def __init__(self, scripter: "GidSqliteScriptProvider") -> None:
        self.scripter = scripter

    def get_column_names(self, phrase: str) -> tuple[str]:
        phrase = self.scripter.get(phrase.removesuffix('.sql'), phrase)
        parsed_data = sqlparse.parse(phrase)[0]
        for token in parsed_data.tokens:
            if isinstance(token, sqlparse.sql.Parenthesis):
                columns_list = tuple(token.get_sublists())[0]
                return tuple(o.value.strip('"' + "'") for o in columns_list.get_identifiers())

    def get_value(self, item: "AbstractBaseItem", column_name: str) -> Any:
        def _get_nested_value(nested_item, nested_attr_name: str) -> Any:
            if '.' in nested_attr_name:
                current_attr_name, nested_attr_name = nested_attr_name.split('.', 1)
                new_item = getattr(nested_item, current_attr_name)
                return _get_nested_value(new_item, nested_attr_name)
            try:
                return getattr(nested_item, nested_attr_name)
            except AttributeError:
                return None
        attr_name = item.___db_insert_parameter___.get(column_name, None)
        if attr_name is None:
            return None

        return _get_nested_value(item, attr_name)

    def handle_insert_params(self, phrase: str, item: "AbstractBaseItem") -> tuple[Any]:
        column_names = self.get_column_names(phrase=phrase)

        params = []
        for c_name in column_names:
            params.append(self.get_value(item, c_name))
        return tuple(params)


class StorageDB:
    _forbidden_content_table_name = {"chars": [char for char in printable if char not in set("_" + ascii_letters + digits)], "words": ["drop", "delete"]}
    _item_registry: dict[str, type] = {}
    lock = RLock()

    def __init__(self, db_path: Path = None, script_folder_path: Path = None, db_config=None) -> None:
        self.db_path = THIS_FILE_DIR.joinpath("storage.db") if db_path is None else db_path
        self.script_folder_path = THIS_FILE_DIR.joinpath('sql_phrases') if script_folder_path is None else script_folder_path
        self.db_config = db_config
        self.db = GidSqliteDatabase(self.db_path, self.script_folder_path, config=self.db_config, log_execution=False)
        self.db.startup_db()
        self.insert_parameter_converter = InsertParameterConverter(self.db.scripter)

    def exists_table(self, name: str) -> bool:
        query = "SELECT 1 FROM sqlite_master WHERE type='table' and name = ?"
        return self.query(phrase=query, variables=(name,), fetch=Fetch.One) is not None

    def _check_safety_table_name(self, table_name: str, check_exists: bool = True) -> str:
        casefolded_table_name = table_name.casefold()
        if any(char in casefolded_table_name for char in self._forbidden_content_table_name['chars']):
            # TODO: Custom Error!
            raise RuntimeError(f"Table name {table_name!r} contains forbidden characters, all forbidden characters={''.join(self._forbidden_content_table_name['chars'])}.")

        if any(word == casefolded_table_name for word in self._forbidden_content_table_name['words']):
            # TODO: Custom Error!
            raise RuntimeError(f"Table name {table_name!r} contains forbidden words, all forbidden words={self._forbidden_content_table_name['Words']!r}.")

        if check_exists is True and self.exists_table(table_name) is False:
            # TODO: Custom Error!
            raise RuntimeError(f"A Table with the name {table_name!r} does not exist in the Database.")

        return table_name

    @classmethod
    def register_item(cls, item_class: type) -> None:
        if item_class.__name__ not in cls._item_registry:
            cls._item_registry[item_class.__name__] = item_class

    def get_item_from_item_registry(self, name: str) -> type:
        return self._item_registry[name]

    def write(self, phrase: str, variables: tuple[Any] = None) -> bool:
        with self.lock:
            return self.db.write(phrase=phrase, variables=variables)

    def query(self, phrase: str, variables: tuple[Any] = None, fetch: Union[Fetch, str] = Fetch.All, row_factory: Union[Callable[[sqlite3.Cursor, tuple[Any]], Any], bool] = None) -> Any:
        if isinstance(fetch, str):
            fetch = Fetch(fetch)
        with self.lock:
            return self.db.query(phrase=phrase, variables=variables, fetch=fetch, row_factory=row_factory)

    def get_items(self, item_class: Union[str, "AbstractBaseItem"], *variables, phrase_key: str = 'all') -> Any:
        if isinstance(item_class, str):
            item_class = self.get_item_from_item_registry(item_class)
        phrase = item_class.___db_phrases___.get(DBItemAction.GET)[phrase_key]
        row_factory = item_class.___get_db_row_factory___()
        variables = tuple(variables) if variables else None

        return self.query(phrase=phrase, row_factory=row_factory, variables=variables)

    def insert_item(self, item: "AbstractBaseItem") -> bool:
        phrase = item.___db_phrases___[DBItemAction.INSERT]
        variables = self.insert_parameter_converter.handle_insert_params(phrase=phrase, item=item)
        return self.write(phrase=phrase, variables=variables)

    def insert_many_items(self, items: Iterable["AbstractBaseItem"]) -> bool:
        phrase = items[0].___db_phrases___[DBItemAction.INSERT]
        variables = [self.insert_parameter_converter.handle_insert_params(phrase=phrase, item=item) for item in items]
        return self.write(phrase=phrase, variables=variables)

    def get_id(self, item: "AbstractBaseItem") -> None:
        table_name = self._check_safety_table_name(item.___db_table_name___, check_exists=True)
        if hasattr(item, "___db_get_id_parameter__"):
            phrase = f'SELECT "id" FROM {table_name} WHERE '
            conditions = []
            variables = []
            for k, v in item.___db_get_id_parameter__.items():
                k = self._check_safety_table_name(k, check_exists=False)
                conditions.append(f'"{k}"=?')
                variables.append(v)
            phrase += ' AND '.join(conditions)
            variables = tuple(variables)
        else:
            variables = (item.name,)
            phrase = f'SELECT "id" FROM {table_name} WHERE "name"=?'

        return self.query(phrase=phrase, variables=variables, fetch=Fetch.One)

    def get_item_by_id(self, item_class: Union[str, "AbstractBaseItem"], item_id: int) -> "AbstractBaseItem":

        if isinstance(item_class, str):
            item_class = self.get_item_from_item_registry(item_class)
        phrase = item_class.___db_phrases___.get(DBItemAction.GET)['by_id']
        row_factory = item_class.___get_db_row_factory___()
        return self.query(phrase=phrase, variables=(item_id,), fetch=Fetch.One, row_factory=row_factory)

    def backup_db(self):
        if self.db.amount_backups_to_keep is None or self.db.amount_backups_to_keep <= 0:
            return
        with self.lock:
            shutil.copy(self.db.path, self.db.backup_path)
            self.db.limit_backups()

# region[Main_Exec]


if __name__ == '__main__':
    pass

# endregion[Main_Exec]
