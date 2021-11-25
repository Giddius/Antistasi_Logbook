"""
Most locks here were from experiments and are not used anymore.

Needs cleanup.


"""
# region [Imports]

from threading import RLock, Lock, Semaphore, Barrier, BoundedSemaphore, Condition, Event, _RLock, get_ident, get_native_id
from typing import Optional, Iterable, Hashable, Union, Any, TYPE_CHECKING
from time import sleep
import random
from pprint import pprint
from datetime import timedelta
from time import thread_time, time, process_time
from pathlib import Path
if TYPE_CHECKING:
    from antistasi_logbook.storage.models.models import LogFile
from gidapptools import get_logger


# endregion[Imports]


log = get_logger(__name__)
DB_LOCK = RLock()

UPDATE_LOCK = Lock()

UPDATE_STOP_EVENT = Event()


WRITE_LOCK = RLock()


class FileLocks:

    def __init__(self) -> None:
        self.locks: dict[str, RLock] = {}

    def get_file_lock(self, in_log_file: "LogFile") -> Lock:
        id_string = str(in_log_file.id)
        if id_string not in self.locks:
            self.locks[id_string] = RLock()
        return self.locks[id_string]


FILE_LOCKS = FileLocks()


class DelayedSemaphore(Semaphore):

    def __init__(self, value: int, delay: float = None) -> None:
        self.delay = 0 if delay is None else delay
        super().__init__(value=value)

    def release(self, n: int = 1) -> None:
        sleep(random.uniform(0.1, max([self.delay, 0.1])))
        super().release(n=n)


class MinDurationSemaphore(Semaphore):
    default_duration = timedelta(seconds=0)
    default_delay = timedelta(seconds=0)

    def __init__(self, value: int = None, minimum_duration: timedelta = None, delay: timedelta = None) -> None:
        self.minimum_duration = self.default_duration if minimum_duration is None else minimum_duration
        self.minimum_duration_seconds = self.minimum_duration.total_seconds()
        self.delay = self.default_delay if delay is None else delay
        self.delay_seconds = self.delay.total_seconds()
        self._start_time_cache: dict[int:float] = {}
        super().__init__(value=value)

    def acquire(self, blocking: bool = True, timeout: float = None) -> bool:
        _out = super().acquire(blocking=blocking, timeout=timeout)
        self._start_time_cache[get_ident()] = process_time()
        return _out

    def __enter__(self, blocking: bool = True, timeout: float = None) -> bool:
        return self.acquire(blocking=blocking, timeout=timeout)

    def _sleep_to_minimum(self) -> None:
        start_time = self._start_time_cache.get(get_ident())
        if start_time is None:
            log.crtical(f"argggggghhhhhhhhh couldn't get start time for {get_ident()=}")
            log.critical(self._start_time_cache)
            return
        duration = process_time() - start_time
        to_sleep = self.minimum_duration_seconds - duration
        if to_sleep <= 0:
            log.debug(f"took longer than minimum, it took {duration!r}")
            return
        log.debug(f"sleeping in {self.__class__.__name__!r} for {to_sleep!r} before releasing")
        sleep(to_sleep)

    def __exit__(self, t, v, tb):
        self._sleep_to_minimum()
        sleep(random.uniform(0.0, float(self.delay_seconds)))
        self.release()
