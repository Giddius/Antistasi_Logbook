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


# endregion[Imports]

# region [TODO]


# endregion [TODO]

# region [Logging]


# endregion[Logging]

# region [Constants]

THIS_FILE_DIR = Path(__file__).parent.absolute()

# endregion[Constants]


@ unique
class LogLevelEnum(Enum):
    NO_LEVEL = 0
    DEBUG = 1
    INFO = 2
    WARNING = 3
    CRITICAL = 4
    ERROR = 5

    @ classmethod
    def _missing_(cls, value: str):
        if value is None:
            return cls.NO_LEVEL
        mod_value = value.casefold()
        _out = {member.name.casefold(): member for member in cls.__members__.values()}.get(mod_value, None)
        if _out is None:
            raise ValueError("%r is not a valid %s" % (value, cls.__name__))
        return _out

    @classmethod
    @property
    def all_possible_names(cls) -> list[str]:
        return [member.name.title() for member in cls.__members__.values() if member is not cls.NO_LEVEL]


@ unique
class PunishmentActionEnum(Enum):
    WARNING = 1
    DAMAGE = 2
    COLLISION = 3
    RELEASE = 4
    GUILTY = 5
    NO_ACTION = 0

    @ classmethod
    def _missing_(cls, value: str):
        if value is None:
            return cls.NO_ACTION
        mod_value = value.casefold()
        _out = {member.name.casefold(): member for member in cls.__members__.values()}.get(mod_value, None)
        if _out is None:
            raise ValueError("%r is not a valid %s" % (value, cls.__name__))
        return _out

    @classmethod
    @property
    def all_possible_names(cls) -> list[str]:
        return [member.name.upper() for member in cls.__members__.values() if member is not cls.NO_ACTION]


# region[Main_Exec]
if __name__ == '__main__':
    pass

# endregion[Main_Exec]
