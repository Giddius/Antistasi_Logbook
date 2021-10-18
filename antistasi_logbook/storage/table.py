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
from pypika import Table, Column, SQLLiteQuery, Field, FormatParameter, Criterion

# endregion[Imports]

# region [TODO]


# endregion [TODO]

# region [Logging]


# endregion[Logging]

# region [Constants]

THIS_FILE_DIR = Path(__file__).parent.absolute()

# endregion[Constants]


TABLE_NAME_REGEX = re.compile(r"""CREATE TABLE (IF NOT EXISTS )?(?P<name>[\"\w]+)""")

COLUMN_REGEX = re.compile(r"""(?P<name>["\w]+)\s(?P<typus>\w+)(?P<extra>.*)\,""")

UNIQUE_REGEX = re.compile(r"""UNIQUE\((?P<items>([\"\w]\,?\s?)+)""")

FOREIGN_KEY_REGEX = re.compile(r"""REFERENCES (?P<table_name>[\"\w]+)\s?\((?P<column_name>[\"\w]+)\)""")


class GidSQLColumn:

    def __init__(self, name: str, typus: str, extra: str = None) -> None:
        self.name = name
        self.typus = typus
        self.extra = extra

    @cached_property
    def is_id(self) -> bool:
        return "PRIMARY KEY" in self.extra

    @cached_property
    def is_foreign_key(self) -> bool:
        return "REFERENCES" in self.extra

    @cached_property
    def foreign_key_table_name(self) -> str:
        return FOREIGN_KEY_REGEX.search(self.extra).group('table_name').strip('"')

    @cached_property
    def foreign_key_column_name(self) -> str:
        return FOREIGN_KEY_REGEX.search(self.extra).group('column_name').strip('"')

    def __repr__(self) -> str:
        return self.name

    def __str__(self) -> str:
        return self.name


class GidSQLTable(Table):

    @classmethod
    def from_create_sql_string(cls, create_string: str) -> "GidSQLTable":

        name = TABLE_NAME_REGEX.match(create_string).group("name").strip('"')
        columns = []
        for column_match in COLUMN_REGEX.finditer(create_string):
            columns.append(GidSQLColumn(**{k: v.strip(' "') for k, v in column_match.groupdict().items()}))

        uniques = None
        unique_match = UNIQUE_REGEX.search(create_string)
        if unique_match:
            column_dict = {c.name: c for c in columns}
            uniques = tuple(column_dict.get(item.strip().strip('"')) for item in unique_match.group('items').split(','))

        return cls(name=name, columns=columns, unique_constrained=uniques)

    def __init__(self, name: str, columns: Iterable[GidSQLColumn], unique_constrained: tuple[GidSQLColumn] = None) -> None:
        super().__init__(name, query_cls=SQLLiteQuery)
        self.columns = columns
        self.name = self._table_name
        self.unique_constrained = unique_constrained

    @cached_property
    def id_column(self) -> Optional[GidSQLColumn]:
        for column in self.columns:
            if column.is_id is True:
                return column

    def get_all(self):
        query = self._query_cls.from_(self.name).select('*')
        return query


bbb = """CREATE TABLE IF NOT EXISTS "LogFile_tbl" (
    "item_id" INTEGER PRIMARY KEY AUTOINCREMENT,
    "name" TEXT NOT NULL,
    "server" INTEGER NOT NULL REFERENCES "Server_tbl" ("item_id") ON DELETE CASCADE,
    "remote_path" REMOTEPATH UNIQUE NOT NULL,
    "size" INTEGER NOT NULL,
    "modified_at" DATETIME NOT NULL,
    "last_parsed_line_number" INTEGER DEFAULT 0,
    "finished" BOOL DEFAULT 0,
    "created_at" DATETIME,
    "game_map" INTEGER REFERENCES "GameMap_tbl" ("item_id") ON DELETE CASCADE,
    "header_text" TEXT,
    "utc_offset" INT,
    "comments" TEXT,
    UNIQUE("name", "server", "remote_path")
);"""

# region[Main_Exec]


if __name__ == '__main__':
    x = GidSQLTable.from_create_sql_string(bbb)
    for c in x.columns:
        if c.is_foreign_key:
            print(f"{c.foreign_key_table_name=} || {c.foreign_key_column_name=}")
# endregion[Main_Exec]
