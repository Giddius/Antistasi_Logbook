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
from sortedcontainers import SortedList
if TYPE_CHECKING:
    from antistasi_logbook.records.base_record import BaseRecord
    from antistasi_logbook.storage.models.models import Server, LogFile

# endregion[Imports]

# region [TODO]


# endregion [TODO]

# region [Logging]


# endregion[Logging]

# region [Constants]

THIS_FILE_DIR = Path(__file__).parent.absolute()

# endregion[Constants]


def discord_format(in_record: "BaseRecord") -> str:
    server = in_record.log_file.server
    log_file = in_record.log_file
    text = f"**__Server:__** `{server.pretty_name}`, **__Log-File:__** `{log_file.pretty_name}`, **__Lines:__** `{in_record.start}`-`{in_record.end}`\n"
    joined_lines = '\n'.join(f"<{ln}> {l}" for ln, l in in_record.log_file.original_file.get_lines_with_line_numbers(start=in_record.start, end=in_record.end))
    text += f"```sqf\n{joined_lines}\n```"
    return text


class DiscordText:
    text_template: str = "**__Server:__** `{server}`, **__Log-File:__** `{log_file}`\n```sqf\n{record_lines}\n```"

    def __init__(self, records: Iterable["BaseRecord"]) -> None:
        self.records = records

    def get_records_map(self) -> defaultdict[tuple["Server", "LogFile"], list["BaseRecord"]]:
        _out = defaultdict(partial(SortedList, key=lambda x: (x.start, x.end)))
        for record in self.records:
            _out[(record.server, record.log_file)].add(record)
        return _out

    def make_text(self) -> str:
        text = ""
        for meta_data, records in self.get_records_map().items():
            record_lines = ""
            last_record_line = None
            for record in records:
                raw_record_lines = record.log_file.original_file.get_lines_with_line_numbers(start=record.start, end=record.end)
                if last_record_line is not None and raw_record_lines[-1][0] != last_record_line + 1:
                    record_lines += '...\n'

                record_lines += '\n'.join(f"<{ln}> {l}" for ln, l in raw_record_lines) + '\n'
                last_record_line = raw_record_lines[-1][0]
            text += self.text_template.format(server=meta_data[0].pretty_name, log_file=meta_data[1].pretty_name, record_lines=record_lines.strip()) + '\n\n'
        return text.strip()

    def __str__(self) -> str:
        return self.make_text()

    def __repr__(self) -> str:
        """
        Basic Repr
        !REPLACE!
        """
        return f'{self.__class__.__name__}'

# region[Main_Exec]


if __name__ == '__main__':
    pass

# endregion[Main_Exec]
