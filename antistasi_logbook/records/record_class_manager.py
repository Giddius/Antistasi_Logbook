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
from sortedcontainers import SortedList, SortedKeyList, SortedSet
from antistasi_logbook.storage.models.models import RecordClass
from antistasi_logbook.records.base_record import BaseRecord, RecordFamily
import attr
if TYPE_CHECKING:
    from antistasi_logbook.records.abstract_record import AbstractRecord
    from antistasi_logbook.parsing.parser import RawRecord

# endregion[Imports]

# region [TODO]


# endregion [TODO]

# region [Logging]


# endregion[Logging]

# region [Constants]
from gidapptools.general_helper.timing import get_dummy_profile_decorator_in_globals
get_dummy_profile_decorator_in_globals()
THIS_FILE_DIR = Path(__file__).parent.absolute()

# endregion[Constants]

RECORD_CLASS_TYPE = Union[type["AbstractRecord"], type["BaseRecord"]]


@attr.s(auto_attribs=True, auto_detect=True, frozen=True, slots=True)
class StoredRecordClass:
    concrete_class: RECORD_CLASS_TYPE = attr.ib()
    model: RecordClass = attr.ib()

    def check(self, raw_record: "RawRecord") -> bool:
        return self.concrete_class.check(raw_record=raw_record)


class RecordClassManager:
    record_class_registry: dict[str, StoredRecordClass] = {}
    generic_record_classes: SortedSet[StoredRecordClass] = SortedSet(key=lambda x: -x.concrete_class.___specificity___)
    antistasi_record_classes: SortedSet[StoredRecordClass] = SortedSet(key=lambda x: -x.concrete_class.___specificity___)

    def __init__(self, default_record_class: RECORD_CLASS_TYPE = None) -> None:
        self._default_record_concrete_class = BaseRecord if default_record_class is None else default_record_class
        self._default_record_class: "StoredRecordClass" = None

    @property
    def default_record_class(self) -> StoredRecordClass:
        if self._default_record_class is None:
            try:
                model = RecordClass.select().where(RecordClass.name == self._default_record_concrete_class.__name__)[0]
            except IndexError:
                model = RecordClass(name=self._default_record_concrete_class.__name__)
                model.save()
            self._default_record_class = StoredRecordClass(self._default_record_concrete_class, model)
        return self._default_record_class

    @classmethod
    def register_record_class(cls, record_class: RECORD_CLASS_TYPE) -> None:
        name = record_class.__name__
        if name in cls.record_class_registry:
            return
        try:
            model = RecordClass.select().where(RecordClass.name == name)[0]
        except IndexError:
            model = RecordClass(name=name)
            model.save()
        stored_item = StoredRecordClass(record_class, model)
        cls.record_class_registry[name] = stored_item
        if RecordFamily.GENERIC in record_class.___record_family___:
            cls.generic_record_classes.add(stored_item)
        if RecordFamily.ANTISTASI in record_class.___record_family___:
            cls.antistasi_record_classes.add(stored_item)

    def get_by_name(self, name: str) -> RECORD_CLASS_TYPE:
        return self.record_class_registry.get(name, self.default_record_class).concrete_class

    @profile
    def determine_record_class(self, raw_record: "RawRecord") -> "RecordClass":
        record_classes = self.antistasi_record_classes if raw_record.is_antistasi_record is True else self.generic_record_classes
        for stored_class in record_classes:
            if stored_class.check(raw_record) is True:
                return stored_class.model
        return self.default_record_class.model

    def reset(self) -> None:
        all_registered_classes = list(self.record_class_registry.values())
        self.record_class_registry.clear()
        self.antistasi_record_classes.clear()
        self.generic_record_classes.clear()
        self._default_record_class = None
        for registered_class in all_registered_classes:
            self.register_record_class(registered_class.concrete_class)
# region[Main_Exec]


if __name__ == '__main__':
    pass

# endregion[Main_Exec]
