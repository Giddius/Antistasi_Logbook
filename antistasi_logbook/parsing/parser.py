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
from threading import RLock, Semaphore
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


class RawRecord:

    __slots__ = ("lines", "_is_antistasi_record", "start", "end", "_content", "parsed_data", "record_class")

    def __init__(self, lines: Iterable["RecordLine"]) -> None:
        self.lines = tuple(lines)
        self._content: str = None
        self._is_antistasi_record: bool = None
        self.start: int = self.lines[0].start
        self.end: int = self.lines[-1].start
        self.parsed_data: dict[str, Any] = None
        self.record_class: "RecordClass" = None

    @property
    def content(self) -> str:
        if self._content is None:
            self._content = ' '.join(line.content.lstrip(" >>>").rstrip() for line in self.lines if line.content)
        return self._content

    @property
    def is_antistasi_record(self) -> bool:
        if self._is_antistasi_record is None:
            self._is_antistasi_record = "| antistasi |" in self.content.casefold()
        return self._is_antistasi_record

    @property
    def unformatted_content(self) -> str:
        return '\n'.join(line.content for line in self.lines)

    def _parse_generic_entry(self, regex_keeper: SimpleRegexKeeper) -> dict[str, Any]:
        match = regex_keeper.generic_record.match(self.content.strip())
        if not match:
            to_record_parsing_error_file(self, "no generic entry match")
            return None

        _out = {"message": match.group("message")}

        _out["local_recorded_at"] = datetime(year=int(match.group("year")),
                                             month=int(match.group("month")),
                                             day=int(match.group("day")),
                                             hour=int(match.group("hour")),
                                             minute=int(match.group("minute")),
                                             second=int(match.group("second")))
        if "error in expression" in self.content.casefold():
            _out['log_level'] = "ERROR"
        return _out

    def _parse_antistasi_entry(self, regex_keeper: SimpleRegexKeeper) -> dict[str, Any]:
        datetime_part, antistasi_indicator_part, log_level_part, file_part, rest = self.content.split('|', maxsplit=4)

        match = regex_keeper.full_datetime.match(datetime_part)
        if not match:
            to_record_parsing_error_file(self, f"Unable to match full datetime, {datetime_part=!r}")
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
                "logged_from": clean_antistasi_function_name(file_part.strip().removeprefix("File:"))}

        if called_by_match := regex_keeper.called_by.match(rest):
            _rest, called_by, _other_rest = called_by_match.groups()
            _out["called_by"] = clean_antistasi_function_name(called_by)
            _out["message"] = (_rest + _other_rest).lstrip()
        else:
            _out["message"] = rest.lstrip()

        return _out

    def parse(self, regex_keeper: SimpleRegexKeeper) -> None:
        if self.is_antistasi_record is False:
            self.parsed_data = self._parse_generic_entry(regex_keeper=regex_keeper)
        else:
            self.parsed_data = self._parse_antistasi_entry(regex_keeper=regex_keeper)

    def determine_record_class(self, record_class_manager: RecordClassManager) -> None:
        if self.parsed_data is not None:
            self.record_class = record_class_manager.determine_record_class(self)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(start={self.start!r}, end={self.end!r}, content={self.content!r}, is_antistasi_record={self.is_antistasi_record!r}, lines={self.lines!r})"

    def __eq__(self, o: object) -> bool:
        if isinstance(o, self.__class__):
            return self.lines == o.lines and self.content == o.content and self.is_antistasi_record == o.is_antistasi_record and self.start == o.start and self.end == o.end


class RecordProcessor:
    record_class_registry: dict[str, type["AbstractRecord"]]

    def __init__(self) -> None:
        pass


class Parser:
    log_file_data_scan_chunk_increase = 27239
    log_file_data_scan_chunk_initial = (104997 // 2)

    __slots__ = ("database", "regex_keeper")

    def __init__(self, database: "GidSQLiteDatabase", regex_keeper: "SimpleRegexKeeper" = None) -> None:
        self.database = database
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
                    yield RawRecord(context.line_cache.dump())

            context.line_cache.append(context.current_line)
            context.advance_line()
        rest_lines = context.line_cache.dump()
        if rest_lines:

            yield RawRecord(rest_lines)

    def process(self, log_file: "LogFile") -> Any:
        if UPDATE_STOP_EVENT.is_set():
            return

        with ParsingContext(log_file=log_file, database=self.database, auto_download=True, record_insert_batch_size=3000) as context:

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
                self._process_record(raw_record=raw_record, context=context)
        return True

    def close(self) -> None:
        ParsingContext.bulk_inserter.shutdown(wait=True, cancel_futures=False)
# region[Main_Exec]


if __name__ == '__main__':
    pass


# endregion[Main_Exec]
