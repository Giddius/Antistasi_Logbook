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

import subprocess
import inspect

from time import sleep, process_time, process_time_ns, perf_counter, perf_counter_ns
from io import BytesIO, StringIO
from abc import ABC, ABCMeta, abstractmethod
from copy import copy, deepcopy
from enum import Enum, Flag, auto, unique
from pprint import pprint, pformat
from pathlib import Path
from string import Formatter, digits, printable, whitespace, punctuation, ascii_letters, ascii_lowercase, ascii_uppercase
from timeit import Timer
from typing import (TYPE_CHECKING, TypeVar, TypeGuard, TypeAlias, Final, TypedDict, Generic, Union, Optional, ForwardRef, final,
                    no_type_check, no_type_check_decorator, overload, get_type_hints, cast, Protocol, runtime_checkable, NoReturn, NewType, Literal, AnyStr, IO, BinaryIO, TextIO, Any)
from collections import Counter, ChainMap, deque, namedtuple, defaultdict
from collections.abc import (AsyncGenerator, AsyncIterable, AsyncIterator, Awaitable, ByteString, Callable, Collection, Container, Coroutine, Generator,
                             Hashable, ItemsView, Iterable, Iterator, KeysView, Mapping, MappingView, MutableMapping, MutableSequence, MutableSet, Reversible, Sequence, Set, Sized, ValuesView)
from zipfile import ZipFile, ZIP_LZMA
from datetime import datetime, timezone, timedelta
from tempfile import TemporaryDirectory
from textwrap import TextWrapper, fill, wrap, dedent, indent, shorten
from functools import wraps, partial, lru_cache, singledispatch, total_ordering, cached_property, cache
from contextlib import contextmanager, asynccontextmanager, nullcontext, closing, ExitStack, suppress
from statistics import mean, mode, stdev, median, variance, pvariance, harmonic_mean, median_grouped
from urllib.parse import urlparse
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, Future, wait, as_completed, ALL_COMPLETED, FIRST_EXCEPTION, FIRST_COMPLETED


if sys.version_info >= (3, 11):
    from typing import Self
else:
    from typing_extensions import Self

if TYPE_CHECKING:
    ...

# endregion [Imports]

# region [TODO]


# endregion [TODO]

# region [Logging]


# endregion [Logging]

# region [Constants]

THIS_FILE_DIR = Path(__file__).parent.absolute()

# endregion [Constants]


class PairedReader(deque):
    # TODO: Find better name for this class.
    # TODO: Maybe add __repr__.

    def __init__(self, file_item: TextIO, chunk_size: int = 512000, *, max_bytes: int = None, max_chunks: int = None):
        self.file_item = file_item
        self.chunk_size = chunk_size
        self.max_bytes = max_bytes
        self.max_chunks = max_chunks
        self.chunks_read: int = 0
        self._inital_loaded: bool = False
        super().__init__(maxlen=2)

    @property
    def bytes_read(self) -> int:
        return self.file_item.tell()

    @property
    def finished(self) -> bool:
        if self[1] == "":
            return True

        if self.max_chunks is not None and self.chunks_read >= self.max_chunks:
            return True

        if self.max_bytes is not None and self.bytes_read >= self.max_bytes:
            return True

        return False

    def _read_chunk(self) -> None:
        self.append(self.file_item.read(self.chunk_size))
        self.chunks_read += 1

    def _load_initial(self) -> None:
        if self._inital_loaded is False:
            while len(self) < self.maxlen:
                self._read_chunk()
            self._inital_loaded = True

    def get_text(self) -> str:
        return self[0] + self[1]

    def read_next(self) -> None:
        if self._inital_loaded is False:
            self._load_initial()

        else:
            self._read_chunk()

    def __iter__(self) -> Generator[str, None, None]:
        self._load_initial()
        yield self.get_text()
        while self.finished is False:
            yield self.get_text()
            self.read_next()

    def __str__(self) -> str:
        return self.get_text()


# region [Main_Exec]
if __name__ == '__main__':
    pass

# endregion [Main_Exec]
