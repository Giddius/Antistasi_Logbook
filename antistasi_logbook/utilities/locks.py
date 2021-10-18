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
from threading import Lock, RLock, Event, Condition, Barrier, Semaphore, BoundedSemaphore, Timer, _RLock
if TYPE_CHECKING:
    from antistasi_logbook.items.log_file import LogFile
# endregion[Imports]

# region [TODO]


# endregion [TODO]

# region [Logging]


# endregion[Logging]

# region [Constants]

THIS_FILE_DIR = Path(__file__).parent.absolute()

# endregion[Constants]


class CustomizeableRLock(_RLock):

    def __init__(self, before_first_aquire: Callable = None, before_args: Iterable = None, before_kwargs: Mapping = None, after_final_release: Callable = None, after_args: Iterable = None, after_kwargs: Mapping = None) -> None:
        super().__init__()
        self._before_first_aquire = before_first_aquire
        self._after_final_release = after_final_release
        self.before_args = before_args or []
        self.before_kwargs = before_kwargs or {}
        self.after_args = after_args or []
        self.after_kwargs = after_kwargs or {}

    def __enter__(self) -> bool:

        if self._count == 0:
            self.before_first_aquire(*self.before_args, **self.before_kwargs)
        return super().__enter__()

    def __exit__(self, t, v, tb) -> None:
        super().__exit__(t, v, tb)
        if self._count == 0:
            self.after_final_release(*self.after_args, **self.after_kwargs)

    def before_first_aquire(self, *args, **kwargs):
        if self._before_first_aquire:
            self._before_first_aquire(*args, **kwargs)

    def after_final_release(self, *args, **kwargs):
        if self._after_final_release:
            self._after_final_release(*args, **kwargs)


class DownloadRlock(CustomizeableRLock):

    def __init__(self, log_file: "LogFile") -> None:
        super().__init__()
        self.log_file = log_file

    def before_first_aquire(self):
        print(f"downloading {self.log_file.name!r}")
        return self.log_file.download()

    def after_final_release(self):
        print(f"deleting {self.log_file.name!r}")
        if self.log_file.keep_downloaded_file is False:
            self.log_file.local_path.unlink(missing_ok=True)


# region[Main_Exec]
if __name__ == '__main__':
    pass

# endregion[Main_Exec]
