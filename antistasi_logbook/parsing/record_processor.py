"""
WiP.

Soon.
"""

# region [Imports]

# * Standard Library Imports ---------------------------------------------------------------------------->
import re
import sys
from time import perf_counter
from queue import Queue
from typing import TYPE_CHECKING, Any, Union, Iterable, Optional
from pathlib import Path
from datetime import datetime, timezone
from threading import Lock, RLock
import threading
from concurrent.futures import Future, ThreadPoolExecutor

# * Third Party Imports --------------------------------------------------------------------------------->
import apsw
import attr
from peewee import DoesNotExist, IntegrityError
from dateutil.tz import UTC, tzoffset
from playhouse.signals import post_save

# * Gid Imports ----------------------------------------------------------------------------------------->
from gidapptools import get_logger
from gidapptools.general_helper.timing import time_func, get_dummy_profile_decorator_in_globals
from gidapptools.general_helper.conversion import number_to_pretty

# * Local Imports --------------------------------------------------------------------------------------->
from antistasi_logbook.parsing.py_raw_record import RawRecord
from antistasi_logbook.storage.models.models import Mod, GameMap, LogFile, Message, RecordClass, ArmaFunction, RecordOrigin, OriginalLogFile, LogFileAndModJoin, ArmaFunctionAuthorPrefix
from antistasi_logbook.parsing.parsing_context import LogParsingContext
from antistasi_logbook.parsing.foreign_key_cache import ForeignKeyCache

# * Type-Checking Imports --------------------------------------------------------------------------------->
if TYPE_CHECKING:
    import apsw

    from gidapptools.gid_config.interface import GidIniConfig

    from antistasi_logbook.backend import Backend
    from antistasi_logbook.parsing.parser import SimpleRegexKeeper, RecordClassManager
    from antistasi_logbook.storage.database import GidSqliteApswDatabase
    from antistasi_logbook.records.record_class_manager import RecordClassChecker
    from antistasi_logbook.parsing.meta_log_finder import RawModData
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
    __slots__ = ("config", "backend", "write_lock", "mods_lock", "consecutive_insert_funcs", "consecutive_insert_funcs_lock", "thread_pool")

    update_record_record_class_phrase = """UPDATE "LogRecord" SET "record_class" = ? WHERE "id" = ?"""

    def __init__(self, config: "GidIniConfig", backend: "Backend") -> None:
        self.config = config
        self.backend = backend
        self.write_lock: RLock = self.database.write_lock
        self.mods_lock = Lock()
        self.consecutive_insert_funcs: int = 0
        self.consecutive_insert_funcs_lock = RLock()
        self.thread_pool = ThreadPoolExecutor(1, thread_name_prefix="inserter", initializer=self.database.connect, initargs=(True,))

    @property
    def database(self) -> "GidSqliteApswDatabase":
        return self.backend.database

    def _insert_func(self, records: Union[Iterable["RawRecord"], Future], context: "LogParsingContext") -> ManyRecordsInsertResult:

        start_time = perf_counter()
        record_params = list(r.to_sql_params(context._log_file) for r in records)
        record_insert_phrase = str(RawRecord.insert_sql_phrase.phrase)
        with self.database.connection() as conn:
            conn.executemany(record_insert_phrase, record_params)

        log.debug("inserted %r records in %.3f s", len(records), perf_counter() - start_time)

        return ManyRecordsInsertResult(max_line_number=max(item.end for item in records), max_recorded_at=max(item.recorded_at for item in records), amount=len([r for r in records]), context=context)

    def _refresh_connection(self):
        self.database.close()
        self.database.connect(False)

    def insert(self, records: Union[Iterable["RawRecord"], Future], context: "LogParsingContext") -> Future:
        def _callback(_context: "LogParsingContext"):

            def _inner(future: "Future"):
                _context._future_callback(future.result())
            return _inner

        future = self.thread_pool.submit(self._insert_func, records=records, context=context)
        future.add_done_callback(_callback(_context=context))

        return future

    def _execute_update_record_class(self, log_record_id: int, record_class_id: int) -> None:

        self.database.connection().execute(self.update_record_record_class_phrase, (record_class_id, log_record_id))

    def _execute_many_update_record_class(self, pairs: tuple[tuple[int, int]]) -> int:

        self.database.connection().executemany(self.update_record_record_class_phrase, tuple(pairs))

        log.info("inserted new record class for %s records", number_to_pretty(len(pairs)))
        return len(pairs)

    def update_record_class(self, log_record_id: int, record_class_id: int) -> Future:
        return self.thread_pool.submit(self._execute_update_record_class, log_record_id=log_record_id, record_class_id=record_class_id)

    def many_update_record_class(self, pairs: tuple[tuple[int, int]]) -> Future:
        return self.thread_pool.submit(self._execute_many_update_record_class, pairs=pairs)

    def _execute_insert_mods(self, mod_data: Iterable["RawModData"], log_file: LogFile) -> None:
        actual_mods = []
        for raw_data in mod_data:
            actual_mod, was_created = Mod.from_raw_mod_data(raw_data)
            if was_created is True:
                log.debug("created Mod %r", actual_mod)
            actual_mods.append(actual_mod)

        log.debug("creating insert_mods_parameters")
        log_file_mod_params = tuple({"log_file": log_file.id, "mod": m.id} for m in actual_mods if m)

        log.debug("inserting insert_mods")
        LogFileAndModJoin.insert_many(log_file_mod_params).on_conflict_ignore().execute()
        log.debug("finished inserting_mods")
        if len(log_file_mod_params) > 0:
            log.info("Assigned %r mods to log file %r", len(log_file_mod_params), log_file)

    def insert_mods(self, mod_data: Iterable["RawModData"], log_file: LogFile) -> Future:
        return self.thread_pool.submit(self._execute_insert_mods, mod_data=mod_data, log_file=log_file)

    def _execute_update_log_file_from_dict(self, log_file: LogFile, in_dict: dict):
        log.debug("running log_file update for %r", log_file)

        try:
            in_dict = dict(in_dict)
            try:
                del in_dict["id"]
            except KeyError:
                pass
            for key_name in ("server", "game_map", "version", "original_file", "mod_set"):
                value = in_dict.get(key_name)
                if value is not None and isinstance(value, dict):
                    in_dict[key_name] = value["id"]

            in_dict["mod_set"] = log_file.determine_mod_set()

            LogFile.update(**{k: v for k, v in in_dict.items() if v is not None}).where(LogFile.id == log_file.id).execute()

            LogFile.get_by_id_cached.cache_clear()

            return log_file.id
        except Exception as e:
            log.critical("log_file_data_dict: \n        %s", '\n        '.join(f"{k!r}:{v!r}" for k, v in in_dict.items()))
            log.error(e, exc_info=True)
            raise

    def update_log_file_from_dict(self, log_file: LogFile, in_dict: dict) -> Future:

        future = self.thread_pool.submit(self._execute_update_log_file_from_dict, log_file=log_file, in_dict=in_dict)

        return future

    def _execute_insert_game_map(self, game_map: "GameMap"):

        try:

            game_map.save()
            log.info("inserted game map %r", game_map)
            ForeignKeyCache.reset_all_instances()
        except IntegrityError as e:
            log.critical("encountered error %r while inserting game-map %r", e, game_map)

    def insert_game_map(self, game_map: "GameMap") -> Future:
        return self.thread_pool.submit(self._execute_insert_game_map, game_map=game_map)

    def _execute_insert_original_log_file(self, original_log_file: OriginalLogFile, log_file: LogFile):

        try:

            OriginalLogFile.insert(text_hash=original_log_file.text_hash, name=original_log_file.name, server=original_log_file.server).on_conflict_replace().execute()
            LogFile.update(original_file=OriginalLogFile.select(OriginalLogFile.id).where(OriginalLogFile.text_hash == original_log_file.text_hash)).where(LogFile.id == log_file.id).execute()
        except Exception as e:
            log.error(e, exc_info=True)
            raise
        return original_log_file

    def insert_original_log_file(self, file_path: Path, log_file: LogFile) -> Future:
        return self.thread_pool.submit(self._execute_insert_original_log_file, original_log_file=OriginalLogFile.init_from_file(file_path, server=log_file.server), log_file=log_file)

    def _execute_insert_messages(self, records: Iterable["RawRecord"]):
        start_time = perf_counter()
        message_params = list({(Message.md5_hash.db_value(r.message_hash), Message.text.db_value(r.message)) for r in records if r and r.message_hash not in self.database.most_common_messages.keys()})

        with self.database.connection() as conn:
            conn.executemany('INSERT OR IGNORE INTO "Message" ("md5_hash", "text") VALUES (?, ?)', message_params)

        end_time = perf_counter()
        log.debug("inserted %r messsages in %.3f s", len(message_params), end_time - start_time)

    def insert_messages(self, records: Iterable["RawRecord"]) -> Future:
        if isinstance(records, Future):
            records = records.result()
        return self.thread_pool.submit(self._execute_insert_messages, records=records)

    def _execute_update_original_log_file(self, original_log_file: OriginalLogFile):

        OriginalLogFile.update(text_hash=original_log_file.text_hash).where(OriginalLogFile.id == original_log_file.id).execute()

        return original_log_file

    def update_original_log_file(self, existing_original_log_file: OriginalLogFile, file_path: Path) -> Future:
        return self.thread_pool.submit(self._execute_update_original_log_file, original_log_file=existing_original_log_file.modify_update_from_file(file_path=file_path))

    def __call__(self, records: Union[Iterable["RawRecord"], Future], context: "LogParsingContext") -> Future:
        return self.insert(records=records, context=context)

    def shutdown(self) -> None:
        def _close_connection(a_number: int):
            self.database.commit()
            conn: apsw.Connection = self.database.connection()
            if conn is not None:
                conn.close(True)

        for pool in [self.thread_pool]:
            dummy = list(range(pool._max_workers * 2))
            list(pool.map(lambda x: _close_connection, dummy))

        self.thread_pool.shutdown(wait=True)


class RecordProcessor:
    _error_words: tuple[str] = tuple(w.casefold() for w in ("error", "error:"))
    msg_word_split_regex: re.Pattern = re.compile(r"\s|\:|\,|\.|\!|\?|\||\;|\[|\]|\(|\)|\<|\>|\=")
    _default_origin: "RecordOrigin" = None
    _antistasi_origin: "RecordOrigin" = None
    _arma_function_lock: RLock = RLock()
    __slots__ = ("regex_keeper", "backend", "foreign_key_cache", "_record_checker")

    def __init__(self, backend: "Backend", regex_keeper: "SimpleRegexKeeper", foreign_key_cache: "ForeignKeyCache") -> None:
        self.backend = backend
        self.regex_keeper = regex_keeper
        self.foreign_key_cache = foreign_key_cache

        self._record_checker = None

    @property
    def record_checker(self) -> "RecordClassChecker":
        if self._record_checker is None:
            self._record_checker = self.backend.record_class_manager.get_record_checker()
        return self._record_checker

    @ property
    def record_class_manager(self) -> "RecordClassManager":
        return self.backend.record_class_manager

    @ property
    def database(self) -> "GidSqliteApswDatabase":
        return self.backend.database

    @ staticmethod
    def clean_antistasi_function_name(in_name: str) -> str:
        return in_name.strip().removeprefix("A3A_fnc_").removeprefix("fn_").removesuffix('.sqf').removeprefix("HR_GRG_fnc_")

    @ property
    def default_origin(self) -> RecordOrigin:
        if self.__class__._default_origin is None:
            self.__class__._default_origin = [origin for origin in self.foreign_key_cache.all_origin_objects.values() if origin.is_default is True][0]
        return self.__class__._default_origin

    @ property
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
                                             microsecond=0,
                                             tzinfo=raw_record.utc_offset)

        msg_words = set(self.msg_word_split_regex.split(raw_record.content.casefold()))
        if any(error_word in msg_words for error_word in self._error_words):
            _out['log_level'] = "ERROR"
        elif "warning" in msg_words:
            _out["log_level"] = "WARNING"
        raw_record.parsed_data = _out

        return raw_record

    def _process_antistasi_record(self, raw_record: "RawRecord") -> "RawRecord":
        datetime_part, antistasi_indicator_part, log_level_part, file_part, rest = raw_record.content.split('|', maxsplit=4)

        match = self.regex_keeper.full_datetime.match(datetime_part)
        if not match:
            log.critical("unable to parse full datetime for Antistasi record with rest %r, content: %r", rest, raw_record.content)
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
                "logged_from": file_part.strip().removeprefix("File:")}

        if called_by_match := self.regex_keeper.called_by.match(rest):
            _rest, called_by, _other_rest = called_by_match.groups()
            _out["called_by"] = called_by
            _out["message"] = (_rest + _other_rest).lstrip()
        else:
            _out["message"] = rest.strip()
        if _out["message"].startswith('"') and _out["message"].endswith('"'):
            _out["message"] = _out["message"].strip('"').strip()
        raw_record.parsed_data = _out

        return raw_record

    def determine_record_class(self, raw_record: "RawRecord") -> "RecordClass":
        record_class = self.record_checker._determine_record_class(raw_record)
        return record_class

    def _get_or_create_antistasi_file(self, raw_name: str) -> ArmaFunction:
        parsed_function_data = ArmaFunction.parse_raw_function_name(raw_name)

        try:
            return self.foreign_key_cache.all_arma_file_objects[(parsed_function_data["name"], parsed_function_data["author_prefix"])]

        except KeyError:
            with self.database.connection_context() as ctx:
                try:
                    author_prefix = next(ArmaFunctionAuthorPrefix.select().where(ArmaFunctionAuthorPrefix.name == parsed_function_data["author_prefix"]).limit(1).iterator())
                    created_author_prefix = False
                except (DoesNotExist, IndexError, AttributeError, StopIteration):
                    ArmaFunctionAuthorPrefix.insert(name=parsed_function_data["author_prefix"]).on_conflict_ignore().execute(self.database)
                    created_author_prefix = True
                author_prefix = next(ArmaFunctionAuthorPrefix.select().where(ArmaFunctionAuthorPrefix.name == parsed_function_data["author_prefix"]).limit(1).iterator())
                if created_author_prefix is True:
                    post_save.send(author_prefix, created=True)

                arma_function_insert_result = ArmaFunction.insert(name=parsed_function_data["name"], author_prefix=author_prefix).on_conflict_ignore().execute(self.database)

                arma_function = next(ArmaFunction.select().where((ArmaFunction.name == parsed_function_data["name"]) & (ArmaFunction.author_prefix == author_prefix)).limit(1).iterator())
                if arma_function_insert_result > 0:
                    post_save.send(arma_function, created=True)
                return arma_function

    def _convert_raw_record_foreign_keys(self, parsed_data: Optional[dict[str, Any]]) -> Optional[dict[str, Any]]:

        if parsed_data is None:
            return parsed_data

        if parsed_data.get("log_level") is not None:
            parsed_data["log_level"] = self.foreign_key_cache.all_log_levels[parsed_data["log_level"]]
        else:
            parsed_data["log_level"] = self.foreign_key_cache.all_log_levels["NO_LEVEL"]

        if parsed_data.get("logged_from") is not None:
            parsed_data["logged_from"] = self._get_or_create_antistasi_file(parsed_data["logged_from"])

        if parsed_data.get("called_by") is not None:
            parsed_data["called_by"] = self._get_or_create_antistasi_file(parsed_data["called_by"])

        if parsed_data.get("local_recorded_at"):
            local_recorded_at: datetime = parsed_data.pop("local_recorded_at")

            parsed_data["recorded_at"] = local_recorded_at.astimezone(UTC)
        return parsed_data

    def determine_origin(self, raw_record: "RawRecord") -> RecordOrigin:
        found_origin = self.default_origin
        for origin in (o for o in self.foreign_key_cache.all_origin_objects.values() if o.is_default is False):
            if origin.check(raw_record) is True:
                found_origin = origin
                break
        return found_origin

    def __call__(self, raw_record: "RawRecord") -> "RawRecord":
        if self.regex_keeper.fault_error_start.search(raw_record.content):
            log.warning("found fault-error in record %r", raw_record)
            line_split_1 = [idx for idx, l in enumerate(raw_record.lines) if l.content == "======================================================="][0]
            line_split_2 = [idx for idx, l in enumerate(raw_record.lines) if l.content == "-------------------------------------------------------"][0]
            if line_split_2 == line_split_1 + 1:
                new_lines = list(raw_record.lines)[:line_split_1]
                raw_record = raw_record.__class__(lines=new_lines, utc_offset=raw_record.utc_offset)

        raw_record.record_origin = self.determine_origin(raw_record)
        if raw_record.record_origin == self.antistasi_origin:
            raw_record = self._process_antistasi_record(raw_record)
        else:
            raw_record = self._process_generic_record(raw_record)
        if raw_record is None:
            return

        raw_record.parsed_data = self._convert_raw_record_foreign_keys(parsed_data=raw_record.parsed_data)
        raw_record._message_hash = Message.hash_text(raw_record.message)

        raw_record.record_class = self.determine_record_class(raw_record=raw_record)
        return raw_record


# region[Main_Exec]

if __name__ == '__main__':
    pass

# endregion[Main_Exec]
