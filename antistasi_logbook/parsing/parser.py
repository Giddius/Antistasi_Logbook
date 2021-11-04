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
from antistasi_logbook.regex.regex_keeper import RegexKeeper
from gidapptools.general_helper.timing import time_func, time_execution
from antistasi_logbook.parsing.parsing_context import ParsingContext, RecordLine
from antistasi_logbook.utilities.misc import Version, ModItem
from dateutil.tz import UTC
from gidapptools.general_helper.timing import time_func
from gidapptools.general_helper.enums import MiscEnum
from rich.console import Console as RichConsole
from antistasi_logbook.parsing.record_class_manager import RecordClassManager
from antistasi_logbook.storage.models.models import LogFile, RecordClass, LogRecord, LogLevel, PunishmentAction, AntstasiFunction
from antistasi_logbook.records.enums import PunishmentActionEnum
from dateutil.tz import UTC
import peewee
from playhouse.signals import Model, post_save
from antistasi_logbook.utilities.locks import DB_LOCK
from threading import RLock
if TYPE_CHECKING:

    from antistasi_logbook.records.abstract_record import AbstractRecord
    from antistasi_logbook.storage.database import GidSQLiteDatabase
# endregion[Imports]

# region [TODO]


# endregion [TODO]

# region [Logging]


# endregion[Logging]

# region [Constants]
CONSOLE = RichConsole(soft_wrap=True)


def dprint(*args, **kwargs):
    CONSOLE.print(*args, **kwargs)
    CONSOLE.rule()


print = dprint


class FakeLogger:
    def __init__(self) -> None:
        self.debug = dprint
        self.info = dprint
        self.warning = dprint
        self.error = dprint
        self.critical = dprint


THIS_FILE_DIR = Path(__file__).parent.absolute()
log = FakeLogger()
# endregion[Constants]


class MetaFinder:

    game_map_regex = re.compile(r"\sMission world\:\s*(?P<game_map>.*)")
    game_file_regex = re.compile(r"\s+Mission file\:\s*(?P<game_file>.*)")
    full_datetime_regex = re.compile(r"""(?P<local_year>\d{4})
                                         [^\d]
                                         (?P<local_month>[01]?\d)
                                         [^\d]
                                         (?P<local_day>[0-3]?\d)
                                         \,\s+
                                         (?P<local_hour>[0-2\s]?\d)
                                         [^\d]
                                         (?P<local_minute>[0-6]\d)
                                         [^\d]
                                         (?P<local_second>[0-6]\d)
                                         \s?
                                         (?P<year>\d{4})
                                         [^\d]
                                         (?P<month>[01]?\d)
                                         [^\d]
                                         (?P<day>[0-3]?\d)
                                         [^\d]
                                         (?P<hour>[0-2\s]?\d)
                                         [^\d]
                                         (?P<minute>[0-6]\d)
                                         [^\d]
                                         (?P<second>[0-6]\d)
                                         [^\d]
                                         (?P<microsecond>\d+)""", re.VERBOSE)
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
        self.game_map: str = MiscEnum.NOT_FOUND if not context.log_file.game_map else MiscEnum.DEFAULT
        self.full_datetime: datetime = MiscEnum.NOT_FOUND if not context.log_file.utc_offset else MiscEnum.DEFAULT
        self.version: Version = MiscEnum.NOT_FOUND if not context.log_file.version else MiscEnum.DEFAULT
        self.mods: list[ModItem] = MiscEnum.NOT_FOUND if not context.log_file.get_mods() else MiscEnum.DEFAULT

    def all_found(self) -> bool:
        return all(i is not MiscEnum.NOT_FOUND for i in [self.game_map, self.full_datetime, self.version])

    def _resolve_full_datetime(self, text: str) -> None:
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
                log.debug(f"incomplete version from line: {match.group('game_file')!r}")
                self.version = None

    def _resolve_game_map(self, text: str) -> Optional[str]:
        if match := self.game_map_regex.search(text):
            self.game_map = match.group('game_map')

    def _resolve_mods(self, text: str) -> Optional[list[ModItem]]:
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
        if self.game_map is MiscEnum.NOT_FOUND:
            self.game_map = None

        if self.version is MiscEnum.NOT_FOUND:
            self.version = None

        if self.full_datetime is MiscEnum.NOT_FOUND:
            self.full_datetime = None

        if self.mods is MiscEnum.NOT_FOUND:
            self.mods = None


record_parsing_error_lock = RLock()
record_parsing_error_file = Path.cwd().with_name('record_parsing_errors.txt')
record_parsing_error_file.parent.mkdir(exist_ok=True, parents=True)
record_parsing_error_file.unlink(missing_ok=True)
record_parsing_error_file.touch(exist_ok=True)


def to_record_parsing_error_file(raw_record: "RawRecord", problem: str) -> None:
    def _make_error_entry(_raw_record: "RawRecord", _problem: str) -> str:
        sep = '-' * 50
        sep_2 = '+' * 25
        parts = []
        parts.append(sep)
        parts.append(f"is_antistasi= {_raw_record.is_antistasi_record}")
        parts.append(f"file= {_raw_record.log_file.name!r}")
        parts.append(f"server= {_raw_record.log_file.server.name!r}")
        parts.append(sep_2)
        parts.append(_raw_record.content)
        parts.append(sep_2)
        parts.append(f"PROBLEM: {_problem!r}")
        parts.append(sep)
        parts.append('\n')
        return '\n'.join(parts)
    with record_parsing_error_lock:
        with record_parsing_error_file.open("a", encoding='utf-8', errors='ignore') as f:
            f.write(_make_error_entry(raw_record, problem))


class RawRecord:
    antistasi_file_model_lock = RLock()
    _all_log_levels: tuple[LogLevel] = None
    _all_punishment_actions: tuple[PunishmentAction] = None
    _all_antistasi_file_objects: dict[str, AntstasiFunction] = None
    __slots__ = ("lines", "is_antistasi_record", "start", "end", "content", "parsed_data", "record_class", "log_file")

    def __init__(self, lines: Iterable["RecordLine"], log_file: "LogFile") -> None:
        self.lines = tuple(lines)
        self.log_file = log_file
        self.is_antistasi_record: bool = any("| antistasi |" in line.content.casefold() for line in lines)
        self.start: int = min(line.start for line in self.lines)
        self.end: int = max(line.start for line in self.lines)
        self.content: str = ' '.join(line.content.lstrip(" >>>").rstrip() for line in self.lines if line.content)
        self.parsed_data: dict[str, Any] = None
        self.record_class: "RecordClass" = None

        try:
            post_save.connect(self.on_save_handler, sender=AntstasiFunction)
        except ValueError:
            pass

    def on_save_handler(self, sender, instance, created):
        if created:
            self._all_antistasi_file_objects = None
            print(('-' * 25) + f" reseted '_all_antistasi_file_objects', because {instance.name!r} of {sender!r} was {created!r}")

    @property
    def all_antistasi_file_objects(self) -> dict[str, AntstasiFunction]:
        if self.__class__._all_antistasi_file_objects is None:
            with self.__class__.antistasi_file_model_lock:
                self.__class__._all_antistasi_file_objects = {item.name: item for item in AntstasiFunction.select()}
        return self.__class__._all_antistasi_file_objects

    @property
    def unformatted_content(self) -> str:
        return '\n'.join(line.content for line in self.lines)

    @property
    def all_log_levels(self) -> tuple[LogLevel]:
        if self.__class__._all_log_levels is None:
            self.__class__._all_log_levels = tuple(LogLevel.select())
        return self.__class__._all_log_levels

    @property
    def all_punishment_actions(self) -> tuple[PunishmentAction]:
        if self.__class__._all_punishment_actions is None:
            self.__class__._all_punishment_actions = tuple(PunishmentAction.select())
        return self.__class__._all_punishment_actions

    def _parse_generic_entry(self, regex_keeper: RegexKeeper) -> dict[str, Any]:
        match = regex_keeper.generic_entry.search(self.content)
        if not match:
            to_record_parsing_error_file(self, "no generic entry match")
            return None
        recorded_at_kwargs = {k.removeprefix('local_'): int(v) for k, v in match.groupdict().items() if k.startswith('local_')} | {'tzinfo': self.log_file.utc_offset}
        recorded_at = datetime(**recorded_at_kwargs).astimezone(UTC)
        message = match.group("message")
        _out = {"message": message, "recorded_at": recorded_at}
        if "error in expression" in self.content.casefold():
            _out['log_level'] = [l for l in self.all_log_levels if l.name == "ERROR"][0]
        return _out

    def _parse_antistasi_entry(self, regex_keeper: RegexKeeper) -> dict[str, Any]:
        datetime_part, antistasi_indicator_part, log_level_part, file_part, *other_parts = self.content.split('|')
        try:
            recorded_at_kwargs = {k.removeprefix("utc_"): int(v) for k, v in regex_keeper.full_datetime.match(datetime_part).groupdict().items() if k.startswith("utc_")} | {"tzinfo": UTC}
        except AttributeError:
            to_record_parsing_error_file(self, f"datetime_part did not match, datetime_part={datetime_part}")

            return
        _out = {}
        _out["recorded_at"] = datetime(**recorded_at_kwargs)
        _out["log_level"] = [l for l in self.all_log_levels if l.name == log_level_part.strip().upper()][0]
        logged_from_item_name = AntstasiFunction.clean_name(file_part.strip().removeprefix("File:"))
        # logged_from_item = AntstasiFunction.create_or_get(name=logged_from_item_name)

        logged_from_item = self.all_antistasi_file_objects.get(logged_from_item_name, None)
        if logged_from_item is None:
            print(f"file {logged_from_item_name!r} not found")
            with self.antistasi_file_model_lock:
                logged_from_item = AntstasiFunction(name=logged_from_item_name)
                logged_from_item.save()

        # with self.antistasi_file_model_lock:

        #     logged_from_item = AntstasiFunction.get_or_none(name=logged_from_item_name)
        #     if logged_from_item is None:
        #         logged_from_item = AntstasiFunction(name=logged_from_item_name)
        #         logged_from_item.save()
        _out["logged_from"] = logged_from_item
        to_pop = []
        for idx, part in enumerate(other_parts):
            part = part.strip()

            if part.startswith('Called By:'):
                called_by_item_name = AntstasiFunction.clean_name(part.strip().removeprefix("Called By:"))
                called_by_item = self.all_antistasi_file_objects.get(called_by_item_name, None)
                if called_by_item is None:
                    print(f"file {called_by_item_name!r} not found")
                    with self.antistasi_file_model_lock:

                        called_by_item = AntstasiFunction(name=called_by_item)
                        called_by_item.save()
                _out["called_by"] = called_by_item
                to_pop.append(idx)
            elif part.startswith("Client:"):
                _out['client'] = part.removeprefix("Client:").strip()
                to_pop.append(idx)
            elif part in PunishmentActionEnum.__members__:
                _out["punishment_action"] = [p for p in self.all_punishment_actions if p.name == part.strip().upper()][0]
                to_pop.append(idx)

        rest = [p for idx, p in enumerate(other_parts) if idx not in to_pop]
        _out["message"] = '|'.join(rest).strip()

        return _out

    def parse(self, regex_keeper: RegexKeeper) -> None:
        if self.is_antistasi_record is False:
            self.parsed_data = self._parse_generic_entry(regex_keeper=regex_keeper)
        else:
            self.parsed_data = self._parse_antistasi_entry(regex_keeper=regex_keeper)

    def determine_record_class(self, record_class_manager: RecordClassManager) -> None:
        if self.parsed_data is not None:
            self.record_class = record_class_manager.determine_record_class(self)

    def as_log_record(self) -> "LogRecord":
        if self.parsed_data is not None:
            return LogRecord(start=self.start, end=self.end, is_antistasi_record=self.is_antistasi_record, log_file=self.log_file, record_class=self.record_class, **self.parsed_data)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(start={self.start!r}, end={self.end!r}, content={self.content!r}, is_antistasi_record={self.is_antistasi_record!r}, lines={self.lines!r})"


class RecordProcessor:
    record_class_registry: dict[str, type["AbstractRecord"]]

    def __init__(self) -> None:
        pass


class Parser:
    log_file_data_scan_chunk_initial = 104997
    log_file_data_scan_chunk_increase = 27239

    def __init__(self, database: "GidSQLiteDatabase", regex_keeper: "RegexKeeper" = None) -> None:
        self.database = database
        self.regex_keeper = RegexKeeper() if regex_keeper is None else regex_keeper

    def _process_record(self, context: "ParsingContext") -> None:
        raw_record = RawRecord(context.line_cache.dump(), log_file=context.log_file)
        raw_record.parse(self.regex_keeper)
        raw_record.determine_record_class(self.database.record_class_manager)
        context.add_record(raw_record.as_log_record())

    def _get_log_file_meta_data(self, context: ParsingContext) -> bool:
        with context.log_file.open(cleanup=False) as file:

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
        if finder.full_datetime is None:
            context.set_unparsable()

            return False

        context.set_found_meta_data(finder=finder)
        return True

    def _parse_header_text(self, context: ParsingContext) -> None:
        while self.regex_keeper.only_time.match(context.current_line.content) is None:
            context.line_cache.append(context.current_line)
            context.advance_line()
        context.set_header_text()

    def _parse_startup_entries(self, context: ParsingContext) -> None:
        while not self.regex_keeper.local_datetime.match(context.current_line.content):
            context.line_cache.append(context.current_line)
            context.advance_line()
        context.set_startup_text()

    def parse_entries(self, context: ParsingContext) -> None:
        while context.current_line is not ...:
            if self.regex_keeper.local_datetime.match(context.current_line.content):
                if match := self.regex_keeper.continued_record.match(context.current_line.content):
                    context.line_cache.append(RecordLine(content=match.group('content'), start=context.current_line.start))
                    context.advance_line()
                    continue

                if context.line_cache.is_empty() is False:
                    self._process_record(context=context)

            context.line_cache.append(context.current_line)
            context.advance_line()

    def __call__(self, log_file: "LogFile") -> Any:
        with ParsingContext(log_file=log_file, database=self.database, auto_download=True) as context:
            log.info("getting meta_data")
            if self._get_log_file_meta_data(context=context) is False or context.unparsable is True:
                return
            if context.log_file.header_text is None:
                log.info("parsing header text of", log_file)
                self._parse_header_text(context)
            if context.log_file.startup_text is None:
                log.info("parsing startup entries of", log_file)
                self._parse_startup_entries(context)
            log.info("parsing entries of", log_file)
            self.parse_entries(context)


# region[Main_Exec]

if __name__ == '__main__':
    pass


# endregion[Main_Exec]
