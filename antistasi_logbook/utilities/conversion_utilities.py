"""
WiP.

Soon.
"""

# region [Imports]

import gc
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
import unicodedata
import inspect

from time import sleep, process_time, process_time_ns, perf_counter, perf_counter_ns
from io import BytesIO, StringIO
from abc import ABC, ABCMeta, abstractmethod
from copy import copy, deepcopy
from enum import Enum, Flag, auto
from time import time, sleep
from pprint import pprint, pformat
from pathlib import Path
from string import Formatter, digits, printable, whitespace, punctuation, ascii_letters, ascii_lowercase, ascii_uppercase
from timeit import Timer
from typing import TYPE_CHECKING, Union, Callable, Iterable, Optional, Mapping, Any, IO, TextIO, BinaryIO
from zipfile import ZipFile, ZIP_LZMA
from datetime import datetime, timezone, timedelta
from tempfile import TemporaryDirectory
from textwrap import TextWrapper, fill, wrap, dedent, indent, shorten
from functools import wraps, partial, lru_cache, singledispatch, total_ordering, cached_property
from importlib import import_module, invalidate_caches
from contextlib import contextmanager, asynccontextmanager
from statistics import mean, mode, stdev, median, variance, pvariance, harmonic_mean, median_grouped
from collections import Counter, ChainMap, deque, namedtuple, defaultdict
from urllib.parse import urlparse
from importlib.util import find_spec, module_from_spec, spec_from_file_location
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from importlib.machinery import SourceFileLoader
from typing import Any
import logging

# endregion[Imports]

# region [TODO]


# endregion [TODO]

# region [Logging]

log = logging.getLogger(__name__)

# endregion[Logging]

# region [Constants]

THIS_FILE_DIR = Path(__file__).parent.absolute()

# endregion[Constants]


BOOL_TRUE_STRINGS = ['true', 'yes', 'on', 'y', '1']
BOOL_FALSE_STRINGS = ['false', 'no', 'off', 'n', '0']


def is_int(in_data: Any) -> bool:
    """
    Checks if data can be converted to a integer.
    """
    try:
        int(in_data)
        return True
    except ValueError:
        return False


def is_float(in_data: Any) -> bool:
    """
    Checks if data can be converted to a float.
    """
    try:
        float(in_data)
        return True
    except ValueError:
        return False


def is_bool(in_data: Any) -> bool:
    """
    Checks if data can be converted to a boolean.
    """
    if isinstance(in_data, bool):
        return in_data
    in_data = str(in_data).casefold()
    if in_data in BOOL_TRUE_STRINGS + BOOL_FALSE_STRINGS:
        return True
    return False


def str_to_bool(in_data: str) -> bool:
    """
    Converts a string to a boolean value.

    Checks against hard coded values, case-insensitive.

    Args:
        in_data (str): string to convert.

    Raises:
        ValueError: if the entered string can not be converted to a boolean, because it is not found in the hard coded values.

    Returns:
        bool: resulting boolean
    """
    in_data = in_data.casefold()
    if in_data in BOOL_TRUE_STRINGS:
        return True
    if in_data in BOOL_FALSE_STRINGS:
        return False
    raise ValueError(f"Unable to convert data '{in_data}' to boolean")

# region[Main_Exec]


if __name__ == '__main__':
    pass

# endregion[Main_Exec]
