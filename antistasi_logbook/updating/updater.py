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
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, wait, ALL_COMPLETED, Future
from importlib.machinery import SourceFileLoader
from gidapptools import get_meta_config
import mmap
from threading import Thread, Event, Condition
from antistasi_logbook.errors import UpdateExceptionHandler
from antistasi_logbook.storage.models.models import Server, LogFile, LogRecord
from antistasi_logbook.parsing.parser import Parser
from rich.console import Console as RichConsole
from antistasi_logbook.utilities.locks import UPDATE_LOCK, UPDATE_STOP_EVENT
from antistasi_logbook.utilities.misc import NoThreadPoolExecutor
from gidapptools.gid_signal.interface import get_signal

if TYPE_CHECKING:

    from antistasi_logbook.updating.remote_managers import AbstractRemoteStorageManager, InfoItem
    from antistasi_logbook.storage.database import GidSQLiteDatabase, GidSqliteQueueDatabase
# endregion[Imports]

# region [TODO]

# Not sure if using stop_event via an Event is the right way and if it is implemented the right way here.

# endregion [TODO]

# region [Logging]


# endregion[Logging]

# region [Constants]
from gidapptools.general_helper.timing import get_dummy_profile_decorator_in_globals
get_dummy_profile_decorator_in_globals()
THIS_FILE_DIR = Path(__file__).parent.absolute()
CONFIG = get_meta_config().get_config("general")
CONSOLE = RichConsole(soft_wrap=True)
# endregion[Constants]


def dprint(*args, **kwargs):
    CONSOLE.print(*args, **kwargs)
    CONSOLE.rule()


print = dprint


class FakeLogger:
    def __init__(self) -> None:
        self.debug = dprint
        self.info = dprint
        self.warning = dprint
        self.error = dprint
        self.critical = dprint


log = FakeLogger()


class IntervallKeeper:

    def __init__(self, stop_event: Event) -> None:
        self.stop_event = stop_event
        self.next_datetime: datetime = None

    @property
    def intervall(self) -> timedelta:
        return CONFIG.get("updater", "update_intervall", default=timedelta(seconds=300))

    @property
    def now(self) -> datetime:
        return datetime.now(tz=timezone.utc)

    def sleep_to_next(self) -> bool:
        seconds_left = (next(self) - self.now).total_seconds()
        sleep_seconds = max([seconds_left, 1])
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
    threads_prefix = "log_file_update_"
    config_name = "updater"
    log_file_updated_signal = get_signal("log_file_updated")

    def __init__(self, database: "GidSqliteQueueDatabase", parser: Parser = None, thread_pool_class: type[ThreadPoolExecutor] = None) -> None:
        self.database = database
        self.parser = Parser(database=self.database) if parser is None else parser
        if thread_pool_class is None:
            thread_pool_class = ThreadPoolExecutor
        self.thread_pool = thread_pool_class(max_workers=self.max_threads, thread_name_prefix=self.threads_prefix)
        self.tasks: list[Future] = []

    @property
    def max_threads(self) -> Optional[int]:
        return CONFIG.get(self.config_name, "max_threads", default=os.cpu_count())

    @property
    def remove_items_older_than_max_update_time_frame(self) -> bool:
        if self.get_cutoff_datetime() is None:
            return False
        return CONFIG.get(self.config_name, "remove_items_older_than_max_update_time_frame", default=False)

    def get_cutoff_datetime(self) -> Optional[datetime]:
        days = CONFIG.get(self.config_name, "max_update_time_frame_days", default=None)
        if days is None:
            return None
        return datetime.now(tz=timezone.utc) - timedelta(days=days)

    @classmethod
    def register_remote_manager_class(cls, remote_manager_class: type["AbstractRemoteStorageManager"]) -> None:
        name = remote_manager_class.___remote_manager_name___
        if name not in cls.remote_manager_classes:
            cls.remote_manager_classes[name] = remote_manager_class

    def _get_remote_manager(self, server: "Server") -> "AbstractRemoteStorageManager":
        manager_class = self.remote_manager_classes[server.remote_storage.manager_type]
        return manager_class.from_remote_storage_item(server.remote_storage)

    def _create_new_log_file(self, server: "Server", remote_info: "InfoItem") -> LogFile:
        new_log_file = LogFile(server=server, size=0, **{k: v for k, v in remote_info.as_dict().items() if k not in {"size"}})

        new_log_file.save()

        new_log_file.size = remote_info.size
        self.log_file_updated_signal.emit(new_log_file)
        return new_log_file

    def _update_log_file(self, log_file: LogFile, remote_info: "InfoItem") -> LogFile:
        log_file.modified_at = remote_info.modified_at
        log_file.size = remote_info.size
        self.log_file_updated_signal.emit(log_file)
        return log_file

    @profile
    def _get_updated_log_files(self, server: "Server"):
        to_update_files = []
        current_log_files = server.get_current_log_files()
        cutoff_datetime = self.get_cutoff_datetime()
        for remote_info in server.get_remote_files(server.remote_manager):
            if cutoff_datetime is not None and remote_info.modified_at < cutoff_datetime:
                continue
            stored_file: LogFile = current_log_files.get(remote_info.name, None)

            if stored_file is None:
                to_update_files.append(self._create_new_log_file(server=server, remote_info=remote_info))

            elif stored_file.modified_at < remote_info.modified_at or stored_file.size < remote_info.size:
                to_update_files.append(self._update_log_file(log_file=stored_file, remote_info=remote_info))
        return sorted(to_update_files, key=lambda x: x.modified_at, reverse=True)

    def _handle_old_log_files(self, server: "Server") -> None:
        if self.remove_items_older_than_max_update_time_frame is False:
            return
        cutoff_datetime = self.get_cutoff_datetime()
        if cutoff_datetime is None:
            return

        for log_file in server.log_files.select().where(LogFile.modified_at < cutoff_datetime):
            print(f"removing log_file {log_file.name!r} of server {log_file.server.name!r}")
            q = LogRecord.delete().where(LogRecord.log_file == log_file)
            q.execute()

            log_file.delete_instance()

    def update_server(self, server: "Server") -> None:
        def _create_done_callback(_idx: int, _amount: int, _log_file: "LogFile"):
            def _inner(future: Future):
                print(f"<[b green]{_idx}[/b green]/[b red]{_amount}[/b red]> FINISHED PROCESSING LOGFILE", _log_file)
            return _inner
        server.ensure_remote_manager(remote_manager=self._get_remote_manager(server))
        log_files = self._get_updated_log_files(server=server)
        amount = len(log_files)
        for idx, log_file in enumerate(log_files):
            print(f"<[b green]{idx}[/b green]/[b red]{amount}[/b red]> STARTING PROCESSING LOGFILE", log_file)
            task = self.thread_pool.submit(self.parser.process, log_file)

            self.tasks.append(task)
        # for log_file in updated_log_files:
        #     sleep(0.1)
        #     self.parser(log_file)

        self._handle_old_log_files(server=server)

        return True

    def __call__(self, server: "Server") -> None:
        if server.is_updatable() is False:
            return False

        return self.update_server(server)

    def close(self) -> None:
        self.thread_pool.shutdown(wait=True, cancel_futures=False)
        self.parser.close()


class UpdateThread(Thread):
    config_name = "updater"
    thread_name = "updater_thread"

    def __init__(self, database: "GidSqliteQueueDatabase", updater: "Updater") -> None:
        super().__init__(name=self.thread_name)
        self.updater = updater
        self.database = database

        self.intervaller = IntervallKeeper(UPDATE_STOP_EVENT)
        self.exception_handler = UpdateExceptionHandler()
        self.is_updating: bool = False

    @ property
    def updates_enabled(self) -> bool:
        return CONFIG.get(self.config_name, "updates_enabled", default=False)

    @ contextmanager
    def set_is_updating(self) -> None:
        self.is_updating = True
        yield
        self.is_updating = False

    def _update(self) -> None:
        self.before_update()
        try:
            for server in tuple(Server.select()):
                if UPDATE_STOP_EVENT.is_set():
                    return
                print(f"updating server {server.name!r}")

                self.updater(server)

        # except Exception as error:
        #     self.exception_handler.handle_exception(error)
        finally:
            self.after_update()

    def _update_task(self) -> None:
        while not UPDATE_STOP_EVENT.is_set():
            if self.updates_enabled is True:
                with self.set_is_updating():
                    self._update()
            if UPDATE_STOP_EVENT.is_set():
                break
            self.intervaller.sleep_to_next()

    def before_update(self) -> None:
        print("connecting")
        self.database.connect(reuse_if_open=True)

    def after_update(self) -> None:
        if not isinstance(self.updater.thread_pool, NoThreadPoolExecutor):
            wait(self.updater.tasks, timeout=None, return_when=ALL_COMPLETED)
        self.database.stop()
        self.database.start()

    def run(self) -> None:
        self._update_task()

    def shutdown(self) -> bool:
        UPDATE_STOP_EVENT.set()
        self.updater.close()
        self.join()
        while self.is_alive() is True:
            sleep(0.1)
        UPDATE_STOP_EVENT.clear()


def get_updater(database: "GidSqliteQueueDatabase", use_fake_webdav_manager: bool = False, **kwargs) -> "Updater":
    from antistasi_logbook.updating.remote_managers import ALL_REMOTE_MANAGERS_CLASSES, FakeWebdavManager, WebdavManager
    if use_fake_webdav_manager is True:
        ALL_REMOTE_MANAGERS_CLASSES = set(i for i in ALL_REMOTE_MANAGERS_CLASSES if i is not WebdavManager)
        FakeWebdavManager.fake_files_folder = Path(r"D:\Dropbox\hobby\Modding\Programs\Github\My_Repos\Antistasi_Logbook\test\data\fake_log_files")
        FakeWebdavManager.info_file = Path(r"D:\Dropbox\hobby\Modding\Programs\Github\My_Repos\Antistasi_Logbook\test\data\fake_info_data.json")
        _ = FakeWebdavManager.info_data
        ALL_REMOTE_MANAGERS_CLASSES.add(FakeWebdavManager)
    updater = Updater(database=database, **kwargs)
    for remote_manager_class in ALL_REMOTE_MANAGERS_CLASSES:
        updater.register_remote_manager_class(remote_manager_class)
    return updater


def get_update_thread(database: "GidSqliteQueueDatabase", use_fake_webdav_manager: bool = False, ** kwargs) -> "UpdateThread":
    updater = get_updater(database=database, use_fake_webdav_manager=use_fake_webdav_manager, ** kwargs)
    update_thread = UpdateThread(database=database, updater=updater)
    return update_thread


# region[Main_Exec]
if __name__ == '__main__':
    x = 125181 + (27239 * 2)
    print(x)
# endregion[Main_Exec]
