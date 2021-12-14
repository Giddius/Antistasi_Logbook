"""
WiP.

Soon.
"""

# region [Imports]

import os
import re
import sys
import json
from queue import Queue, Empty, Full
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
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, Future, wait, ALL_COMPLETED, as_completed
from importlib.machinery import SourceFileLoader
from threading import Thread, Lock, RLock, Condition, Event
from peewee import fn
from playhouse.shortcuts import update_model_from_dict
from dateutil.tz import UTC, tzoffset
from antistasi_logbook.parsing.raw_record import RawRecord
from antistasi_logbook.storage.models.models import LogRecord, LogLevel, AntstasiFunction, GameMap, LogFile, Mod, LogFileAndModJoin
from playhouse.shortcuts import model_to_dict
from gidapptools import get_logger
from playhouse.signals import post_save
from antistasi_logbook.parsing.foreign_key_cache import ForeignKeyCache
from antistasi_logbook.parsing.parsing_context import LogParsingContext
import attr
if TYPE_CHECKING:
    from antistasi_logbook.parsing.parser import SimpleRegexKeeper, RecordClassManager, RecordClass
    from gidapptools.gid_config.interface import GidIniConfig
    from antistasi_logbook.storage.database import GidSqliteApswDatabase
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


class RecordStorage(Queue):

    def __init__(self, maxsize: int = 0) -> None:
        super().__init__(maxsize=maxsize)
        self.mutex = RLock()

    def dump(self) -> list:
        with self.mutex:
            if self.empty() is False:
                _out = list(self.queue)
                self.queue.clear()
                self.unfinished_tasks -= (len(_out) - 1)
                self.task_done()
                return _out


@attr.s(auto_detect=True, auto_attribs=True, slots=True, weakref_slot=True, frozen=True)
class ManyRecordsInsertResult:
    max_line_number: int = attr.ib()
    max_recorded_at: datetime = attr.ib()
    amount: int = attr.ib()
    context: LogParsingContext = attr.ib()


class RecordInserter:
    insert_phrase = """INSERT INTO "LogRecord" ("start", "end", "message", "recorded_at", "called_by", "is_antistasi_record", "logged_from", "log_file", "log_level", "record_class", "marked") VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"""

    thread_prefix: str = "inserting_thread"

    def __init__(self, config: "GidIniConfig", database: "GidSqliteApswDatabase", thread_pool_class: type["ThreadPoolExecutor"] = None) -> None:
        self.config = config
        self.database = database

        self.thread_pool = ThreadPoolExecutor(self.max_threads, thread_name_prefix=self.thread_prefix) if thread_pool_class is None else thread_pool_class(self.max_threads, thread_name_prefix=self.thread_prefix)
        self.write_lock = Lock()

    @property
    def max_threads(self) -> int:
        return self.config.get("updating", "max_inserting_threads", default=5)

    @profile
    def _insert_func(self, records: Iterable["RawRecord"], context: "LogParsingContext") -> ManyRecordsInsertResult:

        # LogRecord.insert_many(i.to_log_record_dict(log_file=context._log_file) for i in records).execute()
        params = (i.to_sql_params(log_file=context._log_file) for i in records)
        with self.write_lock:
            with self.database:
                cur = self.database.cursor(True)

                cur.executemany(self.insert_phrase, params)

        # for record in records:
        #     params = record.to_sql_params(log_file=context._log_file)
        #     self.database.execute_sql(self.insert_phrase, params=params)

        result = ManyRecordsInsertResult(max_line_number=max(item.end for item in records), max_recorded_at=max(item.recorded_at for item in records), amount=len(records), context=context)
        return result

    def insert(self, records: Iterable["RawRecord"], context: "LogParsingContext") -> Future:
        def _callback(_context: "LogParsingContext"):

            def _inner(future: "Future"):
                _context._future_callback(future.result())
            return _inner
        future = self.thread_pool.submit(self._insert_func, records=records, context=context)
        future.add_done_callback(_callback(_context=context))
        return future

    @profile
    def _execute_insert_mods(self, mod_items: Iterable[Mod], log_file: LogFile) -> None:
        mod_data = [mod_item.as_dict() for mod_item in mod_items]
        q_1 = Mod.insert_many(mod_data).on_conflict_ignore()
        with self.write_lock:
            with self.database:

                q_1.execute()

        refreshed_mods_ids = (Mod.get(**mod_item.as_dict()) for mod_item in mod_items)
        q_2 = LogFileAndModJoin.insert_many({"log_file": log_file.id, "mod": refreshed_mod_id} for refreshed_mod_id in refreshed_mods_ids).on_conflict_ignore()

        with self.write_lock:
            with self.database:

                q_2.execute()

    def insert_mods(self, mod_items: Iterable[Mod], log_file: LogFile) -> Future:
        return self.thread_pool.submit(self._execute_insert_mods, mod_items=mod_items, log_file=log_file)

    @profile
    def _execute_update_log_file_from_dict(self, log_file: LogFile, in_dict: dict):
        item = update_model_from_dict(log_file, in_dict)
        with self.write_lock:
            with self.database:

                item.save()

    def update_log_file_from_dict(self, log_file: LogFile, in_dict: dict) -> Future:
        return self.thread_pool.submit(self._execute_update_log_file_from_dict, log_file=log_file, in_dict=in_dict)

    def _execute_insert_game_map(self, game_map: "GameMap"):
        with self.write_lock:
            with self.database:
                game_map.save()

    def insert_game_map(self, game_map: "GameMap") -> Future:
        return self.thread_pool.submit(self._execute_insert_game_map, game_map=game_map)

    def __call__(self, records: Iterable["RawRecord"], context: "LogParsingContext") -> Future:
        return self.insert(records=records, context=context)

    def shutdown(self) -> None:
        self.thread_pool.shutdown(wait=True, cancel_futures=False)


class RecordProcessor:
    __slots__ = ("regex_keeper", "record_class_manager", "foreign_key_cache")

    def __init__(self, regex_keeper: "SimpleRegexKeeper", foreign_key_cache: "ForeignKeyCache", record_class_manager: "RecordClassManager") -> None:
        self.regex_keeper = regex_keeper
        self.record_class_manager = record_class_manager
        self.foreign_key_cache = foreign_key_cache

    @staticmethod
    def clean_antistasi_function_name(in_name: str) -> str:
        return in_name.strip().removeprefix("A3A_fnc_").removeprefix("fn_").removesuffix('.sqf')

    @profile
    def _process_generic_record(self, raw_record: "RawRecord") -> "RawRecord":
        match = self.regex_keeper.generic_record.match(raw_record.content.strip())
        if not match:
            return None

        _out = {"message": match.group("message").lstrip()}

        _out["local_recorded_at"] = datetime(year=int(match.group("year")),
                                             month=int(match.group("month")),
                                             day=int(match.group("day")),
                                             hour=int(match.group("hour")),
                                             minute=int(match.group("minute")),
                                             second=int(match.group("second")))
        if "error in expression" in raw_record.content.casefold():
            _out['log_level'] = "ERROR"
        raw_record.parsed_data = _out

        return raw_record

    @profile
    def _process_antistasi_record(self, raw_record: "RawRecord") -> "RawRecord":
        datetime_part, antistasi_indicator_part, log_level_part, file_part, rest = raw_record.content.split('|', maxsplit=4)

        match = self.regex_keeper.full_datetime.match(datetime_part)
        if not match:

            return None

        _out = {"recorded_at": datetime(tzinfo=UTC,
                                        year=int(match.group("year")),
                                        month=int(match.group("month")),
                                        day=int(match.group("day")),
                                        hour=int(match.group("hour")),
                                        minute=int(match.group("minute")),
                                        second=int(match.group("second")),
                                        microsecond=int(match.group("microsecond") + "000")),
                "log_level": log_level_part.strip().upper(),
                "logged_from": self.clean_antistasi_function_name(file_part.strip().removeprefix("File:"))}

        if called_by_match := self.regex_keeper.called_by.match(rest):
            _rest, called_by, _other_rest = called_by_match.groups()
            _out["called_by"] = self.clean_antistasi_function_name(called_by)
            _out["message"] = (_rest + _other_rest).lstrip()
        else:
            _out["message"] = rest.lstrip()
        raw_record.parsed_data = _out
        if raw_record.parsed_data.get('logged_from') is None:
            log.info(_out)
        return raw_record

    @profile
    def _determine_record_class(self, raw_record: "RawRecord") -> "RecordClass":
        record_class = self.record_class_manager.determine_record_class(raw_record)
        return record_class

    @profile
    def _convert_raw_record_foreign_keys(self, parsed_data: Optional[dict[str, Any]], utc_offset: tzoffset) -> Optional[dict[str, Any]]:

        def _get_or_create_antistasi_file(raw_name: str) -> AntstasiFunction:
            try:
                return self.foreign_key_cache.all_antistasi_file_objects[raw_name]
            except KeyError:
                AntstasiFunction.insert(name=raw_name).on_conflict_ignore().execute()
                return AntstasiFunction.get(name=raw_name)

        if parsed_data is None:
            return parsed_data

        if parsed_data.get("log_level") is not None:
            parsed_data["log_level"] = self.foreign_key_cache.all_log_levels[parsed_data["log_level"]]
        else:
            parsed_data["log_level"] = self.foreign_key_cache.all_log_levels["NO_LEVEL"]

        if parsed_data.get("logged_from"):
            parsed_data["logged_from"] = _get_or_create_antistasi_file(parsed_data["logged_from"])

        if parsed_data.get("called_by"):
            parsed_data["called_by"] = _get_or_create_antistasi_file(parsed_data["called_by"])

        if parsed_data.get("local_recorded_at"):
            local_recorded_at = parsed_data.pop("local_recorded_at")
            parsed_data["recorded_at"] = local_recorded_at.replace(tzinfo=utc_offset).astimezone(UTC)

        return parsed_data

    @profile
    def __call__(self, raw_record: "RawRecord", utc_offset: timezone) -> "RawRecord":

        if raw_record.is_antistasi_record is True:
            raw_record = self._process_antistasi_record(raw_record)
        else:
            raw_record = self._process_generic_record(raw_record)
        if raw_record is None:
            return
        record_class = self._determine_record_class(raw_record)
        raw_record.record_class = record_class
        raw_record.parsed_data = self._convert_raw_record_foreign_keys(parsed_data=raw_record.parsed_data, utc_offset=utc_offset)

        return raw_record

        # region[Main_Exec]
if __name__ == '__main__':
    pass

# endregion[Main_Exec]
