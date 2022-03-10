"""
WiP.

Soon.
"""

# region [Imports]

# * Standard Library Imports ---------------------------------------------------------------------------->
import os
from typing import TYPE_CHECKING, Union, Protocol, Generator
from pathlib import Path
from weakref import WeakSet
from functools import cached_property
from threading import Lock
import atexit
# * Third Party Imports --------------------------------------------------------------------------------->
from apsw import Connection, SQLITE_CHECKPOINT_TRUNCATE, SQLITE_OK
from peewee import JOIN, DatabaseProxy
from playhouse.apsw_ext import APSWDatabase

# * Gid Imports ----------------------------------------------------------------------------------------->
from gidapptools import get_logger
from gidapptools.meta_data.interface import MetaPaths, get_meta_info, get_meta_paths, get_meta_config
from gidapptools.general_helper.timing import get_dummy_profile_decorator_in_globals
from gidapptools.general_helper.conversion import human2bytes

# * Local Imports --------------------------------------------------------------------------------------->
from antistasi_logbook import setup
from antistasi_logbook.storage.models.models import (Server, GameMap, LogFile, Version, LogLevel, LogRecord, RecordClass, RecordOrigin,
                                                     RemoteStorage, ArmaFunction, DatabaseMetaData, setup_db, ArmaFunctionAuthorPrefix)
from antistasi_logbook.storage.models.migration import run_migration
from gidapptools.general_helper.conversion import ns_to_s
setup()
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

THIS_FILE_DIR = Path(__file__).parent.absolute()
META_PATHS: MetaPaths = get_meta_paths()
META_INFO = get_meta_info()
CONFIG: "GidIniConfig" = get_meta_config().get_config('general')
CONFIG.config.load()
log = get_logger(__name__)
# endregion[Constants]

DEFAULT_DB_NAME = "storage.db"

DEFAULT_PRAGMAS = {
    "cache_size": -1 * 64000,
    "journal_mode": 'wal',
    "synchronous": 0,
    "ignore_check_constraints": 0,
    "foreign_keys": 1,
    "temp_store": "MEMORY",
    "mmap_size": 268435456 * 4,
    "journal_size_limit": human2bytes("100mb"),
    "wal_autocheckpoint": 100,
    "page_size": 32768,
    "analysis_limit": 1000
}


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
    log.debug("WAL-Hook was called with: db_name: %r, pages: %r, conn: %r", db_name, pages, conn)
    return SQLITE_OK


def rollback_hook():
    log.debug("Rollback-Hook was called")


def profile_hook(stmt, time_taken):
    log.debug("statement %r took %r s", stmt, ns_to_s(time_taken))


class GidSqliteApswDatabase(APSWDatabase):

    default_extensions = {"c_extensions": True,
                          "json_contains": True,
                          "regexp_function": False,
                          "bloomfilter": True}

    default_db_path = META_PATHS.db_dir if os.getenv('IS_DEV', 'false') == "false" else THIS_FILE_DIR
    conns = WeakSet()

    def __init__(self,
                 database_path: Path = None,
                 config: "GidIniConfig" = None,
                 auto_backup: bool = False,
                 thread_safe=True,
                 autoconnect=True,
                 pragmas=None,
                 extensions=None):
        self.all_connections: WeakSet[Connection] = WeakSet()
        self.database_path = self.resolve_db_path(database_path=database_path)
        self.database_path.parent.mkdir(exist_ok=True, parents=True)
        self.database_existed: bool = self.database_path.is_file()
        self.database_name = self.database_path.name
        self.config = CONFIG if config is None else config
        self.auto_backup = auto_backup
        self.started_up = False
        self.session_meta_data: "DatabaseMetaData" = None
        extensions = self.default_extensions.copy() | (extensions or {})
        pragmas = DEFAULT_PRAGMAS.copy() | (pragmas or {})
        super().__init__(make_db_path(self.database_path), thread_safe=thread_safe, autoconnect=autoconnect, pragmas=pragmas, timeout=30, statementcachesize=100, ** extensions)

        self.foreign_key_cache: "ForeignKeyCache" = ForeignKeyCache(database=self)
        self.write_lock = Lock()
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

    def _add_conn_hooks(self, conn):
        self.conns.add(conn)
        super()._add_conn_hooks(conn)
        # conn.setwalhook(wal_hook)
        # conn.setprofile(profile_hook)
        # conn.setrollbackhook(rollback_hook)

    def _pre_start_up(self, overwrite: bool = False) -> None:
        self.database_path.parent.mkdir(exist_ok=True, parents=True)
        if overwrite is True:
            self.database_path.unlink(missing_ok=True)

    def _post_start_up(self, **kwargs) -> None:
        self.session_meta_data = DatabaseMetaData.new_session()

    def checkpoint(self, mode=SQLITE_CHECKPOINT_TRUNCATE):
        with self.write_lock:
            self.connect(True)
            conn = self.connection()
            result = conn.wal_checkpoint(mode=mode)
            log.info("checkpoint wal with return: %r", result)
            self.close()

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
        self.checkpoint()
        self.optimize()
        return self

    def optimize(self) -> "GidSqliteApswDatabase":
        log.info("optimizing %r", self)
        # with self.write_lock:
        self.pragma("analysis_limit", None)
        self.pragma("OPTIMIZE")
        log.info("finished optimizing %r", self)
        return self

    def vacuum(self) -> "GidSqliteApswDatabase":
        log.info("vacuuming %r", self)
        with self.write_lock:
            self.execute_sql("VACUUM;")
            self.checkpoint()
        return self

    def shutdown(self, error: BaseException = None) -> None:
        log.debug("shutting down %r", self)
        with self.write_lock:
            self.session_meta_data.save()
        with self.connection_context() as ctx:
            self.checkpoint()
            self.optimize()
            self.checkpoint()
            with self.write_lock:
                self.conns.clear()

        log.debug("finished shutting down %r", self)
        self.started_up = False

    def get_all_server(self, ordered_by=Server.id) -> tuple[Server]:

        result = tuple(Server.select().join(RemoteStorage, on=Server.remote_storage).order_by(ordered_by))

        return result

    def get_log_files(self, server: Server = None, ordered_by=LogFile.id) -> tuple[LogFile]:

        query = LogFile.select(LogFile, Server, GameMap, Version)
        query = query.join(Server, on=LogFile.server).join(RemoteStorage, on=Server.remote_storage).switch(LogFile)
        query = query.join(GameMap, on=LogFile.game_map, join_type=JOIN.LEFT_OUTER).switch(LogFile)
        query = query.join(Version, on=LogFile.version, join_type=JOIN.LEFT_OUTER).switch(LogFile)
        if server is None:
            return tuple(query.order_by(ordered_by).iterator())
        return tuple(query.where(LogFile.server_id == server.id).order_by(ordered_by).iterator())

    def get_all_log_levels(self, ordered_by=LogLevel.id) -> tuple[LogLevel]:

        result = tuple(LogLevel.select().order_by(ordered_by).iterator())

        return result

    def get_all_arma_functions(self, ordered_by=ArmaFunction.id) -> tuple[ArmaFunction]:

        result = tuple(ArmaFunction.select(ArmaFunction).join(ArmaFunctionAuthorPrefix).order_by(ordered_by).iterator())

        return result

    def get_all_game_maps(self, ordered_by=GameMap.id) -> tuple[GameMap]:

        result = tuple(GameMap.select(GameMap).order_by(ordered_by).iterator())

        return result

    def get_all_origins(self, ordered_by=RecordOrigin.id) -> tuple[RecordOrigin]:

        result = tuple(RecordOrigin.select().order_by(ordered_by).iterator())
        return result

    def get_all_versions(self, ordered_by=Version) -> tuple[Version]:

        result = tuple(Version.select(Version).order_by(ordered_by).iterator())
        return result

    def iter_all_records(self, server: Server = None, log_file: LogFile = None, only_missing_record_class: bool = False) -> Generator[LogRecord, None, None]:

        self.connect(True)
        self.foreign_key_cache.preload_all()

        query = LogRecord.select(LogRecord, RecordClass).join(RecordClass, join_type=JOIN.LEFT_OUTER)
        if log_file is not None:
            query = query.switch(LogRecord).join(LogFile).where(LogRecord.log_file_id == log_file.id)
        elif server is not None:
            nested = LogFile.select().where(LogFile.server_id == server.id)
            query = query.switch(LogRecord).join(LogFile).where(LogRecord.log_file << nested)

        if only_missing_record_class is True:
            query = query.where(LogRecord.record_class >> None)
        for record in query.iterator():
            record.called_by = self.foreign_key_cache.get_arma_file_by_id(record.called_by_id)
            record.logged_from = self.foreign_key_cache.get_arma_file_by_id(record.logged_from_id)
            record.origin = self.foreign_key_cache.get_origin_by_id(record.origin_id)
            yield record
        self.close()

    def get_unique_server_ips(self) -> tuple[str]:

        _out = tuple(set(s.ip for s in Server.select().iterator() if s.ip is not None))

        return _out

    def get_unique_campaign_ids(self) -> tuple[int]:

        _out = set(l.campaign_id for l in LogFile.select().where(LogFile.unparsable == False).iterator() if l.campaign_id is not None)
        return tuple(sorted(_out))

    def __repr__(self) -> str:
        repr_attrs = ("database_name", "config", "auto_backup", "thread_safe", "autoconnect")
        _repr = f"{self.__class__.__name__}"
        attr_text = ', '.join(f"{attr_name}={getattr(self, attr_name, None)}" for attr_name in repr_attrs)
        return f"{_repr}({attr_text})"


# region[Main_Exec]
if __name__ == '__main__':

    pass
# endregion[Main_Exec]
