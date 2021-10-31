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
from antistasi_logbook import setup
setup()
import atexit
from time import sleep, process_time, process_time_ns, perf_counter, perf_counter_ns
from io import BytesIO, StringIO, TextIOWrapper
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
from gidapptools import get_meta_config
import mmap
from threading import Thread, Event, Condition
from antistasi_logbook.storage.models.models import Server, LogFile
if TYPE_CHECKING:

    from antistasi_logbook.updating.remote_managers import AbstractRemoteStorageManager, InfoItem
# endregion[Imports]

# region [TODO]

# Not sure if using stop_event via an Event is the right way and if it is implemented the right way here.

# endregion [TODO]

# region [Logging]


# endregion[Logging]

# region [Constants]

THIS_FILE_DIR = Path(__file__).parent.absolute()
CONFIG = get_meta_config().get_config("general")
# endregion[Constants]


class IntervallKeeper:

    def __init__(self, stop_event: Event) -> None:
        self.stop_event = stop_event
        self.next_datetime: datetime = None

    @property
    def intervall(self) -> timedelta:
        seconds = CONFIG.get("updater", "update_intervall", default=300)
        return timedelta(seconds=seconds)

    @property
    def now(self) -> datetime:
        return datetime.now(tz=timezone.utc)

    def sleep_to_next(self) -> bool:
        seconds_left = (next(self) - self.now).total_seconds()
        sleep_seconds = min([seconds_left, 5])
        if self.stop_event.is_set():
            return False
        sleep(sleep_seconds)

        if self.next_datetime > self.now:
            return self.sleep_to_next()
        return True

    def reset(self) -> None:
        self.next_datetime = self.now + self.intervall

    def __next__(self) -> datetime:
        if self.next_datetime is None:
            self.next_datetime = self.now + self.intervall
        if self.next_datetime < self.now:
            self.next_datetime = self.next_datetime + self.intervall
        return self.next_datetime


class Updater:
    remote_manager_classes: dict[str, type["AbstractRemoteStorageManager"]] = {}

    def __init__(self, parser) -> None:
        self.parser = parser

    def get_cutoff_datetime(self) -> Optional[datetime]:
        days = CONFIG.get("updater", "max_update_time_frame_days", default=None)
        if days is None:
            return None
        return datetime.now(tz=timezone.utc) - timedelta(days=days)

    @classmethod
    def register_remote_manager_class(cls, remote_manager_class: type["AbstractRemoteStorageManager"]) -> None:
        name = remote_manager_class.__name__
        if name not in cls.remote_manager_classes:
            cls.remote_manager_classes[name] = remote_manager_class

    def _get_remote_manager(self, server: "Server") -> "AbstractRemoteStorageManager":
        manager_class = self.remote_manager_classes[server.remote_storage.manager_type]
        return manager_class.from_remote_storage_item(server.remote_storage)

    def _create_new_log_file(self, server: "Server", remote_info: "InfoItem") -> LogFile:
        new_log_file = LogFile(server=server, **remote_info.as_dict())
        new_log_file.size = 0
        new_log_file.save()
        new_log_file.size = remote_info.size
        return new_log_file

    def _update_log_file(self, log_file: LogFile, remote_info: "InfoItem") -> LogFile:
        log_file.modified_at = remote_info.modified_at
        log_file.size = remote_info.size
        return log_file

    def _get_updated_log_files(self, server: "Server") -> Generator["LogFile", None, None]:

        current_log_files = server.get_current_log_files()
        cutoff_datetime = self.get_cutoff_datetime()
        for remote_info in server.get_remote_files(server.remote_manager):
            if cutoff_datetime is not None and remote_info.modified_at < cutoff_datetime:
                continue
            stored_file: LogFile = current_log_files.get(remote_info.name, None)

            if stored_file is None:
                yield self._create_new_log_file(server=server, remote_info=remote_info)

            elif stored_file.modified_at < remote_info.modified_at or stored_file.size < remote_info.size:
                yield self._update_log_file(log_file=stored_file, remote_info=remote_info)

    def update_server(self, server: "Server") -> None:
        if server.is_updatable() is False:
            return

        server.ensure_remote_manager(remote_manager=self._get_remote_manager(server))
        with ThreadPoolExecutor() as pool:
            list(pool.map(self.parser, self._get_updated_log_files(server=server)))

        # for log_file in self._get_updated_log_files(server=server):
        #     self.parser(log_file)

    def __call__(self, server: "Server") -> Any:
        return self.update_server(server)


class UpdateThread(Thread):

    def __init__(self, updater: "Updater", server_model: "Server", stop_event: Event = None) -> None:
        super().__init__(name="updater_thread")
        self.updater = updater
        self.server_model = server_model
        self.stop_event = Event() if stop_event is None else stop_event
        self.intervaller = IntervallKeeper(self.stop_event)

    def _update(self) -> None:
        for server in self.server_model.select():
            if self.stop_event.is_set():
                return
            self.updater(server)

    def _update_task(self) -> None:
        while not self.stop_event.is_set():
            self._update()
            self.intervaller.sleep_to_next()


# region[Main_Exec]
if __name__ == '__main__':
    x = 125181 + (27239 * 2)
    print(x)
# endregion[Main_Exec]