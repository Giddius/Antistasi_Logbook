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
from github import Github
import github
import pp

from gidapptools import get_logger

if TYPE_CHECKING:
    from antistasi_logbook.gui.main_window import AntistasiLogbookMainWindow
    from antistasi_logbook.gui.application import AntistasiLogbookApplication

# endregion[Imports]

# region [TODO]


# endregion [TODO]

# region [Logging]


# endregion[Logging]

# region [Constants]

from gidapptools.general_helper.timing import get_dummy_profile_decorator_in_globals

THIS_FILE_DIR = Path(__file__).parent.absolute()
log = get_logger(__name__)

# endregion[Constants]
GITHUB_CLIENT = Github()


def url_to_identifier(in_url: str) -> str:
    _out = in_url.removeprefix("https://").removeprefix("github.com/").split("/")
    _out = _out[0] + '/' + _out[1]
    return _out


def get_repo(in_url: str):
    return GITHUB_CLIENT.get_repo(url_to_identifier(in_url))


def get_branch(repo, branch_name: str = None):
    branch_name = branch_name or repo.default_branch
    return repo.get_branch(branch_name)


def get_repo_file_list(url: str, branch_name: str = None):
    repo = get_repo(url)
    branch = get_branch(repo, branch_name=branch_name)
    latest_sha = branch.commit.sha
    tree = repo.get_git_tree(latest_sha, True)
    file_items = {}
    for item in tree.tree:
        path = str(item.path)
        content_item = repo.get_contents(path, ref=branch.name)

        name = os.path.basename(path)
        try:
            file_items[name] = str(content_item.html_url)
        except AttributeError:
            continue
    return file_items


print(GITHUB_CLIENT.rate_limiting_resettime)
fi = get_repo_file_list("https://github.com/official-antistasi-community/A3-Antistasi")


pp(fi)
# region[Main_Exec]

if __name__ == '__main__':
    pass

# endregion[Main_Exec]
