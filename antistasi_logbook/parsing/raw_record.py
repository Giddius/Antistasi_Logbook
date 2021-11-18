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
from antistasi_logbook.storage.models.models import LogFile
if TYPE_CHECKING:
    from antistasi_logbook.parsing.parser import RecordLine, RecordClass
# endregion[Imports]

# region [TODO]


# endregion [TODO]

# region [Logging]


# endregion[Logging]

# region [Constants]

THIS_FILE_DIR = Path(__file__).parent.absolute()

# endregion[Constants]


class RawRecord:

    __slots__ = ("lines", "_is_antistasi_record", "start", "end", "_content", "parsed_data", "record_class", "log_file")

    def __init__(self, lines: Iterable["RecordLine"], log_file: LogFile) -> None:
        self.log_file = log_file
        self.lines = tuple(lines)
        self._content: str = None
        self._is_antistasi_record: bool = None
        self.start: int = self.lines[0].start
        self.end: int = self.lines[-1].start
        self.parsed_data: dict[str, Any] = None
        self.record_class: "RecordClass" = None

    @property
    def content(self) -> str:
        if self._content is None:
            self._content = ' '.join(line.content.lstrip(" >>>").rstrip() for line in self.lines if line.content)
        return self._content

    @property
    def is_antistasi_record(self) -> bool:
        if self._is_antistasi_record is None:
            self._is_antistasi_record = "| antistasi |" in self.content.casefold()
        return self._is_antistasi_record

    @property
    def unformatted_content(self) -> str:
        return '\n'.join(line.content for line in self.lines)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(start={self.start!r}, end={self.end!r}, content={self.content!r}, is_antistasi_record={self.is_antistasi_record!r}, lines={self.lines!r})"

    def __eq__(self, o: object) -> bool:
        if isinstance(o, self.__class__):
            return self.lines == o.lines and self.content == o.content and self.is_antistasi_record == o.is_antistasi_record and self.start == o.start and self.end == o.end


# region[Main_Exec]
if __name__ == '__main__':
    pass

# endregion[Main_Exec]
