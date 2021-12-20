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
LOG_FILE_DIR = Path(r"D:\Dropbox\hobby\Modding\Programs\Github\My_Repos\Antistasi_Logbook\temp")
LOG_FILE_DIRS = tuple(LOG_FILE_DIR.joinpath(i) for i in ["Mainserver_1", "Mainserver_2", "Testserver_1", "Testserver_2"])
# endregion[Constants]


def all_log_files() -> Generator[Path, None, None]:
    for folder in LOG_FILE_DIRS:
        for file in folder.iterdir():
            if file.is_file() and file.suffix == ".txt":
                yield file


def find_lines(to_find: str, case_sensitive: bool = False) -> Generator[tuple[int, str], None, None]:
    if case_sensitive is False:
        to_find = to_find.casefold()
    for file in all_log_files():
        line_num = 0
        with file.open('r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                line_num += 1
                if case_sensitive is False:
                    line = line.casefold()
                if to_find in line:
                    yield line_num, line.strip()


# region[Main_Exec]

if __name__ == '__main__':
    out = set()
    for line_number, res in find_lines("freeSpawnPositions"):

        out.add(res)
    with THIS_FILE_DIR.joinpath('blah.txt').open("w", encoding='utf-8', errors='ignore') as f:
        f.write(f'\n\n{"-"*50}\n\n'.join(out))

# endregion[Main_Exec]
