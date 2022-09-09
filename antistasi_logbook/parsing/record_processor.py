"""
WiP.

Soon.
"""

# region [Imports]

# * Standard Library Imports ---------------------------------------------------------------------------->
from time import sleep, perf_counter, thread_time
from queue import Queue
import re
from typing import TYPE_CHECKING, Any, Iterable, Optional, Generator
from pathlib import Path
from datetime import datetime, timezone
from threading import Lock, RLock
from concurrent.futures import Future, ThreadPoolExecutor
from hashlib import md5, blake2b, blake2s
from functools import partial
# * Third Party Imports --------------------------------------------------------------------------------->
import attr
import apsw
from peewee import DoesNotExist, chunked, IntegrityError, fn
from dateutil.tz import UTC, tzoffset
from playhouse.shortcuts import update_model_from_dict, chunked
from gidapptools.general_helper.timing import get_dummy_profile_decorator_in_globals
# * Gid Imports ----------------------------------------------------------------------------------------->
from gidapptools import get_logger
from gidapptools.general_helper.conversion import number_to_pretty
from functools import lru_cache
# * Local Imports --------------------------------------------------------------------------------------->
from antistasi_logbook.parsing.raw_record import RawRecord
from antistasi_logbook.storage.models.models import Mod, GameMap, LogFile, LogRecord, Message, RecordClass, ArmaFunction, RecordOrigin, LogFileAndModJoin, ArmaFunctionAuthorPrefix, OriginalLogFile
from antistasi_logbook.parsing.parsing_context import LogParsingContext
from antistasi_logbook.parsing.foreign_key_cache import ForeignKeyCache
from playhouse.signals import post_save
# * Type-Checking Imports --------------------------------------------------------------------------------->
if TYPE_CHECKING:
    from gidapptools.gid_config.interface import GidIniConfig
    import apsw
    from antistasi_logbook.backend import Backend
    from antistasi_logbook.parsing.parser import SimpleRegexKeeper, RecordClassManager
    from antistasi_logbook.storage.database import GidSqliteApswDatabase

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
    __slots__ = ("config", "backend", "write_lock", "mods_lock", "consecutive_insert_funcs", "consecutive_insert_funcs_lock")

    update_record_record_class_phrase = """UPDATE "LogRecord" SET "record_class" = ? WHERE "id" = ?"""

    def __init__(self, config: "GidIniConfig", backend: "Backend") -> None:
        self.config = config
        self.backend = backend
        self.write_lock: RLock = self.backend.database.write_lock
        self.mods_lock = Lock()
        self.consecutive_insert_funcs: int = 0
        self.consecutive_insert_funcs_lock = RLock()

    @property
    def thread_pool(self) -> ThreadPoolExecutor:
        return self.backend.inserting_thread_pool

    @property
    def database(self) -> "GidSqliteApswDatabase":
        return self.backend.database

    # @property
    # def write_lock(self) -> Lock:
    #     return self.database.write_lock
    @lru_cache(1024 * 10)
    def _get_message_id(self, in_message: str) -> int:
        return Message.select(Message.id).where((Message.text == in_message)).scalar()

    def _insert_func(self, records: Iterable["RawRecord"], context: "LogParsingContext") -> ManyRecordsInsertResult:
        messages = ({"text": t} for t in {r.message for r in records if r})
        batch_size = int(context._log_record_batch_size // 10)
        for message_params in chunked(messages, batch_size):
            message_params = tuple(message_params)
            with self.database.atomic() as txn:
                message_insert_start_time = perf_counter()

                Message.insert_many(message_params).on_conflict_ignore().execute()

            message_insert_time_taken = perf_counter() - message_insert_start_time
            log.debug("inserted %r messages in %.3f s", len(message_params), message_insert_time_taken)

        def _resolve_message_item(in_raw_record: "RawRecord", in_log_file: "LogFile") -> dict:

            in_raw_record.message_item_id = self._get_message_id(in_raw_record.message)
            return in_raw_record.to_log_record_dict(log_file=in_log_file)

        amount_collected = 0
        max_amount = len(tuple(r for r in records if r))

        record_params = (_resolve_message_item(r, in_log_file=context._log_file) for r in records if r)
        for record_param_chunk in chunked(record_params, batch_size):

            start_time = perf_counter()

            LogRecord.insert_many(tuple(record_param_chunk)).on_conflict_ignore().execute()

            time_taken = perf_counter() - start_time
            amount_collected += len(record_param_chunk)
            log.debug("inserted %r/%r (%r) records in %.3f s", amount_collected, max_amount, len(record_param_chunk), time_taken)

        return ManyRecordsInsertResult(max_line_number=max(item.end for item in records if item), max_recorded_at=max(item.recorded_at for item in records if item), amount=len([r for r in records if r]), context=context)

    def _refresh_connection(self):
        log.debug("cache stats: %r", self._get_message_id.cache_info())
        self.database.connect(True)
        self.database.optimize()
        self.database.checkpoint()
        self.database.close()
        self.database.connect(True)

    def insert(self, records: Iterable["RawRecord"], context: "LogParsingContext") -> Future:
        def _callback(_context: "LogParsingContext"):

            def _inner(future: "Future"):
                _context._future_callback(future.result())
            return _inner
        future = self.thread_pool.submit(self._insert_func, records=records, context=context)
        future.add_done_callback(_callback(_context=context))
        with self.consecutive_insert_funcs_lock:
            self.consecutive_insert_funcs += 1
            if self.consecutive_insert_funcs >= 25:
                self.consecutive_insert_funcs = 0
                self.thread_pool.submit(self._refresh_connection)
        return future

    def _execute_update_record_class(self, log_record_id: int, record_class_id: int) -> None:

        # with self.database.atomic("IMMEDIATE") as txn:

        cur: apsw.Cursor = self.database.cursor(True)
        cur.execute(self.update_record_record_class_phrase, (record_class_id, log_record_id))
        # txn.commit()

    def _execute_many_update_record_class(self, pairs: tuple[tuple[int, int]]) -> int:

        cur = self.database.cursor(True)
        cur.executemany(self.update_record_record_class_phrase, tuple(pairs))

        log.info("inserted new record class for %s records", number_to_pretty(len(pairs)))
        return len(pairs)

    def update_record_class(self, log_record_id: int, record_class_id: int) -> Future:
        return self.thread_pool.submit(self._execute_update_record_class, log_record_id=log_record_id, record_class_id=record_class_id)

    def many_update_record_class(self, pairs: tuple[tuple[int, int]]) -> Future:
        return self.thread_pool.submit(self._execute_many_update_record_class, pairs=pairs)

    def _execute_insert_mods(self, mod_items: Iterable[Mod], log_file: LogFile) -> None:
        mod_data = [mod_item.as_dict() for mod_item in mod_items]
        log.debug("amount mod_data %r", len(mod_data))
        self.database.commit()
        with self.database.atomic("IMMEDIATE"):

            amount_inserted = Mod.insert_many(mod_data).on_conflict_ignore().execute()
        if amount_inserted > 0:
            log.info("inserted %r (%r) new mods", amount_inserted, len(mod_data))
        join_params = []
        for mod in mod_items:
            sub_query = Mod.select(Mod.id).where((Mod.mod_hash == mod.mod_hash) & (Mod.mod_hash_short == mod.mod_hash_short) & (Mod.name == mod.name) & (Mod.mod_dir == mod.mod_dir) & (Mod.full_path == mod.full_path))
            join_params.append({"log_file": log_file, "mod": sub_query})

        amount_assigned = LogFileAndModJoin.insert_many(join_params).on_conflict_ignore().execute()

        if amount_assigned > 0:
            log.info("Assigned %r mods to log file %r", amount_assigned, log_file)

    def insert_mods(self, mod_items: Iterable[Mod], log_file: LogFile) -> Future:
        return self.thread_pool.submit(self._execute_insert_mods, mod_items=mod_items, log_file=log_file)

    def _execute_update_log_file_from_dict(self, log_file: LogFile, in_dict: dict):
        in_dict = dict(in_dict)
        try:
            del in_dict["id"]
        except KeyError:
            pass
        for key_name in ("server", "game_map", "version", "original_file"):
            value = in_dict.get(key_name)
            if value is not None and isinstance(value, dict):
                in_dict[key_name] = value["id"]

        with self.database.connection_context() as ctx:
            try:
                LogFile.update(**{k: v for k, v in in_dict.items() if v is not None}).where(LogFile.id == log_file.id).execute()
            except Exception as e:
                log.critical("log_file_data_dict: \n        %s", '\n        '.join(f"{k!r}:{v!r}" for k, v in in_dict.items()))
                log.error(e, exc_info=True)
                raise
            # item = update_model_from_dict(LogFile.get_by_id(log_file.id), in_dict)
            # item.save()

        # log.debug("Updated logfile %r modified_at: %r, game_map: %r, version: %r, campaign_id: %r", item, item.modified_at, item.game_map, item.version, item.campaign_id)

    def update_log_file_from_dict(self, log_file: LogFile, in_dict: dict) -> Future:
        return self.thread_pool.submit(self._execute_update_log_file_from_dict, log_file=log_file, in_dict=in_dict)

    def _execute_insert_game_map(self, game_map: "GameMap"):
        with self.write_lock:
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
            OriginalLogFile.insert(text=original_log_file.text, text_hash=original_log_file.text_hash).on_conflict_replace().execute()
            LogFile.update(original_file=OriginalLogFile.select(OriginalLogFile.id).where(OriginalLogFile.text_hash == original_log_file.text_hash)).where(LogFile.id == log_file.id).execute()
        except Exception as e:
            log.error(e, exc_info=True)
            raise
        return original_log_file

    def insert_original_log_file(self, file_path: Path, log_file: LogFile) -> Future:
        return self.thread_pool.submit(self._execute_insert_original_log_file, original_log_file=OriginalLogFile.init_from_file(file_path), log_file=log_file)

    def _execute_update_original_log_file(self, original_log_file: OriginalLogFile):
        with self.database.connection_context() as ctx:
            OriginalLogFile.update(text=original_log_file.text, text_hash=original_log_file.text_hash).where(OriginalLogFile.id == original_log_file.id).execute()

        return original_log_file

    def update_original_log_file(self, existing_original_log_file: OriginalLogFile, file_path: Path) -> Future:
        return self.thread_pool.submit(self._execute_update_original_log_file, original_log_file=existing_original_log_file.modify_update_from_file(file_path=file_path))

    def __call__(self, records: Iterable["RawRecord"], context: "LogParsingContext") -> Future:
        return self.insert(records=records, context=context)

    def shutdown(self) -> None:
        def _close_connection(a_number: int):
            conn: apsw.Connection = self.database.connection()
            if conn is not None:
                conn.close(True)
        dummy = list(range(self.thread_pool._max_workers * 2))
        list(self.thread_pool.map(lambda x: _close_connection, dummy))


class RecordProcessor:
    _error_words: tuple[str] = tuple(w.casefold() for w in ("error", "error:"))
    msg_word_split_regex: re.Pattern = re.compile(r"\s|\:|\,|\.|\!|\?|\||\;|\[|\]|\(|\)|\<|\>|\=")
    _default_origin: "RecordOrigin" = None
    _antistasi_origin: "RecordOrigin" = None
    _arma_function_lock: RLock = RLock()
    __slots__ = ("regex_keeper", "backend", "foreign_key_cache")

    def __init__(self, backend: "Backend", regex_keeper: "SimpleRegexKeeper", foreign_key_cache: "ForeignKeyCache") -> None:
        self.backend = backend
        self.regex_keeper = regex_keeper
        self.foreign_key_cache = foreign_key_cache

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
                                             microsecond=0)

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

        # if _out["logged_from"] in {None, ""}:
        #     log.critical("empty logged from with %r", raw_record.content)
        #     del _out["logged_from"]

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
        record_class = self.record_class_manager.determine_record_class(raw_record)
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

    def _convert_raw_record_foreign_keys(self, parsed_data: Optional[dict[str, Any]], utc_offset: tzoffset) -> Optional[dict[str, Any]]:

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
        if self.regex_keeper.fault_error_start.search(raw_record.content):
            log.warning("found fault-error in record %r", raw_record)
            line_split_1 = [idx for idx, l in enumerate(raw_record.lines) if l.content == "======================================================="][0]
            line_split_2 = [idx for idx, l in enumerate(raw_record.lines) if l.content == "-------------------------------------------------------"][0]
            if line_split_2 == line_split_1 + 1:
                new_lines = list(raw_record.lines)[:line_split_1]
                raw_record = raw_record.__class__(lines=new_lines)

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
