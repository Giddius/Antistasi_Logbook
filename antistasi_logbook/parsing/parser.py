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
from antistasi_logbook.regex.regex_keeper import RegexKeeper
if TYPE_CHECKING:

    from antistasi_logbook.storage.models.models import LogFile
# endregion[Imports]

# region [TODO]


# endregion [TODO]

# region [Logging]


# endregion[Logging]

# region [Constants]

THIS_FILE_DIR = Path(__file__).parent.absolute()

# endregion[Constants]


class Parser:
    log_file_data_scan_chunk = 185931

    def __init__(self, regex_keeper: "RegexKeeper" = None) -> None:
        self.regex_keeper = RegexKeeper() if regex_keeper is None else regex_keeper

    def _get_log_file_data(self, file: TextIOWrapper) -> None:
        text = file.read(self.log_file_data_scan_chunk)
        game_map = None
        full_datetime = None
        while True:
            if game_map is None:
                game_map = self.regex_keeper.game_map.search(text)
            if full_datetime is None:
                full_datetime = self.regex_keeper.full_datetime.search(text)
            if all(item is not None for item in [game_map, full_datetime]):
                print(f"{game_map.group()=}")
                print(f"{full_datetime.group()=}")
                break
            new_text = file.read(self.log_file_data_scan_chunk)
            if not new_text:
                break
            text += new_text

    def __call__(self, log_file: "LogFile") -> Any:
        with log_file.open() as f:
            self._get_log_file_data(f)

            # region[Main_Exec]


if __name__ == '__main__':
    pass

# endregion[Main_Exec]
