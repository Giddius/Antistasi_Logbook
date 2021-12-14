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
from antistasi_logbook.records.base_record import BaseRecord, RecordFamily, BASE_SLOTS, LineNumberLocation, QtAttributes
import pp
from antistasi_logbook.utilities.parsing_misc import parse_text_array
from gidapptools.general_helper.color.color_item import RGBColor, Color
if TYPE_CHECKING:
    from antistasi_logbook.parsing.parser import RawRecord
    from antistasi_logbook.storage.models.models import LogFile, LogRecord, PunishmentAction, LogLevel, AntstasiFunction
# endregion[Imports]

# region [TODO]


# endregion [TODO]

# region [Logging]


# endregion[Logging]

# region [Constants]

THIS_FILE_DIR = Path(__file__).parent.absolute()

# endregion[Constants]

ALL_ANTISTASI_RECORD_CLASSES: set[type[BaseRecord]] = set()


class BaseAntistasiRecord(BaseRecord):
    ___record_family___ = RecordFamily.ANTISTASI
    ___specificity___ = 1
    ___has_multiline_message___ = False
    __slots__ = tuple(BASE_SLOTS)

    @property
    def color(self) -> Optional[RGBColor]:
        if self.qt_attributes.color is None:
            self.qt_attributes.color = Color.get_color_by_name("White").with_alpha(0.5).qcolor
        return self.qt_attributes.color

    @classmethod
    def check(cls, raw_record: "RawRecord") -> bool:
        return True


ALL_ANTISTASI_RECORD_CLASSES.add(BaseAntistasiRecord)


class PerformanceRecord(BaseAntistasiRecord):
    ___record_family___ = RecordFamily.ANTISTASI
    ___specificity___ = 10
    ___has_multiline_message___ = True
    performance_regex = re.compile(r"(?P<name>\w+\s?\w*)(?:\:\s?)(?P<value>\d[\d\.]*)")
    __slots__ = tuple(BASE_SLOTS + ["_stats"])

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._stats: dict[str, Union[float, int]] = None

    @property
    def color(self) -> Optional[RGBColor]:
        if self.qt_attributes.color is None:
            self.qt_attributes.color = Color.get_color_by_name("LightSteelBlue").with_alpha(0.5).qcolor
        return self.qt_attributes.color

    @property
    def stats(self) -> dict[str, Union[int, float]]:
        if self._stats is None:
            self._stats = self._get_stats()
        return self._stats

    def _get_stats(self) -> dict[str, Union[int, float]]:
        data = {item.group('name'): item.group('value') for item in self.performance_regex.finditer(self.message)}
        return {k: float(v) if '.' in v else int(v) for k, v in data.items()}

    def get_formated_message(self, msg_format: "MessageFormat" = MessageFormat.PRETTY) -> str:
        if msg_format is MessageFormat.PRETTY:
            _out = []
            for k, v in self.stats.items():
                try:
                    _full_num, _after_comma = str(v).split('.')
                    _comma = "."
                except ValueError:
                    _full_num = str(v)
                    _comma = ""
                    _after_comma = ""
                _out.append(f"{k:<25}{_full_num:>25}{_comma}{_after_comma}")
            return '\n'.join(_out).strip()
        return super().get_formated_message(msg_format=format)

    @classmethod
    def check(cls, raw_record: "RawRecord") -> bool:
        logged_from = raw_record.parsed_data.get("logged_from")

        if logged_from is None:
            return False

        if logged_from == "logPerformance":

            return True

        return False


ALL_ANTISTASI_RECORD_CLASSES.add(PerformanceRecord)


class IsNewCampaignRecord(BaseAntistasiRecord):
    ___record_family___ = RecordFamily.ANTISTASI
    ___specificity___ = 20
    __slots__ = tuple(BASE_SLOTS)

    @classmethod
    def check(cls, raw_record: "RawRecord") -> bool:
        logged_from = raw_record.parsed_data.get("logged_from")

        if logged_from is None:
            return False
        if logged_from == "initServer" and "Creating new campaign with ID" in raw_record.parsed_data.get("message"):
            return True

        return False


ALL_ANTISTASI_RECORD_CLASSES.add(IsNewCampaignRecord)


class FFPunishmentRecord(BaseAntistasiRecord):
    ___record_family___ = RecordFamily.ANTISTASI
    ___specificity___ = 10
    punishment_type_regex = re.compile(r"(?P<punishment_type>[A-Z]+)")
    __slots__ = tuple(BASE_SLOTS + ["_punishment_type"])

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
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
        if logged_from in {"punishment_FF", "punishment"}:
            return True

        return False


ALL_ANTISTASI_RECORD_CLASSES.add(FFPunishmentRecord)


class UpdatePreferenceRecord(BaseAntistasiRecord):
    ___record_family___ = RecordFamily.ANTISTASI
    ___specificity___ = 20
    ___has_multiline_message___ = True

    msg_start_regex = re.compile(r"(?P<category>[a-zA-Z]+)\_preference")

    __slots__ = tuple(BASE_SLOTS + ["category", "_array_data"])

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.category = self.msg_start_regex.match(self.message.lstrip()).group("category")
        self._array_data: list[list[Any]] = None

    @property
    def array_data(self) -> list[list[Any]]:
        if self._array_data is None:
            self._array_data = parse_text_array(self.msg_start_regex.sub('', self.message).strip())
        return self._array_data

    @classmethod
    def check(cls, raw_record: "RawRecord") -> bool:
        logged_from = raw_record.parsed_data.get("logged_from")

        if logged_from is None:
            return False
        if logged_from in {"updatePreference"} and cls.msg_start_regex.match(raw_record.parsed_data.get("message").lstrip()):
            return True
        return False

    def get_formated_message(self, msg_format: "MessageFormat" = MessageFormat.PRETTY) -> str:
        if msg_format is MessageFormat.PRETTY:
            return f"{self.category}_preference\n" + pp.fmt(self.array_data, indent=4)
        return super().get_formated_message(msg_format=format)


ALL_ANTISTASI_RECORD_CLASSES.add(UpdatePreferenceRecord)


class CreateConvoyInputRecord(BaseAntistasiRecord):
    ___record_family___ = RecordFamily.ANTISTASI
    ___specificity___ = 20
    ___has_multiline_message___ = True
    __slots__ = tuple(BASE_SLOTS + ["_array_data"])

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._array_data: list[list[Any]] = None

    @property
    def array_data(self) -> list[list[Any]]:
        if self._array_data is None:
            array_txt = self.message[self.message.find('['):]
            self._array_data = parse_text_array(array_txt)
        return self._array_data

    @classmethod
    def check(cls, raw_record: "RawRecord") -> bool:
        logged_from = raw_record.parsed_data.get("logged_from")

        if logged_from is None:
            return
        if logged_from in {"createConvoy"} and raw_record.parsed_data.get("message").casefold().startswith("input"):
            return True
        return False

    def get_formated_message(self, msg_format: "MessageFormat" = MessageFormat.PRETTY) -> str:
        if msg_format is MessageFormat.PRETTY:
            txt = "Input is "
            array_data_text_lines = pp.fmt(self.array_data).replace("'", '"').replace('"WEST"', 'WEST').replace('"EAST"', 'EAST').splitlines()
            txt_len = len(txt)
            txt += array_data_text_lines[0] + '\n'
            for line in array_data_text_lines[1:]:
                txt += ' ' * txt_len + line + '\n'
            return txt
        return super().get_formated_message(format=format)


ALL_ANTISTASI_RECORD_CLASSES.add(CreateConvoyInputRecord)
# region[Main_Exec]


if __name__ == '__main__':
    pass

# endregion[Main_Exec]
