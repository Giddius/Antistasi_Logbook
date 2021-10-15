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


from antistasi_serverlog_statistic.regex.regex_pattern import TokenRegexPattern

# endregion[Imports]

# region [TODO]


# endregion [TODO]

# region [Logging]


# endregion[Logging]

# region [Constants]

THIS_FILE_DIR = Path(__file__).parent.absolute()

# endregion[Constants]


class Scanner(re.Scanner):
    def __init__(self, items: Iterable[TokenRegexPattern], flags: re.RegexFlag = 0) -> None:
        super().__init__(self._handle_items(items), flags)

    def _handle_items(self, items: Iterable[TokenRegexPattern]) -> list[tuple[str, Callable]]:
        _out = []
        for item in items:
            if hasattr(item, '___scanner_item___'):
                _out.append(item.___scanner_item___)
            else:
                _out.append(item)
        return _out

# region[Main_Exec]


if __name__ == '__main__':
    ii = [TokenRegexPattern(r'alarm', str), TokenRegexPattern(r'wurst', str), TokenRegexPattern(r'\s', None)]
    x = Scanner(ii)
    tt = "wurst alarm krampf alarm"
    print(x.scan(tt))


# endregion[Main_Exec]
