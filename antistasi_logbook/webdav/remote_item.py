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
from weakref import proxy, WeakMethod
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from itertools import chain
from importlib.machinery import SourceFileLoader
from antistasi_logbook.utilities.path_utilities import RemotePath
from gidapptools.general_helper.conversion import bytes2human
from gidapptools.general_helper.date_time import DatetimeFmt
from gidapptools.general_helper.enums import MiscEnum
from antistasi_logbook.data.content_types import ContentType
from antistasi_logbook.utilities.rich_styles import PANEL_BORDER_STYLE, PANEL_STYLE
from antistasi_logbook.webdav.info_item import InfoItem
from rich.panel import Panel
from rich.padding import Padding
from rich import box
from antistasi_logbook.utilities.enums import RemoteItemType
import attr
if TYPE_CHECKING:
    from antistasi_logbook.webdav.webdav_manager import WebdavManager, WebdavClient
# endregion[Imports]

# region [TODO]


# endregion [TODO]

# region [Logging]


# endregion[Logging]

# region [Constants]

THIS_FILE_DIR = Path(__file__).parent.absolute()

# endregion[Constants]

# {'content_language': None,
#  'content_length': None,
#  'content_type': '',
#  'created': None,
#  'display_name': None,
#  'etag': '"60112172c62eb"',
#  'href': '/dev_drive/remote.php/dav/files/Giddi/E-Books/',
#  'modified': datetime.datetime(2021, 1, 27, 8, 16, 50, tzinfo=datetime.timezone.utc),
#  'name': 'E-Books',
# 'type': 'directory'}


class RemoteItem:
    webdav_manager: "WebdavManager" = None
    item_type: RemoteItemType = None

    def __init__(self, name: str, modified_at: datetime, remote_path: RemotePath, etag: str, original_info_item: InfoItem, **unwanted_kwargs) -> None:
        self.name = name
        self.modified_at = modified_at
        self.remote_path = remote_path
        self.etag = etag
        self.original_info_item = original_info_item

    @cached_property
    def parent(self) -> "RemoteItem":
        if self.remote_path.parent in self.webdav_manager._remote_folder_cache:

            return self.webdav_manager._remote_folder_cache[self.remote_path.parent]
        return self.webdav_manager.get_remote_item(self.remote_path.parent)

    @cached_property
    def modified_at_pretty(self) -> str:
        return self.modified_at.strftime(DatetimeFmt.STANDARD_TZ)

    @cached_property
    def path_pretty(self) -> str:
        return str(self.remote_path)

    @classmethod
    def _attr_names_for_str(cls) -> tuple[str]:
        return (
            "name",
            "modified_at_pretty",
            "path_pretty",
            "etag"
        )

    @classmethod
    def make(cls, info: InfoItem, klass: "RemoteItem" = None) -> Union["RemoteFolder", "RemoteFile", "RemoteAntistasiLogFolder", "RemoteAntistasiLogFile"]:
        def _make_directory(in_info: InfoItem) -> Union[RemoteFolder, RemoteAntistasiLogFolder]:
            return RemoteFolder(**in_info.as_dict(), original_info_item=in_info)

        def _make_file(in_info: InfoItem) -> Union[RemoteFile, RemoteAntistasiLogFile]:
            if in_info.content_type is ContentType.TEXT and in_info.name.casefold().startswith(cls.log_file_name_prefix):
                return RemoteAntistasiLogFile(**in_info.as_dict(), original_info_item=in_info)

            return RemoteFile(**in_info.as_dict(), original_info_item=in_info)
        if klass is not None:
            return klass(**info.as_dict(), original_info_item=info)
        if info.type is RemoteItemType.FILE:
            return _make_file(info)
        elif info.type is RemoteItemType.DIRECTORY:
            return _make_directory(info)

    @classmethod
    def from_path(cls, path: Union[Path, str, RemotePath]) -> Union["RemoteFolder", "RemoteFile", "RemoteAntistasiLogFolder", "RemoteAntistasiLogFile"]:
        return cls.webdav_manager.get_remote_item(path=path, klass=cls)

    @classmethod
    def set_webdav_manager(cls, manager: "WebdavManager") -> None:
        cls.webdav_manager = proxy(manager)

    @classmethod
    @property
    def log_file_name_prefix(cls) -> str:
        return "arma3server_".casefold()

    def is_dir(self) -> bool:
        return self.item_type is RemoteItemType.DIRECTORY

    def is_file(self) -> bool:
        return self.item_type is RemoteItemType.FILE

    def __repr__(self) -> str:
        attr_text = ', '.join(f"{attr_name}={getattr(self,attr_name)!r}" for attr_name in self._attr_names_for_str())
        attr_text = attr_text.replace('_pretty', '')
        return f"{self.__class__.__name__}({attr_text})"

    def __rich__(self):
        attr_text = '\n'.join(f"[b gold1]{attr_name}[/b gold1] = [pale_turquoise1]{getattr(self,attr_name)!r}[/pale_turquoise1]" for attr_name in self._attr_names_for_str())
        attr_text = attr_text.replace('_pretty', '')

        content = f"[b u spring_green3]{self.__class__.__name__}[/b u spring_green3]\n\n{attr_text}"
        return Panel.fit(content, style=PANEL_STYLE, border_style=PANEL_BORDER_STYLE, box=box.DOUBLE)


class RemoteFolder(RemoteItem):

    item_type: RemoteItemType = RemoteItemType.DIRECTORY

    @ property
    def files(self) -> dict[str, "RemoteFile"]:
        return {file.name.casefold(): file for file in self.get_files()}

    @ property
    def dirs(self) -> dict[str, "RemoteFolder"]:
        return {folder.name.casefold(): folder for folder in self.get_dirs()}

    @ property
    def children(self) -> dict[str, Union["RemoteFile", "RemoteFolder"]]:
        return {child.name.casefold(): child for child in self.get_children()}

    def get_files(self, only_file_types: Union[Iterable[ContentType], ContentType] = MiscEnum.ALL) -> Generator["RemoteFile", None, None]:

        if only_file_types is not MiscEnum.ALL and not isinstance(only_file_types, Iterable):
            only_file_types = {only_file_types}

        def _check_file_type(in_file) -> bool:
            if only_file_types is MiscEnum.ALL:
                return True
            return in_file.file_type in only_file_types

        for item in self.webdav_manager.ls(self.remote_path):
            if item.is_file() and _check_file_type(item):
                yield item

    def get_dirs(self) -> Generator[Union["RemoteFolder", "RemoteAntistasiLogFolder"], None, None]:
        for item in self.webdav_manager.ls(self.remote_path):
            if item.is_dir() is False:
                continue
            yield item

    def get_children(self) -> Generator[Union["RemoteFile", "RemoteAntistasiLogFile", "RemoteFolder", "RemoteAntistasiLogFolder"], None, None]:
        for item in self.webdav_manager.ls(self.remote_path):
            yield item

    def get(self, child_name: str, types_to_get: Union[str, RemoteItemType] = MiscEnum.ALL, default: Any = None) -> Union["RemoteFile", "RemoteAntistasiLogFile", "RemoteFolder", "RemoteAntistasiLogFolder"]:
        iterator_selection = {MiscEnum.ALL: self.get_children,
                              RemoteItemType.DIRECTORY: self.get_dirs,
                              RemoteItemType.FILE: self.get_files}
        if isinstance(types_to_get, str):
            types_to_get = RemoteItemType(types_to_get)

        child_name = child_name.casefold()
        for child in iterator_selection.get(types_to_get)():
            if child.name.casefold() == child_name:
                return child

        return default

    def __len__(self) -> int:
        return len(self.children)


class RemoteAntistasiLogFolder(RemoteFolder):

    @property
    def main_log_folder(self) -> RemoteFolder:
        return self.from_path(path=self.remote_path.joinpath('Server'))

    @property
    def hc_folder(self) -> list[RemoteFolder]:
        hc_folder = []
        for i in range(10):
            hc_folder.append(self.get(f"hc_{i}", types_to_get=RemoteItemType.DIRECTORY, default=None))
        return [item for item in hc_folder if item is not None]

    @property
    def sub_dirs(self) -> list["RemoteAntistasiLogFolder"]:
        return [self.main_log_folder] + self.hc_folder

    @property
    def all_log_files(self) -> Generator["RemoteAntistasiLogFile", None, None]:
        for sub_folder in self.sub_dirs:
            for file in sub_folder.get_files():
                if isinstance(file, RemoteAntistasiLogFile):
                    yield file

    @property
    def all_non_hc_log_files(self) -> Generator["RemoteAntistasiLogFile", None, None]:
        for file in self.main_log_folder.get_files():
            if isinstance(file, RemoteAntistasiLogFile):
                yield file


class RemoteFile(RemoteItem):

    item_type: RemoteItemType = RemoteItemType.FILE

    def __init__(self, name: str, modified_at: datetime, remote_path: str, etag: str, remote_size: int, content_type: ContentType, original_info_item: InfoItem, **unwanted_kwargs) -> None:
        self.remote_size = remote_size
        self.content_type = content_type

        super().__init__(name=name, modified_at=modified_at, remote_path=remote_path, etag=etag, original_info_item=original_info_item, **unwanted_kwargs)

    @ property
    def remote_size_pretty(self) -> str:
        return bytes2human(self.remote_size)

    @ classmethod
    def _attr_names_for_str(cls) -> tuple[str]:
        attr_names = list(super()._attr_names_for_str())
        attr_names.append("remote_size_pretty")
        attr_names.append("content_type")
        return tuple(attr_names)

    @property
    def target_folder(self) -> Path:
        return Path(r"D:\Dropbox\hobby\Modding\Programs\Github\My_Repos\Antistasi_ServerLog_Statistic\temp")

    @property
    def local_path(self) -> Path:
        self.target_folder.mkdir(exist_ok=True, parents=True)
        return self.target_folder.joinpath(self.remote_path.name)

    def download(self, random_start_delay: int = None) -> Path:
        if self.target_folder.exists() is False:
            self.target_folder.mkdir(exist_ok=True, parents=True)
        self.webdav_manager.download(self, random_start_delay=random_start_delay)

        return self.local_path


class RemoteAntistasiLogFile(RemoteFile):

    def __init__(self, name: str, modified_at: datetime, remote_path: str, etag: str, remote_size: int, content_type: ContentType, original_info_item: InfoItem, created_at: datetime = None, **unwanted_kwargs) -> None:
        super().__init__(name=name, modified_at=modified_at, remote_path=remote_path, etag=etag, remote_size=remote_size, content_type=content_type, original_info_item=original_info_item, **unwanted_kwargs)
        self.created_at = created_at

    @ cached_property
    def log_file_type(self) -> str:
        return self.remote_path.parent.name.casefold()

    @ cached_property
    def server(self) -> RemoteFolder:
        path_parts = {item.casefold() for item in self.remote_path.parts}
        server_name = [name for name in self.webdav_manager.server if name in path_parts][0]

        return self.webdav_manager.server.get(server_name)

    def is_hc_file(self) -> bool:
        return self.log_file_type.startswith('hc')

    @property
    def target_folder(self) -> Path:
        return super().target_folder


# region[Main_Exec]
if __name__ == '__main__':
    pass

# endregion[Main_Exec]
