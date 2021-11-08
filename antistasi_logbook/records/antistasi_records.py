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

from antistasi_logbook.records.base_record import BaseRecord, RecordFamily
if TYPE_CHECKING:
    from antistasi_logbook.parsing.parser import RawRecord
    from antistasi_logbook.storage.models.models import LogRecord
# endregion[Imports]

# region [TODO]


# endregion [TODO]

# region [Logging]


# endregion[Logging]

# region [Constants]

THIS_FILE_DIR = Path(__file__).parent.absolute()

# endregion[Constants]

ALL_ANTISTASI_RECORD_CLASSES: set[type[BaseRecord]] = set()


class PerformanceRecord(BaseRecord):
    ___record_family___ = RecordFamily.ANTISTASI
    ___specificity___ = 10
    performance_regex = re.compile(r"(?P<name>\w+\s?\w*)(?:\:\s?)(?P<value>\d[\d\.]*)")
    __slots__ = ("log_record", "_stats")

    def __init__(self, log_record: "LogRecord") -> None:
        super().__init__(log_record)
        self._stats: dict[str, Union[float, int]] = None

    @property
    def stats(self) -> dict[str, Union[int, float]]:
        if self._stats is None:
            self._stats = self._get_stats()
        return self._stats

    def _get_stats(self) -> dict[str, Union[int, float]]:
        data = {item.group('name'): item.group('value') for item in self.performance_regex.finditer(self.message)}
        return {k: float(v) if '.' in v else int(v) for k, v in data.items()}

    @classmethod
    def check(cls, raw_record: "RawRecord") -> bool:
        logged_from = raw_record.parsed_data.get("logged_from")

        if logged_from is None:
            return False

        if logged_from.name == "logPerformance":

            return True

        return False


ALL_ANTISTASI_RECORD_CLASSES.add(PerformanceRecord)


class IsNewCampaignRecord(BaseRecord):
    ___record_family___ = RecordFamily.ANTISTASI
    ___specificity___ = 20
    __slots__ = ("log_record",)

    @classmethod
    def check(cls, raw_record: "RawRecord") -> bool:
        logged_from = raw_record.parsed_data.get("logged_from")

        if logged_from is None:
            return False
        if logged_from.name == "initServer" and "Creating new campaign with ID" in raw_record.parsed_data.get("message"):
            return True

        return False


ALL_ANTISTASI_RECORD_CLASSES.add(IsNewCampaignRecord)


class FFPunishmentRecord(BaseRecord):
    ___record_family___ = RecordFamily.ANTISTASI
    ___specificity___ = 10
    punishment_type_regex = re.compile(r"(?P<punishment_type>[A-Z]+)")
    __slots__ = ("log_record", "_punishment_type")

    def __init__(self, log_record: "LogRecord") -> None:
        super().__init__(log_record)
        self._punishment_type: str = None

    @property
    def punishment_type(self) -> str:
        if self._punishment_type is None:
            self._punishment_type = self.punishment_type_regex.search(self.message).group("punishment_type")
        return self._punishment_type

    @classmethod
    def check(cls, raw_record: "RawRecord") -> bool:
        logged_from = raw_record.parsed_data.get("logged_from")

        if logged_from is None:
            return False
        if logged_from.name in {"punishment_FF", "punishment"}:
            return True

        return False


ALL_ANTISTASI_RECORD_CLASSES.add(FFPunishmentRecord)

# region[Main_Exec]


if __name__ == '__main__':
    pass

# endregion[Main_Exec]
