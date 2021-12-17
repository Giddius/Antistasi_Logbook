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
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, wait, ALL_COMPLETED, Future
from importlib.machinery import SourceFileLoader
from gidapptools import get_logger, get_meta_config, get_meta_paths, get_meta_info
from dateutil.tz import UTC
from antistasi_logbook.storage.models.models import Server, LogFile, LogRecord
from threading import Event, Lock, RLock, Condition
from antistasi_logbook.utilities.locks import WRITE_LOCK
from gidapptools.gid_signal.interface import get_signal
from antistasi_logbook.updating.remote_managers import remote_manager_registry

if TYPE_CHECKING:
    from antistasi_logbook.gui.misc import UpdaterSignaler
    from gidapptools.gid_config.interface import GidIniConfig
    from antistasi_logbook.updating.info_item import InfoItem
    from antistasi_logbook.parsing.parsing_context import LogParsingContext
    from antistasi_logbook.storage.database import GidSqliteDatabase, GidSqliteApswDatabase
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


class Updater:
    """
    Class to run updates of log_files from the remote drive.

    """
    config_name: str = "updating"
    thread_prefix: str = "updating_threads"
    new_log_file_signal = get_signal("new_log_file")
    updated_log_file_signal = get_signal("updated_log_file")

    is_updating_event: Event = Event()

    __slots__ = ("config", "parsing_context_factory", "database", "parser", "stop_event", "pause_event", "thread_pool", "_to_close_contexts", "signaler")

    def __init__(self,
                 config: "GidIniConfig",
                 parsing_context_factory: Callable[["LogFile"], "LogParsingContext"],
                 database: "GidSqliteApswDatabase",
                 parser: object,
                 stop_event: Event,
                 pause_event: Event,
                 thread_pool_class: type["ThreadPoolExecutor"] = None,
                 signaler: "UpdaterSignaler" = None) -> None:
        self.config = config
        self.parsing_context_factory = parsing_context_factory
        self.database = database
        self.parser = parser
        self.stop_event = stop_event
        self.pause_event = pause_event
        self.thread_pool = ThreadPoolExecutor(self.max_threads, thread_name_prefix=self.thread_prefix) if thread_pool_class is None else thread_pool_class(self.max_threads, thread_name_prefix=self.thread_prefix)
        self._to_close_contexts = queue.Queue()
        self.signaler = signaler

    @property
    def max_threads(self) -> int:
        """
        Max amount of threads the thread_pool is allowed to use.

        Currently only has an effect when started.

        Returns:
            int: max amount of threads.
        """
        return self.config.get(self.config_name, "max_updating_threads", default=5)

    @property
    def remove_items_older_than_max_update_time_frame(self) -> bool:
        """
        If log-files that are older than the max update time-frame should be removed from the db.

        If no max_update_time_frame is set, then this is ignored.

        """
        if self.get_cutoff_datetime() is None:
            return False
        return self.config.get(self.config_name, "remove_items_older_than_max_update_time_frame", default=False)

    def get_cutoff_datetime(self) -> Optional[datetime]:
        """
        The max_update_time_frame converted to an absolute aware-datetime.

        Uses UTC as timezone.

        If no max_update_time_frame is set, None is returned.

        """
        delta = self.config.get(self.config_name, "max_update_time_frame", default=None)
        if delta is None:
            return None
        return datetime.now(tz=UTC) - delta

    def _create_new_log_file(self, server: "Server", remote_info: "InfoItem") -> LogFile:
        """
        Helper method to create a new `LogFile` instance.

        The new log_file is saved to the database.

        Args:
            server (Server): the `Server`-model instance the log_file belongs to.
            remote_info (InfoItem): The info_item that is received from the `RemoteStorageManager` implementation.

        Returns:
            LogFile: a new instance of the `LogFile`-model
        """
        new_log_file = LogFile(server=server, **remote_info.as_dict())
        new_log_file.save()
        self.new_log_file_signal.emit(log_file=new_log_file)
        return new_log_file

    def _update_log_file(self, log_file: LogFile, remote_info: "InfoItem") -> LogFile:
        """
        Helper Method to update an existing `LogFile`-model instance, from remote_info.

        The log_file is not updated to the database at that point.

        Args:
            log_file (LogFile): the existing `LogFile`-model instance
            remote_info (InfoItem): The info_item that is received from the `RemoteStorageManager` implementation.

        Returns:
            LogFile: the updated `logFile`-instance.
        """
        log_file.modified_at = remote_info.modified_at
        log_file.size = remote_info.size
        self.updated_log_file_signal.emit(log_file=log_file)
        return log_file

    def _get_updated_log_files(self, server: "Server"):
        """
        [summary]

        [extended_summary]

        Args:
            server (Server): [description]

        Returns:
            [type]: [description]
        """
        to_update_files = []
        current_log_files = {log_file.name: log_file for log_file in self.database.get_log_files(server=server)}
        cutoff_datetime = self.get_cutoff_datetime()

        for remote_info in server.get_remote_files():
            if cutoff_datetime is not None and remote_info.modified_at < cutoff_datetime:
                continue
            stored_file: LogFile = current_log_files.get(remote_info.name, None)

            if stored_file is None:
                to_update_files.append(self._create_new_log_file(server=server, remote_info=remote_info))

            elif stored_file.modified_at < remote_info.modified_at or stored_file.size < remote_info.size:
                to_update_files.append(self._update_log_file(log_file=stored_file, remote_info=remote_info))

            elif stored_file.last_parsed_datetime != stored_file.modified_at and stored_file.unparsable is False:
                to_update_files.append(stored_file)

        return sorted(to_update_files, key=lambda x: x.modified_at, reverse=True)

    def _handle_old_log_files(self, server: "Server") -> None:
        if self.remove_items_older_than_max_update_time_frame is False:
            return 0
        cutoff_datetime = self.get_cutoff_datetime()
        if cutoff_datetime is None:
            return 0
        amount_deleted = 0
        for log_file in server.log_files.select().where(LogFile.modified_at < cutoff_datetime):
            log.info("removing log-file %r of server %r", log_file, server)

            log_file.delete_instance(True)
            amount_deleted += 1
        return amount_deleted

    def process(self, server: "Server") -> None:

        def _do(_log_file: "LogFile"):
            sleep(random.uniform(0.1, 2.0))
            self.signaler.send_update_increment()
            if self.stop_event.is_set() is False:
                context = self.parsing_context_factory(log_file=_log_file)
                context.done_signal = self.signaler.send_update_increment
                with context:

                    log.debug("starting to parse %s", _log_file)
                    for processed_record in self.parser(context=context):
                        if self.stop_event.is_set() is True:
                            break
                        context.insert_record(processed_record)
                    context._dump_rest()

        tasks = []
        to_update_log_files = self._get_updated_log_files(server=server)
        self.signaler.send_update_info(len(to_update_log_files) * 3, server.name)
        for log_file in to_update_log_files:
            if self.stop_event.is_set() is False:
                sub_task = self.thread_pool.submit(_do, _log_file=log_file)
                tasks.append(sub_task)

        wait(tasks, return_when=ALL_COMPLETED, timeout=None)

    def before_updates(self):
        log.debug("emiting before_updates_signal")
        self.signaler.send_update_started()

    def after_updates(self):
        log.debug("emiting after_updates_signal")
        self.signaler.send_update_finished()
        remote_manager_registry.close()

    def update(self) -> None:
        if self.is_updating_event.is_set() is True:
            return
        self.is_updating_event.set()
        self.before_updates()
        try:
            self.database.session_meta_data.last_update_started_at = datetime.now(tz=UTC)
            for server in self.database.get_all_server():
                if server.is_updatable() is False:
                    continue
                if self.stop_event.is_set() is False:

                    while self.pause_event.is_set() is True:
                        sleep(0.25)
                    log.info("STARTED updating %r", server)
                    self.process(server=server)
                    log.info("FINISHED updating server %r", server)

            amount_deleted = 0
            for server in self.database.get_all_server():
                if self.stop_event.is_set() is False:
                    log.info("checking old log_files to delete for server %r", server)
                    amount_deleted += self._handle_old_log_files(server=server)

            if amount_deleted > 0:
                if self.stop_event.is_set() is False:
                    self.database.vacuum()
                    self.database.optimize()
            self.database.session_meta_data.last_update_finished_at = datetime.now(tz=UTC)

        finally:
            self.is_updating_event.clear()
            self.after_updates()

    def __call__(self) -> Any:
        return self.update()

    def shutdown(self) -> None:
        self.thread_pool.shutdown(wait=True, cancel_futures=False)


# region[Main_Exec]
if __name__ == '__main__':
    pass

# endregion[Main_Exec]
