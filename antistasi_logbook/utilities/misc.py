
# region [Imports]


# * Standard Library Imports ---------------------------------------------------------------------------->
import re
from json import JSONEncoder
from typing import TYPE_CHECKING, Any, Union, Literal, Callable, ClassVar, Optional, Generator, TypeVar
from pathlib import Path
from datetime import datetime, timedelta
from functools import total_ordering, wraps
import textwrap
from collections import ChainMap
import sys
# * Third Party Imports --------------------------------------------------------------------------------->
import attr
from rich import inspect as rinspect
from yarl import URL
from peewee import Field
from dateutil.tz import UTC
from rich.console import Console as RichConsole
from dateutil.parser import parse as dateutil_parse
from threading import Lock, Condition, Event, Semaphore, Thread
# * Gid Imports ----------------------------------------------------------------------------------------->
from gidapptools import get_logger
from gidapptools.general_helper.timing import get_dummy_profile_decorator_in_globals
from gidapptools.general_helper.conversion import str_to_bool
if sys.version_info >= (3, 11):
    from typing import Self
else:
    from typing_extensions import Self
# * Local Imports --------------------------------------------------------------------------------------->
from antistasi_logbook.utilities.path_utilities import RemotePath

if TYPE_CHECKING:
    from antistasi_logbook.storage.models.models import BaseModel


# endregion [Imports]


get_dummy_profile_decorator_in_globals()

log = get_logger(__name__)


class DatetimeJsonEncoder(JSONEncoder):
    def default(self, o: Any) -> Any:
        if isinstance(o, datetime):
            return datetime.isoformat()
        return super().default(o)


def _no_predicate(klass: type, level: int) -> bool:
    return True


def get_subclasses_recursive(klass: type, predicate: Callable[[type, int], bool] = None, _level: int = 0) -> Generator[type, None, None]:
    predicate = _no_predicate if predicate is None else predicate
    for subclass in klass.__subclasses__():
        if predicate(subclass, _level) is True:
            yield subclass
        yield from get_subclasses_recursive(subclass, predicate=predicate, _level=_level + 1)


class NoFuture:
    __slots__ = ("__weakref__", "_id", "_result", "_exception", "_func", "_args", "_kwargs")
    id_counter = 0

    def __init__(self, func: Callable, *args, **kwargs) -> None:
        self.__class__.id_counter += 1
        self._id = self.__class__.id_counter
        self._func = func
        self._args = args
        self._kwargs = kwargs
        self._result = None
        self._exception = None
        self._run_func()

    def _run_func(self):
        try:
            self._result = self._func(*self._args, **self._kwargs)
        except Exception as e:
            self._exception = e

    def result(self):
        return self._result

    def exception(self):
        return self._exception

    def done(self):
        return True

    def add_done_callback(self, func):
        func(self)

    def __hash__(self) -> int:
        return hash(self._id)


class NoThreadPoolExecutor:

    def __init__(self, *args, **kwargs) -> None:
        self.args = args
        self.kwargs = kwargs

    def __enter__(self) -> "NoThreadPoolExecutor":
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback) -> None:
        pass

    def map(self, func, items) -> Generator:
        return (func(item) for item in items)

    def shutdown(self, *args, **kwargs) -> None:
        return

    def submit(self, func, *args, **kwargs) -> None:

        return NoFuture(func=func, *args, **kwargs)


def try_convert_int(data: Union[str, int, None]) -> Union[str, int, None]:
    if data is None:
        return None
    if isinstance(data, str) and data in {"", "MISSING"}:
        return None
    try:
        return int(data)
    except ValueError:
        return data


@attr.s(slots=True, auto_attribs=True, auto_detect=True, frozen=True)
@total_ordering
class VersionItem:
    major: int = attr.ib(converter=int)
    minor: int = attr.ib(converter=int)
    patch: int = attr.ib(default=None, converter=try_convert_int)
    extra: Union[str, int] = attr.ib(default=None, converter=try_convert_int)
    version_regex: ClassVar = re.compile(r"(?P<major>\d+)\.(?P<minor>\d+)\.(?P<patch>\d+|MISSING)[\-\.]?(?P<extra>.*)?")

    def __str__(self) -> str:
        _out = f"{self.major}.{self.minor}"
        if self.patch is not None:
            _out += f".{self.patch}"
        if self.extra is not None:
            _out += f"-{self.extra}"
        return _out

    @classmethod
    def from_string(cls, string: Optional[str]) -> Optional["VersionItem"]:
        if string is None:
            return
        try:
            match = cls.version_regex.match(string.strip())
            if match is not None:
                return cls(**match.groupdict())
        except AttributeError:
            log.debug("attribute error with %r", string)
            raise

    def as_tuple(self, include_extra: bool = True) -> tuple[Union[str, int]]:
        if include_extra is False:
            return (self.major, self.minor, self.patch)
        return (self.major, self.minor, self.patch, self.extra)

    def __eq__(self, other: object) -> bool:
        if isinstance(other, self.__class__):
            return self.as_tuple() == other.as_tuple()

        if isinstance(other, str):
            return False
        return NotImplemented

    def __lt__(self, other: object) -> bool:
        if other is None:
            return False
        if isinstance(other, self.__class__):

            if (self.major, self.minor, self.patch) == (other.major, other.minor, other.patch):
                if self.extra is None and other.extra is not None:
                    return True
                return False

            if self.major < other.major:
                return True
            elif self.major == other.major and self.minor < other.minor:
                return True
            elif self.major == other.major and self.minor == other.minor and (self.patch is None and other.patch is not None):
                return True
            elif self.major == other.major and self.minor == other.minor and (all([self.patch is not None, other.patch is not None]) and self.patch < other.patch):
                return True
            elif self.major == other.major and self.minor == other.minor and (all([self.patch is not None, other.patch is not None]) and self.patch == other.patch) and (self.extra is None and other.extra is not None):
                return True
            return False

        if isinstance(other, str):
            return False
        return NotImplemented

    def __hash__(self) -> int:
        return hash(self.as_tuple())


def strip_converter(data: Optional[str] = None, extra_strip_chars: str = None) -> Optional[str]:
    if data is None:
        return data
    if extra_strip_chars is not None:
        strip_chars = " " + extra_strip_chars
        return data.strip(strip_chars)
    return data.strip()


def strip_to_path(data):
    data = strip_converter(data)
    if data is None:
        return data
    return Path(data)


_STANDARD_MOD_NAMES = {"utility",
                       "members",
                       "taskforceenforcer",
                       "antistasidevbuild",
                       "enhancedmovement",
                       "tfar",
                       "cbaa3",
                       "ace",
                       "zeusenhanced"}


@ attr.s(slots=True, auto_attribs=True, auto_detect=True, frozen=True)
class ModItem:
    name: str = attr.ib(converter=strip_converter)
    default: bool = attr.ib(converter=str_to_bool)
    official: bool = attr.ib(converter=str_to_bool)
    mod_dir: str = attr.ib(converter=strip_converter)
    full_path: Path = attr.ib(default=None, converter=strip_to_path)
    mod_hash: str = attr.ib(default=None, converter=strip_converter)
    mod_hash_short: str = attr.ib(default=None, converter=strip_converter)

    @ classmethod
    def from_text_line(cls, line: str) -> "ModItem":
        parts = line.split('|')
        name, mod_dir, default, official, origin = parts[:5]
        optional_kwargs = {}
        if len(parts) > 5:
            optional_kwargs['mod_hash'] = parts[5]
            optional_kwargs["mod_hash_short"] = parts[6]
            optional_kwargs["full_path"] = parts[7]

        return cls(name=name, mod_dir=mod_dir, default=default, official=official, **optional_kwargs)

    def as_dict(self) -> dict[str, Any]:

        _out = attr.asdict(self)
        return _out


def frozen_time_giver(utc_date_time: Union[str, datetime]):
    if isinstance(utc_date_time, str):
        utc_date_time = dateutil_parse(utc_date_time)
    utc_date_time = utc_date_time.replace(tzinfo=UTC)
    difference = datetime.now(tz=UTC) - utc_date_time

    def _inner():
        return datetime.now(tz=UTC) - difference

    return _inner


def obj_inspection(obj: object, out_dir: Path = None, out_type: Literal["txt", "html"] = 'html') -> None:
    console = RichConsole(soft_wrap=True, record=True)
    rinspect(obj=obj, methods=True, help=True, console=console)
    out_dir = Path.cwd() if out_dir is None else Path(out_dir)
    try:
        name = obj.__class__.__name__
    except AttributeError:

        name = obj.__name__
    out_file = out_dir.joinpath(f"{name.casefold()}.{out_type}")
    if out_type == "html":
        console.save_html(out_file)
    elif out_type == "txt":
        console.save_text(out_file)


def column_sort_default_factory(in_colum: "Field"):
    typus = in_colum.field_type
    if typus == "BOOL":
        return False

    if typus in {"CHAR", "VARCHAR", "TEXT"}:
        return ""

    if typus == "DATETIME":
        return datetime.now(tz=UTC) - timedelta(weeks=99999999999)

    if typus == "PATH":
        return Path('')

    if typus == "REMOTEPATH":
        return RemotePath("")

    if typus in {"SMALLINT", "INT", "BIGINT"}:
        return 0

    if typus == "URL":
        return URL("")


class EnumLikeModelCache(dict):

    def __init__(self) -> None:
        super().__init__()
        self._lock = Lock()
        self._amount_inserted = 0

    def insert_instance(self, instance: "BaseModel") -> None:
        if instance.id is None:
            return
        with self._lock:

            self[instance.id] = instance
            self._amount_inserted += 1

    def get_by_id(self, value: int) -> Optional["BaseModel"]:
        with self._lock:
            return self.get(value, None)

    def clear(self) -> None:
        with self._lock:
            return super().clear()


def all_subclasses_recursively(klass: type) -> set[type]:
    return set(klass.__subclasses__()).union([s for c in klass.__subclasses__() for s in all_subclasses_recursively(c)])


def _collect_caller():
    caller = []
    idx = 1
    while True:
        try:
            co = sys._getframe(idx).f_code
            if not co.co_name:
                break
            caller.append((co.co_name, co.co_filename, co.co_firstlineno))
            idx += 1
        except Exception:
            break

    return caller


def _log_caller(func_name: str, in_caller: list[tuple[str, str, int]]):
    text = f"{func_name!r} was called by " + textwrap.indent("\n".join(f"↳ {i[0]!r} {i[1]}:{i[2]}" for i in in_caller), "    ")
    log.debug(text)


_T = TypeVar("_T")


def tell_callers(in_func: _T) -> _T:

    @wraps(in_func)
    def _inner(*args, **kwargs):
        caller = _collect_caller()
        _log_caller(in_func.__name__, caller)
        return in_func(*args, **kwargs)

    return _inner


if __name__ == '__main__':
    pass
