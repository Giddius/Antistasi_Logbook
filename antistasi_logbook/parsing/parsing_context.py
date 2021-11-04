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
from collections import Counter, ChainMap, deque, namedtuple, defaultdict, UserString
from urllib.parse import urlparse
from importlib.util import find_spec, module_from_spec, spec_from_file_location
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from importlib.machinery import SourceFileLoader
import attr
from traceback import print_tb
import peewee
from threading import Lock, RLock
from gidapptools.general_helper.enums import MiscEnum
from antistasi_logbook.storage.models.models import LogFile, Mod, LogFileAndModJoin, LogRecord
from antistasi_logbook.utilities.locks import DB_LOCK
if TYPE_CHECKING:

    from antistasi_logbook.parsing.parser import MetaFinder
    from antistasi_logbook.storage.database import GidSQLiteDatabase
# endregion[Imports]

# region [TODO]


# endregion [TODO]

# region [Logging]


# endregion[Logging]

# region [Constants]

THIS_FILE_DIR = Path(__file__).parent.absolute()

# endregion[Constants]


@attr.s(auto_detect=True, auto_attribs=True, slots=True, frozen=True)
class RecordLine:
    content: str = attr.ib()
    start: int = attr.ib()

    def __str__(self) -> str:
        return self.content


class LineCache(deque):

    def is_empty(self) -> bool:
        return len(self) == 0

    def dump(self) -> list["RecordLine"]:
        data = list(self)
        self.clear()
        return data


LINE_ITERATOR_TYPE = Generator[RecordLine, None, None]


class ParsingContext:
    mod_model_lock = RLock()
    game_map_model_lock = RLock()

    def __init__(self, log_file: "LogFile", database: "GidSQLiteDatabase", auto_download: bool = False, record_insert_batch_size: int = 1000) -> None:
        self.log_file = log_file
        self.database = database
        self.record_insert_batch_size = record_insert_batch_size
        self.auto_download = auto_download
        self.line_cache = LineCache()
        self.record_storage: list["LogRecord"] = []
        self._line_iterator: LINE_ITERATOR_TYPE = None
        self._current_line: RecordLine = None
        self._current_line_number = 0

    @property
    def unparsable(self) -> bool:
        return self.log_file.unparsable

    @cached_property
    def bulk_create_batch_size(self) -> int:
        return 32766 // len(LogRecord._meta.columns)

    def add_record(self, record: "LogRecord") -> None:
        if record is None:
            return
        self.record_storage.append(record)

        if len(self.record_storage) >= self.record_insert_batch_size:
            LogRecord.bulk_create(self.record_storage, self.bulk_create_batch_size)
            self.record_storage.clear()

    def set_unparsable(self) -> None:
        print(f"setting {self.log_file.name!r} of {self.log_file.server.name!r} to unparsable")
        self.log_file.unparsable = True
        self.log_file.save()

    def set_found_meta_data(self, finder: "MetaFinder") -> None:
        if finder.game_map is not MiscEnum.DEFAULT:
            with self.game_map_model_lock:
                self.log_file.set_game_map(finder.game_map)
        if finder.version is not MiscEnum.DEFAULT:
            self.log_file.set_version(finder.version)
        if finder.full_datetime is not MiscEnum.DEFAULT:
            self.log_file.set_first_datetime(finder.full_datetime)
        if finder.mods is not None and finder.mods is not MiscEnum.DEFAULT:

            for mod_item in finder.mods:

                with self.mod_model_lock:
                    try:
                        mod_entry = Mod.select().where(*[getattr(Mod, k) == v for k, v in mod_item.as_dict().items() if k in {'name', 'mod_dir', "full_path", "hash", "hash_short"}])[0]
                    except IndexError:
                        mod_entry = Mod(**mod_item.as_dict())
                        mod_entry.save()

                with self.mod_model_lock:
                    try:
                        x = LogFileAndModJoin.select().where(LogFileAndModJoin.log_file == self.log_file, LogFileAndModJoin.mod == mod_entry)[0]
                    except IndexError:
                        x = LogFileAndModJoin(log_file=self.log_file, mod=mod_entry)
                        x.save()

    def set_header_text(self) -> None:
        if self.line_cache.is_empty() is False:
            text = '\n'.join(i.content for i in self.line_cache.dump())
            self.log_file.header_text = text

    def set_startup_text(self) -> None:
        if self.line_cache.is_empty() is False:
            text = '\n'.join(i.content for i in self.line_cache.dump())
            self.log_file.startup_text = text

    def _get_line_iterator(self) -> LINE_ITERATOR_TYPE:
        line_number = 0
        with self.log_file.open() as f:
            for line in f:
                line_number += 1
                if self.log_file.last_parsed_line_number is not None and line_number <= self.log_file.last_parsed_line_number:
                    continue
                line = line.rstrip()
                self._current_line_number = line_number
                yield RecordLine(content=line, start=line_number)

    @property
    def line_iterator(self) -> LINE_ITERATOR_TYPE:
        if self._line_iterator is None:
            self._line_iterator = self._get_line_iterator()
        return self._line_iterator

    @property
    def current_line(self) -> "RecordLine":
        if self._current_line is None:
            self.advance_line()

        return self._current_line

    def advance_line(self) -> None:
        self._current_line = next(self.line_iterator, ...)

    def close(self) -> None:
        if self._line_iterator is not None:
            self._line_iterator.close()
        self.log_file._cleanup()

    def __enter__(self) -> "ParsingContext":
        if self.auto_download is True:
            self.log_file.download()
        return self

    def __exit__(self, exception_type: type = None, exception_value: BaseException = None, traceback: Any = None) -> None:

        if all(i is None for i in [exception_type, exception_value, traceback]):
            if len(self.record_storage) > 0:
                LogRecord.bulk_create(self.record_storage, 32766 // len(LogRecord._meta.columns))
                self.record_storage.clear()
            if not self.unparsable:
                self.log_file.last_parsed_line_number = self._current_line_number - 1
            self.log_file.save()

        self.close()


# region[Main_Exec]
if __name__ == '__main__':
    pass

# endregion[Main_Exec]
