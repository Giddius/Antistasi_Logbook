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
from collections import Counter, ChainMap, deque, namedtuple, defaultdict, UserList
from urllib.parse import urlparse
from importlib.util import find_spec, module_from_spec, spec_from_file_location
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from importlib.machinery import SourceFileLoader
from gidapptools.gid_logger.fake_logger import fake_logger
import numpy as np
from statistics import stdev, mean, median, median_grouped, median_high, median_low, harmonic_mean, geometric_mean, quantiles, multimode, mode, fmean, StatisticsError
if TYPE_CHECKING:
    from antistasi_logbook.storage.models.models import LogFile

# endregion[Imports]

# region [TODO]


# endregion [TODO]

# region [Logging]


# endregion[Logging]

# region [Constants]

THIS_FILE_DIR = Path(__file__).parent.absolute()
log = fake_logger
# endregion[Constants]


# mean + 2 stdev chars for "first_full_datetime" -> 185931
# mean + 2 stdev chars for "game_world" -> 179659

class StatisticsList(list):

    def __init__(self, *items, only_int: bool = False) -> None:
        super().__init__()
        self.only_int = only_int
        self.round_n = 2 if self.only_int else 4
        for item in items:
            self.append(item)

    def append(self, value) -> None:
        if self.only_int is True and isinstance(value, float):
            raise TypeError(f"An {self.__class__.__name__} with 'only_int' set to True, does not accept a float.")
        super().append(value)

    @property
    def stdev(self) -> Optional[float]:
        try:
            return stdev(self)
        except StatisticsError:
            return None

    @property
    def mean(self) -> Optional[Union[float, int]]:
        try:
            return mean(self)
        except StatisticsError:
            return None

    @property
    def fmean(self) -> Optional[Union[float, int]]:
        try:
            return fmean(self)
        except StatisticsError:
            return None

    @property
    def median(self) -> Optional[Union[float, int]]:
        try:
            return median(self)
        except StatisticsError:
            return None

    @property
    def median_high(self) -> Optional[Union[float, int]]:
        try:
            return median_high(self)
        except StatisticsError:
            return None

    @property
    def median_low(self) -> Optional[Union[float, int]]:
        try:
            return median_low(self)
        except StatisticsError:
            return None

    @property
    def mode(self) -> Optional[Union[float, int]]:
        try:
            return mode(self)
        except StatisticsError:
            return None

    @property
    def quantiles(self) -> Optional[Union[float, int]]:
        try:
            return quantiles(self)
        except StatisticsError:
            return None

    @property
    def multimode(self) -> Optional[Union[float, int]]:
        try:
            return multimode(self)
        except StatisticsError:
            return None

    @property
    def geometric_mean(self) -> Optional[Union[float, int]]:
        try:
            return geometric_mean(self)
        except StatisticsError:
            return None

    def as_dict(self) -> dict[str, Union[list, int, float]]:
        _out = {}
        _out["raw_data"] = list(self)
        for attr_name in ["stdev", "mean", "median", "median_high", "median_low", "mode", "quantiles", "fmean", "multimode", "geometric_mean"]:
            attribute = getattr(self, attr_name)
            if isinstance(attribute, float):
                attribute = round(attribute, self.round_n)
            _out[attr_name] = attribute
        return _out


class DiagnosticParser:

    def __init__(self, regexer) -> None:
        self.regexer = regexer
        self.line_numbers: dict[str, list[int]] = defaultdict(StatisticsList)
        self.char_numbers: dict[str, list[int]] = defaultdict(StatisticsList)

    def __call__(self, log_file: "LogFile") -> Any:
        line_num = 0
        char_num = 0
        game_world_found = False
        full_date_time_found = False
        with log_file.open() as f:
            for line in f:
                line_num += 1
                char_num += len(line)
                game_world_match = self.regexer.game_map.search(line)
                if game_world_match:
                    self.line_numbers["game_world"].append(line_num)
                    self.char_numbers["game_world"].append(char_num)
                    log.debug(f'{game_world_match.group("game_map")=} at {line_num=} and {char_num=}')
                    game_world_found = True

                if full_date_time_found is False:
                    full_datetime_match = self.regexer.full_datetime.search(line)
                    if full_datetime_match:
                        self.line_numbers["full_datetime"].append(line_num)
                        self.char_numbers["full_datetime"].append(char_num)
                        log.debug(f'{full_datetime_match.group()=} at {line_num=} and {char_num=}')
                        full_date_time_found = True
                if full_date_time_found is True and game_world_found is True:
                    break

    def close(self) -> None:
        line_num_data = {k: v.as_dict() for k, v in self.line_numbers.items()}
        char_num_data = {k: v.as_dict() for k, v in self.char_numbers.items()}
        with THIS_FILE_DIR.joinpath('diagnostic_parser_output_line_numbers.json').open('w', encoding='utf-8', errors='ignore') as f:
            json.dump(line_num_data, f, indent=4, default=str)
        with THIS_FILE_DIR.joinpath('diagnostic_parser_output_char_numbers.json').open('w', encoding='utf-8', errors='ignore') as f:
            json.dump(char_num_data, f, indent=4, default=str)

# region[Main_Exec]


if __name__ == '__main__':
    pass

# endregion[Main_Exec]
