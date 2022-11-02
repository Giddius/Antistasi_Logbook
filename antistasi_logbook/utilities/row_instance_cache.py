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

from zipfile import ZipFile, ZIP_LZMA
from datetime import datetime, timezone, timedelta
from tempfile import TemporaryDirectory
from textwrap import TextWrapper, fill, wrap, dedent, indent, shorten
from functools import wraps, partial, lru_cache, singledispatch, total_ordering, cached_property, cache, partialmethod
from importlib import import_module, invalidate_caches
from contextlib import contextmanager, asynccontextmanager, nullcontext, closing, ExitStack, suppress
from statistics import mean, mode, stdev, median, variance, pvariance, harmonic_mean, median_grouped
from collections import Counter, ChainMap, deque, namedtuple, defaultdict
from urllib.parse import urlparse
from importlib.util import find_spec, module_from_spec, spec_from_file_location
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from importlib.machinery import SourceFileLoader
from typing import TYPE_CHECKING, TypeVar, TypeGuard, TypeAlias, Final, TypedDict, Generic, Union, Optional, Protocol, runtime_checkable, NoReturn, NewType, Literal, AnyStr, IO, BinaryIO, TextIO, Any
from collections.abc import Hashable, Iterable, Mapping, Sequence, MutableMapping, MutableSet, MutableSequence, Callable, Generator, Collection, Container, Coroutine
if sys.version_info >= (3, 11):
    from typing import Self
else:
    from typing_extensions import Self

from gidapptools import get_logger
from peewee import Model
if TYPE_CHECKING:
    from antistasi_logbook.gui.main_window import AntistasiLogbookMainWindow
    from antistasi_logbook.gui.application import AntistasiLogbookApplication

# endregion[Imports]

# region [TODO]


# endregion [TODO]

# region [Logging]


# endregion[Logging]

# region [Constants]

from gidapptools.general_helper.timing import get_dummy_profile_decorator_in_globals
get_dummy_profile_decorator_in_globals()
THIS_FILE_DIR = Path(__file__).parent.absolute()
log = get_logger(__name__)

# endregion[Constants]


class RowInstanceCache:

    def __init__(self, max_size: int = None) -> None:
        self._max_size = max_size
        self._model_class: type[Model] = None

    def log_cache_info(self) -> None:
        log.debug("Cache-Info for RowInstanceCache of %r: %r", self._model_class, self._model_class.get_by_id.cache_info())

    def __call__(self, model_class: type[Model]) -> type[Model]:
        self._model_class = model_class
        self._model_class.row_instance_cache = self
        model_class.get_by_id = lru_cache(maxsize=self._max_size)(super(model_class, model_class).get_by_id)

        return model_class


# region[Main_Exec]

if __name__ == '__main__':
    pass

# endregion[Main_Exec]
