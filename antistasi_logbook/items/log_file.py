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

import lzma
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
from weakref import proxy
from threading import Lock
from antistasi_serverlog_statistic.utilities.path_utilities import RemotePath
from antistasi_serverlog_statistic.items.base_item import AbstractBaseItem, DbRowToItemConverter
from antistasi_serverlog_statistic.items.enums import DBItemAction
from antistasi_serverlog_statistic.items.entries.entry_line import EntryLine

if TYPE_CHECKING:
    from antistasi_serverlog_statistic.items.server import Server
    from antistasi_serverlog_statistic.webdav.webdav_manager import WebdavManager
    from antistasi_serverlog_statistic.webdav.remote_item import RemoteAntistasiLogFile
    from antistasi_serverlog_statistic.storage.storage_db import StorageDB
    from antistasi_serverlog_statistic.items.game_map import GameMap
    from antistasi_serverlog_statistic.regex.regex_keeper import RegexKeeper
# endregion[Imports]

# region [TODO]


# endregion [TODO]

# region [Logging]


# endregion[Logging]

# region [Constants]

THIS_FILE_DIR = Path(__file__).parent.absolute()

# endregion[Constants]


@total_ordering
class LogFile(AbstractBaseItem):
    ___db_table_name___: str = "LogFile_tbl"
    ___db_phrases___: dict[str, Union[dict[str, str], str]] = {DBItemAction.GET: {"by_id": "get_log_file_by_id",
                                                                                  "by_server": "get_log_file_by_server"},
                                                               DBItemAction.INSERT: "insert_log_file"}
    ___db_insert_parameter___: dict[str, str] = {"id": "item_id",
                                                 "name": "name",
                                                 "server": "server.item_id",
                                                 "remote_path": "remote_path",
                                                 "size": "size",
                                                 "modified_at": "modified_at",
                                                 "created_at": "created_at",
                                                 "last_parsed_line_number": "last_parsed_line_number",
                                                 "finished": "finished",
                                                 "game_map": "game_map.item_id",
                                                 "header_text": "header_text",
                                                 "unparsable": "unparsable",
                                                 "comments": "comments"}

    locks: dict[tuple[str, str], Lock] = {}
    file_name_regex = re.compile(r"""
                                    (?P<prefix>[a-z0-9]+)
                                    .
                                    (?P<architecture>x\d\d)
                                    .
                                    (?P<year>2\d{3})
                                    [^\d]
                                    (?P<month>[01]?\d)
                                    [^\d]
                                    (?P<day>[0-3]?\d)
                                    [^\d]
                                    (?P<hour>[0-2]?\d)
                                    [^\d]
                                    (?P<minute>[0-6]?\d)
                                    [^\d]
                                    (?P<second>[0-6]?\d)
                                    .*
                                    """, re.VERBOSE)

    def __init__(self,
                 item_id: Union[None, int],
                 name: str,
                 server: Union[int, "Server"],
                 remote_path: Union[str, os.PathLike, RemotePath],
                 size: int,
                 modified_at: datetime,
                 created_at: datetime = None,
                 last_parsed_line_number: int = None,
                 finished: bool = False,
                 game_map: Union[int, "GameMap"] = None,
                 header_text: str = None,
                 unparsable: bool = None,
                 comments: str = None) -> None:
        self.name = name
        self._server = server
        self.remote_path = RemotePath(remote_path) if not isinstance(remote_path, RemotePath) else remote_path
        self.size = size
        self.modified_at = modified_at
        self.created_at = created_at
        self.last_parsed_line_number = last_parsed_line_number
        self.finished = finished
        self._game_map = game_map
        self.header_text = header_text
        self.unparsable = unparsable
        self._item_id = item_id
        self.comments = comments
        self._file_name_info: dict[str, Any] = None
        self._lock = None

    @property
    def ___db_get_id_parameter__(self) -> dict[str, Any]:
        return {"name": self.name, "server": self.server.item_id}

    @property
    def lock(self) -> Lock:
        if self._lock is None:
            if (self.server.name, self.name) not in self.locks:
                self.locks[(self.server.name, self.name)] = Lock()
            self._lock = self.locks.get((self.server.name, self.name))
        return self._lock

    def get_line_generator(self) -> Generator[EntryLine, None, None]:
        with self.lock:
            with self.download():
                with self.local_path.open(encoding='utf-8', errors='ignore') as f:
                    last_parsed_line_number = 0 if self.last_parsed_line_number is None else self.last_parsed_line_number
                    current_line_number = 0
                    for line in f:
                        current_line_number += 1
                        line = line.rstrip()
                        if line != '' and current_line_number > last_parsed_line_number:

                            yield EntryLine(line.rstrip(), current_line_number)

    @property
    def file_name_info(self) -> dict[str, Any]:
        if self._file_name_info is None:
            match_data = self.file_name_regex.match(self.name)
            local_created_at = datetime(**{key: int(value) for key, value in match_data.groupdict() if key not in {"prefix", "architecture"}})
            self._file_name_info = {"prefix": match_data.group("prefix"), "architecture": match_data.group("architecture"), "local_created_at": local_created_at}
        return self._file_name_info

    def set_utc_created_at(self, data: dict[str, Any]) -> None:
        first_utc_datetime: datetime = datetime(tzinfo=timezone.utc, **{key.removeprefix("utc_"): int(value) for key, value in data.items() if key.startswith('utc_')})
        local_created_time: datetime = self.file_name_info.get("local_created_at").replace(tzinfo=timezone.utc)
        offset = first_utc_datetime - local_created_time
        offset_hours = timedelta(hours=offset.total_seconds() // (60 * 60))
        local_timezone = timezone(offset=offset_hours)
        self.created_at = local_created_time.replace(tzinfo=local_timezone).astimezone(tz=timezone.utc)

    @property
    def server(self) -> "Server":
        if isinstance(self._server, int):
            self._server = self.database.get_item_by_id("Server", item_id=self._server)

        return self._server

    @property
    def game_map(self) -> Optional[str]:
        if isinstance(self._game_map, int):
            self._game_map = self.database.get_item_by_id("GameMap", item_id=self._game_map)
        return self._game_map

    @game_map.setter
    def game_map(self, value: str) -> None:
        self._game_map = value

    @classmethod
    def ___get_db_row_factory___(cls) -> DbRowToItemConverter:
        return DbRowToItemConverter(cls)

    @property
    def local_path(self) -> Optional[Path]:
        return self.server.local_path.joinpath(self.remote_path.name)

    @classmethod
    def from_remote_log_file(cls, server: "Server", remote_log_file: "RemoteAntistasiLogFile") -> "LogFile":

        log_file = cls(item_id=None, name=remote_log_file.name, server=server, remote_path=remote_log_file.remote_path, size=remote_log_file.remote_size, modified_at=remote_log_file.modified_at, created_at=remote_log_file.created_at)
        log_file.to_db()
        return log_file

    @contextmanager
    def download(self) -> None:
        self.webdav_manager.download(self)
        yield
        self.local_path.unlink(missing_ok=True)

    def update_from_remote_log_file(self, remote_log_file: "RemoteAntistasiLogFile", server: "Server" = None):
        self.size = remote_log_file.remote_size
        self.modified_at = remote_log_file.modified_at
        if server is not None:
            self._server = server
        self.to_db()

    def to_db(self):
        result = self.database.insert_item(self)
        if result is False:
            # TODO: Custom Error!
            raise RuntimeError(f"Inserting {self.name!r} of {self.server.name!r} into db, was FAILED!")

    def __eq__(self, o: object) -> bool:
        if isinstance(o, self.__class__):
            return self.modified_at == o.modified_at

        return NotImplemented

    def __lt__(self, o: object) -> bool:
        if isinstance(o, self.__class__):
            return self.modified_at < o.modified_at

        return NotImplemented

    # def __repr__(self) -> str:
    #     attr_text = ', '.join(f"{attr_name}={attr_value!r}" for attr_name, attr_value in vars(self).items())
    #     return f"{self.__class__.__name__}({attr_text})"

# region[Main_Exec]


if __name__ == '__main__':
    pass

# endregion[Main_Exec]
