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
from typing import TYPE_CHECKING, Union, Callable, Iterable, Optional, Mapping, Any, IO, TextIO, BinaryIO, Hashable, Generator, Literal, TypeVar, TypedDict, AnyStr, ClassVar
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
from gidapptools.general_helper.timing import time_func
from antistasi_logbook.data.misc import LOG_FILE_DATE_REGEX
import attr
from antistasi_logbook.utilities.enums import RemoteItemType
from antistasi_logbook.data.content_types import ContentType
from antistasi_logbook.utilities.path_utilities import RemotePath
from gidapptools.general_helper.dict_helper import replace_dict_keys
from marshmallow import Schema, fields, pre_load
from dateutil.tz import UTC
from gidapptools import get_logger
# endregion[Imports]

# region [TODO]


# endregion [TODO]

# region [Logging]


# endregion[Logging]

# region [Constants]

THIS_FILE_DIR = Path(__file__).parent.absolute()

from gidapptools.general_helper.timing import get_dummy_profile_decorator_in_globals
get_dummy_profile_decorator_in_globals()
log = get_logger(__name__)
# endregion[Constants]

# {'content_language': None,
#  'content_length': None,
#  'content_type': '',
#  'created': None,
#  'display_name': None,
#  'etag': '"60112172c62eb"',
#  'href': '/dev_drive/remote.php/dav/files/Giddi/E-Books/',
#  'modified': datetime.datetime(2021, 1, 27, 8, 16, 50, tzinfo=datetime.timezone.utc),
#  'name': 'E-Books',
# 'type': 'directory'}


class InfoItemSchema(Schema):
    """
    Used for Testing.
    """
    type = fields.String()
    remote_path = fields.String()
    name = fields.String()
    etag = fields.String()
    raw_created_at = fields.AwareDateTime(load_default=None, default_timezone=UTC)
    modified_at = fields.AwareDateTime(default_timezone=UTC)
    content_type = fields.String(load_default=None)
    display_name = fields.String(load_default=None)
    size = fields.Integer()
    content_language = fields.String(load_default=None)
    raw_info = fields.Dict()

    @pre_load
    def handle_enums(self, in_data, **kwargs):
        in_data['type'] = in_data['type'].split('.')[-1]
        in_data["content_type"] = in_data['content_type'].split('.')[-1]
        return in_data


@attr.s(slots=True, auto_attribs=True, auto_detect=True, kw_only=True, frozen=True)
class InfoItem:
    """
    Class to convert the received Json to and item and also change some names to abstract the remote-storage implementation.


    """
    type: RemoteItemType = attr.ib(converter=RemoteItemType)
    remote_path: RemotePath = attr.ib(converter=RemotePath)
    name: str = attr.ib()
    etag: str = attr.ib(converter=lambda x: x.strip('"' + "'"))
    raw_created_at: datetime = attr.ib(default=None)
    modified_at: datetime = attr.ib()
    content_type: ContentType = attr.ib(default=None, converter=ContentType)
    display_name: str = attr.ib(default=None)
    size: int = attr.ib(default=None)
    content_language: str = attr.ib(default=None)
    raw_info: dict[str, Any] = attr.ib()
    schema: ClassVar = InfoItemSchema()

    @name.default
    def _name_from_remote_path(self) -> str:
        return self.remote_path.stem

    @classmethod
    def from_webdav_info(cls, webdav_info: dict[str, Any]) -> "InfoItem":
        webdav_info = webdav_info.copy()
        raw_info = webdav_info.copy()
        webdav_info = replace_dict_keys(webdav_info, ('name', 'remote_path'), ('created', 'raw_created_at'), ('modified', 'modified_at'), ("content_length", "size"))
        webdav_info.pop('href')
        webdav_info['raw_info'] = raw_info
        return cls(**webdav_info)

    @classmethod
    def from_schema_item(cls, item) -> "InfoItem":
        """
        Used for Testing.
        """
        return cls(**item)

    def as_dict(self) -> dict[str, Any]:
        """
        Converts the instance to a dict.

        """
        return attr.asdict(self)

    def dump(self) -> dict:
        """
        Used for Testing.
        """
        return self.schema.dump(self)


# region[Main_Exec]
if __name__ == '__main__':
    pass

# endregion[Main_Exec]
