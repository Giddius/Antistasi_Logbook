"""
WiP.

Soon.
"""

# region [Imports]

import os

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
from io import TextIOWrapper
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
from antistasi_logbook.regex.regex_keeper import SimpleRegexKeeper
from gidapptools.general_helper.timing import time_func, time_execution
from antistasi_logbook.parsing.parsing_context import ParsingContext, RecordLine
from antistasi_logbook.utilities.misc import Version, ModItem
from dateutil.tz import UTC
from gidapptools.general_helper.timing import time_func
from gidapptools.general_helper.enums import MiscEnum
from rich.console import Console as RichConsole
from antistasi_logbook.parsing.record_class_manager import RecordClassManager
from antistasi_logbook.storage.models.models import LogFile, RecordClass, LogRecord, LogLevel, AntstasiFunction
from antistasi_logbook.records.enums import PunishmentActionEnum
from dateutil.tz import UTC
from antistasi_logbook.utilities.locks import UPDATE_STOP_EVENT
import peewee
from playhouse.signals import Model, post_save
import re
from gidapptools.gid_logger.fake_logger import fake_logger
from threading import RLock, Semaphore, Event
from antistasi_logbook.parsing.raw_record import RawRecord
from antistasi_logbook.parsing.record_processor import RecordInserter, RecordProcessor, RecordProcessorWorker, RecordInserter, ForeignKeyCache
if TYPE_CHECKING:

    from antistasi_logbook.records.abstract_record import AbstractRecord
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


def clean_antistasi_function_name(in_name: str) -> str:
    return in_name.strip().removeprefix("A3A_fnc_").removeprefix("fn_").removesuffix('.sqf')


class MetaFinder:

    game_map_regex = re.compile(r"\sMission world\:\s*(?P<game_map>.*)")
    game_file_regex = re.compile(r"\s+Mission file\:\s*(?P<game_file>.*)")
    full_datetime_regex = re.compile(r"""^
                                         (?P<local_year>\d{4})
                                         /
                                         (?P<local_month>[01]\d)
                                         /
                                         (?P<local_day>[0-3]\d)
                                         \,\s+
                                         (?P<local_hour>[0-2]\d)
                                         \:
                                         (?P<local_minute>[0-6]\d)
                                         \:
                                         (?P<local_second>[0-6]\d)
                                         \s
                                         (?P<year>\d{4})
                                         \-
                                         (?P<month>[01]\d)
                                         \-
                                         (?P<day>[0-3]\d)
                                         \s
                                         (?P<hour>[0-2]\d)
                                         \:
                                         (?P<minute>[0-6]\d)
                                         \:
                                         (?P<second>[0-6]\d)
                                         \:
                                         (?P<microsecond>\d{3})
                                         (?=\s)""", re.VERBOSE | re.MULTILINE)
    mods_regex = re.compile(r"""^([0-2\s]?\d)
                                  [^\d]
                                  ([0-6]\d)
                                  [^\d]
                                  ([0-6]\d)
                                  \s?\=+\sList\sof\smods\s\=*
                                  \n
                                  (?P<mod_lines>(^([0-2\s]?\d)
                                                  [^\d]
                                                  ([0-6]\d)
                                                  [^\d]
                                                  ([0-6]\d)
                                                  \s(?!\=).*\n)
                                                  +
                                  )
                                  ^([0-2\s]?\d)
                                  [^\d]
                                  ([0-6]\d)
                                  [^\d]
                                  ([0-6]\d)
                                  \s?\=+""", re.VERBOSE | re.MULTILINE)

    mod_time_strip_regex = re.compile(r"""^([0-2\s]?\d)
                                          [^\d]
                                          ([0-6]\d)
                                          [^\d]
                                          ([0-6]\d)""", re.VERBOSE)

    __slots__ = ("game_map", "full_datetime", "version", "mods")

    def __init__(self, context: "ParsingContext") -> None:
        self.game_map: str = MiscEnum.NOT_FOUND if not context.log_file.has_game_map() else MiscEnum.DEFAULT
        self.full_datetime: tuple[datetime, datetime] = MiscEnum.NOT_FOUND if not context.log_file.utc_offset else MiscEnum.DEFAULT
        self.version: Version = MiscEnum.NOT_FOUND if not context.log_file.version else MiscEnum.DEFAULT
        self.mods: list[ModItem] = MiscEnum.NOT_FOUND if not context.log_file.has_mods() else MiscEnum.DEFAULT

    def all_found(self) -> bool:
        # takes about 0.000742 s
        return all(i is not MiscEnum.NOT_FOUND for i in [self.game_map, self.full_datetime, self.version])

    def _resolve_full_datetime(self, text: str) -> None:
        # takes about 0.378868 s
        if match := self.full_datetime_regex.search(text):
            utc_datetime_kwargs = {k: int(v) for k, v in match.groupdict().items() if not k.startswith('local_')}
            local_datetime_kwargs = {k.removeprefix('local_'): int(v) for k, v in match.groupdict().items() if k.startswith('local_')}
            self.full_datetime = (datetime(tzinfo=UTC, **utc_datetime_kwargs), datetime(tzinfo=UTC, **local_datetime_kwargs))

    def _resolve_version(self, text: str) -> Optional[Version]:
        if match := self.game_file_regex.search(text):
            raw = match.group('game_file')
            version_args = [c for c in raw if c.isnumeric()]
            if version_args:
                while len(version_args) < 3:
                    version_args.append('MISSING')
                version = Version(*version_args)
                self.version = version
            else:
                log.debug("incomplete version from line:", repr(match.group('game_file')))
                self.version = None

    def _resolve_game_map(self, text: str) -> Optional[str]:
        # takes about 0.170319 s
        if match := self.game_map_regex.search(text):
            self.game_map = match.group('game_map')

    def _resolve_mods(self, text: str) -> Optional[list[ModItem]]:
        # takes about 0.263012 s
        if match := self.mods_regex.search(text):
            mod_lines = match.group('mod_lines').splitlines()

            cleaned_mod_lines = [self.mod_time_strip_regex.sub("", line) for line in mod_lines if '|' in line and 'modDir' not in line]

            self.mods = [ModItem.from_text_line(line) for line in cleaned_mod_lines]

    def search(self, text: str) -> None:
        if self.game_map is MiscEnum.NOT_FOUND:
            self._resolve_game_map(text)

        if self.version is MiscEnum.NOT_FOUND:
            self._resolve_version(text)

        if self.full_datetime is MiscEnum.NOT_FOUND:
            self._resolve_full_datetime(text)

        if self.mods is MiscEnum.NOT_FOUND:
            self._resolve_mods(text)

    def change_missing_to_none(self) -> None:
        # takes about 0.0001006 s
        if self.game_map is MiscEnum.NOT_FOUND:
            self.game_map = None

        if self.version is MiscEnum.NOT_FOUND:
            self.version = None

        if self.full_datetime is MiscEnum.NOT_FOUND:
            self.full_datetime = None

        if self.mods is MiscEnum.NOT_FOUND:
            self.mods = None


def to_record_parsing_error_file(raw_record: "RawRecord", problem: str) -> None:
    def _make_error_entry(_raw_record: "RawRecord", _problem: str) -> str:
        sep = '-' * 50
        sep_2 = '+' * 25
        parts = []
        parts.append(sep)
        parts.append(f"is_antistasi= {_raw_record.is_antistasi_record}")
        parts.append(sep_2)
        parts.append(_raw_record.content)
        parts.append(sep_2)
        parts.append(f"PROBLEM: {_problem!r}")
        parts.append(sep)
        parts.append('\n')
        return '\n'.join(parts)

    log.error(_make_error_entry(raw_record, problem))


class Parser:
    log_file_data_scan_chunk_increase = 27239
    log_file_data_scan_chunk_initial = (104997 // 2)

    __slots__ = ("database", "regex_keeper", "record_process_worker", "foreign_key_cache")

    def __init__(self, database: "GidSQLiteDatabase", record_processor_worker: RecordProcessorWorker, foreign_key_cache: "ForeignKeyCache", regex_keeper: "SimpleRegexKeeper" = None) -> None:
        self.database = database
        self.foreign_key_cache = foreign_key_cache
        self.record_process_worker = record_processor_worker
        self.regex_keeper = SimpleRegexKeeper() if regex_keeper is None else regex_keeper

    def _process_record(self, raw_record: "RawRecord", context: "ParsingContext") -> None:
        raw_record.parse(self.regex_keeper)
        raw_record.determine_record_class(self.database.record_class_manager)
        context.add_record(raw_record)

    def _get_log_file_meta_data(self, context: ParsingContext) -> "MetaFinder":
        with context.open(cleanup=False) as file:

            text = file.read(self.log_file_data_scan_chunk_initial)
            finder = MetaFinder(context=context)

            while True:
                finder.search(text)
                if finder.all_found() is True:
                    break

                new_text = file.read(self.log_file_data_scan_chunk_increase)
                if not new_text:
                    break
                text += new_text
        finder.change_missing_to_none()

        return finder

    def _parse_header_text(self, context: ParsingContext) -> None:
        # takes about 0.726222 s
        while not self.regex_keeper.only_time.match(context.current_line.content):
            context.line_cache.append(context.current_line)
            context.advance_line()
        return context.line_cache.dump()

    def _parse_startup_entries(self, context: ParsingContext) -> None:
        # takes about 0.533279 s
        while not self.regex_keeper.local_datetime.match(context.current_line.content):
            context.line_cache.append(context.current_line)
            context.advance_line()
        return context.line_cache.dump()

    def parse_entries(self, context: ParsingContext) -> None:
        while context.current_line is not ... and not UPDATE_STOP_EVENT.is_set():
            if self.regex_keeper.local_datetime.match(context.current_line.content):
                if match := self.regex_keeper.continued_record.match(context.current_line.content):
                    context.line_cache.append(RecordLine(content=match.group('content'), start=context.current_line.start))
                    context.advance_line()
                    continue

                if context.line_cache.is_empty() is False:
                    yield RawRecord(context.line_cache.dump(), context.log_file)

            context.line_cache.append(context.current_line)
            context.advance_line()
        rest_lines = context.line_cache.dump()
        if rest_lines:

            yield RawRecord(rest_lines, context.log_file)

    def process(self, log_file: "LogFile") -> Any:
        if UPDATE_STOP_EVENT.is_set():
            return

        with ParsingContext(foreign_key_cache=self.foreign_key_cache, log_file=log_file, database=self.database, auto_download=True) as context:

            if UPDATE_STOP_EVENT.is_set():
                return
            log.info("Parsing meta-data for ", context.log_file)
            context.set_found_meta_data(self._get_log_file_meta_data(context=context))
            if context.unparsable is True:
                return

            if UPDATE_STOP_EVENT.is_set():
                return

            if context.log_file.header_text is None:

                context.set_header_text(self._parse_header_text(context))

            if UPDATE_STOP_EVENT.is_set():
                return

            if context.log_file.startup_text is None:

                context.set_startup_text(self._parse_startup_entries(context))
            log.info("Parsing entries for ", context.log_file)
            for raw_record in self.parse_entries(context):

                self.record_process_worker.add(raw_record=raw_record)
        self.record_process_worker.inserter.clear_record_storage()
        return True

    def close(self) -> None:
        self.record_process_worker.shutdown()


def get_parser(database, record_processor_class: type[RecordProcessor] = RecordProcessor, record_inserter_class: type[RecordInserter] = RecordInserter, foreign_key_cache_class: type[ForeignKeyCache] = ForeignKeyCache, regex_keeper: "SimpleRegexKeeper" = None, record_class_manager=None) -> Parser:
    if record_class_manager is None:
        record_class_manager = database.record_class_manager
    if regex_keeper is None:
        regex_keeper = SimpleRegexKeeper()
    foreign_key_cache = foreign_key_cache_class()
    record_inserter = record_inserter_class(foreign_key_cache=foreign_key_cache)
    record_inserter.start()
    record_processor = record_processor_class(regex_keeper=regex_keeper, record_class_manager=record_class_manager)
    record_processor_worker = RecordProcessorWorker(record_processor=record_processor, inserter=record_inserter)
    record_processor_worker.start()
    parser = Parser(database=database, record_processor_worker=record_processor_worker, regex_keeper=regex_keeper, foreign_key_cache=foreign_key_cache)
    import atexit
    atexit.register(parser.close)
    return parser
# region[Main_Exec]


if __name__ == '__main__':
    pass


# endregion[Main_Exec]
