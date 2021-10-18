from json import JSONDecoder, JSONEncoder
from typing import Any, Callable, Union, Optional, Generator
from datetime import datetime, timezone, timedelta


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
