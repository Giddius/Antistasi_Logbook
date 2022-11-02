"""
WiP.

Soon.
"""

# region [Imports]

# * Standard Library Imports ---------------------------------------------------------------------------->
import re
from typing import TYPE_CHECKING, Any, TextIO, Callable, Iterable, Generator
from pathlib import Path
import random
from datetime import timedelta
from time import sleep
from threading import Lock, RLock
from contextlib import contextmanager
from collections import deque
from concurrent.futures import FIRST_EXCEPTION, Future, wait, ALL_COMPLETED
from traceback import format_exc, format_tb

# * Third Party Imports --------------------------------------------------------------------------------->
import attr
from dateutil.tz import UTC, tzoffset
from playhouse.shortcuts import model_to_dict

# * Gid Imports ----------------------------------------------------------------------------------------->
from gidapptools import get_logger
from gidapptools.general_helper.enums import MiscEnum
from gidapptools.gid_signal.interface import get_signal
from collections import namedtuple
# * Local Imports --------------------------------------------------------------------------------------->
from antistasi_logbook.storage.models.models import GameMap, LogFile, Version, LogRecord
from antistasi_logbook.parsing.py_raw_record import RawRecord
from gidapptools.general_helper.timing import get_dummy_profile_decorator_in_globals
# * Type-Checking Imports --------------------------------------------------------------------------------->
if TYPE_CHECKING:
    from gidapptools.gid_config.interface import GidIniConfig

    from antistasi_logbook.parsing.parser import MetaFinder, ForeignKeyCache
    from antistasi_logbook.parsing.record_processor import RecordInserter, ManyRecordsInsertResult
    from antistasi_logbook.parsing.foreign_key_cache import ForeignKeyCache

# endregion[Imports]

# region [TODO]


# endregion [TODO]

# region [Logging]


# endregion[Logging]

# region [Constants]

get_dummy_profile_decorator_in_globals()
THIS_FILE_DIR = Path(__file__).parent.absolute()
log = get_logger(__name__)
# endregion[Constants]

try:
    from antistasi_logbook.parsing.record_line import RecordLine
except ImportError:
    @attr.s(slots=True, weakref_slot=False, frozen=True)
    class RecordLine:
        content: str = attr.ib()
        start: int = attr.ib()

        def __repr__(self) -> str:
            return self.content

        def __str__(self) -> str:
            return self.content

        def __eq__(self, o: object) -> bool:
            if isinstance(o, self.__class__):
                return self.content == o.content and self.start == o.start
            return NotImplemented


LINE_ITERATOR_TYPE = Generator[RecordLine, None, None]


class LineCache(deque):

    def __init__(self, maxlen: int = None) -> None:
        super().__init__(maxlen=maxlen)
        self.lock = Lock()

    @property
    def is_empty(self) -> bool:
        with self.lock:
            return len(self) == 0

    @property
    def is_full(self) -> bool:
        if self.maxlen is None:
            return False
        with self.lock:
            return len(self) == self.maxlen

    def append(self, x: "RecordLine") -> None:
        with self.lock:
            super().append(x)

    def appendleft(self, x: "RecordLine") -> None:
        with self.lock:
            return super().appendleft(x)

    def pop(self) -> "RecordLine":
        with self.lock:
            return super().pop()

    def popleft(self) -> "RecordLine":
        with self.lock:
            return super().popleft()

    def insert(self, i: int, x: "RecordLine") -> None:
        with self.lock:
            super().insert(i, x)

    def extend(self, iterable: Iterable["RecordLine"]) -> None:
        with self.lock:
            super().extend(iterable)

    def extendleft(self, iterable: Iterable["RecordLine"]) -> None:
        with self.lock:
            super().extendleft(iterable)

    def index(self, x: "RecordLine", start: int = None, stop: int = None) -> int:
        with self.lock:
            kwargs = {}
            if start is not None:
                kwargs["start"] = start
            if stop is not None:
                kwargs["stop"] = stop
            return super().index(x, **kwargs)

    def remove(self, value: "RecordLine") -> None:
        with self.lock:
            super().remove(value)

    def copy(self) -> deque["RecordLine"]:
        with self.lock:
            return super().copy()

    def dump(self) -> list:
        with self.lock:
            data = list(self)
            super().clear()
            return data


class LogParsingContext:
    new_log_record_signal = get_signal("new_log_record")
    mem_cache_regex = re.compile(r"-MaxMem\=(?P<max_mem>\d+)")
    __slots__ = ("__weakref__", "_log_file", "record_lock", "log_file_data", "data_lock", "foreign_key_cache", "line_cache", "_line_iterator",
                 "_current_line", "_current_line_number", "futures", "record_storage", "inserter", "_bulk_create_batch_size", "database", "config", "is_open", "done_signal", "force", "log_file_done_signal")

    def __init__(self, log_file: "LogFile", inserter: "RecordInserter", config: "GidIniConfig", foreign_key_cache: "ForeignKeyCache") -> None:
        self._log_file = log_file
        self.database = self._log_file.get_meta().database
        self.inserter = inserter
        self.log_file_data = model_to_dict(self._log_file, exclude=[LogFile.log_records, LogFile.mods, LogFile.comments, LogFile.marked], extra_attrs=["is_downloaded"])
        self.log_file_data["unparsable"] = False
        self.data_lock = RLock()
        self.foreign_key_cache = foreign_key_cache
        self.config = config
        self.line_cache = LineCache()
        self.record_storage: list["RawRecord"] = []
        self._line_iterator: LINE_ITERATOR_TYPE = None
        self._current_line: RecordLine = None
        self._current_line_number = 0
        self.futures: list[Future] = []
        self._bulk_create_batch_size: int = None
        self.record_lock = RLock()
        self.is_open: bool = False
        self.done_signal: Callable[[], None] = None
        self.log_file_done_signal: Callable[[], None] = None
        self.force: bool = False

    @property
    def _log_record_batch_size(self) -> int:

        if self._bulk_create_batch_size is None:
            # self._bulk_create_batch_size = RawRecord.insert_sql_phrase.batch_size
            self._bulk_create_batch_size = 10_000

        return self._bulk_create_batch_size

    @property
    def unparsable(self) -> bool:
        return self.log_file_data.get("unparsable", False)

    def set_unparsable(self) -> None:
        self.log_file_data["unparsable"] = True

    def set_found_meta_data(self, finder: "MetaFinder") -> None:
        log.debug("starting to set meta-data for %r", self._log_file)
        # TODO: Refractor this Monster!

        if finder is None or finder.full_datetime is None:
            log.debug("setting to unparsable, because either finder(%r) is None or finder.full_datetime(%r) is None or finder.campaign_id(%r) is None", finder, finder.full_datetime, finder.campaign_id)
            self.set_unparsable()
            if self.done_signal:
                self._log_file._cleanup()
            return

        if self.log_file_data.get("game_map") is None:
            game_map_item = self.foreign_key_cache.get_game_map_case_insensitive(finder.game_map)
            if game_map_item is None:
                game_map_item = GameMap(name=finder.game_map, full_name=f"PLACE_HOLDER {finder.game_map}")
                self.futures.append(self.inserter.insert_game_map(game_map=game_map_item))

            self.log_file_data["game_map"] = game_map_item

        if self.log_file_data.get("version") is None:
            try:
                version = self.foreign_key_cache.all_version_objects[str(finder.version)]
            except KeyError:
                version = self.inserter.thread_pool.submit(Version.add_or_get_version, finder.version)
                self.inserter.thread_pool.submit(self.foreign_key_cache.reset_sender_for_all_instances, sender=Version, created=True, isinstance=finder.version)
            self.log_file_data["version"] = version

        if self.log_file_data.get("is_new_campaign") is None:
            self.log_file_data["is_new_campaign"] = finder.is_new_campaign

        if self.log_file_data.get("campaign_id") is None and finder.campaign_id is not None:
            self.log_file_data["campaign_id"] = finder.campaign_id

        if self.log_file_data.get("utc_offset") is None:
            difference_seconds = (finder.full_datetime.utc_datetime - finder.full_datetime.local_datetime).total_seconds()

            offset_timedelta = timedelta(seconds=int(difference_seconds))
            offset = tzoffset(self.log_file_data["name"], offset_timedelta)

            self.log_file_data["utc_offset"] = offset

            with self.database.write_lock:
                self.inserter.thread_pool.submit(self._log_file.update, utc_offset=offset)

            self.log_file_data["created_at"] = self._log_file.name_datetime.replace(tzinfo=offset).astimezone(UTC)

        if finder.mods is not None and finder.mods is not MiscEnum.DEFAULT:

            self.futures.append(self.inserter.insert_mods(mod_items=finder.mods, log_file=self._log_file))
        if self.done_signal:
            self.done_signal()

    def set_header_text(self, lines: Iterable["RecordLine"]) -> None:
        if lines:
            text = '\n'.join(i.content for i in lines if i.content)
            if match := self.mem_cache_regex.search(text):
                max_mem = int(match.group("max_mem"))
                self.log_file_data["max_mem"] = max_mem
            self.log_file_data["header_text"] = text

    def set_startup_text(self, lines: Iterable["RecordLine"]) -> None:
        if lines:
            text = '\n'.join(i.content for i in lines if i.content)
            self.log_file_data["startup_text"] = text

    def _get_line_iterator(self) -> LINE_ITERATOR_TYPE:
        line_number = 0
        with self._log_file.open() as f:
            for line in f:
                line_number += 1
                if self._log_file.last_parsed_line_number is not None and line_number <= self._log_file.last_parsed_line_number:
                    continue
                line = line.rstrip()
                self._current_line_number = line_number

                yield RecordLine(content=line, start=line_number)

    @property
    def line_iterator(self) -> LINE_ITERATOR_TYPE:
        if self._line_iterator is None:
            self._line_iterator = self._get_line_iterator()
        return self._line_iterator

    @property
    def current_line(self) -> "RecordLine":
        if self._current_line is None:
            self.advance_line()

        return self._current_line

    def advance_line(self) -> None:
        self._current_line = next(self.line_iterator, ...)

    @contextmanager
    def open(self, cleanup: bool = True) -> TextIO:
        with self._log_file.open(cleanup=cleanup) as f:
            yield f

    def close(self) -> None:

        self.wait_on_futures()
        with self.data_lock:
            log.debug("updating log-file %r", self._log_file)
            self.log_file_data.pop("original_file")
            self.log_file_data.pop("is_downloaded")
            data_dict = {}
            for k, v in self.log_file_data.items():
                if isinstance(v, Future):
                    v = v.result()
                data_dict[k] = v
            task = self.inserter.update_log_file_from_dict(log_file=self._log_file, in_dict=data_dict)
            log.debug("waiting for result of 'updating log-file %r'", self._log_file)
            maybe_error = task.exception()
            if maybe_error:
                log.error(maybe_error, exc_info=True)
                raise maybe_error
            _ = task.result()

        if self._line_iterator is not None:
            self._line_iterator.close()

        # self._log_file._cleanup()
        self.is_open = False

        if self.done_signal:
            self.done_signal()
        if self.log_file_done_signal:
            self.log_file_done_signal()
        self.foreign_key_cache = None
        self.inserter = None
        log.debug("finished closing %r", self)

    def _future_callback(self, result: "ManyRecordsInsertResult") -> None:
        max_line_number = result.max_line_number
        max_recorded_at = result.max_recorded_at
        amount = result.amount

        with self.data_lock:
            try:

                self.log_file_data["last_parsed_line_number"] = max([self.log_file_data.get("last_parsed_line_number", 0), max_line_number])

            except TypeError as error:
                log.error(error)
                log.debug(max_line_number)

            try:
                if self.log_file_data.get("last_parsed_datetime") is None:
                    self.log_file_data["last_parsed_datetime"] = max_recorded_at
                else:
                    self.log_file_data["last_parsed_datetime"] = max([self.log_file_data.get("last_parsed_datetime"), max_recorded_at])
            except TypeError as error:
                log.error(error)
                log.debug(max_recorded_at)

    def insert_record(self, record: "RawRecord") -> None:
        if record is None:
            return
        with self.record_lock:
            # record.record_class = self.database.backend.record_class_manager.determine_record_class(record)[0]
            self.record_storage.append(record)

            if len(self.record_storage) == self._log_record_batch_size:
                while len([i for i in self.futures if i.done() is False]) > 5:
                    sleep(random.randint(1, 3))
                self.futures.append(self.inserter.insert_and_assign_messages(records=list(self.record_storage)))
                self.futures.append(self.inserter.insert(records=list(self.record_storage), context=self))
                self.record_storage = []

    def _dump_rest(self) -> None:
        with self.record_lock:
            if len(self.record_storage) > 0:
                self.futures.append(self.inserter.insert_and_assign_messages(records=list(self.record_storage)))
                self.futures.append(self.inserter.insert(records=list(self.record_storage), context=self))
                self.record_storage = []

    def wait_on_futures(self, timeout: float = None) -> None:
        with self.record_lock:
            log.debug("Waiting for futures of %r (amount: %r)", self, len(self.futures))
            done, not_done = wait(self.futures, return_when=ALL_COMPLETED, timeout=timeout)
            log.debug("finished waiting for futures")

            try:
                for t in list(done) + list(not_done):
                    exception = t.exception()
                    if exception is not None:
                        log.error(exception, exc_info=True)
                        raise exception
            except Exception as e:
                log.error(e, exc_info=True)
                log.critical("error %r encountered with log-file %r", e, self._log_file)

            self.log_file_data["last_parsed_datetime"] = self.log_file_data.get("modified_at")

    def __enter__(self) -> "LogParsingContext":
        self._log_file.download()
        self.is_open = True
        return self

    def __exit__(self, exception_type: type = None, exception_value: BaseException = None, traceback: Any = None) -> None:
        try:
            self.close()
        except Exception as e:
            log.error(e, exc_info=True)
        finally:
            if exception_value is not None:
                log.error("%s, %s", exception_type, exception_value)
                log.error(''.join(format_tb(traceback)))
                raise exception_value

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(log_file={self._log_file!r})"


# region[Main_Exec]
if __name__ == '__main__':
    pass
# endregion[Main_Exec]
