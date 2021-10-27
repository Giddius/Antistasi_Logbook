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
from collections import Counter, ChainMap, deque, namedtuple, defaultdict, UserString
from urllib.parse import urlparse
from importlib.util import find_spec, module_from_spec, spec_from_file_location
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from rich.panel import Panel
from importlib.machinery import SourceFileLoader
from antistasi_logbook.utilities.nextcloud import get_username
from antistasi_logbook.utilities.rich_styles import PANEL_BORDER_STYLE, PANEL_STYLE
import urllib.parse as urllib_parse
import urllib.request as urllib_request

# endregion[Imports]

# region [TODO]


# endregion [TODO]

# region [Logging]


# endregion[Logging]

# region [Constants]

THIS_FILE_DIR = Path(__file__).parent.absolute()

# endregion[Constants]


def clean_path(in_path: Union[str, Path, os.PathLike]) -> Path:
    to_clean_parts = {"dev_drive", "remote.php", "dav", "files", get_username()}
    path = Path(in_path)
    try:
        split_on_id = max(path.parts.index(indicator) + 1 for indicator in to_clean_parts if indicator in path.parts)
        path = Path('/'.join(list(path.parts)[split_on_id:]))
    except ValueError:
        pass
    return path


class RemotePath(UserString):

    def __init__(self, path: os.PathLike) -> None:
        self._path: Path = clean_path(path)
        super().__init__(self._path.as_posix())

    def __getattr__(self, name: str) -> Any:
        if hasattr(self._path, name):
            return getattr(self._path, name)
        raise AttributeError(name)

    def joinpath(self, *other) -> "RemotePath":
        new_path = self._path.joinpath(*other)
        return self.__class__(new_path)

    @property
    def parent(self) -> "RemotePath":
        if self._path.parent:
            return RemotePath(self._path.parent)
        # TODO: add custom error
        raise RuntimeError(f'{self!r} has no Parent.')

    def __fspath__(self):
        return str(self)

    def __rich__(self):
        to_panel = []
        to_panel.append(f"[b u spring_green3]{self.__class__.__name__}[/b u spring_green3]\n")

        to_panel.append(f"[b gold1]path[/b gold1] = [pale_turquoise1]{self._path.as_posix()}[/pale_turquoise1]")
        return Panel('\n'.join(to_panel), style=PANEL_STYLE, border_style=PANEL_BORDER_STYLE)

    def __conform__(self, protocol):
        if protocol is sqlite3.PrepareProtocol:
            return self.__fspath__()


def url_to_path(url: str) -> Path:
    """
    Convert a file: URL to a path.
    """
    if not isinstance(url, str):
        url = str(url)
    assert url.startswith('file:'), (f"You can only turn file: urls into filenames (not {url!r})")

    _, netloc, path, _, _ = urllib_parse.urlsplit(url)

    # if we have a UNC path, prepend UNC share notation
    if netloc:
        netloc = '\\\\' + netloc

    path = urllib_request.url2pathname(netloc + path)
    return Path(path)
# region[Main_Exec]


if __name__ == '__main__':
    pass

# endregion[Main_Exec]
