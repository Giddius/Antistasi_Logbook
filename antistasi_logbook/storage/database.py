"""
WiP.

Soon.
"""

# region [Imports]
from contextlib import contextmanager
# * Standard Library Imports ---------------------------------------------------------------------------->
from gidapptools.general_helper.timing import get_dummy_profile_decorator_in_globals
from gidapptools.general_helper.conversion import human2bytes
from gidapptools.meta_data.interface import MetaPaths, get_meta_info, get_meta_paths, get_meta_config
from gidapptools import get_logger
from antistasi_logbook.parsing.foreign_key_cache import ForeignKeyCache
from antistasi_logbook.storage.models.models import Server, GameMap, LogFile, LogLevel, RecordClass, RemoteStorage, AntstasiFunction, DatabaseMetaData, setup_db, LogRecord, RecordOrigin
from playhouse.apsw_ext import APSWDatabase
from peewee import DatabaseProxy, JOIN
from apsw import Connection
from threading import Lock, Thread, Event, Condition, Barrier, Semaphore
from functools import cached_property
from pathlib import Path
from typing import TYPE_CHECKING, Union, Protocol, Iterable, Generator, Any, Optional
import os
from weakref import WeakSet

# * Third Party Imports --------------------------------------------------------------------------------->
from antistasi_logbook import setup

setup()
# * Standard Library Imports ---------------------------------------------------------------------------->

# * Third Party Imports --------------------------------------------------------------------------------->

# * Gid Imports ----------------------------------------------------------------------------------------->

if TYPE_CHECKING:
    # * Gid Imports ----------------------------------------------------------------------------------------->
    from gidapptools.gid_config.interface import GidIniConfig
    from antistasi_logbook.parsing.record_processor import RecordProcessor, RecordInserter

# endregion[Imports]

# region [TODO]


# endregion [TODO]

# region [Logging]


# endregion[Logging]

# region [Constants]
get_dummy_profile_decorator_in_globals()
THIS_FILE_DIR = Path(__file__).parent.absolute()
META_PATHS: MetaPaths = get_meta_paths()
META_INFO = get_meta_info()
CONFIG: "GidIniConfig" = get_meta_config().get_config('general')
CONFIG.config.load()
log = get_logger(__name__)
# endregion[Constants]

DEFAULT_DB_NAME = "storage.db"

DEFAULT_PRAGMAS = {
    "cache_size": -1 * 128000,
    "journal_mode": 'wal',
    "synchronous": 0,
    "ignore_check_constraints": 0,
    "foreign_keys": 1,
    "temp_store": "MEMORY",
    "mmap_size": human2bytes("1 gb")
}


def make_db_path(in_path: Union[str, os.PathLike, Path]) -> str:
    return Path(in_path).resolve().as_posix().replace('/', '\\')


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


class GidSqliteApswDatabase(APSWDatabase):
    all_connections: WeakSet[Connection] = WeakSet()
    default_extensions = {"json_contains": True,
                          "regexp_function": False}

    default_db_path = META_PATHS.db_dir if os.getenv('IS_DEV', 'false') == "false" else THIS_FILE_DIR

    def __init__(self,
                 database_path: Path = None,
                 config: "GidIniConfig" = None,
                 auto_backup: bool = False,
                 thread_safe=True,
                 autoconnect=True,
                 pragmas=None,
                 extensions=None):
        self.database_path = self.default_db_path.joinpath(DEFAULT_DB_NAME) if database_path is None else Path(database_path).joinpath(DEFAULT_DB_NAME)
        self.database_name = self.database_path.name
        self.config = CONFIG if config is None else config
        self.auto_backup = auto_backup
        self.started_up = False
        self.session_meta_data: "DatabaseMetaData" = None
        extensions = self.default_extensions.copy() | (extensions or {})
        pragmas = DEFAULT_PRAGMAS.copy() | (pragmas or {})
        super().__init__(make_db_path(self.database_path), thread_safe=thread_safe, autoconnect=autoconnect, pragmas=pragmas, timeout=30, **extensions)
        self.foreign_key_cache = ForeignKeyCache(self)
        self.write_lock = Lock()
        self.record_processor: "RecordProcessor" = None
        self.record_inserter: "RecordInserter" = None

    @property
    def default_backup_folder(self) -> Path:
        return self.database_path.parent.joinpath("backups")

    @cached_property
    def base_record_id(self) -> int:
        return RecordClass.select().where(RecordClass.name == "BaseRecord").scalar()

    # def _add_conn_hooks(self, conn):
    #     super()._add_conn_hooks(conn)
    #     self.all_connections.add(conn)

    def _pre_start_up(self, overwrite: bool = False) -> None:
        self.database_path.parent.mkdir(exist_ok=True, parents=True)
        if overwrite is True:
            self.database_path.unlink(missing_ok=True)

    def _post_start_up(self, **kwargs) -> None:
        self.session_meta_data = DatabaseMetaData.new_session()

    def start_up(self,
                 overwrite: bool = False,
                 force: bool = False) -> "GidSqliteApswDatabase":

        if self.started_up is True and force is False:
            return
        log.info("starting up %r", self)
        self._pre_start_up(overwrite=overwrite)
        self.connect(reuse_if_open=True)
        with self.write_lock:
            setup_db(self)

        self._post_start_up()
        self.started_up = True
        self.foreign_key_cache.reset_all()
        log.info("finished starting up %r", self)
        return self

    def optimize(self) -> "GidSqliteApswDatabase":
        log.info("optimizing %r", self)
        with self.write_lock:
            self.pragma("OPTIMIZE")
        return self

    def vacuum(self) -> "GidSqliteApswDatabase":
        log.info("vacuuming %r", self)
        with self.write_lock:
            self.execute_sql("VACUUM;")
        return self

    def close(self):
        return super().close()

    def shutdown(self,
                 error: BaseException = None,
                 backup_folder: Union[str, os.PathLike, Path] = None) -> None:
        log.debug("shutting down %r", self)
        with self.write_lock:
            self.session_meta_data.save()

        is_closed = self.close()
        for conn in self.all_connections:
            conn.close()
        if self.auto_backup is True and error is None:
            # self.backup(backup_folder=backup_folder)
            log.warning("'backup-method' is not written!")
        log.debug("finished shutting down %r", self)
        self.started_up = False

    def get_all_server(self, ordered_by=Server.id) -> tuple[Server]:
        with self.connection_context() as ctx:
            result = tuple(Server.select().join(RemoteStorage, on=Server.remote_storage).order_by(ordered_by))

        return result

    def get_log_files(self, server: Server = None, ordered_by=LogFile.id) -> tuple[LogFile]:
        with self:
            query = LogFile.select()
            query = query.join(Server, on=LogFile.server).join(RemoteStorage, on=Server.remote_storage).switch(LogFile)
            query = query.join(GameMap, on=LogFile.game_map, join_type=JOIN.LEFT_OUTER).switch(LogFile)
            if server is None:
                return tuple(query.order_by(ordered_by))
            return tuple(query.where(LogFile.server_id == server.id).order_by(ordered_by))

    def get_all_log_levels(self, ordered_by=LogLevel.id) -> tuple[LogLevel]:
        with self.connection_context() as ctx:
            result = tuple(LogLevel.select().order_by(ordered_by))

        return result

    def get_all_antistasi_functions(self, ordered_by=AntstasiFunction.id) -> tuple[AntstasiFunction]:
        with self.connection_context() as ctx:
            result = tuple(AntstasiFunction.select().order_by(ordered_by))

        return result

    def get_all_game_maps(self, ordered_by=GameMap.id) -> tuple[GameMap]:
        with self.connection_context() as ctx:
            result = tuple(GameMap.select().order_by(ordered_by))

        return result

    def get_all_origins(self, ordered_by=RecordOrigin.id) -> tuple[RecordOrigin]:
        with self.connection_context() as ctx:
            result = tuple(RecordOrigin.select().order_by(ordered_by))
        return result

    def iter_all_records(self, server: Server = None, only_missing_record_class: bool = False) -> Generator[LogRecord, None, None]:
        self.connect(True)

        query = LogRecord.select().join(RecordClass, join_type=JOIN.LEFT_OUTER).switch(LogRecord).join(LogFile).switch(LogRecord).join(AntstasiFunction, on=(LogRecord.logged_from == AntstasiFunction.id), join_type=JOIN.LEFT_OUTER)
        if server is not None:
            nested = LogFile.select().where(LogFile.server_id == server.id)
            query = query.where(LogRecord.log_file << nested)
        if only_missing_record_class is True:
            query = query.where(LogRecord.record_class == None)
        for record in query.iterator():
            yield record
        self.close()

    def __repr__(self) -> str:
        repr_attrs = ("database_name", "config", "auto_backup", "thread_safe", "autoconnect")
        _repr = f"{self.__class__.__name__}"
        attr_text = ', '.join(f"{attr_name}={getattr(self, attr_name)}" for attr_name in repr_attrs)
        return f"{_repr}({attr_text})"


# region[Main_Exec]
if __name__ == '__main__':
    pass
    # endregion[Main_Exec]
