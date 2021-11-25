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

from gidapptools.general_helper.timing import time_execution
import re
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


class SimpleRegexKeeper:

    __slots__ = ("only_time", "local_datetime", "continued_record", "generic_record", "full_datetime", "called_by", "game_map", "game_file", "mods", "mod_time_strip", "campaign_id", "first_full_datetime")

    def __init__(self) -> None:

        self.only_time = re.compile(r"[1-2\s]\d\:[0-6]\d\:[0-6]\d(?=\s)")

        self.local_datetime = re.compile(r"\d{4}/[01]\d/[0-3]\d\,\s[0-2]\d\:[0-6]\d\:[0-6]\d(?=\s)")

        self.continued_record = re.compile(r"\d{4}/[01]\d/[0-3]\d\,\s[0-2]\d\:[0-6]\d\:[0-6]\d" + r"\s+(?P<content>\>{3}\s*.*)")

        self.generic_record = re.compile(r"""(?P<year>\d{4})/(?P<month>[01]\d)/(?P<day>[0-3]\d)\,\s(?P<hour>[0-2]\d)\:(?P<minute>[0-6]\d)\:(?P<second>[0-6]\d)\s(?P<message>.*)""")

        self.full_datetime = re.compile(r"\d{4}/[01]\d/[0-3]\d\,\s[0-2]\d\:[0-6]\d\:[0-6]\d\s(?P<year>\d{4})\-(?P<month>[01]\d)\-(?P<day>[0-3]\d)\s(?P<hour>[0-2]\d)\:(?P<minute>[0-6]\d)\:(?P<second>[0-6]\d)\:(?P<microsecond>\d{3})\s")

        self.called_by = re.compile(r"(.*)(?:\s\|\s*Called\sBy\:\s*)([^\s\|]+)(.*)")

        self.game_map = re.compile(r"\sMission world\:\s*(?P<game_map>.*)")
        self.game_file = re.compile(r"\s+Mission file\:\s*(?P<game_file>.*)")
        self.campaign_id = re.compile(r"((?P<text_loading>Loading last campaign ID)|(?P<text_creating>Creating new campaign with ID))\s*(?P<campaign_id>\d+)")
        self.mods = re.compile(r"""^([0-2\s]?\d)
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

        self.mod_time_strip = re.compile(r"""^([0-2\s]?\d)
                                                    [^\d]
                                                    ([0-6]\d)
                                                    [^\d]
                                                    ([0-6]\d)""", re.VERBOSE)
        self.first_full_datetime = re.compile(r"""^
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


# region[Main_Exec]
if __name__ == '__main__':
    pass
# endregion[Main_Exec]
