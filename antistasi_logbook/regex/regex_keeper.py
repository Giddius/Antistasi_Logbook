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
from importlib.util import find_spec, module_from_spec, spec_from_file_location
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from importlib.machinery import SourceFileLoader
from antistasi_logbook.regex.regex_pattern import RegexPattern

import pyparsing as pp
import pyparsing.common as ppc
if TYPE_CHECKING:
    from antistasi_logbook.storage.models.models import LogRecord
# endregion[Imports]

# region [TODO]


# endregion [TODO]

# region [Logging]


# endregion[Logging]

# region [Constants]

THIS_FILE_DIR = Path(__file__).parent.absolute()

# endregion[Constants]


def multiline_to_single_line(in_string: str) -> str:
    return r"".join([line.lstrip() for line in in_string.splitlines()])


def regex_groups_to_datetime(prefix: str = None, tz: timezone = timezone.utc):
    def _inner(match_token: re.Match):
        match_token = match_token[0]
        if prefix is None:
            kwargs = {k: int(v) for k, v in match_token.groupdict().items()}
        else:
            kwargs = {k.removeprefix(prefix): int(v) for k, v in match_token.groupdict().items() if k.startswith(prefix)}
        return datetime(tzinfo=tz, **kwargs)
    return _inner


UTC_DATETIME_REGEX_STRING = multiline_to_single_line(r"""
                                    \s?
                                    (?P<utc_year>\d{4})
                                    [^\d]
                                    (?P<utc_month>[01]?\d)
                                    [^\d]
                                    (?P<utc_day>[0-3]?\d)
                                    [^\d]
                                    (?P<utc_hour>[0-2\s]?\d)
                                    [^\d]
                                    (?P<utc_minute>[0-6]\d)
                                    [^\d]
                                    (?P<utc_second>[0-6]\d)
                                    [^\d]
                                    (?P<utc_microsecond>\d+)""")

LOCAL_DATETIME_REGEX_STRING = multiline_to_single_line(r"""
                                            ^
                                            (?P<local_year>\d{4})
                                            [^\d]
                                            (?P<local_month>[01]?\d)
                                            [^\d]
                                            (?P<local_day>[0-3]?\d)
                                            \,\s+
                                            (?P<local_hour>[0-2\s]?\d)
                                            [^\d]
                                            (?P<local_minute>[0-6]\d)
                                            [^\d]
                                            (?P<local_second>[0-6]\d)""")


class AntistasiEntryGrammar:
    parts_separator = pp.Suppress('|')
    antistasi_indicator = pp.Suppress("Antistasi")
    utc_datetime = pp.Regex(re.compile(UTC_DATETIME_REGEX_STRING), as_match=True)("utc_created_at").set_parse_action(regex_groups_to_datetime(prefix="utc_", tz=timezone.utc))
    _local_datetime = pp.Regex(re.compile(LOCAL_DATETIME_REGEX_STRING), as_match=True)
    file_part = pp.Keyword("File:").suppress() + pp.Word(pp.printables.replace('|', ''))("file")
    message_part = pp.OneOrMore(pp.Word(pp.printables.replace('|', '')))("message")

    @classmethod
    def get_local_time_with_tz(cls, local_timezone: timezone) -> pp.ParserElement:
        return cls._local_datetime("local_created_at").set_parse_action(regex_groups_to_datetime(prefix="local_", tz=local_timezone))

    @classmethod
    def get_log_level_grammar(cls, log_level_values) -> pp.ParserElement:
        return pp.one_of(log_level_values, as_keyword=True)("log_level")

    @classmethod
    def get_grammar(cls, local_timezone: timezone, log_level_values=None) -> pp.ParserElement:
        return cls.get_local_time_with_tz(local_timezone=local_timezone) + cls.utc_datetime + cls.parts_separator + pp.OneOrMore(cls.antistasi_indicator | cls.file_part | cls.get_log_level_grammar(LogLevel.all_possible_names) | cls.message_part)


class RegexKeeper:
    only_time = RegexPattern(r"^([0-2\s]?\d)[^\d]([0-6]\d)[^\d]([0-6]\d)")

    local_datetime = RegexPattern(multiline_to_single_line(r"""
                                            ^
                                            (?P<local_year>\d{4})
                                            [^\d]
                                            (?P<local_month>[01]?\d)
                                            [^\d]
                                            (?P<local_day>[0-3]?\d)
                                            \,\s+
                                            (?P<local_hour>[0-2\s]?\d)
                                            [^\d]
                                            (?P<local_minute>[0-6]\d)
                                            [^\d]
                                            (?P<local_second>[0-6]\d)"""), re.MULTILINE)

    utc_datetime = RegexPattern(multiline_to_single_line(r"""
                                    \s?
                                    (?P<utc_year>\d{4})
                                    [^\d]
                                    (?P<utc_month>[01]?\d)
                                    [^\d]
                                    (?P<utc_day>[0-3]?\d)
                                    [^\d]
                                    (?P<utc_hour>[0-2\s]?\d)
                                    [^\d]
                                    (?P<utc_minute>[0-6]\d)
                                    [^\d]
                                    (?P<utc_second>[0-6]\d)
                                    [^\d]
                                    (?P<utc_microsecond>\d+)"""), re.MULTILINE)

    alt_full_datetime = re.compile(r"""\d{4}
                                    [^\d]
                                    [01]?\d
                                    [^\d]
                                    [0-3]?\d
                                    \,\s+
                                    [0-2\s]?\d
                                    [^\d]
                                    [0-6]\d
                                    [^\d]
                                    [0-6]\d
                                    \s?
                                    (?P<utc_year>\d{4})
                                    [^\d]
                                    (?P<utc_month>[01]?\d)
                                    [^\d]
                                    (?P<utc_day>[0-3]?\d)
                                    [^\d]
                                    (?P<utc_hour>[0-2\s]?\d)
                                    [^\d]
                                    (?P<utc_minute>[0-6]\d)
                                    [^\d]
                                    (?P<utc_second>[0-6]\d)
                                    [^\d]
                                    (?P<utc_microsecond>\d+)""", re.VERBOSE)

    antistasi_identifier = RegexPattern(r"(?P<identifier>Antistasi)")

    file = RegexPattern(r"File\:\s*(?P<file>[\w\_\.]*)")

    caller = RegexPattern(r"Called By\:\s*(?P<called_by>[\w\_\.]*)")

    client = RegexPattern(r"Client:\s(?P<client>[^\|]+)")

    default_message = RegexPattern(r"(?P<message>[^\|]*)")

    full_datetime = local_datetime + utc_datetime

    start_mod_table = only_time + RegexPattern(r"\s*\=+\s+List of mods\s+\=+")

    end_mod_table = only_time + RegexPattern(r"\s*\=+$")

    game_map = local_datetime + RegexPattern(r"\s+Mission world\:\s(?P<game_map>.*)", re.MULTILINE)

    game_file = local_datetime + RegexPattern(r"\s+Mission file\:\s(?P<game_file>.*)", re.MULTILINE)
    continued_record = local_datetime + RegexPattern(r"\s+\>\>\>\s?(?P<content>.*)")

    def __init__(self, log_level_values: Iterable[str] = None, punishment_action_values: Iterable[str] = None) -> None:
        self.log_level = RegexPattern(r"(?P<log_level>)")
        self.punishment_action = RegexPattern(r"(?P<punishment_action>)")
        self.generic_entry = self.local_datetime + self.default_message
        self.antistasi_entry = RegexPattern(r'|').join([self.full_datetime, self.antistasi_identifier, self.file, self.caller, self.client, self.log_level, self.punishment_action, self.default_message])
        self._log_level_values = log_level_values
        self._punishment_action_values = punishment_action_values
        if self._log_level_values is not None:
            self._set_log_level_values(*self._log_level_values)
        if self._punishment_action_values is not None:
            self._set_punishment_action_values(*self._punishment_action_values)

    @property
    def log_level_values(self) -> tuple[str]:
        if self._log_level_values is None:
            return tuple()
        return tuple(self._log_level_values)

    @log_level_values.setter
    def log_level_values(self, value) -> None:
        self._log_level_values = value
        self._set_log_level_values(*self._log_level_values)

    @property
    def punishment_action_values(self) -> tuple[str]:
        if self._punishment_action_values is None:
            return tuple()
        return tuple(self._punishment_action_values)

    @punishment_action_values.setter
    def punishment_action_values(self, value) -> None:
        self._punishment_action_values = value
        self._set_punishment_action_values(*self._punishment_action_values)

    def _set_log_level_values(self, *values: str) -> None:
        self.log_level = self.log_level.format_group_values(log_level=r"|".join(values))
        self.antistasi_entry = self.antistasi_entry.format_group_values(log_level=r"|".join(values))

    def _set_punishment_action_values(self, *values: str) -> None:
        self.punishment_action = self.punishment_action.format_group_values(punishment_action=r"|".join(values))
        self.antistasi_entry = self.antistasi_entry.format_group_values(punishment_action=r"|".join(values))


class LogRegex:

    _patterns = {
        'only_time': r"^([012\s]?\d)[^\d]([0123456]\d)[^\d]([0123456]\d)",
        'local_datetime': r"^(?P<local_year>\d\d\d\d)[^\d](?P<local_month>\d+?)[^\d](?P<local_day>\d+)\,\s+(?P<local_hour>[012\s]?\d)[^\d](?P<local_minute>[0123456]\d)[^\d](?P<local_second>[0123456]\d)",
        # 'local_datetime': r"^(?P<local_hour>[012\s]?\d)[^\d](?P<local_minute>[0123456]\d)[^\d](?P<local_second>[0123456]\d)",
        'utc_datetime': r"\s(?P<utc_year>\d\d\d\d)[^\d](?P<utc_month>\d+?)[^\d](?P<utc_day>\d+)[^\d](?P<utc_hour>[012\s]?\d)[^\d](?P<utc_minute>[0123456]\d)[^\d](?P<utc_second>[0123456]\d)[^\d](?P<utc_microsecond>\d+)",
        'antistasi_identifier': r"(?P<identifier>Antistasi)",
        'log_level': r"(?P<log_level>Info|Debug|Warning|Critical|Error)",
        'punishment_action': r"(?P<punishment_action>DAMAGE|WARNING)",
        'file': r"File\:\s*(?P<file>[\w\_\.]*)",
        'caller': r"Called By\:\s*(?P<called_by>[\w\_\.]*)",
        'client': r"Client:\s(?P<client>[^\|]+)",
        'default_message': r"(?P<message>[^\|]*)"

    }

    antistasi_entry_flags: re.RegexFlag = None
    excluded_antistasi_entry_keys = {'local_year', 'local_month', 'local_day', 'local_hour', 'local_minute', 'local_second', 'identifier'}
    _is_init: bool = False

    def __init__(self) -> None:
        self.additional_patterns = {
            'full_datetime': self._patterns['local_datetime'] + self._patterns['utc_datetime'],
            'start_mod_table': self._patterns['only_time'] + r"\s*\=+\s+List of mods\s+\=+",
            'end_mod_table': self._patterns['only_time'] + r"\s*\=+$"
        }
        self.regexes = {}
        self.antistasi_entry: re.Pattern = None
        self.generic_entry: re.Pattern = None
        self.compile_all_regexes()
        self.compile_antistasi_entry_regex()
        self.compile_generic_entry_regex()
        self._is_init = True

    @ property
    def patterns(self):
        return self._patterns | self.additional_patterns

    def compile_all_regexes(self):
        for key, value in self.patterns.items():
            self.regexes[key] = re.compile(value)

    def _antistasi_entry_patterns(self):
        part_key_names = ['full_datetime', 'antistasi_identifier', 'file', 'caller', 'client', 'log_level', 'punishment_action', 'default_message']
        return [self.patterns.get(key_name) for key_name in part_key_names if self.patterns.get(key_name)]

    def compile_generic_entry_regex(self):
        self.generic_entry = re.compile(self._patterns['local_datetime'] + self._patterns['default_message'])

    def compile_antistasi_entry_regex(self):
        pattern = r'|'.join(self._antistasi_entry_patterns())
        if self.antistasi_entry_flags is None:
            self.antistasi_entry = re.compile(pattern)
        else:
            self.antistasi_entry = re.compile(pattern, self.antistasi_parts_flags)

    def _get_default_entry_dict(self):
        entry_dict = {key: None for key in self.antistasi_entry.groupindex if key not in self.excluded_antistasi_entry_keys}
        entry_dict['message'] = []
        return entry_dict

    def _parse_antistasi_entry(self, entry: "LogRecord") -> dict[str, str]:
        _out = self._get_default_entry_dict()
        for part in entry.content.split('|'):
            part = part.strip()
            part_match = self.antistasi_entry.search(part)
            if part_match:
                for key, value in part_match.groupdict().items():
                    if value:
                        if key == 'message':
                            _out[key].append(value)
                        else:
                            _out[key] = value
        _out['message'] = '||'.join(_out['message']).replace('\n', '')
        return _out

    def _parse_generic_entry(self, entry: "LogRecord") -> dict[str, str]:
        entry_match = self.generic_entry.search(entry.content)
        if entry_match:
            return entry_match.groupdict()

    def parse_entry(self, entry: "LogRecord"):
        if '| Antistasi |' in entry.content:
            return self._parse_antistasi_entry(entry=entry)
        else:
            return self._parse_generic_entry(entry=entry)

    def __getattr__(self, name: str) -> Any:
        if not name.startswith('_'):
            try:
                return self.regexes[name]
            except KeyError:
                pass
        raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")


# region[Main_Exec]
if __name__ == '__main__':
    pass

# endregion[Main_Exec]
