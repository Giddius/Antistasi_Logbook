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
from collections import Counter, ChainMap, deque, namedtuple, defaultdict, UserString
from urllib.parse import urlparse
from importlib.util import find_spec, module_from_spec, spec_from_file_location
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from importlib.machinery import SourceFileLoader
from webdav4.client import Client as WebdavClient
from antistasi_logbook.utilities.nextcloud import get_nextcloud_options, DEFAULT_BASE_FOLDER, DEFAULT_SUB_FOLDER_NAME, get_webdav_client, DEFAULT_LOG_FOLDER_TEMPLATE, get_username
from dotenv import load_dotenv, find_dotenv
from icecream import ic
from gidapptools.general_helper.timing import time_func
from antistasi_logbook.utilities.path_utilities import clean_path, RemotePath
from antistasi_logbook.webdav.remote_item import RemoteItem, RemoteFolder, RemoteFile, RemoteItemType, RemoteAntistasiLogFile, RemoteAntistasiLogFolder
from mimetypes import common_types, types_map
import atexit
from gidapptools.general_helper.timing import time_execution, time_func
from threading import Semaphore, Thread
from gidapptools.general_helper.conversion import human2bytes
from queue import Queue

from collections import deque
from antistasi_logbook.webdav.info_item import InfoItem
import antistasi_serverlog_statistic
from gidapptools.meta_data import app_meta, get_meta_item, get_meta_paths
from threading import RLock
from rich import print as rprint
from antistasi_logbook.items.base_item import AbstractBaseItem
from antistasi_logbook.items.server import Server
from antistasi_logbook.storage.storage_db import StorageDB
if TYPE_CHECKING:
    from gidapptools.meta_data.meta_print.meta_print_item import MetaPrint
    from antistasi_logbook.items.log_file import LogFile
    from gidapptools.meta_data.interface import MetaPaths
# endregion[Imports]

# region [TODO]


# endregion [TODO]

# region [Logging]


# endregion[Logging]

# region [Constants]

THIS_FILE_DIR = Path(__file__).parent.absolute()
META_PRINT: "MetaPrint" = get_meta_item('meta_print')
META_PATHS: "MetaPaths" = get_meta_paths()
atexit.register(META_PATHS.clean_up)
# endregion[Constants]


class NoThreadPoolExecutor:

    def map(self, func, items):
        return map(func, items)

    def shutdown(self):
        return


# LS_SAVE_JSON = THIS_FILE_DIR.joinpath('fake_ls_data.json')
# if LS_SAVE_JSON.exists() is False:
#     LS_SAVE_JSON.write_text('{}', encoding='utf-8', errors='ignore')
# LS_SAVE_LOCK = RLock()


# @contextmanager
# def save_ls_values():
#     with LS_SAVE_LOCK:
#         data = json.loads(LS_SAVE_JSON.read_text(encoding='utf-8', errors='ignore'))
#         yield data
#         with LS_SAVE_JSON.open('w', encoding='utf-8', errors='ignore') as f:
#             json.dump(data, f, sort_keys=True, indent=4, default=str)


# INFO_SAVE_LOCK = RLock()
# INFO_SAVE_JSON = THIS_FILE_DIR.joinpath('fake_info_data.json')
# INFO_SAVE_JSON.write_text('{}', encoding='utf-8', errors='ignore')


# @contextmanager
# def save_info_values():
#     with INFO_SAVE_LOCK:
#         data = json.loads(INFO_SAVE_JSON.read_text(encoding='utf-8', errors='ignore'))
#         yield data
#         with INFO_SAVE_JSON.open('w', encoding='utf-8', errors='ignore') as f:
#             json.dump(data, f, sort_keys=True, indent=4, default=str)


class WebdavManager:

    _always_exclude_folder_names: list[str] = ['.vscode']
    _default_client: WebdavClient = None
    download_semaphore = Semaphore(4)
    _remote_folder_cache: dict[RemotePath:Union[RemoteFolder, RemoteAntistasiLogFolder]] = {}

    def __init__(self, log_folder_remote_path: Path, database: StorageDB, client: WebdavClient = None) -> None:
        self._client = client
        self.database = database
        self._add_manager_to_objects()
        self.log_folder_path = RemotePath(log_folder_remote_path)

        self.downloads = []
        atexit.register(self.client.http.close)

    def _add_manager_to_objects(self) -> None:
        RemoteItem.set_webdav_manager(self)
        AbstractBaseItem.set_webdav_manager(self)
        AbstractBaseItem.set_database(self.database)

    def ls(self, path: Union[Path, str, RemotePath], klass: RemoteItem = None) -> Generator[Union[RemoteFile, RemoteFolder, RemoteAntistasiLogFile, RemoteAntistasiLogFolder], None, None]:
        path = RemotePath(path)
        # with save_ls_values() as stored_ls_data:
        #     if str(path) not in stored_ls_data:
        #         stored_ls_data[str(path)] = []
        for info in self.client.ls(path=path):
            # if info["etag"] not in {item["etag"] for item in stored_ls_data[str(path)]}:
            #     stored_ls_data[str(path)].append(info.copy())
            info_item = InfoItem.from_webdav_info(info)
            item = RemoteItem.make(info_item, klass=klass)
            if item.is_dir() and item.name.casefold() in self.always_exclude_folder_names:
                continue
            if item.is_dir() is True:
                self._remote_folder_cache[item.remote_path] = item

            yield item

    def info(self, path: Union[Path, str, RemotePath]) -> InfoItem:
        path = RemotePath(path)
        # with save_info_values() as stored_info_data:
        info = self.client.info(path=path)
        # stored_info_data[str(path)] = info.copy()
        return InfoItem.from_webdav_info(info)

    def get_remote_item(self, path: Union[Path, str, RemotePath], klass: RemoteItem = None) -> RemoteItem:
        if path in self._remote_folder_cache:
            return self._remote_folder_cache[path]

        info_item = self.info(path=path)
        return RemoteItem.make(info=info_item, klass=klass)

    def get_server_folder(self) -> dict[str, Server]:
        return {server.name: server for server in self.database.get_items(Server)}

    @ property
    def client(self) -> WebdavClient:
        if self._client is None:
            return self.default_client

        return self._client

    @ classmethod
    @ property
    def always_exclude_folder_names(cls) -> set[str]:
        return {item.casefold() for item in cls._always_exclude_folder_names}

    @ classmethod
    @ property
    def default_client(cls) -> WebdavClient:

        def _create_client() -> WebdavClient:
            return get_webdav_client()

        if cls._default_client is None:
            cls._default_client = _create_client()
        return cls._default_client

    @ classmethod
    def set_default_client(cls, client: WebdavClient) -> None:
        cls._default_client = client

    def _download(self, remote_path: RemotePath, local_path: Path):
        with self.download_semaphore:
            print(f"downloading {local_path.stem!r} to {local_path.as_posix()!r}.")
            self.client.download_file(remote_path, local_path, chunk_size=human2bytes("1 mb"))

    def download(self, file: Union[RemoteFile, "LogFile"], random_start_delay: int = None) -> RemoteFile:

        if random_start_delay is not None:
            sleep(random.randint(0, random_start_delay))

        file.local_path.parent.mkdir(exist_ok=True, parents=True)

        self._download(file.remote_path, file.local_path)

        return file
    # region[Main_Exec]


if __name__ == '__main__':
    pass

# endregion[Main_Exec]
