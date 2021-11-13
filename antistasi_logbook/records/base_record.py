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

from antistasi_logbook.records.abstract_record import AbstractRecord, RecordFamily, MessageFormat
from antistasi_logbook.records.enums import LogLevelEnum, PunishmentActionEnum
if TYPE_CHECKING:
    from antistasi_logbook.storage.models.models import LogFile, LogRecord, PunishmentAction, LogLevel, AntstasiFunction
    from antistasi_logbook.parsing.parser import RawRecord
# endregion[Imports]

# region [TODO]


# endregion [TODO]

# region [Logging]


# endregion[Logging]

# region [Constants]

THIS_FILE_DIR = Path(__file__).parent.absolute()

# endregion[Constants]


class BaseRecord(AbstractRecord):
    ___record_family___ = RecordFamily.GENERIC | RecordFamily.ANTISTASI
    ___specificity___ = 0
    __slots__ = ("log_record",)

    def __init__(self,
                 log_record: "LogRecord"
                 ) -> None:
        self.log_record = log_record

    def mark(self) -> None:
        self.log_record.marked = True
        self.log_record.save()

    @property
    def comments(self) -> Optional[str]:
        return self.log_record.comments

    def add_comment(self, comment: str) -> None:
        if self.log_record.comments is None:
            self.log_record.comments = comment
        else:
            self.log_record.comments = self.log_record.comments + '\n' + comment
        self.log_record.save()

    def get_formated_message(self, format: "MessageFormat") -> str:
        return self.message

    def __getattr__(self, name: str) -> Any:

        return getattr(self.log_record, name)

    @classmethod
    def check(cls, raw_record: "RawRecord") -> bool:
        return True


# region[Main_Exec]


if __name__ == '__main__':
    pass

# endregion[Main_Exec]
