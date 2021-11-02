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
from peewee import Model, TextField, IntegerField, BooleanField, AutoField, DateTimeField, ForeignKeyField, SQL, BareField, SqliteDatabase, Field, BlobField
from antistasi_logbook.utilities.path_utilities import RemotePath
from playhouse.fields import CompressedField
import httpx
import yarl
from antistasi_logbook.utilities.misc import Version
from dateutil.tz import tzoffset
from hashlib import blake2b
from PIL import Image
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
import base64
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
# endregion[Imports]

# region [TODO]


# endregion [TODO]

# region [Logging]


# endregion[Logging]

# region [Constants]

THIS_FILE_DIR = Path(__file__).parent.absolute()

# endregion[Constants]


class RemotePathField(Field):
    field_type = "REMOTEPATH"

    def db_value(self, value: RemotePath) -> Optional[str]:
        if value is not None:
            return value._path.as_posix()

    def python_value(self, value) -> Optional[RemotePath]:
        if value is not None:
            return RemotePath(value)


class PathField(Field):
    field_type = "PATH"

    def db_value(self, value: Path) -> Optional[str]:
        if value is not None:
            return value.as_posix()

    def python_value(self, value) -> Optional[Path]:
        if value is not None:
            return Path(value)


class VersionField(Field):
    field_type = "VERSION"

    def db_value(self, value: Version):
        if value is not None:
            return str(value)

    def python_value(self, value) -> Optional[Version]:
        if value is None:
            return None
        return Version.from_string(value)


class URLField(Field):
    field_type = "URL"

    def db_value(self, value: Union[str, yarl.URL, httpx.URL, Path]):
        if value is None:
            return value
        if isinstance(value, Path):
            value = value.as_uri()
        if not isinstance(value, yarl.URL):
            value = yarl.URL(str(value))
        return str(value)

    def python_value(self, value):
        if value is not None:
            return yarl.URL(value)


class BetterDateTimeField(Field):
    field_type = 'DATETIME'

    def db_value(self, value: Optional[datetime]):
        if value is not None:
            return value.isoformat()

    def python_value(self, value):
        if value is not None:
            return datetime.fromisoformat(value)


class TzOffsetField(Field):
    field_type = "TZOFFSET"

    def db_value(self, value: Optional[tzoffset]) -> Optional[str]:
        if value is not None:
            return f"{value.tzname(None)}||{value.utcoffset(None).total_seconds()}"

    def python_value(self, value: Optional[str]):
        if value is not None:
            name, seconds = value.split('||')
            seconds = int(seconds.split('.')[0])
            delta = timedelta(seconds=seconds)
            return tzoffset(name, delta)


class CompressedTextField(CompressedField):

    def db_value(self, value: str):
        if value is not None:
            value = value.encode(encoding='utf-8', errors='ignore')
            return super().db_value(value)

    def python_value(self, value):
        if value is not None:
            value: bytes = super().python_value(value)
            return value.decode(encoding='utf-8', errors='ignore')


class CompressedImageField(CompressedField):

    def __init__(self, return_as: Union[Literal["pil_image"], Literal['bytes'], Literal['qt_image']] = "pil_image", **kwargs):
        super().__init__(**kwargs)
        return_func_table = {"pil_image": self.return_as_pil_image,
                             "bytes": self.return_as_bytes,
                             "qt_image": self.return_as_not_implemented}
        self.return_as = return_func_table.get(return_as, self.return_as_not_implemented)

    @staticmethod
    def image_to_byte_array(image: Image.Image):
        with BytesIO() as bf:
            image.save(bf, format=image.format)
            imgByteArr = bf.getvalue()
            return imgByteArr

    @staticmethod
    def return_as_pil_image(data: bytes) -> Image.Image:
        with BytesIO() as bf:
            bf.write(data)
            bf.seek(0)
            image = Image.open(bf)
            image.load()
            return image

    @staticmethod
    def return_as_bytes(data: bytes) -> bytes:
        return data

    @staticmethod
    def return_as_not_implemented(data: bytes) -> NotImplemented:
        return NotImplemented

    def db_value(self, value: Union[bytes, Path, Image.Image]):
        if value is not None:
            if isinstance(value, Path):
                bytes_value = self.image_to_byte_array(Image.open(value))
            elif isinstance(value, Image.Image):
                bytes_value = self.image_to_byte_array(value)
            elif isinstance(value, bytes):
                bytes_value = value
            return super().db_value(bytes_value)

    def python_value(self, value):
        if value is not None:
            bytes_value = super().python_value(value)
            return self.return_as(bytes_value)


class LoginField(BlobField):

    @property
    def fallback_env_name(self) -> str:
        return f"{self.model.name}_login"

    @property
    def key(self) -> bytes:
        raw_key = os.environ["USERDOMAIN"].encode(encoding='utf-8', errors='ignore')
        kdf = PBKDF2HMAC(algorithm=hashes.SHA256(),
                         length=32,
                         salt=os.getlogin().encode(encoding='utf-8', errors='ignore'),
                         iterations=100000)
        return base64.urlsafe_b64encode(kdf.derive(raw_key))

    def db_value(self, value: str):
        if value is not None:
            fernet = Fernet(self.key)
            return fernet.encrypt(value.encode(encoding='utf-8', errors='ignore'))

    def python_value(self, value):
        if value is not None:
            fernet = Fernet(self.key)
            return fernet.decrypt(value).decode(encoding='utf-8', errors='ignore')
        return os.getenv(self.fallback_env_name, None)


class PasswordField(BlobField):

    @property
    def fallback_env_name(self) -> str:
        return f"{self.model.name}_password"

    @property
    def key(self) -> bytes:
        raw_key = os.environ["USERDOMAIN"].encode(encoding='utf-8', errors='ignore')
        kdf = PBKDF2HMAC(algorithm=hashes.SHA256(),
                         length=32,
                         salt=b"1",
                         iterations=100000)
        return base64.urlsafe_b64encode(kdf.derive(raw_key))

    def db_value(self, value: str):
        if value is not None:
            fernet = Fernet(self.key)
            return fernet.encrypt(value.encode(encoding='utf-8', errors='ignore'))

    def python_value(self, value):
        if value is not None:
            fernet = Fernet(self.key)
            return fernet.decrypt(value).decode(encoding='utf-8', errors='ignore')
        return os.getenv(self.fallback_env_name, None)


# region[Main_Exec]
if __name__ == '__main__':

    pass
# endregion[Main_Exec]
