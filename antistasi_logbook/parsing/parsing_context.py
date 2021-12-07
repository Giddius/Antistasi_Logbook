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
from functools import wraps, partial, lru_cache, singledispatch, total_ordering, cached_property, reduce
from importlib import import_module, invalidate_caches
from contextlib import contextmanager, asynccontextmanager, nullcontext, closing, ExitStack, suppress
from statistics import mean, mode, stdev, median, variance, pvariance, harmonic_mean, median_grouped
from collections import Counter, ChainMap, deque, namedtuple, defaultdict, UserString
from urllib.parse import urlparse
from importlib.util import find_spec, module_from_spec, spec_from_file_location
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, wait, ALL_COMPLETED, as_completed, Future, FIRST_EXCEPTION, FIRST_COMPLETED
from importlib.machinery import SourceFileLoader
import attr
from dateutil.tz import UTC
from traceback import print_tb
import peewee
from playhouse.shortcuts import model_to_dict
from operator import or_
from playhouse.signals import post_save
from threading import Lock, RLock, Semaphore
from gidapptools.general_helper.enums import MiscEnum
from antistasi_logbook.storage.models.models import LogFile, Mod, LogFileAndModJoin, LogRecord, RecordClass, AntstasiFunction, LogLevel, GameMap
from traceback import format_tb, print_tb
from gidapptools import get_logger
from dateutil.tz import tzoffset, UTC

from playhouse.shortcuts import model_to_dict, dict_to_model, update_model_from_dict
from antistasi_logbook.utilities.misc import Version

from antistasi_logbook.utilities.locks import WRITE_LOCK
from gidapptools.gid_signal.interface import get_signal
if TYPE_CHECKING:

    from antistasi_logbook.parsing.parser import MetaFinder, RawRecord, ModItem, ForeignKeyCache
    from antistasi_logbook.storage.database import GidSQLiteDatabase
    from antistasi_logbook.parsing.record_processor import ManyRecordsInsertResult
    from antistasi_logbook.parsing.record_processor import RecordInserter
    from antistasi_logbook.parsing.foreign_key_cache import ForeignKeyCache
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
log = get_logger(__name__)
# endregion[Constants]


@attr.s(auto_detect=True, auto_attribs=True, slots=True, frozen=True)
class RecordLine:
    content: str = attr.ib()
    start: int = attr.ib()

    def __repr__(self) -> str:
        return self.content

    def __str__(self) -> str:
        return self.content

    def __eq__(self, o: object) -> bool:
        if isinstance(o, self.__class__):
            return self.content == o.content and self.start == o.start


LINE_ITERATOR_TYPE = Generator[RecordLine, None, None]


class LineCache(deque):

    def __init__(self, maxlen: int = None) -> None:
        super().__init__(maxlen=maxlen)
        self.lock = Lock()

    @property
    def is_empty(self) -> bool:
        with self.lock:
            return len(self) == 0

    @property
    def is_full(self) -> bool:
        if self.maxlen is None:
            return False
        with self.lock:
            return len(self) == self.maxlen

    def append(self, x: "RecordLine") -> None:
        with self.lock:
            super().append(x)

    def appendleft(self, x: "RecordLine") -> None:
        return super().appendleft(x)

    def pop(self) -> "RecordLine":
        with self.lock:
            return super().pop()

    def popleft(self) -> "RecordLine":
        with self.lock:
            return super().popleft()

    def insert(self, i: int, x: "RecordLine") -> None:
        with self.lock:
            super().insert(i, x)

    def extend(self, iterable: Iterable["RecordLine"]) -> None:
        with self.lock:
            super().extend(iterable)

    def extendleft(self, iterable: Iterable["RecordLine"]) -> None:
        with self.lock:
            super().extendleft(iterable)

    def index(self, x: "RecordLine", start: int = None, stop: int = None) -> int:
        with self.lock:
            kwargs = {}
            if start is not None:
                kwargs["start"] = start
            if stop is not None:
                kwargs["stop"] = stop
            return super().index(x, **kwargs)

    def remove(self, value: "RecordLine") -> None:
        with self.lock:
            super().remove(value)

    def copy(self) -> deque["RecordLine"]:
        with self.lock:
            return super().copy()

    def dump(self) -> list:
        with self.lock:
            data = list(self)
            super().clear()
            return data


class LogParsingContext:
    new_log_record_signal = get_signal("new_log_record")
    __slots__ = ("__weakref__", "_log_file", "record_lock", "log_file_data", "data_lock", "foreign_key_cache", "line_cache", "_line_iterator",
                 "_current_line", "_current_line_number", "futures", "record_storage", "inserter", "_bulk_create_batch_size", "database", "config", "is_open")

    def __init__(self, log_file: "LogFile", inserter: "RecordInserter", config: "GidIniConfig", foreign_key_cache: "ForeignKeyCache") -> None:
        self._log_file = log_file
        self.database = self._log_file.get_meta().database
        self.inserter = inserter
        self.log_file_data = model_to_dict(self._log_file, exclude=[LogFile.log_records, LogFile.mods, LogFile.comments, LogFile.marked])
        self.data_lock = RLock()
        self.foreign_key_cache = foreign_key_cache
        self.config = config
        self.line_cache = LineCache()
        self.record_storage: list["RawRecord"] = []
        self._line_iterator: LINE_ITERATOR_TYPE = None
        self._current_line: RecordLine = None
        self._current_line_number = 0
        self.futures: list[Future] = []
        self._bulk_create_batch_size: int = None
        self.record_lock = Lock()
        self.is_open: bool = False

    @property
    def _log_record_batch_size(self) -> int:

        if self._bulk_create_batch_size is None:
            self._bulk_create_batch_size = self.config.get("parsing", "record_insert_batch_size", default=(32767 // (len(LogRecord.get_meta().columns) * 1)))

        return self._bulk_create_batch_size

    @property
    def unparsable(self) -> bool:
        return self.log_file_data.get("unparsable", False)

    def set_unparsable(self) -> None:
        self.log_file_data["unparsable"] = True

    @profile
    def set_found_meta_data(self, finder: "MetaFinder") -> None:

        # TODO: Refractor this Monster!
        LogFile.get_meta().database.connect(True)
        if finder is None or finder.full_datetime is None:
            self.set_unparsable()
            return

        if self.log_file_data.get("game_map") is None:
            game_map_item = self.foreign_key_cache.all_game_map_objects.get(finder.game_map)
            if game_map_item is None:
                game_map_item = GameMap(name=finder.game_map, full_name=f"PLACE_HOLDER {finder.game_map}")
                self.futures.append(self.inserter.insert_game_map(game_map=game_map_item))

            self.log_file_data["game_map"] = game_map_item

        if self.log_file_data.get("version") is None:
            self.log_file_data["version"] = finder.version

        if self.log_file_data.get("is_new_campaign") is None:
            self.log_file_data["is_new_campaign"] = finder.is_new_campaign

        if self.log_file_data.get("campaign_id") is None:
            self.log_file_data["campaign_id"] = finder.campaign_id

        if self.log_file_data.get("utc_offset") is None:
            difference_seconds = (finder.full_datetime[0] - finder.full_datetime[1]).total_seconds()
            if difference_seconds > (60 * 60 * 24):
                difference_seconds = difference_seconds - (60 * 60 * 24)
            offset_timedelta = timedelta(hours=difference_seconds // (60 * 60))
            offset = tzoffset(self.log_file_data["name"], offset_timedelta)
            self.log_file_data["utc_offset"] = offset
            self.log_file_data["created_at"] = self._log_file.name_datetime.astimezone(offset)

        if finder.mods is not None and finder.mods is not MiscEnum.DEFAULT:

            self.futures.append(self.inserter.insert_mods(mod_items=tuple(finder.mods), log_file=self._log_file))

    def set_header_text(self, lines: Iterable["RecordLine"]) -> None:
        # takes about 0.0003763 s
        if lines:
            text = '\n'.join(i.content for i in lines if i.content)
            self.log_file_data["header_text"] = text

    def set_startup_text(self, lines: Iterable["RecordLine"]) -> None:
        # takes about 0.0103124 s
        if lines:
            text = '\n'.join(i.content for i in lines if i.content)
            self.log_file_data["startup_text"] = text

    def _get_line_iterator(self) -> LINE_ITERATOR_TYPE:
        line_number = 0
        with self._log_file.open() as f:
            for line in f:
                line_number += 1
                if self._log_file.last_parsed_line_number is not None and line_number <= self._log_file.last_parsed_line_number:
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

    @contextmanager
    def open(self, cleanup: bool = True) -> TextIO:
        with self._log_file.open(cleanup=cleanup) as f:
            yield f

    def close(self) -> None:
        if self._line_iterator is not None:
            self._line_iterator.close()
        self._log_file._cleanup()
        self.is_open = False

    @profile
    def _future_callback(self, result: "ManyRecordsInsertResult") -> None:
        max_line_number = result.max_line_number
        max_recorded_at = result.max_recorded_at
        amount = result.amount

        with self.data_lock:
            try:
                self.log_file_data["last_parsed_line_number"] = max([self.log_file_data.get("last_parsed_line_number", 0), max_line_number])

            except TypeError as error:
                log.error(error)
                log.debug(max_line_number)

            try:
                if self.log_file_data.get("last_parsed_datetime") is None:
                    self.log_file_data["last_parsed_datetime"] = max_recorded_at
                else:
                    self.log_file_data["last_parsed_datetime"] = max([self.log_file_data.get("last_parsed_datetime"), max_recorded_at])
            except TypeError as error:
                log.error(error)
                log.debug(max_recorded_at)

    @profile
    def insert_record(self, record: "RawRecord") -> None:
        with self.record_lock:
            self.record_storage.append(record)
            if len(self.record_storage) == self._log_record_batch_size:

                self.futures.append(self.inserter(records=tuple(self.record_storage), context=self))
                self.record_storage.clear()

    def _dump_rest(self) -> None:
        if len(self.record_storage) > 0:
            self.futures.append(self.inserter(records=tuple(self.record_storage), context=self))
            self.record_storage.clear()

    def wait_on_futures(self, timeout: float = None) -> None:
        done, not_done = wait(self.futures, return_when=FIRST_EXCEPTION, timeout=timeout)
        if len(not_done) == 0:
            with self.data_lock:
                self.log_file_data["last_parsed_datetime"] = self.log_file_data.get("modified_at")

    def __enter__(self) -> "LogParsingContext":
        self._log_file.download()
        self.is_open = True
        return self

    @profile
    def __exit__(self, exception_type: type = None, exception_value: BaseException = None, traceback: Any = None) -> None:
        if exception_value is not None:
            log.error("%s, %s", exception_type, exception_value, exc_info=True)
        self.wait_on_futures()
        with self.data_lock:

            task = self.inserter.update_log_file_from_dict(log_file=self._log_file, in_dict=self.log_file_data)
        task.result()
        self.close()

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(log_file={self._log_file!r})"


# region[Main_Exec]
if __name__ == '__main__':
    pass
# endregion[Main_Exec]
