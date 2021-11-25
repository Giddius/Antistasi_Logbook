
"""
WiP.

Soon.
"""

# region [Imports]


import re


from pathlib import Path
from typing import Union
from datetime import datetime, timezone, timedelta, tzinfo
from functools import total_ordering
from antistasi_logbook.errors import DurationTimezoneError
import attr
import tzlocal
from gidapptools.general_helper.string_helper import replace_by_dict, extract_by_map
from gidapptools.general_helper.timing import time_execution, time_func
from gidapptools import get_logger

# endregion[Imports]

# region [TODO]


# endregion [TODO]

# region [Logging]

from gidapptools.general_helper.timing import get_dummy_profile_decorator_in_globals
get_dummy_profile_decorator_in_globals()
log = get_logger(__name__)

# endregion[Logging]

# region [Constants]

THIS_FILE_DIR = Path(__file__).parent.absolute()

# endregion[Constants]


DEFAULT_DATE_TIME_FORMAT = "%Y-%m-%d_%H-%M-%S"


def convert_to_utc(date_time: datetime) -> datetime:
    if date_time.tzinfo is timezone.utc:
        return date_time
    if date_time.tzinfo is None:
        date_time = date_time.replace(tzinfo=tzlocal.get_localzone())
    return date_time.astimezone(tz=timezone.utc)


def convert_to_timezone(tz_data: Union[str, int]) -> tzinfo:
    try:
        tz_data = int(tz_data)
    except ValueError:
        pass

    if isinstance(tz_data, int):
        return timezone(timedelta(hours=tz_data))

    raise TypeError(f"Can only convert 'int' or 'str' to timezone not {type(tz_data)!r}")


def convert_match_dict_to_int_or_timezone(match_dict: dict[str, str]) -> dict[str, Union[int, tzinfo, None]]:
    new_dict = {}
    for key, value in match_dict.items():
        if key in {'tzinfo', 'tz'}:
            new_dict[key] = convert_to_timezone(value)
        else:
            new_dict[key] = int(value)
    return new_dict


def datetime_format_to_regex(fmt: str, make_separator_generic: bool = False, re_flags: re.RegexFlag = None) -> re.Pattern:
    replace_table = {r'%Y': r"(?P<year>\d{4})",
                     r'%m': r"(?P<month>\d{2})",
                     r'%d': r"(?P<day>\d{2})",
                     r'%H': r"(?P<hour>\d{2})",
                     r'%M': r"(?P<minute>\d{2})",
                     r'%S': r"(?P<second>\d{2})",
                     r'%f': r"(?P<microseconds>\d+)",
                     r'%Z': r"(?P<tzinfo>\w+)?",
                     r'%z': r"(?P<offset>(\+|\-)\d+)?"}

    if make_separator_generic is True:
        regex_string = r'.'.join(extract_by_map(fmt, replace_table))
    else:
        regex_string = replace_by_dict(fmt, replace_table)

    re_flags = 0 if re_flags is None else re_flags
    return re.compile(regex_string, re_flags)


def datetime_from_date_time_match(in_match: re.Match):
    date_time_match_groups = in_match.groups()
    date_time_string = '-'.join(date_time_match_groups[:3]) + '_' + '-'.join(date_time_match_groups[3:])
    return datetime.strptime(date_time_string, DEFAULT_DATE_TIME_FORMAT)


def _validate_date_time_frame_tzinfo(instance: "DateTimeFrame", attribute: attr.Attribute, value: datetime):
    if instance.start.tzinfo is None or instance.end.tzinfo is None:
        raise DurationTimezoneError(instance, instance.start.tzinfo, instance.end.tzinfo, 'start time and end time need to be timezone aware')
    if instance.start.tzinfo != instance.end.tzinfo:
        raise DurationTimezoneError(instance, instance.start.tzinfo, instance.end.tzinfo, 'start time and end time do not have the same timezone')


@attr.s(auto_attribs=True, auto_detect=True, frozen=True)
@total_ordering
class DateTimeFrame:
    start: datetime = attr.ib(validator=_validate_date_time_frame_tzinfo)
    end: datetime = attr.ib(validator=_validate_date_time_frame_tzinfo)

    @property
    def delta(self) -> timedelta:
        return self.end - self.start

    @property
    def tzinfo(self) -> timezone:
        return self.start.tzinfo

    def __eq__(self, other: object) -> bool:
        if isinstance(other, datetime):
            return self.start <= other <= self.end
        if isinstance(other, self.__class__):
            return self.start == other.start and self.end == other.end
        if isinstance(other, timedelta):
            return self.delta == other
        return NotImplemented

    def __lt__(self, other: object) -> bool:
        if isinstance(other, datetime):
            return self.start < other
        if isinstance(other, self.__class__):
            return self.end < other.start
        if isinstance(other, timedelta):
            return self.delta < other
        return NotImplemented

    def __contains__(self, other: object) -> bool:
        if isinstance(other, datetime):
            return self.start <= other <= self.end
        return NotImplemented

    def __str__(self) -> str:
        return f"{self.start.isoformat()} until {self.end.isoformat()}"

    def __hash__(self) -> int:
        return hash(self.start) + hash(self.end) + hash(self.delta)


# region[Main_Exec]
if __name__ == '__main__':
    pass
# endregion[Main_Exec]
