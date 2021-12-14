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
import pyparsing as pp
from pyparsing import pyparsing_common as ppc
# endregion[Imports]

# region [TODO]


# endregion [TODO]

# region [Logging]


# endregion[Logging]

# region [Constants]

THIS_FILE_DIR = Path(__file__).parent.absolute()

# endregion[Constants]

# Array parsing Grammar

colon = pp.Suppress(',')
sqb_open = pp.Suppress('[')
sqb_close = pp.Suppress(']')
quote = pp.Suppress('"')
keywords = pp.Keyword("EAST") | pp.Keyword("WEST")
items = pp.Forward()
content = pp.Group(pp.ZeroOrMore(items + pp.Optional(colon)))
array = sqb_open + content + sqb_close
string = quote + pp.OneOrMore(pp.Word(pp.printables.replace('"', ''))) + quote
number = ppc.number
items <<= string | keywords | array | number


def parse_text_array(in_text: str) -> list[list[Any]]:
    return array.parse_string(in_text, parse_all=True).as_list()[0]

# region[Main_Exec]


if __name__ == '__main__':
    x = """[
        ["LAND_LIGHT",-1,"GROUP"]
["LAND_LIGHT",-1,"GROUP"]
["LAND_DEFAULT",0,"EMPTY"]
["HELI_TRANSPORT",-1,"SQUAD"]
["HELI_TRANSPORT",0,"EMPTY"]
["LAND_LIGHT",-1,"SQUAD"]
]"""
    pprint(parse_text_array(x))
# endregion[Main_Exec]
