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
from gidapptools.general_helper.enums import MiscEnum
from rich.console import Console as RichConsole
if TYPE_CHECKING:

    from antistasi_logbook.storage.models.models import LogFile
    from antistasi_logbook.records.abstract_record import AbstractRecord
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


class RawRecord:
    __slots__ = ("lines", "is_antistasi_record", "start", "end", "content")

    def __init__(self, lines: Iterable["RecordLine"]) -> None:
        self.lines = tuple(lines)
        self.is_antistasi_record = any("| Antistasi |" in line.content for line in lines)
        self.start = min(line.start for line in self.lines)
        self.end = max(line.start for line in self.lines)
        self.content = ' '.join(line.content.lstrip(" >>>").rstrip() for line in self.lines if line.content)

    @property
    def unformatted_content(self) -> str:
        return '\n'.join(line.content for line in self.lines)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(start={self.start!r}, end={self.end!r}, content={self.content!r}, is_antistasi_record={self.is_antistasi_entry!r}, lines={self.lines!r})"


class RecordProcessor:
    record_class_registry: dict[str, type["AbstractRecord"]]

    def __init__(self) -> None:
        pass


class Parser:
    log_file_data_scan_chunk_initial = 104997
    log_file_data_scan_chunk_increase = 27239

    def __init__(self, regex_keeper: "RegexKeeper" = None) -> None:
        self.regex_keeper = RegexKeeper() if regex_keeper is None else regex_keeper
        self.records = []

    def _process_record(self, context: "ParsingContext") -> None:
        raw_record = RawRecord(context.line_cache.dump())
        self.records.append(raw_record)

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

    @time_func()
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
        with ParsingContext(log_file=log_file, auto_download=True) as context:
            log.info("getting meta_data")
            if self._get_log_file_meta_data(context=context) is False or context.unparsable is True:
                return
            log.info("parsing header text of", log_file)
            self._parse_header_text(context)
            log.info(f"parsing startup entries of", log_file)
            self._parse_startup_entries(context)
            log.info(f"parsing entries of", log_file)
            self.parse_entries(context)

        self.records.clear()

# region[Main_Exec]


if __name__ == '__main__':
    pass


# endregion[Main_Exec]
