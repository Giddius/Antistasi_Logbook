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

from dateutil.tz import UTC, tzoffset
from antistasi_logbook.parsing.raw_record import RawRecord
from antistasi_logbook.storage.models.models import LogRecord, LogLevel, AntstasiFunction, GameMap
from playhouse.shortcuts import model_to_dict
from gidapptools.gid_logger.fake_logger import fake_logger
from playhouse.signals import post_save
if TYPE_CHECKING:
    from antistasi_logbook.parsing.parser import SimpleRegexKeeper, RecordClassManager, RecordClass
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


class BlockingEvent(Event):

    def __init__(self) -> None:
        super().__init__()
        self.set()

    def __enter__(self) -> None:
        self.clear()

    def __exit__(self, exception_type: type = None, exception_value: BaseException = None, traceback: Any = None) -> None:
        self.set()


class ForeignKeyCache:
    log_levels_blocker = BlockingEvent()
    game_map_model_blocker = BlockingEvent()
    antistasi_file_model_blocker = BlockingEvent()
    _all_log_levels: dict[str, LogLevel] = None
    _all_antistasi_file_objects: dict[str, AntstasiFunction] = None
    _all_game_map_objects: dict[str, GameMap] = None

    def __init__(self) -> None:
        self.update_map = {AntstasiFunction: (self.antistasi_file_model_blocker, "_all_antistasi_file_objects"),
                           GameMap: (self.game_map_model_blocker, "_all_game_map_objects"),
                           LogLevel: (self.log_levels_blocker, "_all_log_levels")}
        self._register_signals()

    def _register_signals(self) -> None:
        for model_class in self.update_map:
            try:
                post_save.connect(self.on_save_handler, sender=model_class)
            except ValueError:
                continue

    @property
    def all_log_levels(self) -> dict[str, LogLevel]:

        if self.__class__._all_log_levels is None:
            self.log_levels_blocker.wait()
            self.__class__._all_log_levels = {item.name: item for item in LogLevel.select()}

        return self.__class__._all_log_levels

    @property
    def all_antistasi_file_objects(self) -> dict[str, AntstasiFunction]:

        if self.__class__._all_antistasi_file_objects is None:
            self.antistasi_file_model_blocker.wait()
            self.__class__._all_antistasi_file_objects = {item.name: item for item in AntstasiFunction.select()}

        return self.__class__._all_antistasi_file_objects

    @property
    def all_game_map_objects(self) -> dict[str, GameMap]:

        if self.__class__._all_game_map_objects is None:
            self.game_map_model_blocker.wait()
            self.__class__._all_game_map_objects = {item.name: item for item in GameMap.select()}

        return self.__class__._all_game_map_objects

    def on_save_handler(self, sender, instance, created):
        if created:
            event, class_attr_name = self.update_map.get(sender, (None, None))
            if event is None:
                return
            with event:
                setattr(self.__class__, class_attr_name, None)
            log.warning(('-' * 25) + f" reseted '{class_attr_name}', because {model_to_dict(instance)} of {sender.__name__!r} was created:{created!r}")


class RecordStorage(Queue):

    def __init__(self, maxsize: int = 0) -> None:
        super().__init__(maxsize=maxsize)

    def dump(self) -> list:
        with self.mutex:
            _out = list(self.queue)
            self.queue.clear()
            return _out


class RecordInserter(Thread):
    _bulk_create_batch_size: int = None

    def __init__(self, foreign_key_cache: ForeignKeyCache) -> None:
        self.foreign_key_cache = foreign_key_cache
        self.stop_event = Event()
        self.task_queue: Queue = Queue()
        self.thread_pool = ThreadPoolExecutor(10)
        self.record_storage = RecordStorage(maxsize=self._log_record_batch_size)
        self.futures: list[Future] = []

        super().__init__(name=f"{self.__class__.__name__}_thread")

    @property
    def _log_record_batch_size(self) -> int:
        if self._bulk_create_batch_size is None:
            self._bulk_create_batch_size = (32766 // len(LogRecord._meta.columns))
        return self._bulk_create_batch_size

    @profile
    def _convert_raw_record_foreign_keys(self, parsed_data: Optional[dict[str, Any]], utc_offset: tzoffset) -> Optional[dict[str, Any]]:

        def _get_or_create_antistasi_file(raw_name: str) -> AntstasiFunction:
            item = self.foreign_key_cache.all_antistasi_file_objects.get(raw_name)
            if item is None:
                xxx = AntstasiFunction.insert(name=raw_name).on_conflict_ignore().execute()
                log.critical(f"{xxx=}")
                item = AntstasiFunction.get(name=raw_name)

            return item

        if parsed_data is None:
            return parsed_data

        new_parsed_data = parsed_data.copy()

        if parsed_data.get("log_level") is not None:
            new_parsed_data["log_level"] = self.foreign_key_cache.all_log_levels.get(parsed_data.get("log_level"))

        if parsed_data.get("logged_from"):
            new_parsed_data["logged_from"] = _get_or_create_antistasi_file(parsed_data.get("logged_from"))
            if new_parsed_data.get("logged_from") is None:
                log.critical(parsed_data)
        if parsed_data.get("called_by"):
            new_parsed_data["called_by"] = _get_or_create_antistasi_file(parsed_data.get("called_by"))

        if parsed_data.get("local_recorded_at", None):
            new_parsed_data["recorded_at"] = parsed_data.pop("local_recorded_at").replace(tzinfo=utc_offset).astimezone(UTC)
            new_parsed_data.pop("local_recorded_at", None)
        return new_parsed_data

    @profile
    def _raw_record_to_log_record(self, raw_record: "RawRecord") -> dict[str, Any]:
        converted_data = self._convert_raw_record_foreign_keys(raw_record.parsed_data, utc_offset=raw_record.log_file.utc_offset)
        if converted_data is not None:
            logged_from = converted_data.pop("logged_from", None)
            return dict(start=raw_record.start, end=raw_record.end, is_antistasi_record=raw_record.is_antistasi_record, log_file=raw_record.log_file, record_class=raw_record.record_class, logged_from=logged_from, ** converted_data)

    @profile
    def _mass_insert_records(self, records: list[RawRecord]) -> None:

        # different_log_files = set(i.log_file for i in records)
        # for log_file in different_log_files:
        #     last_parsed_line = max(i.end for i in records if i.log_file == log_file)
        #     log_file.last_parsed_line_number = last_parsed_line
        #     log_file.save()

        res = LogRecord.insert_many((i for i in (self._raw_record_to_log_record(x) for x in records) if i is not None)).execute()
        return len(records), res

    def clear_record_storage(self) -> None:
        if not self.record_storage.empty():
            records_left = self.record_storage.dump()
            if records_left:
                self.task_queue.put(records_left)

    def add(self, item: Callable) -> None:

        if isinstance(item, RawRecord):
            try:
                self.record_storage.put(item, block=False)
            except Full:
                self.task_queue.put(self.record_storage.dump())
                self.record_storage.put(item)
        else:
            self.task_queue.put(item)

    def process_queue(self) -> None:
        def _callback(_future: Future):
            self.task_queue.task_done()

        try:
            item = self.task_queue.get(timeout=0.5)
        except Empty:
            return
        if isinstance(item, list) and item != [] and isinstance(item[0], RawRecord):
            future = self.thread_pool.submit(self._mass_insert_records, item)
        else:
            future = self.thread_pool.submit(item)
        self.futures.append(future)
        future.add_done_callback(_callback)

    def run(self) -> None:
        while self.stop_event.is_set() is False:
            self.process_queue()
        while self.task_queue.unfinished_tasks > 0:
            self.process_queue()

    def wait(self) -> None:
        self.clear_record_storage()

        self.task_queue.join()

        # wait(self.futures, timeout=None, return_when=ALL_COMPLETED)

    def shutdown(self) -> None:

        self.stop_event.set()
        self.wait()
        self.thread_pool.shutdown(wait=True, cancel_futures=False)
        self.join()


class RecordProcessor:

    def __init__(self, regex_keeper: "SimpleRegexKeeper", record_class_manager: "RecordClassManager") -> None:
        self.regex_keeper = regex_keeper
        self.record_class_manager = record_class_manager

    @staticmethod
    def clean_antistasi_function_name(in_name: str) -> str:
        return in_name.strip().removeprefix("A3A_fnc_").removeprefix("fn_").removesuffix('.sqf')

    @profile
    def _process_generic_record(self, raw_record: "RawRecord") -> "RawRecord":
        match = self.regex_keeper.generic_record.match(raw_record.content.strip())
        if not match:
            return None

        _out = {"message": match.group("message")}

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
    def process(self, raw_record: "RawRecord") -> "RawRecord":

        if raw_record.is_antistasi_record is True:
            raw_record = self._process_antistasi_record(raw_record)
        else:
            raw_record = self._process_generic_record(raw_record)
        if raw_record is None:
            return
        record_class = self._determine_record_class(raw_record)
        raw_record.record_class = record_class

        return raw_record


class RecordProcessorWorker(Thread):

    def __init__(self, record_processor: RecordProcessor, inserter: RecordInserter) -> None:
        self.record_processor = record_processor
        self.inserter = inserter
        self.raw_records_queue: Queue["RawRecord"] = Queue()
        self.shutdown_event = Event()
        super().__init__(name=f"{self.__class__.__name__}_thread")

    def add(self, raw_record: "RawRecord") -> None:
        self.raw_records_queue.put(raw_record)

    def run(self) -> None:
        while self.shutdown_event.is_set() is False:
            try:
                raw_record = self.raw_records_queue.get(timeout=0.5)
            except Empty:
                continue

            processed_record = self.record_processor.process(raw_record)
            if processed_record is not None:
                self.inserter.add(processed_record)
            self.raw_records_queue.task_done()
        while self.raw_records_queue.unfinished_tasks > 0:
            try:
                raw_record = self.raw_records_queue.get(timeout=0.5)
            except Empty:
                continue

            processed_record = self.record_processor.process(raw_record)
            if processed_record is not None:
                self.inserter.add(processed_record)
            self.raw_records_queue.task_done()

    def shutdown(self) -> None:
        self.shutdown_event.set()
        self.join()
        self.inserter.shutdown()

        # region[Main_Exec]


if __name__ == '__main__':
    pass

# endregion[Main_Exec]
