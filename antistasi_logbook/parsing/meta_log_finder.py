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
from antistasi_logbook.utilities.misc import Version, ModItem
from gidapptools.general_helper.enums import MiscEnum
from dateutil.tz import UTC
from gidapptools import get_logger
if TYPE_CHECKING:
    from antistasi_logbook.parsing.parsing_context import ParsingContext
    from antistasi_logbook.regex.regex_keeper import SimpleRegexKeeper
# endregion[Imports]

# region [TODO]


# endregion [TODO]

# region [Logging]


# endregion[Logging]

# region [Constants]

THIS_FILE_DIR = Path(__file__).parent.absolute()
log = get_logger(__name__)
# endregion[Constants]


class MetaFinder:

    __slots__ = ("game_map", "full_datetime", "version", "mods", "campaign_id", "is_new_campaign", "regex_keeper")

    def __init__(self, regex_keeper: "SimpleRegexKeeper", context: "ParsingContext") -> None:
        self.regex_keeper = regex_keeper
        self.game_map: str = MiscEnum.NOT_FOUND if not context._log_file.has_game_map() else MiscEnum.DEFAULT
        self.full_datetime: tuple[datetime, datetime] = MiscEnum.NOT_FOUND if not context._log_file.utc_offset else MiscEnum.DEFAULT
        self.version: Version = MiscEnum.NOT_FOUND if not context._log_file.version else MiscEnum.DEFAULT
        self.mods: list[ModItem] = MiscEnum.NOT_FOUND if not context._log_file.has_mods() else MiscEnum.DEFAULT
        self.campaign_id: int = MiscEnum.NOT_FOUND if context._log_file.campaign_id is None else MiscEnum.DEFAULT
        self.is_new_campaign: bool = MiscEnum.NOT_FOUND if context._log_file.is_new_campaign is None else MiscEnum.DEFAULT

    def all_found(self) -> bool:
        # takes about 0.000742 s
        return all(i is not MiscEnum.NOT_FOUND for i in [self.game_map, self.full_datetime, self.version, self.campaign_id, self.is_new_campaign])

    def _resolve_full_datetime(self, text: str) -> None:
        if match := self.regex_keeper.first_full_datetime.search(text):
            utc_datetime_kwargs = {k: int(v) for k, v in match.groupdict().items() if not k.startswith('local_')}
            local_datetime_kwargs = {k.removeprefix('local_'): int(v) for k, v in match.groupdict().items() if k.startswith('local_')}
            self.full_datetime = (datetime(tzinfo=UTC, **utc_datetime_kwargs), datetime(tzinfo=UTC, **local_datetime_kwargs))

    def _resolve_version(self, text: str) -> None:
        if match := self.regex_keeper.game_file.search(text):
            raw = match.group('game_file')
            version_args = [c for c in raw if c.isnumeric()]
            if version_args:
                while len(version_args) < 3:
                    version_args.append('MISSING')
                version = Version(*version_args)
                self.version = version
            else:
                log.debug("incomplete version from line: %r", match.group('game_file'))
                self.version = None

    def _resolve_game_map(self, text: str) -> None:
        # takes about 0.170319 s
        if match := self.regex_keeper.game_map.search(text):
            log.debug("found game-map as %r", match)
            self.game_map = match.group('game_map')

    def _resolve_mods(self, text: str) -> None:
        # takes about 0.263012 s
        if match := self.regex_keeper.mods.search(text):
            mod_lines = match.group('mod_lines').splitlines()

            cleaned_mod_lines = [self.regex_keeper.mod_time_strip.sub("", line) for line in mod_lines if '|' in line and 'modDir' not in line]

            self.mods = [ModItem.from_text_line(line) for line in cleaned_mod_lines]

    def _resolve_campaign_id(self, text: str) -> None:
        if match := self.regex_keeper.campaign_id.search(text):

            self.campaign_id = int(match.group("campaign_id"))

            if match.group("text_loading") is not None:
                self.is_new_campaign = False
            elif match.group("text_creating") is not None:
                self.is_new_campaign = True

    def search(self, text: str) -> None:
        if self.campaign_id is MiscEnum.NOT_FOUND:
            self._resolve_campaign_id(text)

        if self.game_map is MiscEnum.NOT_FOUND:
            self._resolve_game_map(text)

        if self.version is MiscEnum.NOT_FOUND:
            self._resolve_version(text)

        if self.full_datetime is MiscEnum.NOT_FOUND:
            self._resolve_full_datetime(text)

        if self.mods is MiscEnum.NOT_FOUND:
            self._resolve_mods(text)

    def change_missing_to_none(self) -> None:

        if self.campaign_id is MiscEnum.NOT_FOUND:
            self.campaign_id = None

        if self.is_new_campaign is MiscEnum.NOT_FOUND:
            self.is_new_campaign = None

        if self.game_map is MiscEnum.NOT_FOUND:
            self.game_map = None

        if self.version is MiscEnum.NOT_FOUND:
            self.version = None

        if self.full_datetime is MiscEnum.NOT_FOUND:
            self.full_datetime = None

        if self.mods is MiscEnum.NOT_FOUND:
            self.mods = None


# region[Main_Exec]
if __name__ == '__main__':
    pass

# endregion[Main_Exec]
