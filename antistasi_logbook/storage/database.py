"""
WiP.

Soon.
"""

# region [Imports]

# * Standard Library Imports ---------------------------------------------------------------------------->
import gc
import os
import re
import sys
import random
from time import sleep, perf_counter
from pprint import pformat
from typing import TYPE_CHECKING, Union, Protocol, Generator
from pathlib import Path
from weakref import WeakSet
from datetime import datetime
from functools import cached_property
from threading import Lock, RLock, current_thread
from collections import defaultdict
from concurrent.futures import Future, ThreadPoolExecutor

# * Third Party Imports --------------------------------------------------------------------------------->
import apsw
from apsw import SQLITE_OK, SQLITE_OPEN_CREATE, SQLITE_OPEN_NOMUTEX, SQLITE_OPEN_READWRITE, SQLITE_CHECKPOINT_TRUNCATE, ConnectionClosedError, ThreadingViolationError
from peewee import JOIN, Model, DatabaseProxy, chunked
from playhouse.apsw_ext import APSWDatabase
from playhouse.sqlite_ext import CYTHON_SQLITE_EXTENSIONS

# * Gid Imports ----------------------------------------------------------------------------------------->
from gidapptools import get_logger
from gidapptools.meta_data.interface import MetaPaths, get_meta_info, get_meta_paths
from gidapptools.gid_config.interface import GidIniConfig
from gidapptools.general_helper.conversion import ns_to_s, bytes2human, human2bytes

# * Local Imports --------------------------------------------------------------------------------------->
from antistasi_logbook import setup
from antistasi_logbook.utilities.locks import FakeLock
from antistasi_logbook.storage.models.models import (Server, GameMap, LogFile, Message, Version, LogLevel, LogRecord, RecordClass, ArmaFunction,
                                                     RecordOrigin, RemoteStorage, DatabaseMetaData, ArmaFunctionAuthorPrefix, initialize_db)
from antistasi_logbook.storage.models.migration import run_migration

setup()
# * Third Party Imports --------------------------------------------------------------------------------->
from frozendict import frozendict

# * Gid Imports ----------------------------------------------------------------------------------------->
from gidapptools.gid_database.orm_peewee.sqlite.pragma_info import PragmaInfo

# * Local Imports --------------------------------------------------------------------------------------->
from antistasi_logbook.storage.setup_data import setup_from_data
from antistasi_logbook.parsing.foreign_key_cache import ForeignKeyCache

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

DEFAULT_DB_NAME = "storage.logbook_db"

DEFAULT_PRAGMAS = frozendict({
    "auto_vacuum": 2,
    "cache_size": -1 * 128_000,


    "journal_mode": 'WAL',
    # "synchronous": 'OFF',
    "synchronous": 0,


    "ignore_check_constraints": 0,
    "foreign_keys": 1,
    # "temp_store": "memory",
    # "mmap_size": 30_000_000_000,


    "journal_size_limit": human2bytes("1500mb"),
    "page_size": 8192,
    "wal_autocheckpoint": 500_000,

    # "read_uncommitted": False,
    "case_sensitive_like": False,
    "threads": 8,
})


DEFAULT_PRAGMAS = frozendict({
    "auto_vacuum": 2,
    "cache_size": -1 * 256_000,  # 128mb
    "journal_mode": 'WAL',
    "synchronous": 0,
    "ignore_check_constraints": 0,
    "foreign_keys": 1,
    "journal_size_limit": human2bytes("1500mb"),
    # "wal_autocheckpoint": 150_000,
    "page_size": 8192,
    "analysis_limit": 1_000_000,
    "case_sensitive_like": False,
    "threads": 8,
    # "temp_store": "MEMORY",
    # "mmap_size": 30_000_000_000
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


SQL_PROFILING_FILE_PATH = THIS_FILE_DIR.joinpath(f"{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}_SQL_PROFILING.txt")
# SQL_PROFILING_FILE = SQL_PROFILING_FILE_PATH.open("a", encoding='utf-8', errors='ignore')
# atexit.register(SQL_PROFILING_FILE.close)
SQL_PROFILING_FILE = None


def give_prof_dict_default():
    return {"overall_time": 0.0, "amount_called": 0, "all_times": []}


prof_dict = defaultdict(give_prof_dict_default)
prof_dict_lock = RLock()


def write_prof_dict():
    with SQL_PROFILING_FILE_PATH.open("w", encoding='utf-8', errors='ignore') as f:
        with prof_dict_lock:
            for k, values in sorted(prof_dict.items(), key=lambda x: x[1]["overall_time"], reverse=True):
                f.write(f"{k!s}\n")
                for sk, sv in values.items():
                    if sk == "all_times":
                        sv = '\n\t\t           '.join(l.strip() for l in pformat(sv).splitlines())
                        f.write(f"\t\t{sk!s}: {sv!s}\n")
                    else:
                        f.write(f"\t\t{sk!s}: {sv!r}\n")
                f.write("\n\n")


def wal_hook(conn, db_name, pages):
    now = datetime.now().strftime('%H-%M-%S')
    log.info('<<SQL-WAL>> {"time": "%s", "db_name": "%s", "pages": %s, "conn": "%s"}\n', now, db_name, pages, conn)
    return SQLITE_OK


def rollback_hook():
    now = datetime.now().strftime('%H-%M-%S')
    log.info("<<SQL-ROLLBACK>> -%s- Rollback-Hook was called\n", now)


param_regex = re.compile(r"(\((\?\,? ?)+\).*)|(VALUES.*)")


def profile_hook(stmt: str, time_taken):

    if "PRAGMA" in stmt:
        return
    # now = datetime.now().strftime('%H:%M:%S.%f')
    time_taken = ns_to_s(time_taken, 6)
    stmt = stmt.replace('"', r'\"')
    # stmt = param_regex.sub("", stmt, 1)

    with prof_dict_lock:
        prof_dict[stmt]["overall_time"] += time_taken
        prof_dict[stmt]["amount_called"] += 1
        prof_dict[stmt]["per_call"] = prof_dict[stmt]["overall_time"] / prof_dict[stmt]["amount_called"]
        # prof_dict[stmt]["all_times"].append([now, time_taken])
    # SQL_PROFILING_FILE.write(f'-{now}- <<SQL-PROFILING>> {{"time_taken": {ns_to_s(time_taken, 6)!sr}, "statement": "{stmt!r}"}}\n')


performance_write_lock = RLock()


# def profile_hook(stmt: str, time_taken):
#     def _write_it(_stmt: str, _time_taken):
#         with performance_write_lock:
#             with SQL_PROFILING_FILE_PATH.open("a", encoding="utf-8", errors="ignore") as f:
#                 f.write(f"time_taken: {ns_to_s(_time_taken)!r}, stmt: {_stmt!r}\n")

#     if "PRAGMA " in stmt:
#         return
#     QApplication.instance().gui_thread_pool.submit(_write_it, stmt, time_taken)
#     # log.info("<<SQL-PROFILING>> time_taken: %r, stmt: %r", ns_to_s(time_taken, 4), stmt[:500])


def update_hook(typus: int, database_name: str, table_name: str, row_id: int):
    typus = apsw.mapping_authorizer_function[typus]
    now = datetime.now().strftime('%H-%M-%S')
    SQL_PROFILING_FILE.write(f'<<SQL-UPDATE>> {{"time": {now}, "typus": "{typus!s}", "database_name": "{database_name!s}2, "table_name": "{table_name!s}", "row_id": {row_id}}}\n')


def connection_hook(conn: apsw.Connection):
    now = datetime.now().strftime('%H-%M-%S')

    call_frame = sys._getframe().f_back.f_back.f_back.f_back.f_back

    while Path(call_frame.f_code.co_filename).stem in {"peewee", "line_profile"} or Path(call_frame.f_code.co_filename).parent.stem in {"playhouse", "line_profile"}:
        call_frame = call_frame.f_back
    caller = call_frame.f_code.co_name
    # module_name: str = 'main.' + call_frame.f_globals.get("__name__").split(".", 1)[-1]
    line_number = call_frame.f_lineno
    caller_file = Path(call_frame.f_code.co_filename)

    # SQL_PROFILING_FILE.write(" -%s- opening connection %r in thread %r and caller %r, file: %r\n", datetime.now().strftime('%H-%M-%S'), conn, current_thread(), caller, caller_file.name, extra={"function_name": caller, "module": module_name})

    log.info(f" -{now}- opening connection {conn!r} in thread {current_thread()!r} and caller {caller!r}, file: {caller_file!r}, line_number: {line_number!r}\n")


def log_connection_pragmas(in_conn: apsw.Connection):

    for pragma_name in DEFAULT_PRAGMAS:
        value = in_conn.execute(f"PRAGMA {pragma_name}").fetchone()
        log.info("<CONNECTION_PRAGMA> %r -> %r", pragma_name, value)


class GidSqliteApswDatabase(APSWDatabase):

    default_extensions = {"c_extensions": True,
                          "rank_functions": False,
                          "hash_functions": True,
                          "json_contains": True,
                          "bloomfilter": False,
                          "regexp_function": True}

    default_db_path = META_PATHS.db_dir if os.getenv('IS_DEV', 'false') == "false" else THIS_FILE_DIR
    start_up_lock = RLock()

    def __init__(self,
                 database_path: Path = None,
                 config: "GidIniConfig" = None,
                 auto_backup: bool = False,
                 thread_safe=True,
                 autoconnect=True,
                 pragmas=None,
                 extensions=None,
                 autorollback: bool = False):
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

        super().__init__(make_db_path(self.database_path),
                         thread_safe=thread_safe,
                         autoconnect=autoconnect,
                         pragmas=pragmas,
                         timeout=100,
                         statementcachesize=100,
                         autorollback=autorollback,
                         flags=SQLITE_OPEN_READWRITE | SQLITE_OPEN_CREATE | SQLITE_OPEN_NOMUTEX, ** extensions)

        self.foreign_key_cache: "ForeignKeyCache" = ForeignKeyCache(database=self)
        self.write_lock = FakeLock()
        self.record_processor: "RecordProcessor" = None
        self.record_inserter: "RecordInserter" = None
        self.backend: "Backend" = None

        self.most_common_messages: frozendict[str, Message] = {}
        self._wal_hook_lock = Lock()
        self._actual_page_size: int = None
        self._actual_journal_size_limit: int = None
        self._resolve_arma_functions_future: Future = None
        self._resolve_arma_functions_check_lock = RLock()
        self._base_model: Model = None
        self._view_base_model = None
        self.pragma_info = None
        self.log_file_data_update_futures: list[Future] = []

    def get_model(self, model_name: str) -> Model:
        model_name = model_name.casefold()
        _out = next((m for m in self._base_model.get_all_models() if m.__name__.casefold() == model_name), None)
        if _out is None:
            raise KeyError(model_name)
        return _out

    def wal_hook(self, conn: apsw.Connection, db_name: str, pages: int):
        try:
            if self._actual_page_size is not None and self._actual_journal_size_limit is not None:
                if (pages * self._actual_page_size) >= int(self._actual_journal_size_limit * 1.5):
                    aquired = self._wal_hook_lock.acquire(blocking=False)
                    log.debug("running top wal-checkpoint: %r", aquired)
                    if aquired is True:
                        try:

                            log.debug("WAL-Checkpoint because WAL-Size: %r", bytes2human((pages * self._actual_page_size)))
                            self.backend.inserting_thread_pool.submit(self.checkpoint).result()

                            sleep(1)
                        finally:
                            self._wal_hook_lock.release()
        except Exception as e:
            log.error(e, exc_info=True)

        return apsw.SQLITE_OK

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
    def database_file_size(self) -> int:
        return self.database_path.stat().st_size

    @property
    def backup_folder(self) -> Path:
        return self.database_path.parent.joinpath("backups")

    @cached_property
    def base_record_id(self) -> int:
        return RecordClass.select().where(RecordClass.name == "BaseRecord").scalar()

    def _add_conn_hooks(self, conn: "apsw.Connection"):
        if "auto_vacuum" in [i[0] for i in self._pragmas]:
            cursor = conn.cursor()
            for pragma, value in (i for i in self._pragmas if i[0] == "auto_vacuum"):
                cursor.execute('PRAGMA %s = %s;' % (pragma, value))
            cursor.close()
        self.all_connections.update([])
        self.all_connections.add(conn)
        conn.setbusyhandler(self._busy_handling)
        conn.setwalhook(self.wal_hook)
        if self.config.get("database", "enable_connection_creation_logging") is True:
            connection_hook(conn)

        if self.config.get("database", "enable_profiling_hook_logging") is True:
            conn.setprofile(profile_hook)

        if self.config.get("database", "enable_update_hook_logging") is True:
            conn.setupdatehook(update_hook)

        if self.config.get("database", "enable_rollback_hook_logging") is True:
            conn.setrollbackhook(rollback_hook)

        super()._add_conn_hooks(conn)

        conn.setbusyhandler(self._busy_handling)
        conn.setwalhook(self.wal_hook)
        wal_autocheckpoint = next((i[1] for i in self._pragmas if i[0] == "wal_autocheckpoint"), None)
        if wal_autocheckpoint is not None:
            conn.wal_autocheckpoint(wal_autocheckpoint)

    def _busy_handling(self, prior_calls: int) -> bool:
        # if prior_calls > 0 and prior_calls % 5 == 0:

        sleep(random.random())
        #     if META_INFO.is_dev is True:
        #         log.debug("%r busy sleeping for %r prior-calls", round(sleep_time, 4), prior_calls)
        return True

    # def _busy_handling(self, prior_calls: int) -> bool:

    #     sleep_time = 0.5 + random.random() + (prior_calls / 100)

    #     sleep(sleep_time)
    #     if prior_calls > 0 and prior_calls % 5 == 0 and META_INFO.is_dev is True:
    #         try:
    #             call_frame = sys._getframe().f_back.f_back.f_back
    #             while Path(call_frame.f_code.co_filename).stem in {"peewee", "threading"} or Path(call_frame.f_code.co_filename).parent.stem in {"playhouse", "futures"}:
    #                 call_frame = call_frame.f_back
    #             caller = call_frame.f_code.co_name
    #             module_name: str = 'main.' + call_frame.f_globals.get("__name__").split(".", 1)[-1]
    #             line_number = call_frame.f_lineno
    #             caller_file = Path(call_frame.f_code.co_filename)

    #             log.debug("%r busy sleeping for %r prior-calls caller: %r, module_name: %r, caller_file: %r, line_number: %r", round(sleep_time, 4), prior_calls, caller, module_name, caller_file, line_number)
    #         except AttributeError:
    #             try:
    #                 call_frame = sys._getframe().f_back.f_back.f_back.f_back
    #                 while Path(call_frame.f_code.co_filename).stem in {"threading"} or Path(call_frame.f_code.co_filename).parent.stem in {"futures"}:
    #                     call_frame = call_frame.f_back
    #                 caller = call_frame.f_code.co_name
    #                 module_name: str = 'main.' + call_frame.f_globals.get("__name__").split(".", 1)[-1]
    #                 line_number = call_frame.f_lineno
    #                 caller_file = Path(call_frame.f_code.co_filename)

    #                 log.debug("%r busy sleeping for %r prior-calls caller: %r, module_name: %r, caller_file: %r, line_number: %r", round(sleep_time, 4), prior_calls, caller, module_name, caller_file, line_number)
    #             except AttributeError:
    #                 log.debug("%r busy sleeping for %r prior-calls", round(sleep_time, 4), prior_calls)
    #     return True

    def _close(self, conn: "apsw.Connection"):

        if self.config.get("database", "enable_connection_creation_logging") is True:
            log.debug("closed connection %r (changes: %r, total changes: %r) of thread %r", conn, conn.changes(), conn.totalchanges(), current_thread())

        self.all_connections.remove(conn)
        super()._close(conn)

    def _pre_start_up(self, overwrite: bool = False) -> None:
        self.database_path.parent.mkdir(exist_ok=True, parents=True)
        if overwrite is True:
            self.database_path.unlink(missing_ok=True)

    def _post_start_up(self, **kwargs) -> None:
        self.pragma_info = PragmaInfo(self).fill_with_data()
        self._actual_page_size = self.page_size
        self._actual_journal_size_limit = self.journal_size_limit or 1_000_000
        log.debug("self._actual_journal_size_limit = %r", self._actual_journal_size_limit)
        self.session_meta_data = DatabaseMetaData.new_session()
        self.backend.inserting_thread_pool.submit(self.resolve_all_armafunction_extras)

    def checkpoint(self):
        time_start = perf_counter()

        try:
            conn: apsw.Connection = self.connection()

            result = conn.wal_checkpoint(mode=SQLITE_CHECKPOINT_TRUNCATE)
        except apsw.BusyError:
            return
        time_taken = perf_counter() - time_start
        log.info("checkpoint wal with return: %r, time taken: %rs", result, round(time_taken, 3))

    def _set_page_size(self):
        print("setting page size")
        wal_mode = False
        conn: apsw.Connection = self.connection()
        journal_mode = conn.execute("PRAGMA journal_mode;").fetchone()[0]
        if journal_mode.casefold() == "wal":
            wal_mode = True
        page_size = next((i[1] for i in self._pragmas if i[0] == "page_size"), None)
        print(f"{page_size=}")
        if page_size is None:
            return

        conn.execute(f"PRAGMA page_size={page_size};").fetchall()

        if wal_mode is True:
            conn.execute("PRAGMA journal_mode=OFF;").fetchall()

        conn.execute("VACUUM;").fetchall()

        if wal_mode is True:
            conn.execute("PRAGMA journal_mode=WAL;").fetchall()

    def start_up(self,
                 overwrite: bool = False,
                 force: bool = False) -> "GidSqliteApswDatabase":
        with self.start_up_lock:
            if self.started_up is True and force is False:
                return self
            log.info("starting up %r", self)
            self._pre_start_up(overwrite=overwrite)
            if self.database_path.exists() is False:
                self._set_page_size()
            wal_autocheckpoint = next((i[1] for i in self._pragmas if i[0] == "wal_autocheckpoint"), None)
            if wal_autocheckpoint:
                self.pragma("wal_autocheckpoint", 1_000, True)
            log.debug("starting setup for %r", self)
            initialize_db(self)
            setup_from_data(self)
            log.debug("finished setup for %r", self)
            log.debug("starting migration for %r", self)
            run_migration(self)
            log.debug("finished migration for %r", self)

            self._post_start_up()
            self.started_up = True
            self.foreign_key_cache.reset_all()
            self.foreign_key_cache.preload_all()

            log.info("finished starting up %r", self)
            log.info("server-version: %r", ".".join(str(i) for i in self.server_version))
            log.info("apsw-compile-options: %r", apsw.compile_options)
            log.info("Uses CYTHON_SQLITE_EXTENSIONS: %r", CYTHON_SQLITE_EXTENSIONS)
            log.info("Using Amalgamation: %r", apsw.using_amalgamation)
            log.info("current installed vfs: %r", apsw.vfsnames())
            log.info("registered_modules: %r", list(self._modules))
            log.info("%r context_options: %r", self, self.get_context_options())
            log.info("database application_id: %r", self.application_id)
            log.info("database user_version: %r", self.user_version)
            log.info("database data_version: %r", self.data_version)

            return self

    def ensure_log_file_data_update_futures(self):

        rounds_slept = 0
        sleep_amount = 0.5
        while len([i for i in self.log_file_data_update_futures if i.done() is False]) >= 1:
            sleep(sleep_amount)
            rounds_slept += 1

        log.debug("slept %r (%r s) rounds to update log_file data", rounds_slept, sleep_amount * rounds_slept)
        self.log_file_data_update_futures.clear()

    def optimize(self) -> "GidSqliteApswDatabase":
        log.debug("optimizing connection")
        try:
            result = self.pragma("optimize")
            log.debug("finished optimizing connection -> %r", result)

        except Exception as e:
            log.error(e, exc_info=True)

        return self

    def vacuum(self) -> "GidSqliteApswDatabase":
        log.info("vacuuming %r", self)
        time_start = perf_counter()
        with self.connection_context() as ctx:

            self.checkpoint()
            # self.execute_sql("VACUUM;")
            # self.pragma("auto_vacuum", 2, True)
            log.debug("freelist_count: %r", self.pragma("freelist_count"))
            res = self.pragma("incremental_vacuum", 1000)
            log.debug("incremental_vacuum result: %r", res)
            self.checkpoint()
            self.optimize()

            time_taken = perf_counter() - time_start

        log.debug("finished vacuuming %r, time taken: %rs", self, round(time_taken, 3))
        return self

    # def close(self):
    #     if not self.is_closed():
    #         try:
    #             self.optimize()
    #         except apsw.BusyError:
    #             log.warning("unable to optimize because database is busy")

    #     return super().close()

    def shutdown(self, error: BaseException = None) -> None:
        self.log_all_cache_infos()
        log.debug("shutting down %r", self)

        self.session_meta_data.save()

        self.pragma("incremental_vacuum")
        self.checkpoint()

        for conn in set(self.all_connections):

            try:
                self.vacuum()
                # self.execute_sql("VACUUM;")
                cur = conn.cursor()
                log.debug("optimizing before closing connection %r", conn)
                _result = cur.execute("PRAGMA analysis_limit=1000;PRAGMA optimize").fetchall()
                log.debug("optimizing result for connection %r: %r", conn, tuple(_result))
                cur.close()
                log.debug("Trying to close connection %r", conn)
                conn.close()
                del conn
            except (ThreadingViolationError, ConnectionClosedError) as e:
                log.critical("encountered error %r while closing connection %r", e, conn)
        self.close()
        self.started_up = False
        log.debug("finished shutting down %r", self)
        if len(prof_dict) > 0:
            write_prof_dict()
        gc.collect()

    def get_all_server(self, ordered_by=Server.id) -> tuple[Server]:
        return tuple(Server.select(Server, RemoteStorage).join_from(Server, RemoteStorage, on=Server.remote_storage).order_by(ordered_by).iterator())

    def log_all_cache_infos(self):
        for model in self._base_model.get_all_models():
            try:
                log.debug("cache-info for %r ('get_by_id_cached'): %r", model, model.get_by_id_cached.cache_info())
            except AttributeError:
                continue
        _cache = LogLevel._instance_cache
        log.debug("LogLevel_instances -> amount: %r, content: %r", len(_cache._full_map), _cache._full_map)
        log.debug("LogLevel_instances -> unique_field_names: %r, unique_indexes: %r", _cache.unique_field_names, _cache.unique_indexes)
        _cache = ArmaFunctionAuthorPrefix._instance_cache
        log.debug("ArmaFunctionAuthorPrefix_instances -> amount: %r, content: %r", len(_cache._full_map), _cache._full_map)
        log.debug("ArmaFunctionAuthorPrefix_instances -> unique_field_names: %r, unique_indexes: %r", _cache.unique_field_names, _cache.unique_indexes)

    def get_log_files(self, server: Server = None, ordered_by=LogFile.id, exclude_unparsable: bool = False) -> tuple[LogFile]:

        def _resolve_game_map_and_version(in_log_file: LogFile) -> LogFile:
            if in_log_file.server_id is not None:
                if server is not None:
                    in_log_file.server = server
                else:
                    in_log_file.server = Server.get_by_id_cached(in_log_file.server_id)
            if in_log_file.game_map_id is not None:
                in_log_file.game_map = GameMap.get_by_id_cached(in_log_file.game_map_id)
            if in_log_file.version_id is not None:
                in_log_file.version = Version.get_by_id_cached(in_log_file.version_id)

            return in_log_file

        query = LogFile.select(LogFile)
        if server is None:
            query = query
        else:
            query = query.where((LogFile.server_id == server.id))

        if exclude_unparsable is True:
            query = query.where((LogFile.unparsable == False))

        _out = tuple(_resolve_game_map_and_version(i) for i in query.order_by(ordered_by).iterator())

        return _out

    def get_all_log_levels(self, ordered_by=LogLevel.id) -> tuple[LogLevel]:
        with self.connection_context() as ctx:
            return tuple(LogLevel.select().order_by(ordered_by).iterator())

    def get_all_arma_functions(self, ordered_by=None) -> tuple[ArmaFunction]:
        with self._resolve_arma_functions_check_lock:
            if self._resolve_arma_functions_future is None or self._resolve_arma_functions_future.running() is False:
                self._resolve_arma_functions_future = self.record_inserter.thread_pool.submit(self.resolve_all_armafunction_extras)

        with self.atomic() as txn:
            _ = list(ArmaFunctionAuthorPrefix.select().iterator())
            if not ordered_by:
                return tuple(ArmaFunction.select(ArmaFunction, ArmaFunctionAuthorPrefix).join_from(ArmaFunction, ArmaFunctionAuthorPrefix).iterator())

            return tuple(ArmaFunction.select(ArmaFunction, ArmaFunctionAuthorPrefix).join_from(ArmaFunction, ArmaFunctionAuthorPrefix).order_by(ordered_by).iterator())

    def get_all_game_maps(self, ordered_by=GameMap.id) -> tuple[GameMap]:
        with self.connection_context() as ctx:
            _out = []
            for _id, in GameMap.select(GameMap.id).order_by(ordered_by).tuples().iterator():
                _out.append(GameMap.get_by_id_cached(_id))
        return tuple(_out)

    def get_all_origins(self, ordered_by=RecordOrigin.id) -> tuple[RecordOrigin]:
        with self.connection_context() as ctx:
            _out = []
            for _id, in RecordOrigin.select(RecordOrigin.id).order_by(ordered_by).tuples().iterator():
                _out.append(RecordOrigin.get_by_id_cached(_id))
        return tuple(_out)

    def get_all_versions(self, ordered_by=Version.id) -> tuple[Version]:
        with self.connection_context() as ctx:
            _out = []
            for _id, in Version.select(Version.id).order_by(ordered_by).tuples().iterator():
                _out.append(Version.get_by_id_cached(_id))
        return tuple(_out)

    def iter_all_records(self, server: Server = None, log_file: LogFile = None, only_missing_record_class: bool = False) -> Generator[LogRecord, None, None]:
        self.connect(True)

        foreign_key_cache = ForeignKeyCache(self)
        foreign_key_cache.preload_all()

        if log_file is not None:
            log_files = LogFile.select(LogFile.id).where(LogFile.id == log_file.id)
        elif server is not None:
            log_files = LogFile.select(LogFile.id).where((LogFile.server_id == server.id) & (LogFile.unparsable == False))
        else:

            log_files = LogFile.select(LogFile.id).where((LogFile.unparsable == False))
        log_files = log_files.order_by(LogFile.id)

        def _get_records(in_log_file_id: int):

            def _resolve_record(in_record, in_foreign_key_cache):
                in_record.origin = in_foreign_key_cache.get_origin_by_id(in_record.origin_id)
                in_record.called_by = in_foreign_key_cache.get_arma_file_by_id(in_record.called_by_id)
                in_record.logged_from = in_foreign_key_cache.get_arma_file_by_id(in_record.logged_from_id)
                in_record.record_class = self.backend.record_class_manager.get_model_by_id(in_record.record_class_id)
                return in_record

            query = LogRecord.select(LogRecord.id, Message.text, LogRecord.origin_id, LogRecord.called_by_id, LogRecord.logged_from_id, LogRecord.record_class_id).join_from(LogRecord, Message, join_type=JOIN.LEFT_OUTER, on=(LogRecord.message_item == Message.md5_hash), attr="_message")
            if only_missing_record_class is True:
                query = query.where(LogRecord.record_class_id >> None)

            for _record_chunk in chunked(query.where(LogRecord.log_file_id == in_log_file_id).iterator(), 1_000):

                yield from [_resolve_record(r, self.foreign_key_cache) for r in _record_chunk]

        log_files_ids = tuple(l.id for l in log_files.iterator())

        with ThreadPoolExecutor(max_workers=max(1, len(log_files_ids) // 10), initializer=self.connect, initargs=(True,)) as pool:
            for idx, records_chunk in enumerate(pool.map(_get_records, log_files_ids)):
                if idx % 10 == 0:
                    gc.collect()
                yield from records_chunk

    def get_amount_iter_all_records(self, server: Server = None, log_file: LogFile = None, only_missing_record_class: bool = False) -> int:
        with self.connection_context() as ctx:
            if log_file is not None:
                log_files = [log_file]
            elif server is not None:
                log_files = LogFile.select(LogFile.id).where((LogFile.server_id == server.id) & (LogFile.unparsable == False))
            else:
                log_files = LogFile.select(LogFile.id).where(LogFile.unparsable == False)

            query = LogRecord.select(LogRecord.id).where(LogRecord.log_file << log_files)

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
        log.debug("resolving all armafunction extras")
        with self.transaction():
            query = ArmaFunction.select(ArmaFunction, ArmaFunctionAuthorPrefix).join_from(ArmaFunction, ArmaFunctionAuthorPrefix, join_type=JOIN.LEFT_OUTER).where((ArmaFunction.file_name == None) | (ArmaFunction.function_name == None))

            for arma_func in tuple(query.iterator()):
                arma_func.load_extras()

    def __repr__(self) -> str:
        repr_attrs = ("database_name", "config", "auto_backup", "thread_safe", "autoconnect")
        _repr = self.__class__.__name__
        attr_text = ', '.join(attr_name + "=" + repr(getattr(self, attr_name, None)) for attr_name in repr_attrs)
        return _repr + "(" + attr_text + ")"


# region[Main_Exec]
if __name__ == '__main__':

    pass
# endregion[Main_Exec]
