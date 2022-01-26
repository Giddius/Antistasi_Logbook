"""
WiP.

Soon.
"""

# region [Imports]

# * Standard Library Imports ---------------------------------------------------------------------------->
from queue import Queue
from typing import TYPE_CHECKING, Any, Iterable, Optional
from pathlib import Path
from datetime import datetime, timezone
from threading import Lock, RLock
from concurrent.futures import Future, ThreadPoolExecutor

# * Third Party Imports --------------------------------------------------------------------------------->
import attr
from dateutil.tz import UTC, tzoffset
from playhouse.shortcuts import update_model_from_dict

# * Gid Imports ----------------------------------------------------------------------------------------->
from gidapptools import get_logger

# * Local Imports --------------------------------------------------------------------------------------->
from antistasi_logbook.parsing.raw_record import RawRecord
from antistasi_logbook.storage.models.models import Mod, GameMap, LogFile, LogRecord, RecordClass, RecordOrigin, AntstasiFunction, LogFileAndModJoin
from antistasi_logbook.parsing.parsing_context import LogParsingContext
from antistasi_logbook.parsing.foreign_key_cache import ForeignKeyCache

# * Type-Checking Imports --------------------------------------------------------------------------------->
if TYPE_CHECKING:
    from gidapptools.gid_config.interface import GidIniConfig

    from antistasi_logbook.backend import Backend
    from antistasi_logbook.parsing.parser import SimpleRegexKeeper, RecordClassManager
    from antistasi_logbook.storage.database import GidSqliteApswDatabase

# endregion[Imports]

# region [TODO]


# endregion [TODO]

# region [Logging]


# endregion[Logging]

# region [Constants]
from gidapptools.general_helper.timing import get_dummy_profile_decorator_in_globals
get_dummy_profile_decorator_in_globals()
THIS_FILE_DIR = Path(__file__).parent.absolute()
log = get_logger(__name__)
# endregion[Constants]


class RecordStorage(Queue):

    def __init__(self, maxsize: int = 0) -> None:
        super().__init__(maxsize=maxsize)
        self.mutex = RLock()

    def dump(self) -> list:
        with self.mutex:
            if self.empty() is False:
                _out = list(self.queue)
                self.queue.clear()
                self.unfinished_tasks -= (len(_out) - 1)
                self.task_done()
                return _out


@attr.s(auto_detect=True, auto_attribs=True, slots=True, weakref_slot=True, frozen=True)
class ManyRecordsInsertResult:
    max_line_number: int = attr.ib()
    max_recorded_at: datetime = attr.ib()
    amount: int = attr.ib()
    context: LogParsingContext = attr.ib()


class RecordInserter:
    insert_records_phrase = """INSERT OR IGNORE INTO "LogRecord" ("start", "end", "message", "recorded_at", "called_by", "origin", "logged_from", "log_file", "log_level", "marked") VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"""
    update_record_record_class_phrase = """UPDATE "LogRecord" SET "record_class" = ? WHERE "id" = ?"""

    def __init__(self, config: "GidIniConfig", backend: "Backend") -> None:
        self.config = config
        self.backend = backend

    @property
    def thread_pool(self) -> ThreadPoolExecutor:
        return self.backend.inserting_thread_pool

    @property
    def database(self) -> "GidSqliteApswDatabase":
        return self.backend.database

    @property
    def write_lock(self) -> Lock:
        return self.database.write_lock

    def _insert_func(self, records: Iterable["RawRecord"], context: "LogParsingContext") -> ManyRecordsInsertResult:

        # LogRecord.insert_many(i.to_log_record_dict(log_file=context._log_file) for i in records).execute()
        params = (i.to_sql_params(log_file=context._log_file) for i in records)
        with self.write_lock:
            with self.database:
                cur = self.database.cursor(True)

                cur.executemany(self.insert_records_phrase, params)

        # for record in records:
        #     params = record.to_sql_params(log_file=context._log_file)
        #     self.database.execute_sql(self.insert_phrase, params=params)

        result = ManyRecordsInsertResult(max_line_number=max(item.end for item in records), max_recorded_at=max(item.recorded_at for item in records), amount=len(records), context=context)
        return result

    def insert(self, records: Iterable["RawRecord"], context: "LogParsingContext") -> Future:
        def _callback(_context: "LogParsingContext"):

            def _inner(future: "Future"):
                _context._future_callback(future.result())
            return _inner
        future = self.thread_pool.submit(self._insert_func, records=records, context=context)
        future.add_done_callback(_callback(_context=context))
        return future

    def _execute_update_record_class(self, log_record: LogRecord, record_class: RecordClass) -> None:
        with self.database.write_lock:
            with self.database:
                LogRecord.update(record_class=record_class).where(LogRecord.id == log_record.id).execute()

    def _execute_many_update_record_class(self, pairs: list[tuple[int, int]]) -> int:

        with self.write_lock:
            with self.database:
                cur = self.database.cursor(True)
                cur.executemany(self.update_record_record_class_phrase, pairs)

        return len(pairs)

    def update_record_class(self, log_record: LogRecord, record_class: RecordClass) -> Future:
        return self.thread_pool.submit(self._execute_update_record_class, log_record=log_record, record_class=record_class)

    def many_update_record_class(self, pairs: list[tuple[int, int]]) -> Future:
        return self.thread_pool.submit(self._execute_many_update_record_class, pairs=pairs)

    def _execute_insert_mods(self, mod_items: Iterable[Mod], log_file: LogFile) -> None:
        mod_data = [mod_item.as_dict() for mod_item in mod_items]
        q_1 = Mod.insert_many(mod_data).on_conflict_ignore()
        with self.write_lock:
            with self.database:

                q_1.execute()

        refreshed_mods_ids = (Mod.get(**mod_item.as_dict()) for mod_item in mod_items)
        q_2 = LogFileAndModJoin.insert_many({"log_file": log_file.id, "mod": refreshed_mod_id} for refreshed_mod_id in refreshed_mods_ids).on_conflict_ignore()

        with self.write_lock:
            with self.database:

                q_2.execute()

    def insert_mods(self, mod_items: Iterable[Mod], log_file: LogFile) -> Future:
        return self.thread_pool.submit(self._execute_insert_mods, mod_items=mod_items, log_file=log_file)

    def _execute_update_log_file_from_dict(self, log_file: LogFile, in_dict: dict):
        item = update_model_from_dict(log_file, in_dict)
        with self.write_lock:
            with self.database:

                item.save()

    def update_log_file_from_dict(self, log_file: LogFile, in_dict: dict) -> Future:
        return self.thread_pool.submit(self._execute_update_log_file_from_dict, log_file=log_file, in_dict=in_dict)

    def _execute_insert_game_map(self, game_map: "GameMap"):
        with self.write_lock:
            with self.database:
                game_map.save()

    def insert_game_map(self, game_map: "GameMap") -> Future:
        return self.thread_pool.submit(self._execute_insert_game_map, game_map=game_map)

    def __call__(self, records: Iterable["RawRecord"], context: "LogParsingContext") -> Future:
        return self.insert(records=records, context=context)

    def shutdown(self) -> None:
        pass


class RecordProcessor:
    _default_origin: "RecordOrigin" = None
    _antistasi_origin: "RecordOrigin" = None
    __slots__ = ("regex_keeper", "backend")

    def __init__(self, backend: "Backend", regex_keeper: "SimpleRegexKeeper") -> None:
        self.backend = backend
        self.regex_keeper = regex_keeper

    @property
    def record_class_manager(self) -> "RecordClassManager":
        return self.backend.record_class_manager

    @property
    def foreign_key_cache(self) -> "ForeignKeyCache":
        return self.backend.foreign_key_cache

    @property
    def database(self) -> "GidSqliteApswDatabase":
        return self.backend.database

    @staticmethod
    def clean_antistasi_function_name(in_name: str) -> str:
        return in_name.strip().removeprefix("A3A_fnc_").removeprefix("fn_").removesuffix('.sqf').removeprefix("HR_GRG_fnc_")

    @property
    def default_origin(self) -> RecordOrigin:
        if self.__class__._default_origin is None:
            self.__class__._default_origin = [origin for origin in self.foreign_key_cache.all_origin_objects.values() if origin.is_default is True][0]
        return self.__class__._default_origin

    @property
    def antistasi_origin(self) -> RecordOrigin:
        if self.__class__._antistasi_origin is None:
            self.__class__._antistasi_origin = [origin for origin in self.foreign_key_cache.all_origin_objects.values() if origin.name.casefold() == "antistasi"][0]
        return self.__class__._antistasi_origin

    def _process_generic_record(self, raw_record: "RawRecord") -> "RawRecord":
        match = self.regex_keeper.generic_record.match(raw_record.content.strip())
        if not match:
            return None
        msg = match.group("message").lstrip()
        if msg.startswith('"') and msg.endswith('"'):
            msg = msg.strip('"').strip()
        _out = {"message": msg}

        _out["local_recorded_at"] = datetime(year=int(match.group("year")),
                                             month=int(match.group("month")),
                                             day=int(match.group("day")),
                                             hour=int(match.group("hour")),
                                             minute=int(match.group("minute")),
                                             second=int(match.group("second")),
                                             microsecond=0)
        if "error in expression" in raw_record.content.casefold():
            _out['log_level'] = "ERROR"
        elif "warning message:" in raw_record.content.casefold() or _out["message"].strip().casefold().startswith("warning:"):
            _out["log_level"] = "WARNING"
        raw_record.parsed_data = _out

        return raw_record

    def _process_antistasi_record(self, raw_record: "RawRecord") -> "RawRecord":
        datetime_part, antistasi_indicator_part, log_level_part, file_part, rest = raw_record.content.split('|', maxsplit=4)

        match = self.regex_keeper.full_datetime.match(datetime_part)
        if not match:

            return None

        _out = {"recorded_at": datetime(tzinfo=UTC,
                                        year=int(match.group("year")),
                                        month=int(match.group("month")),
                                        day=int(match.group("day")),
                                        hour=int(match.group("hour")),
                                        minute=int(match.group("minute")),
                                        second=int(match.group("second")),
                                        microsecond=int(match.group("microsecond") + "000")),
                "log_level": log_level_part.strip().upper(),
                "logged_from": self.clean_antistasi_function_name(file_part.strip().removeprefix("File:"))}

        if called_by_match := self.regex_keeper.called_by.match(rest):
            _rest, called_by, _other_rest = called_by_match.groups()
            _out["called_by"] = self.clean_antistasi_function_name(called_by)
            _out["message"] = (_rest + _other_rest).lstrip()
        else:
            _out["message"] = rest.strip()
        if _out["message"].startswith('"') and _out["message"].endswith('"'):
            _out["message"] = _out["message"].strip('"').strip()
        raw_record.parsed_data = _out
        if raw_record.parsed_data.get('logged_from') is None:
            log.info(_out)
        return raw_record

    def determine_record_class(self, raw_record: "RawRecord") -> "RecordClass":
        record_class = self.record_class_manager.determine_record_class(raw_record)
        return record_class

    def _convert_raw_record_foreign_keys(self, parsed_data: Optional[dict[str, Any]], utc_offset: tzoffset) -> Optional[dict[str, Any]]:

        def _get_or_create_antistasi_file(raw_name: str) -> AntstasiFunction:
            try:
                return self.foreign_key_cache.all_antistasi_file_objects[raw_name]
            except KeyError:
                with self.database.write_lock:
                    AntstasiFunction.insert(name=raw_name).on_conflict_ignore().execute()
                    return AntstasiFunction.get(name=raw_name)

        if parsed_data is None:
            return parsed_data

        if parsed_data.get("log_level") is not None:
            parsed_data["log_level"] = self.foreign_key_cache.all_log_levels[parsed_data["log_level"]]
        else:
            parsed_data["log_level"] = self.foreign_key_cache.all_log_levels["NO_LEVEL"]

        if parsed_data.get("logged_from"):
            parsed_data["logged_from"] = _get_or_create_antistasi_file(parsed_data["logged_from"])

        if parsed_data.get("called_by"):
            parsed_data["called_by"] = _get_or_create_antistasi_file(parsed_data["called_by"])

        if parsed_data.get("local_recorded_at"):
            local_recorded_at = parsed_data.pop("local_recorded_at")
            utc_recorded_at = (local_recorded_at + utc_offset._offset).replace(tzinfo=UTC)
            parsed_data["recorded_at"] = utc_recorded_at
        return parsed_data

    def determine_origin(self, raw_record: "RawRecord") -> RecordOrigin:
        for origin in self.foreign_key_cache.all_origin_objects.values():
            if origin.is_default is False:
                if origin.check(raw_record) is True:
                    return origin
        return self.default_origin

    def __call__(self, raw_record: "RawRecord", utc_offset: timezone) -> "RawRecord":
        raw_record.record_origin = self.determine_origin(raw_record)
        if raw_record.record_origin == self.antistasi_origin:
            raw_record = self._process_antistasi_record(raw_record)
        else:
            raw_record = self._process_generic_record(raw_record)
        if raw_record is None:
            return

        raw_record.parsed_data = self._convert_raw_record_foreign_keys(parsed_data=raw_record.parsed_data, utc_offset=utc_offset)

        return raw_record

        # region[Main_Exec]
if __name__ == '__main__':
    pass

# endregion[Main_Exec]
