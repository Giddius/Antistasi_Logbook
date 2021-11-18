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
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, wait, ALL_COMPLETED, as_completed
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
from gidapptools.gid_logger.fake_logger import fake_logger
if TYPE_CHECKING:

    from antistasi_logbook.parsing.parser import MetaFinder, RawRecord, ModItem, ForeignKeyCache
    from antistasi_logbook.storage.database import GidSQLiteDatabase
# endregion[Imports]

# region [TODO]


# endregion [TODO]

# region [Logging]


# endregion[Logging]

# region [Constants]
from gidapptools.general_helper.timing import get_dummy_profile_decorator_in_globals
get_dummy_profile_decorator_in_globals()
THIS_FILE_DIR = Path(__file__).parent.absolute()
log = fake_logger
# endregion[Constants]


@attr.s(auto_detect=True, auto_attribs=True, slots=True, frozen=True)
class RecordLine:
    content: str = attr.ib()
    start: int = attr.ib()

    def __str__(self) -> str:
        return self.content

    def __eq__(self, o: object) -> bool:
        if isinstance(o, self.__class__):
            return self.content == o.content and self.start == o.start


class LineCache(deque):
    _dump_lock = Lock()

    def is_empty(self) -> bool:
        return len(self) == 0

    def dump(self) -> list["RecordLine"]:
        data = list(self)
        self.clear()
        return data


LINE_ITERATOR_TYPE = Generator[RecordLine, None, None]


class RecordStorage(deque):
    _dump_lock = Lock()

    def __init__(self, maxlen: int = None) -> None:
        super().__init__(maxlen=maxlen)

    @property
    def is_empty(self) -> bool:
        return len(self) == 0

    def dump(self) -> list:
        data = list(self)
        self.clear()
        return data


class ParsingContext:

    tasks = []
    __slots__ = ("foreign_key_cache", "log_file", "_unparsable", "database", "record_insert_batch_size", "auto_download", "line_cache", "record_storage", "_line_iterator", "_current_line", "_current_line_number", "_bulk_create_batch_size")

    def __init__(self, log_file: "LogFile", database: "GidSQLiteDatabase", foreign_key_cache: "ForeignKeyCache", auto_download: bool = False) -> None:
        self.log_file = log_file
        self.database = database
        self.auto_download = auto_download
        self.line_cache = LineCache()
        self.foreign_key_cache = foreign_key_cache
        self._line_iterator: LINE_ITERATOR_TYPE = None
        self._current_line: RecordLine = None
        self._current_line_number = 0

        self._unparsable: bool = None

    @property
    def unparsable(self) -> bool:
        if self._unparsable is None:
            return self.log_file.unparsable
        return self._unparsable

    def set_unparsable(self) -> None:
        self._unparsable = True

        self.log_file.set_unparsable()

    def set_found_meta_data(self, finder: "MetaFinder") -> None:
        if finder is None:
            self.set_unparsable()
            return
        if finder.full_datetime is None:
            self.set_unparsable()
            return
        if finder.game_map is not MiscEnum.DEFAULT:
            game_map_item = self.foreign_key_cache.all_game_map_objects.get(finder.game_map)
            if game_map_item is None:
                game_map_item = GameMap(name=finder.game_map, full_name=f"PLACE_HOLDER {finder.game_map}")
                game_map_item.save()

            self.log_file.game_map = game_map_item
        if finder.version is not MiscEnum.DEFAULT:
            self.log_file.set_version(finder.version)
        if finder.full_datetime is not MiscEnum.DEFAULT:
            self.log_file.set_first_datetime(finder.full_datetime)
        if finder.mods is not None and finder.mods is not MiscEnum.DEFAULT:

            def validation_check_amount_inserted(query, target_amount: int, log_file: "LogFile"):
                if query.execute() != target_amount:
                    # TODO: Custom Error
                    raise ValueError(f"Not all mods have been inserted for {self.log_file}")

            data = [mod_item.as_dict() for mod_item in finder.mods]
            Mod.insert_many(data).on_conflict_ignore().execute()

            mods_log_file_join_insert_query = LogFileAndModJoin.insert_many([{"log_file": self.log_file, "mod": Mod.get(**m_item.as_dict())} for m_item in finder.mods]).on_conflict_ignore()
            validation_check_amount_inserted(query=mods_log_file_join_insert_query, target_amount=len(finder.mods), log_file=self.log_file)

    def set_header_text(self, lines: Iterable["RecordLine"]) -> None:
        # takes about 0.0003763 s
        if lines:
            text = '\n'.join(i.content for i in lines if i.content)
            self.log_file.header_text = text

    def set_startup_text(self, lines: Iterable["RecordLine"]) -> None:
        # takes about 0.0103124 s
        if lines:
            text = '\n'.join(i.content for i in lines if i.content)
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

    @contextmanager
    def open(self, cleanup: bool = True) -> TextIO:
        with self.log_file.open(cleanup=cleanup) as f:
            yield f

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

            self.log_file.save()
        else:
            log.error(f"{exception_type=} || {exception_value=}")
            print_tb(traceback)
        self.close()


# region[Main_Exec]
if __name__ == '__main__':
    pass

# endregion[Main_Exec]
