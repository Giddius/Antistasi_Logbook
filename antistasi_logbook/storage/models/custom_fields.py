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
from typing import TYPE_CHECKING, Union, Callable, Iterable, Optional, Mapping, Any, IO, TextIO, BinaryIO, Hashable, Generator, Literal, TypeVar, TypedDict, AnyStr, ClassVar
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
from peewee import Model, TextField, IntegerField, BooleanField, AutoField, DateTimeField, ForeignKeyField, SQL, BareField, SqliteDatabase, Field
from antistasi_logbook.utilities.path_utilities import RemotePath
import httpx
import yarl
from antistasi_logbook.utilities.misc import Version
from dateutil.tz import tzoffset
# endregion[Imports]

# region [TODO]


# endregion [TODO]

# region [Logging]


# endregion[Logging]

# region [Constants]

THIS_FILE_DIR = Path(__file__).parent.absolute()

# endregion[Constants]


class RemotePathField(Field):
    field_type = "REMOTEPATH"

    def db_value(self, value: RemotePath) -> Optional[str]:
        if value is not None:
            return value._path.as_posix()

    def python_value(self, value) -> Optional[RemotePath]:
        if value is not None:
            return RemotePath(value)


class PathField(Field):
    field_type = "PATH"

    def db_value(self, value: Path) -> Optional[str]:
        if value is not None:
            return value.as_posix()

    def python_value(self, value) -> Optional[Path]:
        if value is not None:
            return Path(value)


class VersionField(Field):
    field_type = "VERSION"

    def db_value(self, value: Version):
        if value is not None:
            return str(value)

    def python_value(self, value) -> Optional[Version]:
        if value is None:
            return None
        return Version.from_string(value)


class URLField(Field):
    field_type = "URL"

    def db_value(self, value: Union[str, yarl.URL, httpx.URL, Path]):
        if value is None:
            return value
        if isinstance(value, Path):
            value = value.as_uri()
        if not isinstance(value, yarl.URL):
            value = yarl.URL(str(value))
        return str(value)

    def python_value(self, value):
        if value is not None:
            return yarl.URL(value)


class BetterDateTimeField(Field):
    field_type = 'DATETIME'

    def db_value(self, value: Optional[datetime]):
        if value is not None:
            return value.isoformat()

    def python_value(self, value):
        if value is not None:
            return datetime.fromisoformat(value)


class TzOffsetField(Field):
    field_type = "TZOFFSET"

    def db_value(self, value: Optional[tzoffset]) -> Optional[str]:
        if value is not None:
            return f"{value.tzname(None)}||{value.utcoffset(None).total_seconds()}"

    def python_value(self, value: Optional[str]):
        if value is not None:
            name, seconds = value.split('||')
            seconds = int(seconds)
            delta = timedelta(seconds=seconds)
            return tzoffset(name, delta)


# region[Main_Exec]
if __name__ == '__main__':
    pass
# endregion[Main_Exec]
