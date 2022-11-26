
"""
WiP.

Soon.
"""

# region [Imports]

# * Standard Library Imports ---------------------------------------------------------------------------->
import re
from typing import Union
from pathlib import Path
from datetime import tzinfo, datetime, timezone, timedelta
from functools import total_ordering
from dateutil.tz import UTC

# * Third Party Imports --------------------------------------------------------------------------------->
import attr
import tzlocal

# * Gid Imports ----------------------------------------------------------------------------------------->
from gidapptools import get_logger
from gidapptools.general_helper.conversion import seconds2human
from gidapptools.general_helper.string_helper import extract_by_map, replace_by_dict

# * Local Imports --------------------------------------------------------------------------------------->
from antistasi_logbook.errors import DurationTimezoneError

# endregion[Imports]

# region [TODO]


# endregion [TODO]

# region [Logging]


log = get_logger(__name__)

# endregion[Logging]

# region [Constants]

THIS_FILE_DIR = Path(__file__).parent.absolute()

# endregion[Constants]


DEFAULT_DATE_TIME_FORMAT = "%Y-%m-%d_%H-%M-%S"


def convert_to_utc(date_time: datetime) -> datetime:
    if date_time.tzinfo in (timezone.utc, UTC):
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


def _validate_date_time_frame_tzinfo(instance: "DateTimeFrame"):
    if instance.start.tzinfo is None or instance.end.tzinfo is None:
        raise DurationTimezoneError(instance, instance.start.tzinfo, instance.end.tzinfo, 'start time and end time need to be timezone aware')
    if instance.start.tzinfo != instance.end.tzinfo:
        raise DurationTimezoneError(instance, instance.start.tzinfo, instance.end.tzinfo, 'start time and end time do not have the same timezone')


@attr.s(auto_attribs=True, auto_detect=True, frozen=True, slots=True, weakref_slot=True)
@total_ordering
class DateTimeFrame:
    start: datetime = attr.ib()
    end: datetime = attr.ib()
    delta: timedelta = attr.ib(init=False)

    def __attrs_post_init__(self):
        _validate_date_time_frame_tzinfo(self)

    @delta.default
    def get_delta(self) -> timedelta:
        return self.end - self.start

    @property
    def tzinfo(self) -> timezone:
        return self.start.tzinfo

    @property
    def seconds(self) -> int:
        return int(self.delta.total_seconds())

    @property
    def minutes(self) -> int:
        minutes = self.delta.total_seconds() / 60
        return int(minutes)

    @property
    def hours(self) -> int:
        minutes = self.delta.total_seconds() / 60
        hours = minutes / 60
        return int(hours)

    @property
    def days(self) -> int:
        minutes = self.delta.total_seconds() / 60
        hours = minutes / 60
        days = hours / 24
        return int(days)

    @property
    def weeks(self) -> int:
        minutes = self.delta.total_seconds() / 60
        hours = minutes / 60
        days = hours / 24
        weeks = days / 7
        return int(weeks)

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

    def __add__(self, other: object) -> "DateTimeFrame":
        if isinstance(other, DateTimeFrame):
            new_start = min(self.start, other.start)
            new_end = max(self.end, other.end)
            return self.__class__(start=new_start, end=new_end)
        return NotImplemented

    def delta_to_string(self) -> str:
        return seconds2human(self.delta, with_year=False, min_unit="millisecond")

    def to_pretty_string(self, fmt=None, multiline: bool = False):
        fmt = "%Y-%m-%d %H:%M:%S %Z" if fmt is None else fmt
        if multiline is False:
            return f"{self.start.strftime(fmt)} until {self.end.strftime(fmt)}"
        else:
            return f"{self.start.strftime(fmt)}\nuntil\n{self.end.strftime(fmt)}"

    def __str__(self) -> str:
        return f"{self.to_pretty_string()} ({self.delta_to_string()})"

    def __hash__(self) -> int:
        return hash(self.start) + hash(self.end) + hash(self.delta)


# region[Main_Exec]
if __name__ == '__main__':
    pass
# endregion[Main_Exec]
