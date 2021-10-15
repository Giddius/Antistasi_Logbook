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
from antistasi_logbook.items.entries.base_entry import BaseEntry
if TYPE_CHECKING:
    from antistasi_logbook.items.log_file import LogFile
    from antistasi_logbook.items.entries.entry_line import EntryLine
# endregion[Imports]

# region [TODO]


# endregion [TODO]

# region [Logging]


# endregion[Logging]

# region [Constants]

THIS_FILE_DIR = Path(__file__).parent.absolute()

# endregion[Constants]


class LineCache(deque):

    def is_empty(self) -> bool:
        return len(self) == 0

    def dump(self) -> list["EntryLine"]:
        data = list(self)
        self.clear()
        return data


class ParseContext:

    def __init__(self, log_file: "LogFile") -> None:
        self.log_file = log_file
        self._line_generator: Generator["EntryLine", None, None] = None
        self._current_line: "EntryLine" = None
        self.header_entry: RawEntry = None
        self.initializing_lines: list["EntryLine"] = None
        self.cache: LineCache["EntryLine"] = LineCache()
        self.after_server_init_lines: bool = False
        self.entries: list["BaseEntry"] = []

    @property
    def line_generator(self) -> Generator["EntryLine", None, None]:
        if self._line_generator is None:
            self._line_generator = self.log_file.get_line_generator()
        return self._line_generator

    @property
    def current_line(self) -> "EntryLine":
        if self._current_line is None:
            self.advance_line()
        return self._current_line

    def advance_line(self) -> None:
        self._current_line = next(self.line_generator, None)

    def cache_current_line(self) -> None:
        self.cache.append(self.current_line)

    def dump_cache(self) -> RawEntry:
        return RawEntry(self.cache.dump())

    def update_last_parsed_line_number(self):
        self.log_file.last_parsed_line_number = self.current_line.start - 1

    def set_header_lines(self) -> None:
        self.header_entry = self.dump_cache()
        self.log_file.header_text = self.header_entry.unformatted_content

    def close(self) -> None:
        if self.entries:
            db = BaseEntry.database
            db.insert_many_items([entry for entry in self.entries if entry])
        self.line_generator.close()
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
        return tuple(entry_class for entry_class in self.all_entry_classes if 'antistasi' in entry_class.___entry_family___)

    @cached_property
    def all_generic_entry_classes(self) -> tuple[type]:
        return tuple(entry_class for entry_class in self.all_entry_classes if "generic" in entry_class.___entry_family___)

    def is_antistasi_entry(self, raw_entry: RawEntry) -> bool:
        return self.antistasi_entry_indicator in raw_entry.content

    def _collect_entry_classes(self) -> tuple[type]:
        all_base_classes = [self.entry_base_class] + self.extra_entry_classes
        all_concrete_entry_classes = SortedList(key=lambda x: x[1])

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
        return entry_class.from_parser(context=context, raw_entry=raw_entry)


class Parser:

    def __init__(self, regex_keeper: RegexKeeper = None, entry_factory: EntryFactory = None, raise_on_unparseable_entry: bool = False) -> None:
        self.regex_keeper = RegexKeeper(log_level_values=LogLevel.all_possible_names, punishment_action_values=PunishmentAction.all_possible_names) if regex_keeper is None else regex_keeper

        self.entry_factory = EntryFactory() if entry_factory is None else entry_factory
        self.raise_on_unparseable_entry = raise_on_unparseable_entry

    @property
    def default_antistasi_entry_data(self) -> dict[str, Union[None, list]]:
        default_entry_data = {key: None for key in self.regex_keeper.antistasi_entry.group_names if not key.startswith('local_') and key not in {'identifier'}}
        default_entry_data['message'] = []
        return default_entry_data

    def _parse_antistasi_entry(self, raw_entry: RawEntry) -> Optional[dict[str, Any]]:
        # TODO: REFRACTOR THIS !!! Maybe use the subclass of re.Scanner or use Pyparsing.
        data = self.default_antistasi_entry_data
        for part in raw_entry.content.split('|'):
            part = part.strip()
            part_match = self.regex_keeper.antistasi_entry.search(part)
            if part_match:
                for key, value in part_match.groupdict().items():
                    if value:
                        if key == 'message':
                            data[key].append(value)
                        else:
                            data[key] = value
        data['message'] = '||'.join(data['message']).replace('\n', '')
        return data

    def _parse_generic_entry(self, raw_entry: RawEntry) -> Optional[dict[str, Any]]:
        data_match = self.regex_keeper.generic_entry.search(raw_entry.content)
        if data_match:
            return data_match.groupdict()

    def _check_for_mod_data(self, context: ParseContext, raw_entry: RawEntry):
        pass

    def _process_new_record(self, context: ParseContext):
        raw_entry = context.dump_cache()

        if raw_entry.is_antistasi_entry is True:
            raw_entry.is_antistasi_entry = True
            raw_entry.parsed_data = self._parse_antistasi_entry(raw_entry)
            if context.log_file.created_at is None:
                context.log_file.set_utc_created_at(data=raw_entry.parsed_data.copy())
        else:
            raw_entry.parsed_data = self._parse_generic_entry(raw_entry)

        if context.after_server_init_lines is False and raw_entry.is_antistasi_entry is False:
            self._check_for_mod_data(context, raw_entry)

        if context.after_server_init_lines is False and raw_entry.is_antistasi_entry is True:
            context.after_server_init_lines = True

        if raw_entry.parsed_data is None and self.raise_on_unparseable_entry is True:
            # TODO: Custom Error!
            raise RuntimeError(f"Unable to parse raw entry:\n{raw_entry.unformatted_content!r}.")

        entry = self.entry_factory.new_entry(context, raw_entry)
        context.entries.append(entry)
        context.update_last_parsed_line_number()

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
            if context.log_file.last_parsed_line_number is None or context.log_file.last_parsed_line_number == 0:
                print(f"Starting to parse HEADER_TEXT for {log_file_item.name!r}")
                self.parse_header_lines(context=context)
            print(f"Starting to parse ENTRIES for {log_file_item.name!r}")
            self.parse_entries(context=context)
        finally:
            print(f"finished parsing {log_file_item.name!r} of server {log_file_item.server.name!r}")
            context.close()
# region[Main_Exec]


if __name__ == '__main__':
    pass

# endregion[Main_Exec]
