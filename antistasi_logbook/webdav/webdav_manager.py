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
from httpx import Limits, Timeout
from collections import deque
from antistasi_logbook.webdav.info_item import InfoItem
import antistasi_logbook
from gidapptools.meta_data import app_meta, get_meta_item, get_meta_paths
from threading import RLock
from rich import print as rprint
import yarl
from antistasi_logbook.errors import MissingLoginError
from antistasi_logbook.utilities.path_utilities import url_to_path
from antistasi_logbook.utilities.enums import RemoteItemType
if TYPE_CHECKING:

    from gidapptools.meta_data.interface import MetaPaths
# endregion[Imports]

# region [TODO]


# endregion [TODO]

# region [Logging]


# endregion[Logging]

# region [Constants]

THIS_FILE_DIR = Path(__file__).parent.absolute()

META_PATHS: "MetaPaths" = get_meta_paths()
atexit.register(META_PATHS.clean_up)
# endregion[Constants]


class AbstractRemoteStorageManager(ABC):

    @abstractmethod
    def get_files(self, folder_path: RemotePath) -> Generator:
        ...

    @abstractmethod
    def get_info(self, file_path: RemotePath) -> InfoItem:
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


class WebdavManager(AbstractRemoteStorageManager):
    _extra_base_url_parts = ["dev_drive", "remote.php", "dav", "files"]

    def __init__(self, base_url: yarl.URL, login: str, password: str) -> None:
        self.raw_base_url = base_url
        self.login = login
        self.password = password
        self.full_base_url = self._make_full_base_url()
        self._client: WebdavClient = None

    @property
    def client(self) -> WebdavClient:
        if self._client is None:
            self._client = WebdavClient(base_url=str(self.full_base_url), auth=(self.login, self.password))
        return self._client

    def _make_full_base_url(self) -> yarl.URL:
        extra_parts = '/'.join([str(part) for part in self._extra_base_url_parts if part not in self.raw_base_url.parts])
        return self.raw_base_url.join(yarl.URL(extra_parts))

    def get_files(self, folder_path: RemotePath) -> Generator:
        for item in self.client.ls(folder_path):
            info = InfoItem.from_webdav_info(item)
            if info.content_type is RemoteItemType.DIRECTORY:
                continue
            yield info

    def get_info(self, file_path: RemotePath) -> InfoItem:
        info = self.client.info(file_path)
        return InfoItem.from_webdav_info(info)
# region[Main_Exec]


if __name__ == '__main__':
    pass

# endregion[Main_Exec]
