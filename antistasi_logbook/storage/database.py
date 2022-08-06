"""
WiP.

Soon.
"""

# region [Imports]

# * Standard Library Imports ---------------------------------------------------------------------------->
import os
import sys
from typing import TYPE_CHECKING, Union, Protocol, Generator
import random
from pathlib import Path
from weakref import WeakSet
from functools import cached_property
from time import perf_counter
from threading import Lock, current_thread, RLock
from time import sleep
from concurrent.futures import Future, ThreadPoolExecutor, wait, FIRST_COMPLETED
# from more_itertools import chunked
# * Third Party Imports --------------------------------------------------------------------------------->

from apsw import SQLITE_OK, SQLITE_CHECKPOINT_TRUNCATE, Connection, SQLITE_CHECKPOINT_FULL, ConnectionClosedError
from peewee import JOIN, DatabaseProxy, chunked
from playhouse.sqlite_ext import CYTHON_SQLITE_EXTENSIONS

from playhouse.apsw_ext import APSWDatabase
from apsw import ThreadingViolationError
import apsw
# * Gid Imports ----------------------------------------------------------------------------------------->
from gidapptools import get_logger
from gidapptools.meta_data.interface import MetaPaths, get_meta_info, get_meta_paths
from gidapptools.gid_config.interface import GidIniConfig, get_config
from gidapptools.general_helper.conversion import ns_to_s, human2bytes, number_to_pretty

# * Local Imports --------------------------------------------------------------------------------------->
from antistasi_logbook import setup
from antistasi_logbook.storage.models.models import (Server, GameMap, LogFile, Version, LogLevel, LogRecord, RecordClass, ArmaFunction,
                                                     RecordOrigin, RemoteStorage, DatabaseMetaData, ArmaFunctionAuthorPrefix, setup_db)
from antistasi_logbook.storage.models.migration import run_migration
from antistasi_logbook.utilities.locks import FakeLock
import inspect

setup()
# * Local Imports --------------------------------------------------------------------------------------->
from antistasi_logbook.parsing.foreign_key_cache import ForeignKeyCache
from frozendict import frozendict
# * Type-Checking Imports --------------------------------------------------------------------------------->
if TYPE_CHECKING:
    from gidapptools.gid_config.interface import GidIniConfig

    from antistasi_logbook.backend import Backend
    from antistasi_logbook.parsing.record_processor import RecordInserter, RecordProcessor

# endregion[Imports]

# region [TODO]


# endregion [TODO]

# region [Logging]


# endregion[Logging]

# region [Constants]
from gidapptools.general_helper.timing import get_dummy_profile_decorator_in_globals
get_dummy_profile_decorator_in_globals()
THIS_FILE_DIR = Path(__file__).parent.absolute()
META_PATHS: MetaPaths = get_meta_paths()
META_INFO = get_meta_info()

log = get_logger(__name__)

# endregion[Constants]

DEFAULT_DB_NAME = "storage.db"

DEFAULT_PRAGMAS = frozendict({
    "cache_size": -1 * 512_000,
    "journal_mode": 'WAL',
    "synchronous": 0,
    "ignore_check_constraints": 0,
    "foreign_keys": 1,
    "temp_store": "memory",
    "mmap_size": 268_435_456 * 2,
    "auto_vacuum": "INCREMENTAL",
    "journal_size_limit": human2bytes("500mb"),
    "wal_autocheckpoint": 100_000,
    # "page_size": 32_768,
    "read_uncommitted": False,
    "case_sensitive_like": False
})


def make_db_path(in_path: Union[str, os.PathLike, Path]) -> str:
    """
    Returns the provided path resolved and as a String so APSW can understand it.

    Peewee (or APSW) seems to not follow the `os.PathLike`-Protocol.

    Args:
        in_path (Union[str, os.PathLike, Path])

    Returns:
        str: The resolved and normalized path to the db.
    """

    return str(Path(in_path).resolve())


class GidSqliteDatabase(Protocol):

    def _pre_start_up(self, overwrite: bool = False) -> None:
        ...

    def _post_start_up(self, **kwargs) -> None:
        ...

    def start_up(self, overwrite: bool = False, database_proxy: DatabaseProxy = None) -> "GidSqliteDatabase":
        ...

    def shutdown(self, error: BaseException = None) -> None:
        ...

    def optimize(self) -> "GidSqliteDatabase":
        ...

    def vacuum(self) -> "GidSqliteDatabase":
        ...

    def backup(self, backup_path: Union[str, os.PathLike, Path] = None) -> "GidSqliteDatabase":
        ...

# pylint: disable=abstract-method


def wal_hook(conn, db_name, pages):
    log.info('<<SQL-WAL>> {"db_name": "%s", "pages": %r, "conn": "%s"}', db_name, pages, conn)
    return SQLITE_OK


def rollback_hook():
    log.critical("<<SQL-ROLLBACK>> Rollback-Hook was called")


def profile_hook(stmt: str, time_taken):
    log.debug('<<SQL-PROFILING>> {"statement":"%s", "time":%r}', stmt.replace('"', r'\"'), ns_to_s(time_taken, 6))


def update_hook(typus: int, database_name: str, table_name: str, row_id: int):
    typus = apsw.mapping_authorizer_function[typus]
    log.debug('<<SQL-UPDATE>> {"typus": %r, "database_name": %r, "table_name": %r, "row_id": %r', typus, database_name, table_name, row_id)


def connection_hook(conn: apsw.Connection):
    call_frame = sys._getframe().f_back.f_back.f_back.f_back.f_back
    while Path(call_frame.f_code.co_filename).stem == "peewee" or Path(call_frame.f_code.co_filename).parent.stem == "playhouse":
        call_frame = call_frame.f_back
    caller = call_frame.f_code.co_name
    module_name: str = 'main.' + call_frame.f_globals.get("__name__").split(".", 1)[-1]

    caller_file = Path(call_frame.f_code.co_filename)

    log.debug("opening connection %r in thread %r and caller %r, file: %r", conn, current_thread(), caller, caller_file.name, extra={"function_name": caller, "module": module_name})


class GidSqliteApswDatabase(APSWDatabase):

    default_extensions = {"c_extensions": True,
                          "rank_functions": True,
                          "hash_functions": True,
                          "json_contains": True,
                          "bloomfilter": True,
                          "regexp_function": True}

    default_db_path = META_PATHS.db_dir if os.getenv('IS_DEV', 'false') == "false" else THIS_FILE_DIR

    def __init__(self,
                 database_path: Path = None,
                 config: "GidIniConfig" = None,
                 auto_backup: bool = False,
                 thread_safe=True,
                 autoconnect=True,
                 pragmas=None,
                 extensions=None):
        self.all_connections: WeakSet[apsw.Connection] = WeakSet()
        self.database_path = self.resolve_db_path(database_path=database_path)
        self.database_path.parent.mkdir(exist_ok=True, parents=True)
        self.database_existed: bool = self.database_path.is_file()
        self.database_name = self.database_path.name
        self.config = config
        self.auto_backup = auto_backup
        self.started_up = False
        self.session_meta_data: "DatabaseMetaData" = None
        extensions = dict(self.default_extensions.copy() | (extensions or {}))
        pragmas = dict(DEFAULT_PRAGMAS) | (pragmas or {})
        super().__init__(make_db_path(self.database_path), thread_safe=thread_safe, autoconnect=autoconnect, pragmas=pragmas, timeout=100, statementcachesize=10_000, ** extensions)

        self.foreign_key_cache: "ForeignKeyCache" = ForeignKeyCache(database=self)
        self.write_lock = FakeLock()
        self.record_processor: "RecordProcessor" = None
        self.record_inserter: "RecordInserter" = None
        self.backend: "Backend" = None

    @classmethod
    def resolve_db_path(cls, database_path: Path = None) -> Path:
        if database_path is not None:
            database_path = Path(database_path)
            if database_path.suffix == "":
                database_path = database_path.joinpath(DEFAULT_DB_NAME)
        else:
            database_path = cls.default_db_path.joinpath(DEFAULT_DB_NAME)
        return database_path

    @property
    def backup_folder(self) -> Path:
        return self.database_path.parent.joinpath("backups")

    @cached_property
    def base_record_id(self) -> int:
        return RecordClass.select().where(RecordClass.name == "BaseRecord").scalar()

    def _add_conn_hooks(self, conn: "apsw.Connection"):
        self.all_connections.add(conn)

        if self.config.get("database", "enable_connection_creation_logging") is True:
            connection_hook(conn)

        if self.config.get("database", "enable_profiling_hook_logging") is True:
            conn.setprofile(profile_hook)

        if self.config.get("database", "enable_update_hook_logging") is True:
            conn.setupdatehook(update_hook)

        if self.config.get("database", "enable_rollback_hook_logging") is True:
            conn.setrollbackhook(rollback_hook)

        if self.config.get("database", "enable_wal_hook_logging") is True:
            conn.setwalhook(wal_hook)

        super()._add_conn_hooks(conn)
        conn.setbusyhandler(self._busy_handling)

    def _busy_handling(self, prior_calls: int) -> bool:
        if prior_calls == 0:
            sleep_time = 0
        else:
            _prior_calls = prior_calls if prior_calls != 0 else 1
            base = 0.5
            sleep_time = round((base * (_prior_calls / 2)) + (random.random()), 4)

        sleep(sleep_time)
        if prior_calls > 0 and prior_calls % 5 == 0:
            log.debug("%r busy sleeping for %r prior-calls", sleep_time, prior_calls)
        if prior_calls > 1_000:
            return False
        return True

    def _close(self, conn):
        self.optimize()
        if self.config.get("database", "enable_connection_creation_logging") is True:
            log.debug("closed connection %r (changes: %r, total changes: %r) of thread %r", conn, conn.changes(), conn.totalchanges(), current_thread())

        self.all_connections.remove(conn)
        super()._close(conn)

    def _pre_start_up(self, overwrite: bool = False) -> None:
        self.database_path.parent.mkdir(exist_ok=True, parents=True)
        if overwrite is True:
            self.database_path.unlink(missing_ok=True)

    def _post_start_up(self, **kwargs) -> None:

        self.session_meta_data = DatabaseMetaData.new_session()
        self.backend.inserting_thread_pool.submit(self.resolve_all_armafunction_extras)

    def checkpoint(self):
        time_start = perf_counter()
        conn = self.connection()
        conn.setbusyhandler(self._busy_handling)
        result = conn.wal_checkpoint(mode=SQLITE_CHECKPOINT_TRUNCATE)
        time_taken = perf_counter() - time_start
        log.info("checkpoint wal with return: %r, time taken: %rs", result, round(time_taken, 3))

    def start_up(self,
                 overwrite: bool = False,
                 force: bool = False) -> "GidSqliteApswDatabase":

        if self.started_up is True and force is False:
            return
        log.info("starting up %r", self)
        self._pre_start_up(overwrite=overwrite)
        self.connect(reuse_if_open=True)

        with self.write_lock:
            if self.database_existed is True:
                log.debug("starting migration for %r", self)
                run_migration(self)
                log.debug("finished migration for %r", self)
            log.debug("starting setup for %r", self)
            setup_db(self)
            log.debug("finished setup for %r", self)

        self._post_start_up()
        self.started_up = True
        self.foreign_key_cache.reset_all()
        self.foreign_key_cache.preload_all()

        log.info("finished starting up %r", self)
        return self

    def optimize(self) -> "GidSqliteApswDatabase":
        result = self.execute_sql(f"PRAGMA analysis_limit={1_000};PRAGMA optimize;")
        self.commit()
        return self

    def vacuum(self) -> "GidSqliteApswDatabase":
        log.info("vacuuming %r", self)
        time_start = perf_counter()
        with self.connection_context() as ctx:

            self.checkpoint()
            # self.execute_sql("VACUUM;")
            self.pragma("incremental_vacuum")
            self.checkpoint()
            self.optimize()

            time_taken = perf_counter() - time_start

        log.debug("finished vacuuming %r, time taken: %rs", self, round(time_taken, 3))
        return self

    def shutdown(self, error: BaseException = None) -> None:
        log.debug("shutting down %r", self)

        self.session_meta_data.save()
        # self.execute_sql("VACUUM;")
        self.pragma("incremental_vacuum")
        self.checkpoint()

        for conn in self.all_connections:

            try:
                self.pragma("incremental_vacuum")
                # self.execute_sql("VACUUM;")
                cur = conn.cursor()
                log.debug("optimizing before closing connection %r", conn)
                _result = cur.execute(f"PRAGMA analysis_limit={15_000_000};PRAGMA optimize;")
                log.debug("optimizing result for connection %r: %r", conn, tuple(_result))
                cur.close()
                log.debug("Trying to close connection %r", conn)
                conn.close()
                del conn
            except (ThreadingViolationError, ConnectionClosedError) as e:
                log.critical("encountered error %r while closing connection %r", e, conn)
        self.started_up = False
        log.debug("finished shutting down %r", self)

    def get_all_server(self, ordered_by=Server.id) -> tuple[Server]:
        with self.connection_context() as ctx:
            result = tuple(Server.select(Server, RemoteStorage).join(RemoteStorage, on=Server.remote_storage).order_by(ordered_by).iterator(self))

        return result

    def get_log_files(self, server: Server = None, ordered_by=LogFile.id) -> tuple[LogFile]:

        query = LogFile.select(LogFile, Server, GameMap, Version)
        query = query.join(Server, on=LogFile.server).join(RemoteStorage, on=Server.remote_storage).switch(LogFile)
        query = query.join(GameMap, on=LogFile.game_map, join_type=JOIN.LEFT_OUTER).switch(LogFile)
        query = query.join(Version, on=LogFile.version, join_type=JOIN.LEFT_OUTER).switch(LogFile)
        if server is None:
            return tuple(query.order_by(ordered_by).iterator(self))
        return tuple(query.where(LogFile.server_id == server.id).order_by(ordered_by).iterator(self))

    def get_all_log_levels(self, ordered_by=LogLevel.id) -> tuple[LogLevel]:

        result = tuple(LogLevel.select().order_by(ordered_by))

        return result

    def get_all_arma_functions(self, ordered_by=ArmaFunction.id) -> tuple[ArmaFunction]:
        with self:
            return tuple(item for item in ArmaFunction.select(ArmaFunction, ArmaFunctionAuthorPrefix).join(ArmaFunctionAuthorPrefix).order_by(ordered_by))

    def get_all_game_maps(self, ordered_by=GameMap.id) -> tuple[GameMap]:

        result = tuple(GameMap.select(GameMap).order_by(ordered_by))

        return result

    def get_all_origins(self, ordered_by=RecordOrigin.id) -> tuple[RecordOrigin]:

        result = tuple(RecordOrigin.select().order_by(ordered_by))
        return result

    def get_all_versions(self, ordered_by=Version) -> tuple[Version]:

        result = tuple(Version.select(Version).order_by(ordered_by))
        return result

    def iter_all_records(self, server: Server = None, log_file: LogFile = None, only_missing_record_class: bool = False) -> Generator[LogRecord, None, None]:
        self.connect(True)

        foreign_key_cache = ForeignKeyCache(self)
        foreign_key_cache.preload_all()

        if log_file is not None:
            log_files = LogFile.select(LogFile.id).where(LogFile.id == log_file.id)
        elif server is not None:
            log_files = LogFile.select(LogFile.id).where((LogFile.server_id == server.id) & (LogFile.unparsable == False))
        else:
            # log_files = LogFile.select(LogFile.id).where(LogFile.unparsable == False)
            log_files = None

        query = LogRecord.select(LogRecord.id, LogRecord.message, LogRecord.origin_id, LogRecord.called_by_id, LogRecord.logged_from_id, LogRecord.record_class_id)

        if only_missing_record_class is True:
            query = query.where(LogRecord.record_class_id >> None)

        def _get_records(in_log_file_id: int):
            sub_query = query.where(LogRecord.log_file_id == in_log_file_id)
            for _record in sub_query.iterator():
                yield _record

        if log_files is not None:
            sub_query = query.where(LogRecord.log_file_id << log_files).order_by(LogRecord.record_class)
        else:
            sub_query = query.order_by(LogRecord.record_class_id)
        for record in sub_query.iterator():
            record.origin = foreign_key_cache.get_origin_by_id(record.origin_id)
            record.called_by = foreign_key_cache.get_arma_file_by_id(record.called_by_id)
            record.logged_from = foreign_key_cache.get_arma_file_by_id(record.logged_from_id)
            record.record_class = self.backend.record_class_manager.get_model_by_id(record.record_class_id)
            yield record
        self.optimize()

    def get_amount_iter_all_records(self, server: Server = None, log_file: LogFile = None, only_missing_record_class: bool = False) -> int:
        with self.connection_context() as ctx:
            if log_file is not None:
                log_files = [log_file]
            elif server is not None:
                log_files = LogFile.select(LogFile.id).where((LogFile.server_id == server.id) & (LogFile.unparsable == False))
            else:
                log_files = LogFile.select(LogFile.id).where(LogFile.unparsable == False)

            query = LogRecord.select(LogRecord).where(LogRecord.log_file << log_files)

            if only_missing_record_class is True:
                query = query.where(LogRecord.record_class_id >> None)

            return query.count()

    def get_unique_server_ips(self) -> tuple[str]:

        _out = tuple(set(s.ip for s in Server.select().iterator(self) if s.ip is not None))

        return _out

    def get_unique_campaign_ids(self) -> tuple[int]:

        _out = set(l.campaign_id for l in LogFile.select().where(LogFile.unparsable == False).iterator(self) if l.campaign_id is not None)
        return tuple(sorted(_out))

    def resolve_all_armafunction_extras(self) -> None:
        query = ArmaFunction.select(ArmaFunction, ArmaFunctionAuthorPrefix).join(ArmaFunctionAuthorPrefix, join_type=JOIN.LEFT_OUTER)

        for arma_func in query.iterator():
            arma_func.load_extras()

        self.optimize()

    def __repr__(self) -> str:
        repr_attrs = ("database_name", "config", "auto_backup", "thread_safe", "autoconnect")
        _repr = self.__class__.__name__
        attr_text = ', '.join(attr_name + "=" + repr(getattr(self, attr_name, None)) for attr_name in repr_attrs)
        return _repr + attr_text


# region[Main_Exec]
if __name__ == '__main__':

    pass
# endregion[Main_Exec]
