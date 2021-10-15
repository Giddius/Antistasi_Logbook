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
from functools import wraps, partial, lru_cache, singledispatch, total_ordering, cached_property, reduce
from operator import or_, add
from importlib import import_module, invalidate_caches
from contextlib import contextmanager, asynccontextmanager, nullcontext, closing, ExitStack, suppress
from statistics import mean, mode, stdev, median, variance, pvariance, harmonic_mean, median_grouped
from collections import Counter, ChainMap, deque, namedtuple, defaultdict
from urllib.parse import urlparse
from importlib.util import find_spec, module_from_spec, spec_from_file_location
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from importlib.machinery import SourceFileLoader


# endregion[Imports]

# region [TODO]


# endregion [TODO]

# region [Logging]


# endregion[Logging]

# region [Constants]

THIS_FILE_DIR = Path(__file__).parent.absolute()

# endregion[Constants]


def _deconstruct_regex_flags_to_list(flag_value: int) -> list[re.RegexFlag]:
    flag = re.RegexFlag(flag_value)
    return list({member for member in re.RegexFlag.__members__.values() if member in flag})


def insert_regex_group_value(pattern_string: str, group_name: str, new_value: str) -> str:
    new_value = re.sub(r"(?<!\\)\\(?!\\)", r"\\\\", new_value)
    pattern = r"\(\?P\<(?P<group_name>{name})>(?P<group_value>.*?)\)(?P<__rest__>.*)".format(name=group_name)
    replacement = "(?P<\g<group_name>>{value})\g<__rest__>".format(value=new_value)
    return re.sub(pattern, replacement, pattern_string)


class AfterInitMeta(type):

    def __call__(cls, *args: Any, **kwds: Any) -> Any:
        instance = super(AfterInitMeta, cls).__call__(*args, **kwds)
        instance.___after_init___()
        return instance


class RegexPattern(metaclass=AfterInitMeta):
    __slots__ = ("_pattern_string", "_flags", "_compiled_pattern", "_is_init")
    _pattern_string: str
    _flags: list[re.RegexFlag]
    _compiled_pattern: re.Pattern
    _is_init: bool

    # Not sure if this is the corect way to do this

    def __init__(self, pattern_string: str, flags: Union[re.RegexFlag, Iterable[re.RegexFlag]] = None) -> None:

        # super().__setattr__("_pattern_string", pattern_string)
        # super().__setattr__("_flags", self._handle_flags(flags))
        # super().__setattr__("_compiled_pattern", None)
        self._pattern_string = pattern_string
        self._flags = self._handle_flags(flags)
        self._compiled_pattern = None

    def ___after_init___(self):
        self._is_init = True

    @staticmethod
    def _handle_flags(flags: Union[None, re.RegexFlag, Iterable[re.RegexFlag]]) -> list[re.RegexFlag]:
        if flags is None:
            return []
        if isinstance(flags, Iterable):
            return list(flags)

        return [flags]

    @property
    def groupindex(self) -> Mapping[str, int]:
        return self.compiled_pattern.groupindex

    def group_names(self) -> tuple[str]:
        return tuple(self.groupindex)

    @property
    def pattern_string(self) -> str:
        return self._pattern_string

    @ property
    def flags(self) -> int:
        return reduce(or_, self._flags, 0)

    @ property
    def compiled_pattern(self) -> re.Pattern:
        if self._compiled_pattern is None:
            super().__setattr__("_compiled_pattern", re.compile(pattern=self.pattern_string, flags=self.flags))

        return self._compiled_pattern

    def __hash__(self) -> int:
        flag_hash = 0
        for flag in self._flags:
            flag_hash += hash(flag)
        return hash(self._pattern_string) + flag_hash

    def __add__(self, other: object) -> "RegexPattern":
        if isinstance(other, self.__class__):
            new_pattern_string = self.pattern_string + other.pattern_string
            new_flags = set(self._flags + other._flags)
            return self.__class__(new_pattern_string, new_flags)

        if isinstance(other, re.Pattern):
            new_pattern_string = self.pattern_string + other.pattern
            new_flags = set(self._flags + _deconstruct_regex_flags_to_list(other.flags))
            return self.__class__(new_pattern_string, new_flags)

        if isinstance(other, str):
            new_pattern_string = self.pattern_string + other
            return self.__class__(new_pattern_string, self._flags)

        if isinstance(other, re.RegexFlag):
            new_flags = set(self._flags + [other])
            return self.__class__(self.pattern_string, new_flags)

        return NotImplemented

    # TODO: Check if this is needed or wanted.
    # def __radd__(self, other: object) -> "RegexPattern":
    #     return self.__add__(other)

    def __or__(self, other: object) -> "RegexPattern":
        if isinstance(other, self.__class__):
            new_pattern_string = r'|'.join([self._pattern_string, other._pattern_string])
            new_flags = set(self._flags + other._flags)
            return self.__class__(new_pattern_string, new_flags)

        if isinstance(other, re.Pattern):
            new_pattern_string = r'|'.join([self._pattern_string, other.pattern])
            new_flags = set(self._flags + _deconstruct_regex_flags_to_list(other.flags))
            return self.__class__(new_pattern_string, new_flags)

        if isinstance(other, str):
            new_pattern_string = r'|'.join([self._pattern_string, other])
            return self.__class__(new_pattern_string, self._flags)

        return NotImplemented

    # TODO: Check if this is needed or wanted.
    # def __ror__(self, other: object) -> "RegexPattern":
    #     return self.__or__(other)

    def __setattr__(self, name: str, value: Any) -> None:
        if hasattr(self, '_is_init') and self._is_init is True:
            raise TypeError(f"{self.__class__.__name__!r} object does not support item assignment")
        super().__setattr__(name, value)

    def __getattr__(self, name: str):
        if name == '_is_init':
            return getattr(super(), name, False)
        if hasattr(self.compiled_pattern, name):
            # Maybe: implement this explicitly.
            return getattr(self.compiled_pattern, name)
        raise AttributeError(name)

    def format(self, **kwargs) -> "RegexPattern":
        new_pattern_string = self._pattern_string.format(**kwargs)
        return self.__class__(new_pattern_string, self._flags)

    def format_group_values(self, **group_key_values) -> "RegexPattern":
        pattern_string = self._pattern_string
        for key, value in group_key_values.items():
            pattern_string = insert_regex_group_value(pattern_string, key, value)

        return self.__class__(pattern_string, self._flags)

    def search(self, string: AnyStr, pos: int = None, endpos: int = None) -> Optional[re.Match]:
        params = {"string": string, "pos": pos, "endpos": endpos}
        return self.compiled_pattern.search(**{k: v for k, v in params.items() if v is not None})

    def match(self, string: AnyStr, pos: int = None, endpos: int = None) -> Optional[re.Match]:
        params = {"string": string, "pos": pos, "endpos": endpos}
        return self.compiled_pattern.match(**{k: v for k, v in params.items() if v is not None})

    def __str__(self) -> str:
        return self.pattern_string

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(pattern_string='{self._pattern_string}', flags={self._flags!r})"

    def join(self, others: Iterable[Union[re.Pattern, "RegexPattern", str]]) -> "RegexPattern":
        other_pattern_strings = []
        new_flags = []
        for item in others:
            if isinstance(item, self.__class__):
                other_pattern_strings.append(item._pattern_string)
                new_flags += item._flags
            elif isinstance(item, re.Pattern):
                other_pattern_strings.append(item.pattern)
                new_flags += _deconstruct_regex_flags_to_list(item.flags)
            else:
                other_pattern_strings.append(item)
        return self.__class__(self._pattern_string.join(other_pattern_strings), set(new_flags))


class TokenRegexPattern(RegexPattern):

    def __init__(self, pattern_string: str, token: Callable, flags: Union[re.RegexFlag, Iterable[re.RegexFlag]] = None) -> None:
        super().__init__(pattern_string, flags=flags)
        self.token = token

    @property
    def ___scanner_item___(self) -> tuple[str, Callable]:
        if self.token in {str, int, float}:
            def token(s, t): return self.token(t)

        elif hasattr(self.token, "from_scanner_result"):
            def token(s, t): return self.token.from_scanner_result
        else:
            token = self.token

        return self._pattern_string, token

# region[Main_Exec]


if __name__ == '__main__':
    x = RegexPattern(r"\d{name}\d", [re.DOTALL, re.MULTILINE])
    print(x)
    z = TokenRegexPattern(r"\w+", print, re.ASCII)
    print(z.__class__)
    x = x.format(name=r'wuff')
    x |= z
    print(x.__class__)
    re.Scanner
    example_pp = r"(?P<first>.*?)(?P<third>)"
    uu = RegexPattern(example_pp)
    nn = uu.format_group_values(first=r'something|else|this', third=r"\\s")
    nn.match("fths")
    print(nn.match("this ffd 3wuff42 dfdf").groupdict())
    print(nn.groups)


# endregion[Main_Exec]
