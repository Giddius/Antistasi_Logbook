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
from antistasi_logbook.parsing.parsing_context import LogParsingContext, RecordLine
from antistasi_logbook.utilities.misc import Version, ModItem
from dateutil.tz import UTC
from gidapptools.general_helper.timing import time_func
from gidapptools.general_helper.enums import MiscEnum
from rich.console import Console as RichConsole
from antistasi_logbook.records.record_class_manager import RecordClassManager
from antistasi_logbook.storage.models.models import LogFile, RecordClass, LogRecord, LogLevel, AntstasiFunction
from antistasi_logbook.records.enums import PunishmentActionEnum
from dateutil.tz import UTC

import peewee
from playhouse.signals import Model, post_save
import re
from gidapptools import get_logger
from threading import RLock, Semaphore, Event
from antistasi_logbook.parsing.raw_record import RawRecord
from antistasi_logbook.parsing.record_processor import RecordProcessor, RecordInserter
from antistasi_logbook.parsing.foreign_key_cache import foreign_key_cache
from antistasi_logbook.parsing.meta_log_finder import MetaFinder
if TYPE_CHECKING:

    from antistasi_logbook.records.abstract_record import AbstractRecord
    from antistasi_logbook.storage.database import GidSqliteQueueDatabase
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


class Parser:
    """
    Parses all Parsable data from the log file, the actual log_records are parsed by the `record_processor`.

    """
    log_file_data_scan_chunk_increase = 27239
    log_file_data_scan_chunk_initial = (104997 // 2)

    __slots__ = ("database", "regex_keeper", "record_processor", "foreign_key_cache", "stop_event")

    def __init__(self, record_processor: "RecordProcessor", regex_keeper: "SimpleRegexKeeper", stop_event: Event) -> None:

        self.foreign_key_cache = foreign_key_cache
        self.record_processor = record_processor
        self.regex_keeper = regex_keeper
        self.stop_event = stop_event

    def _get_log_file_meta_data(self, context: LogParsingContext) -> "MetaFinder":
        with context.open(cleanup=False) as file:

            text = file.read(self.log_file_data_scan_chunk_initial)
            finder = MetaFinder(context=context, regex_keeper=self.regex_keeper)

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

    def _parse_header_text(self, context: LogParsingContext) -> None:

        while not self.regex_keeper.only_time.match(context.current_line.content):
            context.line_cache.append(context.current_line)
            context.advance_line()
        return context.line_cache.dump()

    def _parse_startup_entries(self, context: LogParsingContext) -> None:

        while not self.regex_keeper.local_datetime.match(context.current_line.content):
            context.line_cache.append(context.current_line)
            context.advance_line()
        return context.line_cache.dump()

    def parse_entries(self, context: LogParsingContext) -> None:
        while context.current_line is not ... and not self.stop_event.is_set():
            if self.regex_keeper.local_datetime.match(context.current_line.content):
                if match := self.regex_keeper.continued_record.match(context.current_line.content):
                    context.line_cache.append(RecordLine(content=match.group('content'), start=context.current_line.start))
                    context.advance_line()
                    continue

                if context.line_cache.is_empty is False:
                    yield RawRecord(context.line_cache.dump())

            context.line_cache.append(context.current_line)
            context.advance_line()
        rest_lines = context.line_cache.dump()
        if rest_lines:

            yield RawRecord(rest_lines)

    def __call__(self, context: "LogParsingContext") -> Any:

        # if self.stop_event.is_set():
        #     return
        log.info("Parsing meta-data for %r", context._log_file)
        context.set_found_meta_data(self._get_log_file_meta_data(context=context))
        if context.unparsable is True:
            return
        if self.stop_event.is_set():
            return
        if context._log_file.header_text is None:

            context.set_header_text(self._parse_header_text(context))
        if self.stop_event.is_set():
            return
        if context._log_file.startup_text is None:

            context.set_startup_text(self._parse_startup_entries(context))
        if self.stop_event.is_set():
            return
        log.info("Parsing entries for %r", context._log_file)
        for raw_record in self.parse_entries(context):

            processed_record = self.record_processor(raw_record=raw_record, utc_offset=context.log_file_data["utc_offset"])
            yield processed_record


# region[Main_Exec]
if __name__ == '__main__':
    pass

# endregion[Main_Exec]
