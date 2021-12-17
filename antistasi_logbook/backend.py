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
from gidapptools.general_helper.timing import time_execution
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
from antistasi_logbook.storage.models.models import LogFile, Server, LogRecord, LogLevel, AntstasiFunction, DatabaseMetaData, GameMap, Mod, LogFileAndModJoin, RecordClass, RemoteStorage
from antistasi_logbook.parsing.parsing_context import LogParsingContext
from antistasi_logbook.parsing.foreign_key_cache import ForeignKeyCache
from antistasi_logbook.regex.regex_keeper import SimpleRegexKeeper
from antistasi_logbook.records.record_class_manager import RecordClassManager, RECORD_CLASS_TYPE
from antistasi_logbook.storage.database import GidSqliteApswDatabase
from dateutil.tz import UTC
from peewee import DatabaseProxy
from antistasi_logbook.updating.time_handling import TimeClock
from antistasi_logbook.utilities.misc import Version
from threading import Event, Condition, RLock, Thread, Barrier, Semaphore, Timer, Lock
from gidapptools import get_meta_info, get_meta_paths, get_logger, get_meta_config, get_main_logger
from antistasi_logbook.updating.update_manager import UpdateManager
from antistasi_logbook.updating.remote_managers import remote_manager_registry
from antistasi_logbook.updating.updater import Updater
from antistasi_logbook.parsing.parsing_context import LogParsingContext
from antistasi_logbook.parsing.parser import Parser
from antistasi_logbook.parsing.foreign_key_cache import ForeignKeyCache
from antistasi_logbook.parsing.record_processor import RecordProcessor, RecordInserter
from weakref import WeakSet
import attr
from gidapptools.gid_signal.interface import get_signal
from concurrent.futures import wait, ALL_COMPLETED
from antistasi_logbook.utilities.locks import FILE_LOCKS
if TYPE_CHECKING:
    from gidapptools.gid_config.interface import GidIniConfig
    from gidapptools.gid_signal.signals import abstract_signal
    from antistasi_logbook.gui.misc import UpdaterSignaler

# endregion[Imports]

# region [TODO]


# endregion [TODO]

# region [Logging]


# endregion[Logging]

# region [Constants]

THIS_FILE_DIR = Path(__file__).parent.absolute()
META_INFO = get_meta_info()
META_PATHS = get_meta_paths()
CONFIG = get_meta_config().get_config("general")

log = get_logger(__name__)
# endregion[Constants]


@attr.s(auto_detect=True, auto_attribs=True, slots=True, frozen=True, kw_only=True)
class Events:
    """
    Simple class to have doted access to an collection of events, that is static.
    """
    stop: Event = attr.ib(default=Event())
    pause: Event = attr.ib(default=Event())


@attr.s(auto_detect=True, auto_attribs=True, slots=True, frozen=True, kw_only=True)
class Locks:
    """
    Simple class to have doted access to an collection of locks, that is static.

    """
    updating: Lock = attr.ib(default=Lock())


@attr.s(auto_detect=True, auto_attribs=True, slots=True, frozen=True, kw_only=True)
class Signals:
    """
    Simple class to have doted access to signals, that are static.

    Signal implementation could be replaced with QSignal in the future.
    """
    new_log_file: "abstract_signal" = get_signal("new_log_file")
    updated_log_file: "abstract_signal" = get_signal("updated_log_file")
    new_log_record: "abstract_signal" = get_signal("new_log_record")
    update_started: "abstract_signal" = get_signal("update_started")


class NoneSignaler:

    def send_update_started(self):
        pass

    def send_update_finished(self):
        pass

    def send_update_increment(self):
        pass

    def send_update_info(self, amount, name):
        pass


class Backend:

    """
    Class to create the complete backend.

    Is used to simplify the complex setup of the backend.

    Args:
        database (`GidSqliteDatabase`): [description]
        config (`GidIniConfig`): [description]
        database_proxy (`peewee.DatabaseProxy`): [description]

    """
    all_parsing_context: WeakSet["LogParsingContext"] = WeakSet()

    def __init__(self, database: "GidSqliteApswDatabase", config: "GidIniConfig", update_signaler: "UpdaterSignaler" = NoneSignaler()) -> None:
        self.events = Events()
        self.locks = Locks()
        self.signals = Signals()
        self.config = config
        self.database = database
        self.update_signaler = update_signaler
        self.foreign_key_cache = self.database.foreign_key_cache
        self.record_class_manager = RecordClassManager(foreign_key_cache=self.foreign_key_cache)

        self.time_clock = TimeClock(config=self.config, stop_event=self.events.stop)
        self.remote_manager_registry = remote_manager_registry
        self.record_processor = RecordProcessor(database=self.database, regex_keeper=SimpleRegexKeeper(), record_class_manager=self.record_class_manager, foreign_key_cache=self.foreign_key_cache)
        self.parser = Parser(record_processor=self.record_processor, regex_keeper=SimpleRegexKeeper(), stop_event=self.events.stop)
        self.updater = Updater(config=self.config, parsing_context_factory=self.get_parsing_context, parser=self.parser, stop_event=self.events.stop, pause_event=self.events.pause, database=self.database, signaler=self.update_signaler)
        self.records_inserter = RecordInserter(config=self.config, database=self.database)
        # thread
        self.update_manager: UpdateManager = None

    @property
    def session_meta_data(self) -> "DatabaseMetaData":
        return self.database.session_meta_data

    def get_update_manager(self) -> "UpdateManager":
        """
        Creates a new `UpdateManager` thread.

        Needed if the previous `UpdateManager` thread was stopped and update loop should restart.

        Returns:
            `UpdateManager`: Thread-subclass that schedules update cycles.
        """
        return UpdateManager(updater=self.updater, config=self.config, time_clock=self.time_clock, pause_event=self.events.pause, stop_event=self.events.stop)

    def get_parsing_context(self, log_file: "LogFile") -> "LogParsingContext":
        """
        Factory method for the parsing_context.

        Overwrite in subclass if different parsing_context class should be used.

        Args:
            log_file(`LogFile`): database model.

        Returns:
            `LogParsingContext`: Instantiated `LogParsingContext` with the provided `LogFile` model.
        """
        context = LogParsingContext(log_file=log_file, inserter=self.records_inserter, foreign_key_cache=self.foreign_key_cache, config=self.config)
        self.all_parsing_context.add(context)
        return context

    def register_record_classes(self, record_classes: Iterable[RECORD_CLASS_TYPE]) -> "Backend":
        for record_class in record_classes:
            self.record_class_manager.register_record_class(record_class=record_class)
        return self

    def start_up(self, overwrite: bool = False) -> "Backend":
        """
        Start up the database, populates the database with all necessary tables and default entries ("or_ignore"), registers all record_classes and connects basic signals.

        """

        self.database.start_up(overwrite=overwrite)

        from antistasi_logbook.records import ALL_ANTISTASI_RECORD_CLASSES
        for record_class in ALL_ANTISTASI_RECORD_CLASSES:
            self.record_class_manager.register_record_class(record_class=record_class)
        RecordClass.record_class_manager = self.record_class_manager

        self.signals.new_log_record.connect(self.database.session_meta_data.increment_added_log_records)
        self.signals.new_log_file.connect(self.database.session_meta_data.increment_new_log_file)
        self.signals.updated_log_file.connect(self.database.session_meta_data.increment_updated_log_file)
        return self

    def shutdown(self) -> None:
        """
        Signals the shutdown to all Backend sub_objects via the `stop`-event. Waits for a limited time on all parsing_context futures and then ensures thes shutdown of all sub_objects
        that can be shut down.


        """
        self.events.stop.set()
        all_futures = []
        log.debug("checking if all ctx are closed")
        for ctx in self.all_parsing_context:
            log.debug("checking ctx %r", ctx)
            while ctx.is_open is True:
                sleep(0.1)
            all_futures += ctx.futures
        log.debug("waiting for all futures to finish")
        wait(all_futures, return_when=ALL_COMPLETED, timeout=3.0)

        if self.update_manager is not None and self.update_manager.is_alive() is True:
            self.update_manager.shutdown()
        self.remote_manager_registry.close()
        self.updater.shutdown()
        self.records_inserter.shutdown()
        self.database.shutdown()

    def remove_and_reset_database(self) -> None:
        self.shutdown()
        self.events.stop.clear()
        FILE_LOCKS.reset()

        self.parser = Parser(record_processor=self.record_processor, regex_keeper=SimpleRegexKeeper(), stop_event=self.events.stop)
        self.updater = Updater(config=self.config, parsing_context_factory=self.get_parsing_context, parser=self.parser, stop_event=self.events.stop, pause_event=self.events.pause, database=self.database, signaler=self.update_signaler)
        self.records_inserter = RecordInserter(config=self.config, database=self.database)
        self.update_manager: UpdateManager = None
        self.foreign_key_cache.reset_all()

        self.start_up(True)
        self.record_class_manager.reset()

    def start_update_loop(self) -> "Backend":
        if self.update_manager is None:
            self.update_manager = self.get_update_manager()
        self.update_manager.start()
        return self


# region[Main_Exec]
if __name__ == '__main__':
    pass
# endregion[Main_Exec]
