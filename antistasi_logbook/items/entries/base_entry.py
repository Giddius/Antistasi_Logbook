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
from antistasi_logbook.items.log_file import LogFile, AbstractBaseItem, DbRowToItemConverter, DBItemAction
from antistasi_logbook.items.entries.message import Message
from antistasi_logbook.items.enums import LogLevel, PunishmentAction
if TYPE_CHECKING:
    from antistasi_logbook.parsing.parser import ParseContext
    from antistasi_logbook.items.entries.raw_entry import RawEntry

    from antistasi_logbook.storage.storage_db import StorageDB
# endregion[Imports]

# region [TODO]


# endregion [TODO]

# region [Logging]


# endregion[Logging]

# region [Constants]

THIS_FILE_DIR = Path(__file__).parent.absolute()

# endregion[Constants]


TEMP_SQL_INSERT = """INSERT
    OR IGNORE INTO "LogRecord_tbl" (
        "record_class",
        "recorded_at",
        "log_file",
        "message",
        "start",
        "end",
        "logged_from",
        "called_by",
        "client",
        "log_level",
        "punishment_action"

    )
VALUES
    (?, ?, ?, (SELECT "item_id" from "Message_tbl" WHERE "message"=?), ?, ?, ?, ?, ?, ?, ?)"""


class EntryFamily(Flag):
    GENERIC = auto()
    ANTISTASI = auto()


class BaseEntry(AbstractBaseItem):
    record_class_registry: dict[str, type["BaseEntry"]] = None
    ___db_table_name___: str = "LogRecord_tbl"
    ___db_insert_parameter___: dict[str, str] = {"item_id": "item_id",
                                                 "log_file": "log_file.item_id",
                                                 "recorded_at": "recorded_at",
                                                 "message": "_message.item_id",
                                                 "start": "start",
                                                 "end": "end",
                                                 "log_level": "log_level",
                                                 "punishment_action": "punishment_action",
                                                 "logged_from": "logged_from",
                                                 "called_by": "called_by",
                                                 "client": "client",
                                                 "record_class": "record_class"}
    ___db_phrases___: dict[str, Union[dict[str, str], str]] = {DBItemAction.GET: {"by_id": "get_entry_by_id",
                                                                                  "by_log_file": "get_entry_by_log_file"},
                                                               DBItemAction.INSERT: "insert_entry"}

    ___entry_family___: EntryFamily = EntryFamily.GENERIC | EntryFamily.ANTISTASI

    _db_row_factory: DbRowToItemConverter = None
    __slots__ = ("_item_id",
                 "_log_file",
                 "recorded_at",
                 "_message",
                 "log_level",
                 "start",
                 "end",
                 "logged_from",
                 "called_by",
                 "client",
                 "punishment_action",
                 "comments")

    def __init__(self,
                 item_id: Union[None, int],
                 log_file: Union[int, "LogFile"],
                 recorded_at: datetime,
                 message: Union["Message", int],
                 start: int,
                 end: int,
                 log_level: Union[int, "LogLevel"] = LogLevel.NO_LEVEL,
                 punishment_action: Union[int, "PunishmentAction"] = PunishmentAction.NO_ACTION,
                 logged_from: str = None,
                 called_by: str = None,
                 client: str = None,
                 comments: str = None):
        self._item_id = item_id
        self._log_file = log_file
        self.recorded_at = recorded_at
        self._message = message
        self.log_level = LogLevel(log_level)
        self.start = start
        self.end = end
        self.logged_from = logged_from
        self.called_by = called_by
        self.client = client
        self.punishment_action = PunishmentAction(punishment_action)
        self.comments = comments

    @property
    def record_class(self) -> str:
        return self.__class__.__name__

    @property
    def log_file(self) -> LogFile:
        if isinstance(self._log_file, int):
            self._log_file = self.database.get_item_by_id(LogFile, self._log_file)
        return self._log_file

    @classmethod
    @abstractmethod
    def from_parser(cls, context: "ParseContext", raw_entry: "RawEntry") -> "BaseEntry":
        ...

    @classmethod
    def from_db_row(cls,
                    record_class: str,
                    item_id: Union[None, int],
                    log_file: Union[int, "LogFile"],
                    recorded_at: datetime,
                    message: str,
                    start: int,
                    end: int,
                    log_level: Union[int, "LogLevel"] = LogLevel.NO_LEVEL,
                    punishment_action: Union[int, "PunishmentAction"] = PunishmentAction.NO_ACTION,
                    logged_from: str = None,
                    called_by: str = None,
                    client: str = None,
                    comments: str = None) -> "BaseEntry":
        record_class = cls.record_class_registry[record_class]
        return record_class(item_id=item_id,
                            log_file=log_file,
                            recorded_at=recorded_at,
                            message=Message(None, message),
                            start=start,
                            end=end,
                            log_level=log_level,
                            punishment_action=punishment_action,
                            logged_from=logged_from,
                            called_by=called_by,
                            client=client,
                            comments=comments)

    @classmethod
    def set_record_registry(cls) -> None:
        cls.record_class_registry = {sub_class.__name__: sub_class for sub_class in BaseEntry.__subclasses__()}

    def to_db(self) -> None:

        variables = [self._item_id, self.record_class, self.recorded_at, self.log_file.item_id, self.message, self.start,
                     self.end, self.logged_from, self.called_by, self.client, self.log_level, self.punishment_action, self.comments]
        possible_id = self.database.insert_item(self, variables=tuple(variables))
        if possible_id is not None:
            self._item_id = possible_id

    @classmethod
    def many_entries_to_db(cls, temp_entries):
        with cls.database.lock:
            with sqlite3.connect(cls.database.db_path, isolation_level=None, detect_types=sqlite3.PARSE_DECLTYPES) as conn:
                conn.execute("PRAGMA cache_size(-250000)")
                conn.execute("PRAGMA synchronous=OFF")
                conn.execute("PRAGMA journal_mode(OFF)")
                conn.executemany("""INSERT OR IGNORE INTO "Message_tbl" ("message") VALUES (?)""", [(entry.message,) for entry in temp_entries])

        values = [(entry.record_class, entry.recorded_at, entry.log_file.item_id, entry.message, entry.start,
                   entry.end, entry.logged_from, entry.called_by, entry.client, entry.log_level.value, entry.punishment_action.value) for entry in temp_entries]

        # cls.database.write(cls.___db_phrases___.get(DBItemAction.INSERT), values)
        with cls.database.lock:
            with sqlite3.connect(cls.database.db_path, isolation_level=None, detect_types=sqlite3.PARSE_DECLTYPES) as conn:
                conn.execute("PRAGMA cache_size(-250000)")
                conn.execute("PRAGMA synchronous=OFF")
                conn.execute("PRAGMA journal_mode(OFF)")
                conn.executemany(TEMP_SQL_INSERT, values)

    @classmethod
    def check(cls, context: "ParseContext", raw_entry: "RawEntry") -> bool:
        ...

    @classmethod
    def ___get_db_row_factory___(cls, **kwargs) -> DbRowToItemConverter:
        if cls._db_row_factory is None:
            cls._db_row_factory = DbRowToItemConverter(cls.from_db_row)
        return cls._db_row_factory

    @property
    def ___db_get_id_parameter__(self) -> dict[str, Any]:
        return {"start": self.start, "end": self.end, "log_file": self.log_file.item_id, "message": self.message, "record_class": self.record_class}


# class ServerInitEntry(BaseEntry):
#     ___entry_family___: str = EntryFamily.GENERIC


class GenericEntry(BaseEntry):
    ___entry_family___: EntryFamily = EntryFamily.GENERIC | EntryFamily.ANTISTASI

    @classmethod
    def from_parser(cls, context: "ParseContext", raw_entry: "RawEntry") -> "BaseEntry":
        log_file = context.log_file
        if raw_entry.parsed_data.get("utc_year") is not None:
            recorded_at = datetime(tzinfo=timezone.utc, **{k.removeprefix('utc_'): int(v) for k, v in raw_entry.parsed_data.items() if k.startswith('utc_')})
        else:
            recorded_at = datetime(tzinfo=context.log_file.local_timezone, **{k.removeprefix('local_'): int(v) for k, v in raw_entry.parsed_data.items() if k.startswith('local_')}).astimezone(tz=timezone.utc)
        message = raw_entry.parsed_data.get('message', "")
        log_level = raw_entry.parsed_data.get("log_level", LogLevel.NO_LEVEL)
        start = raw_entry.start
        end = raw_entry.end
        logged_from = raw_entry.parsed_data.get("file")
        called_by = raw_entry.parsed_data.get("called_by")
        client = raw_entry.parsed_data.get("client")
        return cls(item_id=None, log_file=log_file, recorded_at=recorded_at, message=message, log_level=log_level, start=start, end=end, logged_from=logged_from, called_by=called_by, client=client)

    @classmethod
    def check(cls, context: "ParseContext", raw_entry: "RawEntry") -> bool:
        return True


class AntistasiEntry(GenericEntry):
    ___entry_family___: EntryFamily = EntryFamily.ANTISTASI


# region[Main_Exec]
if __name__ == '__main__':
    pass

# endregion[Main_Exec]
