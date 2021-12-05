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
from threading import Thread, Lock, RLock, Event, Condition
from dateutil.tz import UTC
from gidapptools import get_meta_config
from antistasi_logbook import setup
from gidapptools import get_logger
if TYPE_CHECKING:
    from gidapptools.gid_config.interface import GidIniConfig
# endregion[Imports]

# region [TODO]


# endregion [TODO]

# region [Logging]


# endregion[Logging]

# region [Constants]

from gidapptools.general_helper.timing import get_dummy_profile_decorator_in_globals
get_dummy_profile_decorator_in_globals()
log = get_logger(__name__)
THIS_FILE_DIR = Path(__file__).parent.absolute()
CONFIG = get_meta_config().get_config("general")
# endregion[Constants]


def _default_now_factory(tz: timezone) -> datetime:
    return datetime.now(tz=tz)


TRIGGER_RESULT_TYPE = Union[int, float, timedelta]
TRIGGER_INTERVAL_TYPE = Union[TRIGGER_RESULT_TYPE, Callable[[], TRIGGER_RESULT_TYPE]]


class TimeClock:

    def __init__(self,
                 config: "GidIniConfig",
                 stop_event: Event = None) -> None:
        self.time_zone = UTC
        self.config = config
        self.stop_event = Event() if stop_event is None else stop_event
        self.next_trigger: datetime = None

    @property
    def now(self) -> datetime:
        return datetime.now(tz=UTC)

    @property
    def trigger_interval(self) -> timedelta:
        return self.config.get("updating", "update_interval", default=timedelta(seconds=600))

    def wait_for_trigger(self):
        if self.stop_event.is_set():
            return
        next_trigger = self.get_next_trigger()
        seconds_left = max((next_trigger - self.now).total_seconds(), 1)
        if seconds_left <= 5:
            sleep_durations = [seconds_left]
        else:
            amount, rest = divmod(seconds_left, 5)

            sleep_durations = ([5] * int(amount)) + [rest]
        for part in sleep_durations:
            if self.stop_event.is_set():
                return
            sleep(part)
        if self.next_trigger > self.now:
            return self.wait_for_trigger()
        return

    def reset(self) -> None:
        self.next_trigger = self.now + self.trigger_interval

    def get_next_trigger(self) -> datetime:
        if self.next_trigger is None:
            self.next_trigger = self.now + self.trigger_interval

        if self.next_trigger < self.now:
            self.next_trigger = self.next_trigger + self.trigger_interval

        return self.next_trigger

# region[Main_Exec]


if __name__ == '__main__':
    pass

# endregion[Main_Exec]
