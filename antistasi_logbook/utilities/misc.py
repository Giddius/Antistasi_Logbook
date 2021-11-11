from json import JSONDecoder, JSONEncoder
from typing import Any, Callable, Union, Optional, Generator
from datetime import datetime, timezone, timedelta
import attr
from typing import Union, Optional, ClassVar, Iterable
import re
from gidapptools.general_helper.conversion import str_to_bool
from pathlib import Path


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
        func(*args, **kwargs)


def try_convert_int(data: Union[str, int, None]) -> Union[str, int, None]:
    if data is None:
        return None
    try:
        return int(data)
    except ValueError:
        return data


@attr.s(slots=True, auto_attribs=True, auto_detect=True, frozen=True)
class Version:
    major: int = attr.ib(converter=int)
    minor: int = attr.ib(converter=int)
    patch: int = attr.ib(converter=try_convert_int)
    extra: Union[str, int] = attr.ib(default=None, converter=try_convert_int)
    version_regex: ClassVar = re.compile(r"(?P<major>\d+)\.(?P<minor>\d+)\.(?P<patch>\d+)\-?(?P<extra>.*)?")

    def __str__(self) -> str:
        _out = f"{self.major}.{self.minor}.{self.patch}"
        if self.extra is not None:
            _out += f"-{self.extra}"
        return _out

    @classmethod
    def from_string(cls, string: str) -> "Version":
        match = cls.version_regex.match(string.strip())
        if match is not None:
            return cls(**match.groupdict())


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


@attr.s(slots=True, auto_attribs=True, auto_detect=True, frozen=True)
class ModItem:
    name: str = attr.ib(converter=strip_converter)
    default: bool = attr.ib(converter=str_to_bool)
    official: bool = attr.ib(converter=str_to_bool)
    mod_dir: str = attr.ib(converter=strip_converter)
    full_path: Path = attr.ib(default=None, converter=strip_to_path)
    hash: str = attr.ib(default=None, converter=strip_converter)
    hash_short: str = attr.ib(default=None, converter=strip_converter)
    link: str = attr.ib(default=None, converter=strip_converter)

    @classmethod
    def from_text_line(cls, line: str) -> "ModItem":
        parts = line.split('|')
        name, mod_dir, default, official, origin = parts[:5]
        optional_kwargs = {}
        if len(parts) > 5:
            optional_kwargs['hash'] = parts[5]
            optional_kwargs["hash_short"] = parts[6]
            optional_kwargs["full_path"] = parts[7]
        return cls(name=name, mod_dir=mod_dir, default=default, official=official, **optional_kwargs)

    def as_dict(self) -> dict[str, Any]:
        _out = attr.asdict(self)
        return _out


if __name__ == '__main__':
    pass
