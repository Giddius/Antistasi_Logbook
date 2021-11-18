"""
WiP.

Soon.
"""

# region [Imports]

import gc
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
import unicodedata
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
from typing import TYPE_CHECKING, Union, Callable, Iterable, Optional, Mapping, Any, IO, TextIO, BinaryIO
from zipfile import ZipFile, ZIP_LZMA
from datetime import datetime, timezone, timedelta
from tempfile import TemporaryDirectory
from textwrap import TextWrapper, fill, wrap, dedent, indent, shorten
from functools import wraps, partial, lru_cache, singledispatch, total_ordering, cached_property
from importlib import import_module, invalidate_caches
from contextlib import contextmanager, asynccontextmanager
from statistics import mean, mode, stdev, median, variance, pvariance, harmonic_mean, median_grouped
from collections import Counter, ChainMap, deque, namedtuple, defaultdict
from urllib.parse import urlparse
from importlib.util import find_spec, module_from_spec, spec_from_file_location
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from importlib.machinery import SourceFileLoader

from gidapptools.general_helper.enums import BaseGidEnum
from gidapptools.meta_data import get_meta_info, get_meta_paths, get_meta_item, app_meta
from gidapptools.gid_logger.fake_logger import fake_logger
# endregion[Imports]

# region [TODO]


# endregion [TODO]

# region [Logging]


from gidapptools.general_helper.timing import get_dummy_profile_decorator_in_globals
get_dummy_profile_decorator_in_globals()
log = fake_logger
# endregion[Logging]

# region [Constants]
if app_meta.is_setup is False:
    import antistasi_logbook
THIS_FILE_DIR = Path(__file__).parent.absolute()
META_PATHS = get_meta_paths()
META_INFO = get_meta_info()


# endregion[Constants]


class RemoteItemType(BaseGidEnum):
    DIRECTORY = "directory"
    FILE = "file"

# region[Main_Exec]


if __name__ == '__main__':
    pass

# endregion[Main_Exec]
