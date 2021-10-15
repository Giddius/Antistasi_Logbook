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
from antistasi_serverlog_statistic.items.base_item import AbstractBaseItem, DbRowToItemConverter
from antistasi_serverlog_statistic.items.enums import DBItemAction

# endregion[Imports]

# region [TODO]


# endregion [TODO]

# region [Logging]


# endregion[Logging]

# region [Constants]

THIS_FILE_DIR = Path(__file__).parent.absolute()

# endregion[Constants]


class GameMap(AbstractBaseItem):
    ___db_table_name___: str = "GameMap_tbl"
    ___db_phrases___: dict[str, Union[dict[str, str], str]] = {DBItemAction.GET: {"by_id": "get_game_map_by_id"},
                                                               DBItemAction.INSERT: "insert_log_file"}
    ___db_insert_parameter___: dict[str, str] = {"id": "item_id",
                                                 "name": "name",
                                                 "full_name": "full_name",
                                                 "official": "official",
                                                 "dlc": "dlc",
                                                 "map_image_path": "map_image_path",
                                                 "comments": "comments"}

    def __init__(self,
                 item_id: Optional[int],
                 name: str,
                 full_name: str = None,
                 official: bool = False,
                 dlc: str = None,
                 map_image_path: Path = None,
                 comments: str = None) -> None:
        self._item_id = item_id
        self.name = name
        self.full_name = full_name
        self.official = official
        self.dlc = dlc
        self.map_image_path = map_image_path
        self.comments = comments

    @classmethod
    def ___get_db_row_factory___(cls) -> DbRowToItemConverter:
        return DbRowToItemConverter(cls)

# region[Main_Exec]


if __name__ == '__main__':
    pass

# endregion[Main_Exec]
