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
from typing import TYPE_CHECKING, Union, Callable, Iterable, Optional, Mapping, Any, IO, TextIO, BinaryIO, Hashable, Generator, Literal, TypeVar, TypedDict, AnyStr, Protocol
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
from gidapptools.general_helper.dict_helper import replace_dict_keys
from weakref import proxy
if TYPE_CHECKING:
    from antistasi_logbook.webdav.webdav_manager import WebdavManager
    from antistasi_logbook.storage.sqlite_database import GidSQLiteDatabase
# endregion[Imports]

# region [TODO]


# endregion [TODO]

# region [Logging]


# endregion[Logging]

# region [Constants]

THIS_FILE_DIR = Path(__file__).parent.absolute()

# endregion[Constants]


class DbRowToItemConverter:
    base_name_replacement_pairs = [('id', 'item_id')]

    def __init__(self, item_class: type, name_replacement_pairs: list[tuple[str, str]] = None, **default_kwargs) -> None:
        self.item_class = item_class

        self.item_kwarg_names = tuple(name for name, obj in inspect.signature(self.item_class).parameters.items() if obj.kind is not obj.VAR_KEYWORD)
        self.name_replacement_pairs = self.base_name_replacement_pairs.copy() + name_replacement_pairs if name_replacement_pairs is not None else self.base_name_replacement_pairs.copy()
        self.default_kwargs = default_kwargs

    def create_object_from_row(self, cursor: sqlite3.Cursor, row: tuple[Any]):
        row_kwarg_dict = replace_dict_keys({desc[0]: row[idx] for idx, desc in enumerate(cursor.description)}, *self.name_replacement_pairs)
        kwarg_dict = self.default_kwargs | row_kwarg_dict
        kwargs = {kwarg_name: kwarg_dict.get(kwarg_name, None) for kwarg_name in self.item_kwarg_names}

        return self.item_class(**kwargs)

    def __call__(self, cursor: sqlite3.Cursor, row: tuple[Any]) -> object:
        return self.create_object_from_row(cursor=cursor, row=row)


class AlternativeConstructor(Protocol):

    def __call__(self, **kwds: Any) -> "AbstractBaseItem":
        ...


class BaseRowFactory:

    def __init__(self, klass: type["AbstractBaseItem"], constructor: AlternativeConstructor = None) -> None:
        self.klass = klass
        self.constructor = self.klass if constructor is None else constructor

    @cached_property
    def _constructor_kwarg_names(self) -> tuple[str]:
        return tuple(name for name, obj in inspect.signature(self.constructor).parameters.items() if obj.kind is not obj.VAR_KEYWORD)

    def get_row_dict(self, cursor: sqlite3.Cursor, row: tuple[Any]) -> dict[str, Any]:
        return {desc[0]: row[idx] for idx, desc in enumerate(cursor.description)}

    def object_from_row(self, cursor: sqlite3.Cursor, row: tuple[Any], **kwargs: Any) -> "AbstractBaseItem":
        row_dict = self.get_row_dict(cursor=cursor, row=row)
        full_kwargs = row_dict | kwargs
        return self.constructor(**full_kwargs)

    def __call__(self, cursor: sqlite3.Cursor, row: tuple[Any], **kwargs: Any) -> "AbstractBaseItem":
        return self.object_from_row(cursor=cursor, row=row, **kwargs)


class AbstractBaseItem(ABC):
    webdav_manager: "WebdavManager" = None
    database: "GidSQLiteDatabase" = None
    ___row_factory___: BaseRowFactory = None

    @classmethod
    def ___get_db_row_factory___(cls) -> "BaseRowFactory":
        if cls.___row_factory___ is None:
            cls.___row_factory___ = BaseRowFactory(cls)
        return cls.___row_factory___

    @property
    def item_id(self) -> Optional[int]:
        if self._item_id is None:
            possible_id = self.database.get_id(self)
            if possible_id is not None:
                possible_id = possible_id[0]

            self._item_id = possible_id
        return self._item_id

    @classmethod
    def set_webdav_manager(cls, manager: "WebdavManager"):
        cls.webdav_manager = proxy(manager)
        return cls

    @classmethod
    def set_database(cls, database: "StorageDB"):
        cls.database = database
        return cls


# region[Main_Exec]
if __name__ == '__main__':
    pass

# endregion[Main_Exec]
