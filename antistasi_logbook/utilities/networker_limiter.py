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

from time import sleep, process_time, process_time_ns, perf_counter, perf_counter_ns, time
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
from threading import Lock, RLock, Condition, Event, Semaphore, Barrier, BoundedSemaphore, Thread, Timer as SingleShotTimer

if sys.version_info >= (3, 11):
    from typing import Self
else:
    from typing_extensions import Self

if TYPE_CHECKING:
    ...

# endregion[Imports]

# region [TODO]


# endregion [TODO]

# region [Logging]


# endregion[Logging]

# region [Constants]

THIS_FILE_DIR = Path(__file__).parent.absolute()

# endregion[Constants]


class RefresherThread(Thread):

    def __init__(self, parent: "NetworkSpeedLimiter") -> None:
        super().__init__(target=None, name="RefresherThread", args=(), kwargs=None, daemon=None)
        self._target_signal: Callable[[int], int] = parent._refresh_available
        self._stop_event: Event = parent._stop_event

    def run(self) -> None:
        last_refresh_timestamp: int = int(time())

        while self._stop_event.wait(timeout=1.0) is False:
            last_refresh_timestamp: int = self._target_signal(last_refresh_timestamp)

        print(f"stopping {self!r}", flush=True)


class NetworkSpeedLimiter:

    def __init__(self, max_bytes_per_second: int = None) -> None:
        self._max_bytes_per_second = max_bytes_per_second
        self._lock: Lock = Lock()
        self._stop_event: Event = Event()

        self._max_available_bytes: int = self._max_bytes_per_second * 5
        self._available_bytes: int = self.max_bytes_per_second

        self._refresher: Thread = RefresherThread(self)
        self._taken_bytes = 0

    @property
    def max_bytes_per_second(self) -> int:
        return self._max_bytes_per_second

    def change_max_bytes_per_second(self, new_value: int) -> None:
        with self._lock:
            if new_value == self._max_bytes_per_second:
                return

            self._max_bytes_per_second = new_value
            self._max_available_bytes = self._max_bytes_per_second * 5

    def _refresh_available(self, old_timestamp: int) -> int:
        with self._lock:
            new_timestamp = int(time())
            past_seconds = new_timestamp - old_timestamp
            amount_to_add = self.max_bytes_per_second * past_seconds
            # print(f"adding {amount_to_add!r} for {past_seconds!r} past seconds and {self.max_bytes_per_second!r} max bytes per second", flush=True)
            self._available_bytes = min((self._available_bytes + amount_to_add), self._max_available_bytes)
            # print(f"new amount available: {self._available_bytes!r}")
        return new_timestamp

    def request_bytes_to_download(self, amount: int) -> bool:
        if self._refresher.is_alive() is False:
            raise RuntimeError(f"{self!r} has already shut down!")
        if amount > self.max_bytes_per_second:
            raise ValueError(f"Amount of bytes requested ({amount!r}) is greater than allowed of bytes_per_second {self.max_bytes_per_second!r}")

        while True:

            with self._lock:
                new_amount = self._available_bytes - amount
                if new_amount >= 0:
                    self._available_bytes = new_amount
                    self._taken_bytes += amount
                    # print(f"!! new amount available: {self._available_bytes!r}", flush=True)
                    break

            sleep(0.25)

        return True

    def start_up(self) -> Self:
        self._refresher.start()
        return self

    def shutdown(self) -> None:
        self._stop_event.set()
        self._refresher.join()


def multiple_download(_limiter, amount: int, idx: int):

    for i in range(amount):
        _limiter.request_bytes_to_download(100)
        sleep(random.random() / 10)


def check():
    limiter = NetworkSpeedLimiter(1000)
    limiter._refresher.start()
    _s = perf_counter()
    with ThreadPoolExecutor() as pool:
        list(pool.map(partial(multiple_download, limiter, 50), range(10)))
    _e = perf_counter()
    _s_t = round(_e - _s, ndigits=3)
    _s_p_b = (100 * 50 * 10) // _s_t
    print()
    print(f"{limiter._taken_bytes=}")
    print(f"downloading 10x5000 bytes (50.000) took {_s_t} s or {_s_p_b} b per s")
    limiter.shutdown()


# region[Main_Exec]


if __name__ == '__main__':
    check()
# endregion[Main_Exec]
