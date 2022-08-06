"""
WiP.

Soon.
"""

# region [Imports]

# * Standard Library Imports ---------------------------------------------------------------------------->
from time import sleep
from typing import TYPE_CHECKING, Union, Callable
from pathlib import Path
from datetime import datetime, timezone, timedelta
from threading import Event

# * Third Party Imports --------------------------------------------------------------------------------->
from dateutil.tz import UTC

# * Gid Imports ----------------------------------------------------------------------------------------->
from gidapptools import get_logger

# * Type-Checking Imports --------------------------------------------------------------------------------->
if TYPE_CHECKING:
    from gidapptools.gid_config.interface import GidIniConfig

# endregion[Imports]

# region [TODO]


# endregion [TODO]

# region [Logging]


# endregion[Logging]

# region [Constants]


log = get_logger(__name__)
THIS_FILE_DIR = Path(__file__).parent.absolute()

# endregion[Constants]


def _default_now_factory(tz: timezone) -> datetime:
    return datetime.now(tz=tz)


TRIGGER_RESULT_TYPE = Union[int, float, timedelta]
TRIGGER_INTERVAL_TYPE = Union[TRIGGER_RESULT_TYPE, Callable[[], TRIGGER_RESULT_TYPE]]


class TimeClock:

    def __init__(self,
                 config: "GidIniConfig",
                 stop_event: Event = None) -> None:
        self.time_zone = UTC
        self.config = config
        self.stop_event = Event() if stop_event is None else stop_event
        self.next_trigger: datetime = None

    @property
    def now(self) -> datetime:
        return datetime.now(tz=UTC)

    @property
    def trigger_interval(self) -> timedelta:
        return self.config.get("updating", "update_interval", default=timedelta(seconds=600))

    def wait_for_trigger(self):
        if self.stop_event.is_set():
            return
        next_trigger = self.get_next_trigger()
        seconds_left = max((next_trigger - self.now).total_seconds(), 1)
        if seconds_left <= 5:
            sleep_durations = [seconds_left]
        else:
            amount, rest = divmod(seconds_left, 5)

            sleep_durations = ([5] * int(amount)) + [rest]
        for part in sleep_durations:
            if self.stop_event.is_set():
                return
            sleep(part)
        if self.next_trigger > self.now:
            return self.wait_for_trigger()
        return

    def reset(self) -> None:
        self.next_trigger = self.now + self.trigger_interval

    def get_next_trigger(self) -> datetime:
        if self.next_trigger is None:
            self.next_trigger = self.now + self.trigger_interval

        if self.next_trigger < self.now:
            self.next_trigger = self.next_trigger + self.trigger_interval

        return self.next_trigger

# region[Main_Exec]


if __name__ == '__main__':
    pass

# endregion[Main_Exec]
