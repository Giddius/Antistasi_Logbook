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

import subprocess
import inspect

from time import sleep, process_time, process_time_ns, perf_counter, perf_counter_ns
from io import BytesIO, StringIO
from abc import ABC, ABCMeta, abstractmethod
from copy import copy, deepcopy
from enum import Enum, Flag, auto, unique
from pprint import pprint, pformat
from pathlib import Path
from string import Formatter, digits, printable, whitespace, punctuation, ascii_letters, ascii_lowercase, ascii_uppercase
from timeit import Timer
from typing import (TYPE_CHECKING, TypeVar, TypeGuard, TypeAlias, Final, TypedDict, Generic, Union, Optional, ForwardRef, final,
                    no_type_check, no_type_check_decorator, overload, get_type_hints, cast, Protocol, runtime_checkable, NoReturn, NewType, Literal, AnyStr, IO, BinaryIO, TextIO, Any)
from collections import Counter, ChainMap, deque, namedtuple, defaultdict
from collections.abc import (AsyncGenerator, AsyncIterable, AsyncIterator, Awaitable, ByteString, Callable, Collection, Container, Coroutine, Generator,
                             Hashable, ItemsView, Iterable, Iterator, KeysView, Mapping, MappingView, MutableMapping, MutableSequence, MutableSet, Reversible, Sequence, Set, Sized, ValuesView)
from zipfile import ZipFile, ZIP_LZMA
from datetime import datetime, timezone, timedelta
from tempfile import TemporaryDirectory, TemporaryFile, tempdir, NamedTemporaryFile, mkstemp, gettempdir
from textwrap import TextWrapper, fill, wrap, dedent, indent, shorten
from functools import wraps, partial, lru_cache, singledispatch, total_ordering, cached_property, cache
from contextlib import contextmanager, asynccontextmanager, nullcontext, closing, ExitStack, suppress
from statistics import mean, mode, stdev, median, variance, pvariance, harmonic_mean, median_grouped
from urllib.parse import urlparse
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, Future, wait, as_completed, ALL_COMPLETED, FIRST_EXCEPTION, FIRST_COMPLETED
from gidapptools.general_helper.conversion import ns_to_s
import apsw
from tzlocal import get_localzone
from threading import Lock, RLock
from gidapptools import get_logger
if sys.version_info >= (3, 11):
    from typing import Self
else:
    from typing_extensions import Self

if TYPE_CHECKING:
    from antistasi_logbook.storage.database import GidSqliteApswDatabase, PragmaInfo

# endregion[Imports]

# region [TODO]


# endregion [TODO]

# region [Logging]


# endregion[Logging]

# region [Constants]

THIS_FILE_DIR = Path(__file__).parent.absolute()
log = get_logger(__name__)
# endregion[Constants]


PROFILE_FUNCTION_SIGNATURE = Callable[[str, int], None]
# def profiling_function(statement:str, execution_time:int)->None
# execution_time in nanoseconds

PROFILE_ITEM: TypeAlias = dict[str, object]


class PROFILE_DATA(TypedDict):
    database_path: Path
    database_name: str
    pragma_info: "PragmaInfo"
    start_datetime: datetime
    profile_items: list[PROFILE_ITEM]


class SQLProfiler:
    __slots__ = ("database", "_start_datetime", "_temp_shelve_file_path", "_thread_pool", "reporter")
    _data_lock = Lock()

    def __init__(self, database: "GidSqliteApswDatabase") -> None:
        self.database = database
        self._start_datetime: datetime = datetime.now(tz=get_localzone())
        self._temp_shelve_file_path: Path = self._make_temp_file()
        self._thread_pool = ThreadPoolExecutor(1)
        self.reporter: set["BaseSQLProfileReporter"] = set()

    def add_reporter(self, reporter: "BaseSQLProfileReporter") -> Self:
        if reporter not in self.reporter:
            self.reporter.add(reporter)
        return self

    def _make_temp_file(self) -> Path:
        temp_dir = Path(TemporaryDirectory().name).resolve()
        temp_dir.mkdir(parents=True, exist_ok=True)

        temp_file = temp_dir.joinpath(f"sql_profiler_data_{self._start_datetime.strftime('%Y-%m-%d_%H-%M-%S')}.txt").with_suffix("")

        return temp_file

    def _store_new_data(self, statement: str, execution_time: int) -> None:
        with self._data_lock:
            _storage = shelve.open(os.fspath(self._temp_shelve_file_path), flag="c")

            try:
                if statement not in _storage:
                    _storage[statement] = tuple()
                _storage[statement] = tuple(tuple([execution_time]) + _storage[statement])
            finally:
                _storage.close()

    def _get_final_data(self) -> PROFILE_DATA:
        with self._data_lock:
            data = PROFILE_DATA(database_path=self.database.database_path,
                                database_name=self.database.database_name,
                                pragma_info=self.database.pragma_info,
                                start_datetime=self._start_datetime,
                                profile_items=[])

            _storage: dict[str, tuple[int]] = shelve.open(os.fspath(self._temp_shelve_file_path), flag="c")
            for statement, execution_times in _storage.items():
                item_stdev = 0
                if len(execution_times) >= 2:
                    item_stdev = stdev(execution_times)
                item_data = {"statement": statement,
                             "times": execution_times,
                             "amount": len(execution_times),
                             "sum": sum(execution_times),
                             "mean": mean(execution_times),
                             "median": median(execution_times),
                             "median_grouped": median_grouped(execution_times),
                             "stdev": item_stdev}

                data["profile_items"].append(item_data)

        return data

    def add_data(self, statement: str, execution_time: int) -> None:
        if execution_time <= 0:
            return
        try:
            self._thread_pool.submit(self._store_new_data, statement=statement, execution_time=execution_time)
        except RuntimeError:
            pass

    def close(self) -> None:

        self._thread_pool.shutdown(wait=True, cancel_futures=False)
        while self._data_lock.locked() is True:
            sleep(0.1)
        final_data = self._get_final_data()

        def _create_report(in_reporter: "BaseSQLProfileReporter"):
            in_reporter.process_data(final_data)

        with ThreadPoolExecutor(6) as pool:
            list(pool.map(_create_report, list(self.reporter)))
        for reporter in self.reporter:
            reporter.process_data(final_data)
        self._cleanup()

    def _cleanup(self) -> None:
        self._temp_shelve_file_path.unlink(missing_ok=True)
        try:
            os.rmdir(self._temp_shelve_file_path.parent)
        except (FileNotFoundError, OSError):
            pass


class BaseSQLProfileReporter(ABC):
    def __init__(self, use_seconds: bool = True, sort_by: Optional[str] = "sum") -> None:
        self.use_seconds = use_seconds
        self.sort_by = sort_by

    def modify_item(self, in_item: PROFILE_ITEM) -> dict[str, object]:
        item = in_item.copy()
        if self.use_seconds is True:
            item["times"] = tuple(ns_to_s(i, decimal_places=3) for i in item["times"])
            item["sum"] = ns_to_s(item["sum"], decimal_places=4)
            item["mean"] = ns_to_s(item["mean"], decimal_places=4)
            item["median"] = ns_to_s(item["median"], decimal_places=4)
            item["median_grouped"] = ns_to_s(item["median_grouped"], decimal_places=4)
            item["stdev"] = ns_to_s(item["stdev"], decimal_places=4)

        return item

    def sort_items(self, in_items: list[dict[str, object]]) -> list[dict[str, object]]:
        if self.sort_by is None:
            return in_items.copy()

        if self.sort_by == "sum":
            return sorted(in_items, key=lambda x: x["sum"], reverse=True)

        return sorted(in_items, key=lambda x: len(x["statement"].casefold()), reverse=True)

    def modify_data(self, data: PROFILE_DATA) -> PROFILE_DATA:
        data["profile_items"] = self.sort_items([self.modify_item(i) for i in data["profile_items"]])
        return data

    @abstractmethod
    def create_output(self, data: PROFILE_DATA) -> None:
        ...

    def process_data(self, data: PROFILE_DATA) -> None:
        modified_data = self.modify_data(data.copy())
        self.create_output(modified_data)


class PrintReporter(BaseSQLProfileReporter):

    def create_output(self, data: PROFILE_DATA) -> None:
        print(f'{"="*25} {data["database_name"]} {"="*25}')
        print()
        print("~" * 100)
        print("pragma_data\n" + indent(pformat(dict(data["pragma_info"].pragma_data)), "    "))
        print()
        print("compile_options\n" + indent(pformat(dict(data["pragma_info"].compile_options)), "    "))
        print()
        print("module_list\n" + indent(pformat(data["pragma_info"].module_list), "    "))
        print()
        print("~" * 100)
        for item in data["profile_items"]:
            print(f"{'#'*10} {item['statement']} {'#'*10}")
            print(f"    sum -> {item['sum']}")
            print(f"    amount -> {item['amount']}")
            print(f"    mean -> {item['mean']}")
            print(f"    median -> {item['median']}")
            print(f"    median_grouped -> {item['median_grouped']}")
            print(f"    stdev -> {item['stdev']}")

            for _time in item["times"]:
                print(f"        {_time}")

            print()
            print("-" * 50)


class SimpleTextReporter(BaseSQLProfileReporter):

    def create_output(self, data: PROFILE_DATA) -> None:
        out_file = Path.cwd().joinpath(f'sql_profiling_{data["database_name"].split(".")[0]}_{data["start_datetime"].strftime("%Y-%m-%d_%H-%M-%S")}.txt')
        with out_file.open("w", encoding='utf-8', errors='ignore') as f:
            f.write(f'{"="*25} {data["database_name"]} {"="*25}' + '\n')
            f.write("\n")
            f.write(("~" * 100) + '\n')
            f.write("pragma_data\n" + indent(pformat(dict(data["pragma_info"].pragma_data)), "    ") + '\n')
            f.write("\n")
            f.write("compile_options\n" + indent(pformat(dict(data["pragma_info"].compile_options)), "    ") + '\n')
            f.write('\n')
            f.write("module_list\n" + indent(pformat(data["pragma_info"].module_list), "    ") + '\n')
            f.write("\n")
            f.write(("~" * 100) + '\n')
            for item in data["profile_items"]:
                f.write(f"{'#'*10} {item['statement']} {'#'*10}" + '\n')
                f.write(f"    sum -> {item['sum']}" + '\n')
                f.write(f"    amount -> {item['amount']}" + '\n')
                f.write(f"    mean -> {item['mean']}" + '\n')
                f.write(f"    median -> {item['median']}" + '\n')
                f.write(f"    median_grouped -> {item['median_grouped']}" + '\n')
                f.write(f"    stdev -> {item['stdev']}" + '\n')

                for _time in sorted(item["times"], reverse=True):
                    f.write(f"        {_time}" + '\n')

                f.write("\n")
                f.write(("-" * 50) + '\n')
# region[Main_Exec]


if __name__ == '__main__':
    pass


# endregion[Main_Exec]
