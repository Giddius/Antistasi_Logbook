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

    from antistasi_logbook.parsing.parser import MetaFinder, RawRecord, ModItem
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
    mod_model_lock = RLock()
    game_map_model_lock = RLock()
    antistasi_file_model_lock = RLock()
    _all_log_levels: dict[str, LogLevel] = None
    _all_antistasi_file_objects: dict[str, AntstasiFunction] = None
    _all_game_map_objects: dict[str, GameMap] = None
    bulk_inserter = ThreadPoolExecutor(3)
    tasks = []
    __slots__ = ("log_file", "database", "record_insert_batch_size", "auto_download", "line_cache", "record_storage", "_line_iterator", "_current_line", "_current_line_number", "_bulk_create_batch_size")

    def __init__(self, log_file: "LogFile", database: "GidSQLiteDatabase", auto_download: bool = False, record_insert_batch_size: int = None) -> None:
        self.log_file = log_file
        self.database = database
        self.auto_download = auto_download
        self.line_cache = LineCache()
        self.record_storage: RecordStorage["LogRecord"] = RecordStorage()
        self._line_iterator: LINE_ITERATOR_TYPE = None
        self._current_line: RecordLine = None
        self._current_line_number = 0
        self._bulk_create_batch_size: int = None
        self.record_insert_batch_size = self.bulk_create_batch_size if record_insert_batch_size is None else record_insert_batch_size
        try:
            post_save.connect(self.on_save_antistasi_function_handler, sender=AntstasiFunction)
        except ValueError:
            pass
        try:
            post_save.connect(self.on_save_game_map_function_handler, sender=GameMap)
        except ValueError:
            pass

    def on_save_antistasi_function_handler(self, sender, instance, created):
        if created:
            with self.antistasi_file_model_lock:
                self.__class__._all_antistasi_file_objects = None
            log.warning(('-' * 25) + f" reseted '_all_antistasi_file_objects', because {model_to_dict(instance)} of {sender.__name__!r} was created:{created!r}")

    def on_save_game_map_function_handler(self, sender, instance, created):
        if created:
            with self.game_map_model_lock:
                self.__class__._all_game_map_objects = None
            log.warning(('-' * 25) + f" reseted '_all_game_map_objects', because {model_to_dict(instance)} of {sender.__name__!r} was created:{created!r}")

    @property
    def all_log_levels(self) -> dict[str, LogLevel]:
        if self.__class__._all_log_levels is None:
            self.__class__._all_log_levels = {item.name: item for item in LogLevel.select()}
        return self.__class__._all_log_levels

    @property
    def all_antistasi_file_objects(self) -> dict[str, AntstasiFunction]:
        if self.__class__._all_antistasi_file_objects is None:
            # with self.antistasi_file_model_lock:
            self.__class__._all_antistasi_file_objects = {item.name: item for item in AntstasiFunction.select()}
        return self.__class__._all_antistasi_file_objects

    @property
    def all_game_map_objects(self) -> dict[str, GameMap]:
        if self.__class__._all_game_map_objects is None:
            # with self.game_map_model_lock:
            self.__class__._all_game_map_objects = {item.name: item for item in GameMap.select()}
        return self.__class__._all_game_map_objects

    @property
    def unparsable(self) -> bool:
        return self.log_file.unparsable

    @property
    def bulk_create_batch_size(self) -> int:
        if self._bulk_create_batch_size is None:
            self._bulk_create_batch_size = (32766 // len(LogRecord._meta.columns))
        return self._bulk_create_batch_size

    @profile
    def _convert_raw_record_foreign_keys(self, parsed_data: Optional[dict[str, Any]]) -> Optional[dict[str, Any]]:

        def _get_or_create_antistasi_file(raw_name: str) -> AntstasiFunction:
            item = self.all_antistasi_file_objects.get(raw_name)
            if item is None:
                item = AntstasiFunction(name=raw_name)
                item.save()
            return item

        if parsed_data is None:
            return parsed_data

        if log_level := parsed_data.get("log_level"):
            parsed_data["log_level"] = self.all_log_levels.get(log_level)

        if logged_from := parsed_data.get("logged_from"):
            parsed_data["logged_from"] = _get_or_create_antistasi_file(logged_from)

        if called_by := parsed_data.get("called_by"):
            parsed_data["called_by"] = _get_or_create_antistasi_file(called_by)

        if local_recorded_at := parsed_data.pop("local_recorded_at", None):
            parsed_data["recorded_at"] = local_recorded_at.replace(tzinfo=self.log_file.utc_offset).astimezone(UTC)
        return parsed_data

    @profile
    def raw_record_to_log_record(self, raw_record: "RawRecord") -> Optional["LogRecord"]:
        converted_data = self._convert_raw_record_foreign_keys(raw_record.parsed_data)
        if converted_data is not None:
            return LogRecord(start=raw_record.start, end=raw_record.end, is_antistasi_record=raw_record.is_antistasi_record, log_file=self.log_file, record_class=raw_record.record_class, **converted_data)

    def add_record(self, raw_record: "RawRecord") -> None:
        if raw_record is None or raw_record.parsed_data is None:
            return
        if raw_record.record_class.name == "IsNewCampaignRecord":
            self.log_file.is_new_campaign = True

        self.record_storage.append(raw_record)
        if len(self.record_storage) >= self.record_insert_batch_size:

            self._bulk_insert_records()

    def _insert(self, _stored_records):
        LogRecord.bulk_create((i for i in (self.raw_record_to_log_record(x) for x in _stored_records) if i is not None), self.bulk_create_batch_size)

    @profile
    def _bulk_insert_records(self) -> None:
        stored_records = self.record_storage.dump()
        self.log_file.last_parsed_line_number = max(i.end for i in stored_records)

        self.bulk_inserter.submit(self._insert, stored_records)

    def set_unparsable(self) -> None:
        log.critical(f"setting {self.log_file.name!r} of {self.log_file.server.name!r} to unparsable")
        self.log_file.unparsable = True
        self.log_file.save()

    @profile
    def set_found_meta_data(self, finder: "MetaFinder") -> None:
        if finder.game_map is not MiscEnum.DEFAULT:
            game_map_item = self.all_game_map_objects.get(finder.game_map)
            if game_map_item is None:
                game_map_item = GameMap(name=finder.game_map, full_name=f"PLACE_HOLDER {finder.game_map}")
                game_map_item.save()
            self.log_file.game_map = game_map_item
        if finder.version is not MiscEnum.DEFAULT:
            self.log_file.set_version(finder.version)
        if finder.full_datetime is not MiscEnum.DEFAULT:
            self.log_file.set_first_datetime(finder.full_datetime)
        if finder.mods is not None and finder.mods is not MiscEnum.DEFAULT:

            def _get_or_create_mod(_mod_item: "ModItem") -> Mod:
                with self.mod_model_lock:
                    item = Mod.get_or_none(**_mod_item.as_dict())
                    if item is None:
                        item = Mod(**_mod_item.as_dict())
                        item.save()
                return item

            def _get_or_create_log_file_mod_join(_log_file: "LogFile", _mod: "Mod") -> "LogFileAndModJoin":
                with self.mod_model_lock:
                    item = LogFileAndModJoin.get_or_none(log_file=_log_file, mod=_mod)
                    if item is None:
                        item = LogFileAndModJoin(log_file=_log_file, mod=_mod)
                        item.save()
                return item

            for mod_item in finder.mods:
                m_q = Mod.insert(**mod_item.as_dict()).on_conflict_ignore()
                m_q.execute()

            lf_m_q = LogFileAndModJoin.insert_many([{"log_file": self.log_file, "mod": Mod.get(**m_item.as_dict())} for m_item in finder.mods]).on_conflict_ignore()
            if lf_m_q.execute() != len(finder.mods):
                raise RuntimeError(f"Not all mods have been inserted for {self.log_file}")

    @profile
    def set_header_text(self) -> None:
        if self.line_cache.is_empty() is False:
            text = '\n'.join(i.content for i in self.line_cache.dump())
            self.log_file.header_text = text

    @profile
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
            if self.record_storage.is_empty is False:

                self._bulk_insert_records()

            self.log_file.save()
        else:
            log.error(f"{exception_type=} || {exception_value=}")
            print_tb(traceback)
        self.close()


# region[Main_Exec]
if __name__ == '__main__':
    pass

# endregion[Main_Exec]
