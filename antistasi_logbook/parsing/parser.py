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
from collections import Counter, ChainMap, deque, namedtuple, defaultdict
from urllib.parse import urlparse
from queue import PriorityQueue
from importlib.util import find_spec, module_from_spec, spec_from_file_location
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from sortedcontainers import SortedList
from importlib.machinery import SourceFileLoader
from antistasi_logbook.items.enums import LogLevel, PunishmentAction
from antistasi_logbook.regex.regex_keeper import RegexKeeper
from antistasi_logbook.items.entries.raw_entry import RawEntry
from antistasi_logbook.items.entries.base_entry import BaseEntry, EntryFamily
from antistasi_logbook.utilities.misc import get_subclasses_recursive
from antistasi_logbook.items.entries.message import Message
from dataclasses import dataclass
from antistasi_logbook.items.log_file import LogFile
if TYPE_CHECKING:

    from antistasi_logbook.items.entries.entry_line import EntryLine
# endregion[Imports]

# region [TODO]


# endregion [TODO]

# region [Logging]


# endregion[Logging]

# region [Constants]

THIS_FILE_DIR = Path(__file__).parent.absolute()

# endregion[Constants]


@dataclass
class TempEntry:
    log_file: LogFile
    recorded_at: datetime
    message: Message
    start: int
    end: int
    record_class: str
    log_level: LogLevel = LogLevel.NO_LEVEL
    punishment_action: PunishmentAction = PunishmentAction.NO_ACTION
    logged_from: str = None
    called_by: str = None
    client: str = None
    comments: str = None

    @classmethod
    def from_parser(cls, context: "ParseContext", raw_entry: "RawEntry", record_class: type) -> "BaseEntry":
        log_file = context.log_file
        if raw_entry.parsed_data.get("utc_year") is not None:
            recorded_at = datetime(tzinfo=timezone.utc, **{k.removeprefix('utc_'): int(v) for k, v in raw_entry.parsed_data.items() if k.startswith('utc_')})
        else:
            recorded_at = datetime(tzinfo=context.log_file.local_timezone, **{k.removeprefix('local_'): int(v) for k, v in raw_entry.parsed_data.items() if k.startswith('local_')}).astimezone(tz=timezone.utc)
        message = raw_entry.parsed_data.get('message', "")
        log_level = raw_entry.parsed_data.get("log_level", LogLevel.NO_LEVEL)
        start = raw_entry.start
        end = raw_entry.end
        punishment_action = raw_entry.parsed_data.get("punishment_action")
        logged_from = raw_entry.parsed_data.get("file")
        called_by = raw_entry.parsed_data.get("called_by")
        client = raw_entry.parsed_data.get("client")
        message = message = raw_entry.parsed_data.get('message').strip(' "')
        return cls(log_file=log_file, recorded_at=recorded_at, message=message, start=start, end=end, record_class=record_class.__name__, log_level=LogLevel(log_level), punishment_action=PunishmentAction(punishment_action), logged_from=logged_from, called_by=called_by, client=client, comments=None)


class LineCache(deque):

    def is_empty(self) -> bool:
        return len(self) == 0

    def dump(self) -> list["EntryLine"]:
        data = list(self)
        self.clear()
        return data


class ParseContext:
    __slots__ = ("log_file", "_line_generator", "_current_line", "header_entry", "initializing_lines", "cache", "after_server_init_lines", "entries", "_cur_line_num")

    def __init__(self, log_file: "LogFile") -> None:
        self.log_file = log_file
        self._line_generator: Generator["EntryLine", None, None] = None
        self._current_line: "EntryLine" = ...
        self.header_entry: RawEntry = None
        self.initializing_lines: list["EntryLine"] = None
        self.cache: LineCache["EntryLine"] = LineCache()
        self.after_server_init_lines: bool = False
        self.entries: list["BaseEntry"] = []
        self._cur_line_num: int = None

    @property
    def line_generator(self) -> Generator["EntryLine", None, None]:
        if self._line_generator is None:
            self._line_generator = self.log_file.get_line_generator()
        return self._line_generator

    @property
    def current_line(self) -> "EntryLine":
        if self._current_line is ...:
            self.advance_line()

        return self._current_line

    def advance_line(self) -> None:
        self._current_line = next(self.line_generator, None)
        if self._current_line is not None:
            self._cur_line_num = self._current_line.start

    def cache_current_line(self) -> None:
        self.cache.append(self.current_line)

    def dump_cache(self) -> RawEntry:
        return RawEntry(self.cache.dump())

    def update_last_parsed_line_number(self):
        self.log_file.last_parsed_line_number = self._cur_line_num

    def set_header_lines(self) -> None:
        self.header_entry = self.dump_cache()
        self.log_file.header_text = self.header_entry.unformatted_content

    def add_entry(self, entry: "BaseEntry") -> None:

        self.entries.append(entry)
        if len(self.entries) >= 9999999:
            BaseEntry.many_entries_to_db(self.entries)
            self.entries.clear()

    def close(self) -> None:
        if self.entries:
            BaseEntry.many_entries_to_db(self.entries)
            self.entries.clear()

        self.line_generator.close()
        self.update_last_parsed_line_number()

        self.log_file.to_db()


class EntryFactory:

    def __init__(self, antistasi_entry_indicator: str = "| Antistasi |", entry_base_class: type[BaseEntry] = BaseEntry, extra_entry_classes: Iterable[type] = None) -> None:
        self.antistasi_entry_indicator = antistasi_entry_indicator
        self.entry_base_class = entry_base_class
        self.entry_base_class.set_record_registry()
        self.extra_entry_classes = [] if extra_entry_classes is None else list(extra_entry_classes)
        self._all_entry_classes: tuple[type] = None

    @cached_property
    def all_entry_classes(self) -> tuple[type]:
        if self._all_entry_classes is None:
            self._all_entry_classes = self._collect_entry_classes()
        return self._all_entry_classes

    @cached_property
    def all_antistasi_entry_classes(self) -> tuple[type]:
        return tuple(entry_class for entry_class in self.all_entry_classes if EntryFamily.ANTISTASI in entry_class.___entry_family___)

    @cached_property
    def all_generic_entry_classes(self) -> tuple[type]:
        return tuple(entry_class for entry_class in self.all_entry_classes if EntryFamily.GENERIC in entry_class.___entry_family___)

    def is_antistasi_entry(self, raw_entry: RawEntry) -> bool:
        return self.antistasi_entry_indicator.casefold() in raw_entry.content.casefold()

    def _collect_entry_classes(self) -> tuple[type]:
        all_base_classes = [self.entry_base_class] + self.extra_entry_classes
        all_concrete_entry_classes = SortedList(key=lambda x: -x[1])

        def _handle_class(in_class: type, level: int = 0) -> list[type]:
            concrete_entry_classes = []
            if inspect.isabstract(in_class) is False:
                concrete_entry_classes.append((in_class, level))
            for sub_class in in_class.__subclasses__():
                concrete_entry_classes += _handle_class(sub_class, level=level + 1)
            return concrete_entry_classes

        for base_class in all_base_classes:
            all_concrete_entry_classes += _handle_class(base_class)

        return tuple(item[0] for item in all_concrete_entry_classes)

    def determine_entry_class(self, context: ParseContext, raw_entry: RawEntry) -> type:
        if raw_entry.is_antistasi_entry is True:
            entry_classes = self.all_antistasi_entry_classes
        else:
            entry_classes = self.all_generic_entry_classes

        for entry_class in entry_classes:
            if entry_class.check(context, raw_entry) is True:
                return entry_class
        raise TypeError(f"Unable to determine entry class for record:\n{raw_entry.unformatted_content!r}.")

    def new_entry(self, context: ParseContext, raw_entry: RawEntry) -> BaseEntry:
        entry_class = self.determine_entry_class(context, raw_entry)
        return TempEntry.from_parser(context=context, raw_entry=raw_entry, record_class=entry_class)


class Parser:

    def __init__(self, regex_keeper: RegexKeeper = None, entry_factory: EntryFactory = None, raise_on_unparseable_entry: bool = False) -> None:
        self.regex_keeper = RegexKeeper(log_level_values=LogLevel.all_possible_names, punishment_action_values=PunishmentAction.all_possible_names) if regex_keeper is None else regex_keeper

        self.entry_factory = EntryFactory() if entry_factory is None else entry_factory
        self.raise_on_unparseable_entry = raise_on_unparseable_entry

    @property
    def default_antistasi_entry_data(self) -> dict[str, Union[None, list]]:
        default_entry_data = {key: None for key in self.regex_keeper.antistasi_entry.group_names() if not key.startswith('local_') and key not in {'identifier'}}
        default_entry_data['message'] = []
        return default_entry_data

    def _parse_antistasi_entry(self, raw_entry: RawEntry) -> Optional[dict[str, Any]]:
        # TODO: REFRACTOR THIS !!! Maybe use the subclass of re.Scanner or use Pyparsing.
        data = self.default_antistasi_entry_data.copy()

        for part in raw_entry.content.split('|'):
            part = part.strip()
            part_match = self.regex_keeper.antistasi_entry.search(part)
            if part_match:
                for key, value in part_match.groupdict().items():
                    if value:
                        if key == 'message':
                            data["message"].append(value)
                        else:
                            data[key] = value
        data["message"] = '||'.join(i.strip() for i in data["message"])

        return data

    def _parse_generic_entry(self, raw_entry: RawEntry) -> Optional[dict[str, Any]]:
        data_match = self.regex_keeper.generic_entry.search(raw_entry.content)
        if data_match:
            return data_match.groupdict()

    def _check_for_mod_data(self, context: ParseContext, raw_entry: RawEntry):
        pass

    def _process_new_record(self, context: ParseContext):
        raw_entry = context.dump_cache()

        if self.entry_factory.is_antistasi_entry(raw_entry) is True:

            raw_entry.is_antistasi_entry = True
            raw_entry.parsed_data = self._parse_antistasi_entry(raw_entry)

        else:
            raw_entry.parsed_data = self._parse_generic_entry(raw_entry)

        if raw_entry.parsed_data is None and self.raise_on_unparseable_entry is True:
            # TODO: Custom Error!
            raise RuntimeError(f"Unable to parse raw entry:\n{raw_entry.unformatted_content!r}.")

        try:
            entry = self.entry_factory.new_entry(context, raw_entry)
            context.add_entry(entry)
        except Exception as error:
            print(error)

    def parse_header_lines(self, context: ParseContext):

        while context.current_line is not None and not self.regex_keeper.only_time.search(context.current_line.content):
            context.cache_current_line()
            context.advance_line()
        context.set_header_lines()
        context.update_last_parsed_line_number()

    def parse_entries(self, context: ParseContext):
        while self.regex_keeper.local_datetime.search(context.current_line.content) is None:
            context.advance_line()
        while context.current_line is not None:
            line_match = self.regex_keeper.local_datetime.search(context.current_line.content)

            if line_match and context.cache.is_empty() is False:

                self._process_new_record(context=context)

            context.cache_current_line()
            context.advance_line()
        if context.cache.is_empty() is False:
            self._process_new_record(context=context)

    def parse_log_file(self, log_file_item: "LogFile"):

        context = ParseContext(log_file=log_file_item)
        print(f"Starting to parse {log_file_item.name!r}")
        try:
            with context.log_file.download_lock:
                context.log_file.search_utc_created_at(self.regex_keeper)
                if context.log_file.unparsable is True:
                    return
                if context.log_file.last_parsed_line_number is None or context.log_file.last_parsed_line_number == 0:
                    print(f"Starting to parse HEADER_TEXT for {log_file_item.name!r}")
                    self.parse_header_lines(context=context)
                print(f"Starting to parse ENTRIES for {log_file_item.name!r}")
                self.parse_entries(context=context)
        finally:
            print(f"finished parsing {log_file_item.name!r} of server {log_file_item.server.name!r}")
            context.close()
            print(f"context for {log_file_item.name!r} closed.")
# region[Main_Exec]


if __name__ == '__main__':
    pass

# endregion[Main_Exec]
