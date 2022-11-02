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

import subprocess
import inspect

from time import sleep, process_time, process_time_ns, perf_counter, perf_counter_ns
from io import BytesIO, StringIO
from abc import ABC, ABCMeta, abstractmethod
from copy import copy, deepcopy
from enum import Enum, Flag, auto, unique
from pprint import pprint, pformat
from pathlib import Path
from string import Formatter, digits, printable, whitespace, punctuation, ascii_letters, ascii_lowercase, ascii_uppercase
from timeit import Timer
from typing import (TYPE_CHECKING, TypeVar, TypeGuard, TypeAlias, Final, TypedDict, Generic, Union, Optional, ForwardRef, final,
                    no_type_check, no_type_check_decorator, overload, get_type_hints, cast, Protocol, runtime_checkable, NoReturn, NewType, Literal, AnyStr, IO, BinaryIO, TextIO, Any)
from collections import Counter, ChainMap, deque, namedtuple, defaultdict
from collections.abc import (AsyncGenerator, AsyncIterable, AsyncIterator, Awaitable, ByteString, Callable, Collection, Container, Coroutine, Generator,
                             Hashable, ItemsView, Iterable, Iterator, KeysView, Mapping, MappingView, MutableMapping, MutableSequence, MutableSet, Reversible, Sequence, Set, Sized, ValuesView)
from zipfile import ZipFile, ZIP_LZMA
from datetime import datetime, timezone, timedelta
from tempfile import TemporaryDirectory
from textwrap import TextWrapper, fill, wrap, dedent, indent, shorten
from functools import wraps, partial, lru_cache, singledispatch, total_ordering, cached_property, cache
from contextlib import contextmanager, asynccontextmanager, nullcontext, closing, ExitStack, suppress
from statistics import mean, mode, stdev, median, variance, pvariance, harmonic_mean, median_grouped
from urllib.parse import urlparse
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, Future, wait, as_completed, ALL_COMPLETED, FIRST_EXCEPTION, FIRST_COMPLETED
from PIL import Image
from PIL.ExifTags import TAGS
if sys.version_info >= (3, 11):
    from typing import Self
else:
    from typing_extensions import Self

from hashlib import blake2b, md5, sha256, sha3_512, blake2s
from PySide6.QtGui import QIcon, QImage, QPixmap
from PySide6.QtCore import QSize, Qt
import numpy as np
import numpy.typing as np_typing
if TYPE_CHECKING:
    ...

# endregion[Imports]

# region [TODO]


# endregion [TODO]

# region [Logging]


# endregion[Logging]

# region [Constants]

THIS_FILE_DIR = Path(__file__).parent.absolute()
PATH_TYPE: TypeAlias = Union[os.PathLike, str]
# endregion[Constants]


class BaseImageInfo(ABC):

    def __init__(self) -> None:
        self._file_size: int = None
        self._size: tuple[int, int] = None
        self._format: str = None
        self._exif: Optional[dict] = None
        self._other_info: Optional[dict] = None
        self._content_hash: str = None

    @property
    def file_size(self) -> int:
        return self._file_size

    @property
    def size(self) -> tuple[int, int]:
        return self._size

    @property
    def width(self) -> int:
        return self._size[0]

    @property
    def height(self) -> int:
        return self._size[1]

    @property
    def format(self) -> str:
        return self._format

    @property
    def exif(self) -> Optional[dict]:
        return self._exif

    @property
    def other_info(self) -> Optional[dict]:
        return self._other_info

    @property
    def content_hash(self) -> str:
        if self._content_hash is None:
            self._content_hash = self.get_content_hash()
        return self._content_hash

    @abstractmethod
    def get_content_hash(self) -> str:
        ...

    @abstractmethod
    def load_image_info(self) -> Self:
        ...


class LocalImageInfo(BaseImageInfo):

    def __init__(self, image_path: Path) -> None:
        super().__init__()
        self._image_path = image_path

    def get_content_hash(self) -> str:
        content_hash = blake2s(usedforsecurity=False)
        chunk_size: int = 26214400  # 25mb
        with self._image_path.open("rb", buffering=chunk_size) as f:
            for chunk in f:
                content_hash.update(chunk)
        return content_hash.hexdigest()

    def load_image_info(self) -> Self:
        with Image.open(self._image_path) as image:
            self._size = image.size
            self._format = image.format
            self._exif = {TAGS[k]: v for k, v in image.getexif().items()}
            self._other_info = dict(image.info)
        return self


class LocalImage:
    standard_icon_size: tuple[int, int] = (32, 32)

    def __init__(self, image_path: PATH_TYPE) -> None:
        self.image_path: Path = Path(image_path)
        self._image_info = None

    @property
    def name(self) -> str:
        return self.image_path.stem

    @property
    def image_info(self) -> LocalImageInfo:
        if self._image_info is None:
            self._image_info = LocalImageInfo(self.image_path).load_image_info()
        return self._image_info

    def to_pil_image(self) -> Image.Image:
        return Image.open(self.image_path)

    def to_numpy_array(self, rotate: float = 0.0) -> np_typing.ArrayLike:
        image = Image.open(self.image_path).rotate(rotate)
        return np.asarray(image)

    def to_qimage(self) -> QImage:
        return QImage(self.image_path)

    def to_qicon(self, icon_size: Union[Literal["original", "standard"], tuple[int, int], QSize] = "standard") -> QIcon:
        if isinstance(icon_size, str) and icon_size == "standard":
            icon_size = QSize(self.standard_icon_size[0], self.standard_icon_size[1])
        elif isinstance(icon_size, str) and icon_size == "original":
            icon_size = None

        elif isinstance(icon_size, tuple):
            icon_size = QSize(icon_size[0], icon_size[1])

        if icon_size is not None:
            pixmap = QPixmap(self.image_path)
            pixmap = pixmap.scaled(icon_size, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
            icon = QIcon(pixmap)

        else:
            icon = QIcon(self.image_path)

        return icon

    def to_qpixmap(self) -> QPixmap:
        return QPixmap(self.image_path)

    def to_bytes(self) -> bytes:
        return self.image_path.read_bytes()

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(image_path={self.image_path})"


# region[Main_Exec]
if __name__ == '__main__':
    pass

# endregion[Main_Exec]
