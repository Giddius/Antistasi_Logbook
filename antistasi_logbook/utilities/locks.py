from threading import RLock, Lock, Semaphore, Barrier, BoundedSemaphore, Condition, Event, _RLock
from typing import Optional, Iterable, Hashable, Union, Any
from time import sleep
import random
DB_LOCK = RLock()


class DelayedSemaphore(Semaphore):

    def __init__(self, value: int, delay: float = None) -> None:
        self.delay = 0 if delay is None else delay
        super().__init__(value=value)

    def release(self, n: int = 1) -> None:
        sleep(random.uniform(0.0, self.delay))
        super().release(n=n)

# class GlobalLock:

#     def __init__(self, locks: Iterable[Union[RLock, Lock]]) -> None:
#         self.locks = tuple(locks)

#     def __enter__(self) -> None:
#         for lock in self.locks:
#             lock.acquire()

#     def __exit__(self, exception_type: type = None, exception_value: BaseException = None, traceback: Any = None) -> None:
#         for lock in self.locks:
#             lock.release()


# GLOBAL_LOCK = GlobalLock([DB_LOCK])
