"""
WiP.

Soon.
"""

# region [Imports]

# * Standard Library Imports ---------------------------------------------------------------------------->
from time import sleep
from typing import TYPE_CHECKING, Iterable
from pathlib import Path
from weakref import WeakSet
from datetime import datetime
from itertools import chain
from threading import Lock, Event
from multiprocessing import Process
from concurrent.futures import ALL_COMPLETED, ThreadPoolExecutor, wait

# * Third Party Imports --------------------------------------------------------------------------------->
import attr

# * Qt Imports --------------------------------------------------------------------------------------->
from PySide6.QtWidgets import QApplication

# * Gid Imports ----------------------------------------------------------------------------------------->
from gidapptools import get_logger, get_meta_info, get_meta_paths, get_meta_config
from gidapptools.gid_signal.interface import get_signal
from gidapptools.general_helper.compress import compress_file

# * Local Imports --------------------------------------------------------------------------------------->
from antistasi_logbook.records import ALL_GENERIC_RECORD_CLASSES, ALL_ANTISTASI_RECORD_CLASSES
from antistasi_logbook.parsing.parser import Parser
from antistasi_logbook.utilities.locks import FILE_LOCKS
from antistasi_logbook.storage.database import GidSqliteApswDatabase
from antistasi_logbook.updating.updater import Updater
from antistasi_logbook.regex.regex_keeper import SimpleRegexKeeper
from antistasi_logbook.storage.models.models import LogFile, RecordClass, DatabaseMetaData
from antistasi_logbook.updating.time_handling import TimeClock
from antistasi_logbook.parsing.parsing_context import LogParsingContext
from antistasi_logbook.updating.update_manager import UpdateManager
from antistasi_logbook.parsing.record_processor import RecordInserter, RecordProcessor
from antistasi_logbook.updating.remote_managers import remote_manager_registry
from antistasi_logbook.parsing.foreign_key_cache import ForeignKeyCache
from antistasi_logbook.records.record_class_manager import RECORD_CLASS_TYPE, RecordClassManager

# * Type-Checking Imports --------------------------------------------------------------------------------->
if TYPE_CHECKING:
    from gidapptools.gid_signal.signals import abstract_signal
    from gidapptools.gid_config.interface import GidIniConfig

    from antistasi_logbook.gui.misc import UpdaterSignaler
    from antistasi_logbook.gui.application import AntistasiLogbookApplication

# endregion[Imports]

# region [TODO]


# endregion [TODO]

# region [Logging]


# endregion[Logging]

# region [Constants]

THIS_FILE_DIR = Path(__file__).parent.absolute()
META_INFO = get_meta_info()
META_PATHS = get_meta_paths()
CONFIG = get_meta_config().get_config("general")

log = get_logger(__name__)
# endregion[Constants]


@attr.s(auto_detect=True, auto_attribs=True, slots=True, frozen=True, kw_only=True)
class Events:
    """
    Simple class to have doted access to an collection of events, that is static.
    """
    stop: Event = attr.ib(default=Event())
    pause: Event = attr.ib(default=Event())


@attr.s(auto_detect=True, auto_attribs=True, slots=True, frozen=True, kw_only=True)
class Locks:
    """
    Simple class to have doted access to an collection of locks, that is static.

    """
    updating: Lock = attr.ib(default=Lock())


@attr.s(auto_detect=True, auto_attribs=True, slots=True, frozen=True, kw_only=True)
class Signals:
    """
    Simple class to have doted access to signals, that are static.

    Signal implementation could be replaced with QSignal in the future.
    """
    new_log_file: "abstract_signal" = get_signal("new_log_file")
    updated_log_file: "abstract_signal" = get_signal("updated_log_file")
    new_log_record: "abstract_signal" = get_signal("new_log_record")
    update_started: "abstract_signal" = get_signal("update_started")


class NoneSignaler:

    def send_update_started(self):
        pass

    def send_update_finished(self):
        pass

    def send_update_increment(self):
        pass

    def send_update_info(self, amount, name):
        pass


class Backend:

    """
    Class to create the complete backend.

    Is used to simplify the complex setup of the backend.

    Args:
        database (`GidSqliteDatabase`): [description]
        config (`GidIniConfig`): [description]
        database_proxy (`peewee.DatabaseProxy`): [description]

    """
    all_parsing_context: WeakSet["LogParsingContext"] = WeakSet()

    def __init__(self, database: "GidSqliteApswDatabase", config: "GidIniConfig", update_signaler: "UpdaterSignaler" = NoneSignaler()) -> None:
        self._thread_pool: ThreadPoolExecutor = None
        self._inserting_thread_pool: ThreadPoolExecutor = None
        self.events = Events()
        self.locks = Locks()
        self.signals = Signals()
        self.config = config
        self.database = database
        self.update_signaler = update_signaler
        self.foreign_key_cache = ForeignKeyCache(self)

        self.record_class_manager = RecordClassManager(foreign_key_cache=self.foreign_key_cache)

        self.time_clock = TimeClock(config=self.config, stop_event=self.events.stop)
        self.remote_manager_registry = remote_manager_registry
        self.record_processor = RecordProcessor(backend=self, regex_keeper=SimpleRegexKeeper())
        self.parser = Parser(backend=self, regex_keeper=SimpleRegexKeeper(), stop_event=self.events.stop)
        self.updater = Updater(stop_event=self.events.stop, pause_event=self.events.pause, backend=self, signaler=self.update_signaler)
        self.records_inserter = RecordInserter(config=self.config, backend=self)

        # gui_dependent_on_backend
        self.dependent_objects = set()

        # thread
        self.update_manager: UpdateManager = None

    @property
    def app(self) -> "AntistasiLogbookApplication":
        return QApplication.instance()

    @property
    def thread_pool(self) -> ThreadPoolExecutor:
        if self._thread_pool is None:
            self._thread_pool = ThreadPoolExecutor(max_workers=max(1, self.config.get("general", "max_threads") // 2), thread_name_prefix="backend")
        return self._thread_pool

    @property
    def inserting_thread_pool(self) -> ThreadPoolExecutor:
        if self._inserting_thread_pool is None:
            self._inserting_thread_pool = ThreadPoolExecutor(max_workers=max(1, self.config.get("general", "max_threads") // 2), thread_name_prefix="backend_inserting")
        return self._inserting_thread_pool

    @property
    def session_meta_data(self) -> "DatabaseMetaData":
        return self.database.session_meta_data

    def get_update_manager(self) -> "UpdateManager":
        """
        Creates a new `UpdateManager` thread.

        Needed if the previous `UpdateManager` thread was stopped and update loop should restart.

        Returns:
            `UpdateManager`: Thread-subclass that schedules update cycles.
        """
        return UpdateManager(updater=self.updater, config=self.config, time_clock=self.time_clock, pause_event=self.events.pause, stop_event=self.events.stop)

    def get_parsing_context(self, log_file: "LogFile") -> "LogParsingContext":
        """
        Factory method for the parsing_context.

        Overwrite in subclass if different parsing_context class should be used.

        Args:
            log_file(`LogFile`): database model.

        Returns:
            `LogParsingContext`: Instantiated `LogParsingContext` with the provided `LogFile` model.
        """
        context = LogParsingContext(log_file=log_file, inserter=self.records_inserter, foreign_key_cache=self.foreign_key_cache, config=self.config)
        self.all_parsing_context.add(context)
        return context

    def register_record_classes(self, record_classes: Iterable[RECORD_CLASS_TYPE]) -> "Backend":
        for record_class in record_classes:
            self.record_class_manager.register_record_class(record_class=record_class)
        return self

    def fill_record_class_manager(self) -> None:
        for record_class in chain(ALL_ANTISTASI_RECORD_CLASSES, ALL_GENERIC_RECORD_CLASSES):
            self.record_class_manager.register_record_class(record_class=record_class)
        RecordClass.record_class_manager = self.record_class_manager

    def start_up(self, overwrite: bool = False) -> "Backend":
        """
        Start up the database, populates the database with all necessary tables and default entries ("or_ignore"), registers all record_classes and connects basic signals.

        """
        self.events.stop.clear()
        self.events.pause.clear()
        self.database.record_inserter = self.records_inserter
        self.database.record_processor = self.record_processor
        self.database.start_up(overwrite=overwrite)

        self.database.connect(True)
        self.fill_record_class_manager()
        _ = self.foreign_key_cache.all_antistasi_file_objects
        _ = self.foreign_key_cache.all_antistasi_file_objects_by_id
        _ = self.foreign_key_cache.all_game_map_objects
        _ = self.foreign_key_cache.all_game_map_objects_by_id
        _ = self.foreign_key_cache.all_log_levels
        _ = self.foreign_key_cache.all_log_levels_by_id
        _ = self.foreign_key_cache.all_origin_objects
        _ = self.foreign_key_cache.all_origin_objects_by_id

        self.signals.new_log_record.connect(self.database.session_meta_data.increment_added_log_records)
        self.signals.new_log_file.connect(self.database.session_meta_data.increment_new_log_file)
        self.signals.updated_log_file.connect(self.database.session_meta_data.increment_updated_log_file)
        for obj in self.dependent_objects:
            obj.start()
        return self

    def shutdown(self) -> None:
        """
        Signals the shutdown to all Backend sub_objects via the `stop`-event. Waits for a limited time on all parsing_context futures and then ensures thes shutdown of all sub_objects
        that can be shut down.


        """
        for obj in self.dependent_objects:
            obj.shutdown()
        self.events.stop.set()
        all_futures = []
        log.debug("checking if all ctx are closed")
        for ctx in self.all_parsing_context:
            log.debug("checking ctx %r", ctx)
            while ctx.is_open is True:
                sleep(0.1)
            all_futures += ctx.futures
        log.debug("waiting for all futures to finish")
        wait(all_futures, return_when=ALL_COMPLETED, timeout=3.0)

        if self.update_manager is not None and self.update_manager.is_alive() is True:
            self.update_manager.shutdown()
        self.remote_manager_registry.close()
        self.updater.shutdown()
        self.records_inserter.shutdown()
        self.database.shutdown()
        self.thread_pool.shutdown(cancel_futures=True, wait=True)
        self.inserting_thread_pool.shutdown(cancel_futures=True, wait=True)
        self._thread_pool = None
        self._inserting_thread_pool = None

    def remove_and_reset_database(self) -> None:
        self.shutdown()
        self.events.stop.clear()
        FILE_LOCKS.reset()

        self.parser = Parser(backend=self, regex_keeper=SimpleRegexKeeper(), stop_event=self.events.stop)
        self.updater = Updater(config=self.config, parsing_context_factory=self.get_parsing_context, parser=self.parser, stop_event=self.events.stop, pause_event=self.events.pause, database=self.database, signaler=self.update_signaler)
        self.records_inserter = RecordInserter(config=self.config, backend=self)
        self.update_manager: UpdateManager = None
        self.foreign_key_cache.reset_all()

        self.start_up(True)
        self.record_class_manager.reset()

    def backup_db(self, backup_folder: Path = None):

        def limit_backups(_folder: Path):
            limit_amount = self.config.get("database", "backup_limit")
            backups = [p for p in _folder.iterdir() if p.is_file() and f"{self.database.database_path.stem}_backup" in p.stem]
            backups = sorted(backups, key=lambda x: x.stat().st_ctime)
            while len(backups) > limit_amount:
                to_delete = backups.pop(0)
                to_delete.unlink(missing_ok=True)

        if backup_folder is None:
            backup_folder = self.database.backup_folder
        backup_folder.mkdir(parents=True, exist_ok=True)
        backup_path = backup_folder.joinpath(f"{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}_{self.database.database_path.stem}_backup{self.database.database_path.suffix}")
        compress_file(source=self.database.database_path, target=backup_path)
        limit_backups(backup_folder)

    def start_update_loop(self) -> "Backend":
        if self.update_manager is None:
            self.update_manager = self.get_update_manager()
        self.update_manager.start()
        return self


# region[Main_Exec]
if __name__ == '__main__':
    pass
# endregion[Main_Exec]
