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


# endregion[Imports]

# region [TODO]


# endregion [TODO]

# region [Logging]


# endregion[Logging]

# region [Constants]

THIS_FILE_DIR = Path(__file__).parent.absolute()

# endregion[Constants]


DEFAULT_AMOUNT_BACKUPS_TO_KEEP = 5
DEFAULT_BACKUP_DATETIME_FORMAT = "%Y-%m-%d_%H-%M-%S"
DEFAULT_BACKUP_NAME_TEMPLATE = "[{date_and_time}_UTC]_{original_name}_backup.{original_file_extension}"


class BackupManager:

    def __init__(self, db_path: Path, config: None, backup_datetime_format: str = None, backup_name_template: str = None, backup_folder: Path = None) -> None:
        self.db_path = Path(db_path)
        self.config = config
        self.backup_datetime_format = DEFAULT_BACKUP_DATETIME_FORMAT if backup_datetime_format is None else backup_datetime_format
        self.backup_name_template = DEFAULT_BACKUP_NAME_TEMPLATE if backup_name_template is None else backup_name_template
        self.backup_folder = self.db_path.parent.joinpath('backups') if backup_folder is None else Path(backup_folder)

    @property
    def amount_backups_to_keep(self) -> int:
        if self.config is None:
            return DEFAULT_AMOUNT_BACKUPS_TO_KEEP

    @property
    def all_backup_files(self) -> tuple[Path]:
        _out = []
        for file in self.backup_folder.iterdir():
            if file.is_file() and self.db_path.stem.casefold() in file.stem.casefold() and file.suffix == self.db_path.suffix:
                _out.append(file)
        return sorted(_out, key=lambda x: x.stat().st_ctime)

    def _make_backup_name(self) -> str:
        original_file_extension = self.db_path.suffix.removeprefix('.')
        original_name = self.db_path.stem
        date_and_time = datetime.now(tz=timezone.utc).strftime(self.backup_datetime_format)
        return self.backup_name_template.format(date_and_time=date_and_time, original_name=original_name, original_file_extension=original_file_extension)

    def _copy_db(self) -> None:
        src = self.db_path
        tgt = self.backup_folder.joinpath(self._make_backup_name())
        shutil.copy(src=src, dst=tgt)

    def _delete_excess_backups(self) -> None:
        for backup in self.all_backup_files[:self.amount_backups_to_keep]:
            backup.unlink(missing_ok=True)

    def backup(self) -> None:
        self.backup_folder.mkdir(parents=True, exist_ok=True)
        self._copy_db()
        self._delete_excess_backups()


# region[Main_Exec]
if __name__ == '__main__':
    pass

# endregion[Main_Exec]
