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

from gidapptools.general_helper.string_helper import StringCaseConverter, StringCase
from antistasi_logbook.gui.resources.style_sheets import ALL_STYLE_SHEETS
from difflib import ndiff
# endregion[Imports]

# region [TODO]


# endregion [TODO]

# region [Logging]


# endregion[Logging]

# region [Constants]

THIS_FILE_DIR = Path(__file__).parent.absolute()

# endregion[Constants]

TAG_LINE = """
/*
__TAGS__:
*/

""".lstrip()


def convert_stem(stem: str) -> str:
    new_stem = stem[0].casefold()
    last_char = stem[0]
    for char in stem[1:]:
        if char.isupper() and not last_char.isupper():
            new_stem += '_' + char.casefold()

        else:
            new_stem += char.casefold()

        last_char = char

    return new_stem


def rename_file(path: Path):
    old_stem = path.stem
    new_stem = convert_stem(old_stem)
    path.rename(path.with_stem(new_stem))


def add_tag_line(path: Path):
    text = path.read_text(encoding='utf-8', errors='ignore')
    path.write_text(TAG_LINE + text, encoding='utf-8', errors='ignore')


# for v in ALL_STYLE_SHEETS.values():
#     add_tag_line(v)

# region[Main_Exec]

if __name__ == '__main__':
    file_1 = Path(r"D:\Dropbox\hobby\Modding\Ressources\qss\console_style.qss")
    file_2 = Path(r"D:\Dropbox\hobby\Modding\Programs\Github\My_Repos\Antistasi_Logbook\antistasi_logbook\gui\resources\style_sheets\console.qss")
    diff = ndiff(file_1.read_text(encoding='utf-8', errors='ignore').splitlines(keepends=True), file_2.read_text(encoding='utf-8', errors='ignore').splitlines(keepends=True))
    import pp
    pp(''.join(diff))
# endregion[Main_Exec]
