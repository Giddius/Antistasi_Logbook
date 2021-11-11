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
import pyparsing as pp
import pyparsing.common as ppc
from dateutil.tz import UTC
from antistasi_logbook.storage.models.models import LogLevel
from gidapptools.general_helper.enums import MiscEnum
from rich.console import Console as RichConsole
# endregion[Imports]

# region [TODO]


# endregion [TODO]

# region [Logging]


# endregion[Logging]

# region [Constants]

THIS_FILE_DIR = Path(__file__).parent.absolute()
CONSOLE = RichConsole(soft_wrap=True)
# endregion[Constants]


def multiline_to_single_line(in_string: str) -> str:
    return r"".join([line.lstrip() for line in in_string.splitlines()])


def regex_groups_to_datetime(prefix: str = None, tz: timezone = None):
    def _inner(match_token: re.Match):
        match_token = match_token[0]
        if prefix is None:
            kwargs = {k: int(v) for k, v in match_token.groupdict().items()}
        else:
            kwargs = {k.removeprefix(prefix): int(v) for k, v in match_token.groupdict().items() if k.startswith(prefix)}
        return datetime(tzinfo=tz, **kwargs)
    return _inner


def combine_tokens(tokens: pp.ParseResults) -> str:
    return ' '.join(str(t) for t in tokens).replace(">>>", "")


def handle_called_by(tokens: pp.ParseResults) -> Optional[str]:

    try:
        return tokens[0]
    except IndexError:
        return None


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
                                            (?P<local_year>\d{4})
                                            /
                                            (?P<local_month>[01]\d)
                                            /
                                            (?P<local_day>[0-3]\d)
                                            \,\s
                                            (?P<local_hour>[0-2]\d)
                                            \:
                                            (?P<local_minute>[0-6]\d)
                                            \:
                                            (?P<local_second>[0-6]\d)""".strip())


# class RecordsGrammar:
#     non_message_printables = pp.printables.replace("|", "")
#     message_printables = pp.printables + "➥"

#     sep = pp.Suppress('|')
#     continuation_marker = pp.Keyword(">>>").suppress()

#     utc_datetime = pp.Regex(re.compile(UTC_DATETIME_REGEX_STRING, re.MULTILINE), as_match=True)("utc_recorded_at").set_parse_action(regex_groups_to_datetime(prefix="utc_", tz=UTC))
#     local_datetime = pp.Regex(re.compile(LOCAL_DATETIME_REGEX_STRING, re.MULTILINE), as_match=True)("local_recorded_at").set_parse_action(regex_groups_to_datetime(prefix="local_", tz=None))

#     full_datetime_part = local_datetime.suppress() + utc_datetime

#     antistasi_indicator = pp.Keyword("Antistasi", caseless=False)("antistasi_indicator")

#     log_level_part = pp.one_of(["NO_LEVEL", "DEBUG", "INFO", "WARNING", "CRITICAL", "ERROR"], as_keyword=True, caseless=True)("log_level")

#     file_part = pp.Keyword("File:").suppress() + pp.Word(non_message_printables)("logged_from")
#     called_by_part = pp.Keyword("Called By:").suppress() + pp.Word(non_message_printables)("called_by")
#     optional_called_by_part = pp.Optional(called_by_part, default=MiscEnum.NOT_FOUND)("called_by").set_parse_action(handle_called_by)
#     # message_part = pp.OneOrMore(pp.Word(pp.printables), stop_on=sep + called_by_part)("message").set_parse_action(combine_tokens)
#     continued_line = local_datetime.suppress() + continuation_marker
#     client_part = pp.Keyword("Client:") + pp.OneOrMore(pp.Word(message_printables), stop_on=local_datetime)
#     _message_part = pp.OneOrMore(pp.Word(message_printables), stop_on=local_datetime ^ (sep + called_by_part) ^ (sep + client_part))

#     message_part = (_message_part + pp.Optional(pp.OneOrMore(continued_line + _message_part)))("message").set_parse_action(combine_tokens)

#     antistasi_record_grammar = full_datetime_part + sep + antistasi_indicator + sep + log_level_part + sep + file_part + sep + message_part + \
#         pp.Optional(sep + called_by_part, default=MiscEnum.NOT_FOUND)("called_by").set_parse_action(handle_called_by) + pp.Optional(sep + client_part)("client")

#     generic_record_grammar = local_datetime + message_part

#     full_record_grammar = antistasi_record_grammar | generic_record_grammar

# region[Main_Exec]


if __name__ == '__main__':
    pass
# endregion[Main_Exec]
