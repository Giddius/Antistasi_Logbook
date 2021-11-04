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
from mimetypes import common_types, types_map
import atexit
from gidapptools.general_helper.timing import time_execution, time_func
from threading import Semaphore, Thread
from antistasi_logbook.utilities.enums import RemoteItemType
from gidapptools.general_helper.conversion import human2bytes
from queue import Queue
from httpx import Limits, Timeout
from collections import deque
from antistasi_logbook.updating.info_item import InfoItem
import antistasi_logbook
from gidapptools.general_helper.conversion import human2bytes
from gidapptools import get_meta_item, get_meta_paths, get_meta_config
from threading import RLock
from rich import print as rprint
import yarl
import httpx
from antistasi_logbook.errors import MissingLoginError
from antistasi_logbook.utilities.path_utilities import url_to_path
from antistasi_logbook.utilities.locks import DelayedSemaphore, MinDurationSemaphore
if TYPE_CHECKING:

    from gidapptools.meta_data.interface import MetaPaths
    from gidapptools.gid_config.meta_factory import GidIniConfig
    from antistasi_logbook.storage.models.models import RemoteStorage, LogFile
# endregion[Imports]

# region [TODO]


# endregion [TODO]

# region [Logging]


# endregion[Logging]

# region [Constants]

THIS_FILE_DIR = Path(__file__).parent.absolute()

META_PATHS: "MetaPaths" = get_meta_paths()
CONFIG: "GidIniConfig" = get_meta_config().get_config('general')

# endregion[Constants]


class AbstractRemoteStorageManager(ABC):

    @abstractmethod
    def get_files(self, folder_path: RemotePath) -> Generator:
        ...

    @abstractmethod
    def get_info(self, file_path: RemotePath) -> InfoItem:
        ...

    @abstractmethod
    def download_file(self, log_file: "LogFile") -> "LogFile":
        ...

    @classmethod
    def from_remote_storage_item(cls, remote_storage_item: "RemoteStorage") -> "AbstractRemoteStorageManager":
        return cls(base_url=remote_storage_item.base_url, login=remote_storage_item.login, password=remote_storage_item.password)

    @abstractmethod
    def close(self) -> None:
        ...


class LocalManager(AbstractRemoteStorageManager):

    def __init__(self, base_url: yarl.URL, login: str, password: str) -> None:
        try:
            self.path = url_to_path(base_url)
        except AssertionError:
            self.path = Path.cwd()

    def get_files(self, folder_path: Path) -> Generator:
        return (self.get_info(file) for file in folder_path.iterdir() if file.is_file())

    def get_info(self, file_path: Path) -> InfoItem:
        stat = file_path.stat()
        info = {"size": stat.st_size,
                "created_at": stat.st_ctime,
                "modified_at": stat.st_mtime,
                "name": file_path.stem}
        return info

    def download_file(self, log_file: "LogFile") -> "LogFile":
        return log_file

    def close(self) -> None:
        pass


class WebdavManager(AbstractRemoteStorageManager):
    _extra_base_url_parts = ["dev_drive", "remote.php", "dav", "files"]

    download_semaphores: dict[yarl.URL, MinDurationSemaphore] = {}
    config_name = 'webdav'

    def __init__(self, base_url: yarl.URL, login: str, password: str) -> None:
        self.raw_base_url = base_url
        self.login = login
        self.password = password
        self.full_base_url = self._make_full_base_url()
        self._client: WebdavClient = None
        self.download_semaphore = self._get_download_semaphore()
        CONFIG.config.changed_signal.connect(self.reset_client)

    def _get_download_semaphore(self) -> MinDurationSemaphore:
        download_semaphore = self.download_semaphores.get(self.full_base_url)
        if download_semaphore is None:
            delay = CONFIG.get(self.config_name, "delay_between_downloads", default=0)
            minimum_duration = CONFIG.get(self.config_name, "minimum_download_duration", default=0)
            download_semaphore = MinDurationSemaphore(self.max_connections, minimum_duration=timedelta(seconds=int(minimum_duration)), delay=timedelta(seconds=int(delay)))

            self.download_semaphores[self.full_base_url] = download_semaphore
        return download_semaphore

    def reset_client(self, config: "GidIniConfig") -> None:
        print("client reset called")
        self._client = None

    @property
    def max_connections(self) -> Optional[int]:
        return CONFIG.get(self.config_name, "max_concurrent_connections", default=100)

    @property
    def client(self) -> WebdavClient:
        if any([self.login is None, self.password is None]):
            # Todo: Custom Error
            raise RuntimeError(f"login and password can not be None for {self.__class__.__name__!r}.")

        if self._client is None:
            self._client = WebdavClient(base_url=str(self.full_base_url),
                                        auth=(self.login, self.password),
                                        retry=True,
                                        limits=httpx.Limits(max_connections=self.max_connections, max_keepalive_connections=self.max_connections),
                                        timeout=httpx.Timeout(timeout=None))
        return self._client

    def _make_full_base_url(self) -> yarl.URL:
        extra_parts = '/'.join([str(part) for part in self._extra_base_url_parts if part not in self.raw_base_url.parts])
        base_url = self.raw_base_url / extra_parts / self.login
        return base_url

    def get_files(self, folder_path: RemotePath) -> Generator:
        for item in self.client.ls(folder_path):
            info = InfoItem.from_webdav_info(item)
            if info.type is RemoteItemType.DIRECTORY:
                continue
            yield info

    def get_info(self, file_path: RemotePath) -> InfoItem:
        info = self.client.info(file_path)
        return InfoItem.from_webdav_info(info)

    def download_file(self, log_file: "LogFile", try_num: int = 0) -> "LogFile":
        download_url = log_file.download_url
        local_path = log_file.local_path
        chunk_size = CONFIG.get("downloading", "chunk_size", default=None)
        chunk_size = human2bytes(chunk_size) if chunk_size is not None else None
        try:
            with self.download_semaphore:
                print(f"downloading {log_file!r}")

                result = self.client.http.get(str(download_url), auth=(self.login, self.password))
                with local_path.open("wb") as f:
                    for chunk in result.iter_bytes(chunk_size=chunk_size):
                        f.write(chunk)
                log_file.is_downloaded = True
                return local_path
        except httpx.RemoteProtocolError as error:
            if try_num > 3:
                raise RuntimeError("blah") from error
            print('+' * 25 + " RemoteProtocolError, reconnecting")
            self.close()
            return self.download_file(log_file=log_file, try_num=try_num + 1)

    def close(self) -> None:
        if self._client is not None:
            self._client.http.close()
            self._client = None
# region[Main_Exec]


if __name__ == '__main__':
    pass

# endregion[Main_Exec]
