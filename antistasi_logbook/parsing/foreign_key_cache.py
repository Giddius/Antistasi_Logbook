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
from gidapptools.general_helper.concurrency.events import BlockingEvent
from playhouse.signals import post_save, pre_save, pre_delete, pre_init
from antistasi_logbook.storage.models.models import GameMap, LogFile, LogRecord, LogLevel, AntstasiFunction, Server
from playhouse.shortcuts import model_to_dict, dict_to_model
# endregion[Imports]

# region [TODO]


# endregion [TODO]

# region [Logging]


# endregion[Logging]

# region [Constants]

THIS_FILE_DIR = Path(__file__).parent.absolute()

# endregion[Constants]


class ForeignKeyCache:
    log_levels_blocker = BlockingEvent()
    game_map_model_blocker = BlockingEvent()
    antistasi_file_model_blocker = BlockingEvent()
    _all_log_levels: dict[str, LogLevel] = None
    _all_antistasi_file_objects: dict[str, AntstasiFunction] = None
    _all_game_map_objects: dict[str, GameMap] = None

    __slots__ = ("update_map")

    def __init__(self) -> None:
        self.update_map = {AntstasiFunction: (self.antistasi_file_model_blocker, "_all_antistasi_file_objects"),
                           GameMap: (self.game_map_model_blocker, "_all_game_map_objects"),
                           LogLevel: (self.log_levels_blocker, "_all_log_levels")}
        self._register_signals()

    def _register_signals(self) -> None:
        for model_class in self.update_map:
            try:
                post_save.connect(self.on_save_handler, sender=model_class)
            except ValueError:
                continue

    @property
    def all_log_levels(self) -> dict[str, LogLevel]:

        if self.__class__._all_log_levels is None:
            self.log_levels_blocker.wait()
            self.__class__._all_log_levels = {item.name: item for item, _id in ((i, i.id) for i in LogLevel.select())}

        return self.__class__._all_log_levels

    @property
    def all_antistasi_file_objects(self) -> dict[str, AntstasiFunction]:

        if self.__class__._all_antistasi_file_objects is None:
            self.antistasi_file_model_blocker.wait()
            self.__class__._all_antistasi_file_objects = {item.name: item for item, _id in ((i, i.id) for i in AntstasiFunction.select())}

        return self.__class__._all_antistasi_file_objects

    @property
    def all_game_map_objects(self) -> dict[str, GameMap]:

        if self.__class__._all_game_map_objects is None:
            self.game_map_model_blocker.wait()
            self.__class__._all_game_map_objects = {item.name: item for item, _id in ((i, i.id) for i in GameMap.select())}

        return self.__class__._all_game_map_objects

    def on_save_handler(self, sender, instance, created):
        if created:
            event, class_attr_name = self.update_map.get(sender, (None, None))
            if event is None:
                return
            with event:
                setattr(self.__class__, class_attr_name, None)
            log.warning(f" reseted '{class_attr_name}', because {model_to_dict(instance, recurse=False)} of {sender.__name__!r} was created:{created!r}")


foreign_key_cache = ForeignKeyCache()


# region[Main_Exec]

if __name__ == '__main__':
    pass

# endregion[Main_Exec]
