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
from threading import Thread, RLock, Lock, Semaphore, Barrier, Timer, Event, Condition
from gidapptools import get_logger
if TYPE_CHECKING:
    from antistasi_logbook.updating.time_handling import TimeClock
    from gidapptools.gid_config.interface import GidIniConfig
    from antistasi_logbook.updating.updater import Updater
# endregion[Imports]

# region [TODO]


# endregion [TODO]

# region [Logging]


# endregion[Logging]

# region [Constants]

THIS_FILE_DIR = Path(__file__).parent.absolute()
log = get_logger(__name__)
# endregion[Constants]


class UpdateManager(Thread):
    config_name = "updating"

    def __init__(self,
                 updater: "Updater",
                 config: "GidIniConfig",
                 time_clock: "TimeClock",
                 pause_event: Event,
                 stop_event: Event) -> None:
        super().__init__(name=f"{self.__class__.__name__}Thread")
        self.updater = updater
        self.config = config
        self.time_clock = time_clock
        self.pause_event = pause_event
        self.stop_event = stop_event

    @ property
    def updates_enabled(self) -> bool:
        return self.config.get(self.config_name, "updates_enabled", default=False)

    def _pause_loop(self) -> None:
        log.debug("%r is paused", self)
        while self.pause_event.is_set() is True:
            sleep(1)
            if self.stop_event.is_set() is True:
                return
        log.debug("%r continues after being paused")

    def run(self) -> None:
        log.info("starting %r", self)

        while self.stop_event.is_set() is False:

            if self.pause_event.is_set() is True:
                self._pause_loop()
                continue

            if self.updates_enabled is True:
                self.updater()

            self.time_clock.wait_for_trigger()

    def shutdown(self) -> None:
        log.debug("shutting down %s", self)
        self.stop_event.set()
        self.join()
        log.debug("%s finished shutting down", self)


# region[Main_Exec]
if __name__ == '__main__':
    pass

# endregion[Main_Exec]
