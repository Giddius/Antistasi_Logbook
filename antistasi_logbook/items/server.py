"""
WiP.

Soon.
"""

# region [Imports]

import gc
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
import unicodedata
import inspect

from time import sleep, process_time, process_time_ns, perf_counter, perf_counter_ns
from io import BytesIO, StringIO
from abc import ABC, ABCMeta, abstractmethod
from copy import copy, deepcopy
from enum import Enum, Flag, auto
from time import time, sleep
from pprint import pprint, pformat
from pathlib import Path
from string import Formatter, digits, printable, whitespace, punctuation, ascii_letters, ascii_lowercase, ascii_uppercase
from timeit import Timer
from typing import TYPE_CHECKING, Union, Callable, Iterable, Optional, Mapping, Any, IO, TextIO, BinaryIO, Generator
from zipfile import ZipFile, ZIP_LZMA
from datetime import datetime, timezone, timedelta
from tempfile import TemporaryDirectory
from textwrap import TextWrapper, fill, wrap, dedent, indent, shorten
from functools import wraps, partial, lru_cache, singledispatch, total_ordering, cached_property
from importlib import import_module, invalidate_caches
from contextlib import contextmanager, asynccontextmanager
from statistics import mean, mode, stdev, median, variance, pvariance, harmonic_mean, median_grouped
from collections import Counter, ChainMap, deque, namedtuple, defaultdict
from urllib.parse import urlparse
from importlib.util import find_spec, module_from_spec, spec_from_file_location
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from importlib.machinery import SourceFileLoader
from yarl import URL
from weakref import proxy
import logging
from rich.rule import Rule
from sortedcontainers import SortedList, SortedSet
from gidapptools.meta_data import get_meta_item, get_meta_paths
from concurrent.futures import ThreadPoolExecutor, wait, ALL_COMPLETED
from gidapptools.utility.helper import make_pretty
from gidapptools.general_helper.timing import time_func
from rich.panel import Panel
from rich.padding import Padding
from rich.tree import Tree
from rich import box
from rich.text import Text
from rich.console import Console as RichConsole, ConsoleOptions, RenderResult, Group
from rich.pretty import Pretty, pprint, pretty_repr
from rich.segment import Segment, Segments, SegmentLines
from antistasi_logbook.utilities.rich_styles import PANEL_BORDER_STYLE, PANEL_STYLE
from antistasi_logbook.utilities.path_utilities import RemotePath
from antistasi_logbook.webdav.remote_item import RemoteAntistasiLogFolder, RemoteAntistasiLogFile
from antistasi_logbook.items.log_file import LogFile
from antistasi_logbook.items.base_item import AbstractBaseItem, BaseRowFactory
from antistasi_logbook.items.enums import DBItemAction
if TYPE_CHECKING:
    from gidapptools.meta_data.meta_print.meta_print_item import MetaPrint
    from gidapptools.meta_data.interface import MetaPaths
    from antistasi_logbook.webdav.webdav_manager import WebdavManager

# endregion[Imports]

# region [TODO]


# endregion [TODO]

# region [Logging]

log = logging.getLogger(__name__)

# endregion[Logging]

# region [Constants]

THIS_FILE_DIR = Path(__file__).parent.absolute()
META_PRINT: "MetaPrint" = get_meta_item('meta_print')
META_PATHS: "MetaPaths" = get_meta_paths()
# endregion[Constants]


class Server(AbstractBaseItem):
    remote_item_class = RemoteAntistasiLogFolder

    def __init__(self,
                 item_id: Optional[int],
                 name: str,
                 remote_path: Union[str, os.PathLike, Path, RemotePath],
                 local_path: Union[str, os.PathLike, Path] = None,
                 comments: str = None) -> None:
        self._item_id = item_id
        self.name = name
        self.remote_path = RemotePath(remote_path)
        self.local_path = META_PATHS.get_new_temp_dir(name=self.name) if local_path is None else Path(local_path)
        # self.local_path = THIS_FILE_DIR.joinpath('fake_log_files').joinpath(self.name)
        self.remote_item = self.remote_item_class.from_path(self.remote_path)
        self.comments = comments
        self._log_files: dict[str, "LogFile"] = None

    @classmethod
    def get_all_server(cls) -> tuple("Server"):
        return cls.database.read("get_all_server.sql", row_factory=cls.___get_db_row_factory___())

    @property
    def log_files(self) -> dict[str, "LogFile"]:
        if self._log_files is None:
            log_items = self.database.get_items("LogFile", self.item_id, phrase_key="by_server")
            collected_log_items = {}
            for item in log_items:
                item._server = self
                collected_log_items[item.name] = item
            self._log_files = collected_log_items
        return self._log_files

    @property
    def log_file_time_limit(self) -> datetime:
        return datetime.now(tz=timezone.utc) - timedelta(weeks=2)

    def __len__(self) -> int:
        return len(self.log_files)

    def get_remote_log_files(self) -> list[RemoteAntistasiLogFile]:
        return (item for item in self.remote_item.all_non_hc_log_files if item.modified_at >= self.log_file_time_limit)

    def update(self) -> Generator["LogFile", None, None]:

        def add_new_log_file(in_remote_file):
            new_log_file = LogFile.from_remote_log_file(server=self, remote_log_file=in_remote_file)
            self._log_files[new_log_file.name] = new_log_file

            return new_log_file

        def update_log_file(in_remote_file, in_local_file):
            in_local_file.update_from_remote_log_file(in_remote_file, server=self)

            return in_local_file

        self._log_files = None

        finished_log_file_names = {name for name, item in self.log_files.items() if item.finished is True}
        local_log_files = {name: log_file for name, log_file in self.log_files.items() if name not in finished_log_file_names}
        for remote_log_file in reversed(list(self.get_remote_log_files())):

            if remote_log_file.name in finished_log_file_names:
                continue
            local_log_file = local_log_files.pop(remote_log_file.name, None)
            if local_log_file is None:
                yield add_new_log_file(remote_log_file)

            elif remote_log_file.remote_size > local_log_file.size:
                yield update_log_file(remote_log_file, local_log_file)

            elif remote_log_file.remote_size < local_log_file.size:
                raise RuntimeError(f'\n{"-"*25}\nSOMETHINGS WRONG WITH SIZE COMPARISON, REMOTE SIZE IS SMALLER THAN LOCAL SIZE {remote_log_file.remote_size=} < {local_log_file.size}\n{"-"*25}\n')
            sleep(0.5)
        for name, log_file in local_log_files.items():
            if log_file.modified_at <= (datetime.now(tz=timezone.utc) + timedelta(hours=6)):
                log_file.finished = True
                log_file.to_db()

    # def __repr__(self) -> str:
    #     attr_text = ', '.join(f"{attr_name}={attr_value!r}" for attr_name, attr_value in (vars(self)).items() if not attr_name.startswith('_'))
    #     return f"{self.__class__.__name__}({attr_text})"

    def __rich_console__(self, console: RichConsole, options: ConsoleOptions) -> RenderResult:

        tree = Tree(label=Group(f"[b u spring_green3]{self.__class__.__name__}[/b u spring_green3]"), guide_style="b", style="")

        for attr_name, attr_value in (vars(self) | {"len": len(self)}).items():
            if attr_name.startswith('_'):
                continue

            typus = str(type(attr_value)).strip('<>').removeprefix('class ').strip("\'").split('.')[-1]
            type_string = f"[overline underline magenta2]{typus}[/overline underline magenta2]"
            full_type_text = f"{type_string}"
            sub_tree = tree.add(f"[b gold1]{attr_name}[/b gold1] | {full_type_text}")

            if not hasattr(attr_value, '__rich__'):
                sub_tree.add(Panel.fit(f"[b blue]{attr_value!r}[/b blue]", style=PANEL_STYLE, border_style=PANEL_BORDER_STYLE, box=box.DOUBLE))
            else:
                sub_tree.add(attr_value)

        yield Panel.fit(tree, style=PANEL_STYLE, border_style=PANEL_BORDER_STYLE, box=box.DOUBLE, padding=1)


# region[Main_Exec]


if __name__ == '__main__':
    pass

# endregion[Main_Exec]
