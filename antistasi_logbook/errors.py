
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
from typing import TYPE_CHECKING, Union, Callable, Iterable, Optional, Mapping, Any, IO, TextIO, BinaryIO
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
import yarl
from datetime import datetime, timedelta, timezone
from typing import Optional, Union, TYPE_CHECKING
import logging
import threading
from types import TracebackType
if TYPE_CHECKING:
    from antistasi_logbook.utilities.date_time_utilities import DatetimeDuration
    from antistasi_logbook.storage.models.models import RemoteStorage
# endregion[Imports]

# region [TODO]


# endregion [TODO]

# region [Logging]

log = logging.getLogger(__name__)

# endregion[Logging]

# region [Constants]

THIS_FILE_DIR = Path(__file__).parent.absolute()

# endregion[Constants]


class BaseAntistasiLogBookError(Exception):
    """
    Base Error for antistasi_serverlog_statistics package.
    """


class BaseRemoteStorageError(BaseAntistasiLogBookError):
    ...


class MissingLoginAndPasswordError(BaseRemoteStorageError):

    def __init__(self, remote_storage_item: "RemoteStorage") -> None:
        self.remote_storage_item = remote_storage_item
        self.remote_storage_name = self.remote_storage_item.name
        self.login = self.remote_storage_item.get_login()
        self.password = self.remote_storage_item.get_password()
        self.base_url = self.remote_storage_item.base_url
        self.msg = self._determine_message()

        super().__init__(self.msg)

    def _determine_message(self) -> str:
        if self.login is None and self.password is None:
            return f"Missing both 'login' and 'password' for 'RemoteStorage': {self.remote_storage_name!r} with base_url {str(self.base_url)!r}."
        if self.login is None:
            return f"Missing 'login' for 'RemoteStorage': {self.remote_storage_name!r} with base_url {str(self.base_url)!r}."
        if self.password is None:
            return f"Missing 'password' for 'RemoteStorage': {self.remote_storage_name!r} with base_url {str(self.base_url)!r}."


class DurationTimezoneError(BaseAntistasiLogBookError):
    def __init__(self, duration_item: "DatetimeDuration", start_tz: Optional[timezone], end_tz: Optional[timezone], message: str) -> None:
        self.duration_item = duration_item
        self.start_tz = start_tz
        self.end_tz = end_tz
        self.message = message + f", {start_tz=}, {end_tz=}."
        super().__init__(self.message)


    # region[Main_Exec]
if __name__ == '__main__':
    pass

# endregion[Main_Exec]
