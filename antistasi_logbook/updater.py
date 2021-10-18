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
from antistasi_logbook.webdav.webdav_manager import WebdavManager
from antistasi_logbook.items.log_file import LogFile
from antistasi_logbook.items.server import Server
from antistasi_logbook.items.game_map import GameMap
from antistasi_logbook.storage.storage_db import StorageDB
from antistasi_logbook.parsing.parser import Parser
from gidapptools.general_helper.timing import time_func
import atexit
from threading import Thread, Event, Condition, Lock, RLock, Semaphore, Barrier
# endregion[Imports]

# region [TODO]


# endregion [TODO]

# region [Logging]


# endregion[Logging]

# region [Constants]

THIS_FILE_DIR = Path(__file__).parent.absolute()

# endregion[Constants]


class Updater(Thread):
    update_lock = Lock()

    def __init__(self, interval: Union[timedelta, int], database: StorageDB, webdav_manager: "WebdavManager", thread_pool: ThreadPoolExecutor = None) -> None:
        super().__init__(name=f"{self.__class__.__name__}_thread")
        self.interval = timedelta(seconds=interval) if isinstance(interval, int) else interval
        self.database = database
        self.webdav_manager = webdav_manager
        self.parser = Parser()
        self.thread_pool = ThreadPoolExecutor(10) if thread_pool is None else thread_pool
        self.close_event = Event()
        self.update_requested_condition = Condition()
        self.interval_number = 0
        self._next_scheduled_run_at: datetime = None
        atexit.register(self.thread_pool.shutdown)

    def set_next_scheduled_run(self) -> None:
        self._next_scheduled_run_at = datetime.now(tz=timezone.utc) + self.interval

    @property
    def seconds_to_next_run(self) -> float:
        if self._next_scheduled_run_at is None:
            self.set_next_scheduled_run()
        now = datetime.now(tz=timezone.utc)
        delta = self._next_scheduled_run_at - now
        seconds = delta.total_seconds()
        if seconds <= 0:
            return 0
        return seconds

    def _update_server(self, server: "Server"):
        list(self.thread_pool.map(self.parser.parse_log_file, server.update()))

    def _update(self) -> None:
        with self.update_lock:

            for server in self.webdav_manager.get_server_folder().values():
                if server.name == "Mainserver_1":
                    self._update_server(server)

    def run(self) -> None:
        with self.update_requested_condition:
            self._update()
        while not self.close_event.is_set():
            with self.update_requested_condition:
                self.update_requested_condition.wait(timeout=self.seconds_to_next_run)
                if self.close_event.is_set():
                    break
                self.interval_number += 1
                self.set_next_scheduled_run()
                self._update()
                print(f"interval {self.interval_number!r} done!")
        print("closing updated down!")

    def close(self) -> None:
        self.close_event.set()
        self.join(timeout=self.interval.total_seconds() / 2)

    def update(self) -> None:
        if self.is_alive():

            if self.update_requested_condition.acquire(timeout=10) is True:
                try:
                    self.update_requested_condition.notify_all()
                finally:
                    self.update_requested_condition.release()
            else:
                return
        else:
            self._update()


# region[Main_Exec]
if __name__ == '__main__':
    pass

# endregion[Main_Exec]
