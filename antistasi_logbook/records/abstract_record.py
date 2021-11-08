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

if TYPE_CHECKING:
    from antistasi_logbook.parsing.parser import RawRecord
    from antistasi_logbook.storage.models.models import LogRecord
# endregion[Imports]

# region [TODO]


# endregion [TODO]

# region [Logging]


# endregion[Logging]

# region [Constants]

THIS_FILE_DIR = Path(__file__).parent.absolute()

# endregion[Constants]


class MessageFormat(Enum):
    PRETTY = auto()


class RecordFamily(Flag):
    GENERIC = auto()
    ANTISTASI = auto()


class AbstractRecord(ABC):
    ___record_family___: RecordFamily = ...
    ___specificity___: int = ...

    # def __init_subclass__(cls) -> None:
    #     if not hasattr(cls, "___record_family___") or cls.___record_family___ is ...:
    #         # TODO: Custom Error!
    #         raise RuntimeError("Records need to implement the class attribute '___record_family___' and its value needs to be of type 'EntryFamily'.")
    #     if not hasattr(cls, "___specificity___") or cls.___specificity___ is ...:
    #         # TODO: Custom Error!
    #         raise RuntimeError("Records need to implement the class attribute '___specificity___' and its value needs to be of type 'int'.")

    @classmethod
    @abstractmethod
    def check(cls, raw_record: "RawRecord") -> bool:
        ...

    @abstractmethod
    def get_formated_message(self, format: "MessageFormat") -> str:
        ...


# region[Main_Exec]

if __name__ == '__main__':
    pass

# endregion[Main_Exec]
