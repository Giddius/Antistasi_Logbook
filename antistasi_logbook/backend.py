"""
WiP.

Soon.
"""

# region [Imports]

# * Standard Library Imports ---------------------------------------------------------------------------->
import gc
import shutil
from time import time, sleep
from typing import TYPE_CHECKING, Iterable, Optional
from pathlib import Path
from weakref import WeakSet
from itertools import chain
from threading import Lock, Event
from concurrent.futures import ALL_COMPLETED, ThreadPoolExecutor, wait, Future

# * Qt Imports --------------------------------------------------------------------------------------->
from PySide6.QtWidgets import QApplication

# * Third Party Imports --------------------------------------------------------------------------------->
import attr

# * Gid Imports ----------------------------------------------------------------------------------------->
from gidapptools import get_logger, get_meta_info, get_meta_paths
from gidapptools.gid_signal.interface import get_signal

# * Local Imports --------------------------------------------------------------------------------------->
from antistasi_logbook.records import get_all_antistasi_record_classes, get_all_generic_record_classes
from antistasi_logbook.parsing.parser import Parser
from antistasi_logbook.storage.database import GidSqliteApswDatabase, make_db_path
from antistasi_logbook.updating.updater import Updater
from antistasi_logbook.storage.models.models import LogFile, RecordClass, DatabaseMetaData
from antistasi_logbook.updating.time_handling import TimeClock
from antistasi_logbook.parsing.parsing_context import LogParsingContext
from antistasi_logbook.updating.update_manager import UpdateManager
from antistasi_logbook.parsing.record_processor import RecordInserter, RecordProcessor
from antistasi_logbook.regex_store.regex_keeper import SimpleRegexKeeper
from antistasi_logbook.updating.remote_managers import AbstractRemoteStorageManager, remote_manager_registry
from antistasi_logbook.parsing.foreign_key_cache import ForeignKeyCache
from antistasi_logbook.records.record_class_manager import RECORD_CLASS_TYPE, RecordClassManager
from antistasi_logbook.utilities.networker_limiter import NetworkSpeedLimiter
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
        update_signaler (`UpdaterSignaler`): [description]

    """
    all_parsing_context: WeakSet["LogParsingContext"] = WeakSet()
    minimum_thread_amount = 10
    average_seconds_per_log_file: float = 12.5

    def __init__(self, database: "GidSqliteApswDatabase", config: "GidIniConfig", update_signaler: "UpdaterSignaler" = NoneSignaler()) -> None:
        self._thread_pool: ThreadPoolExecutor = None
        self._inserting_thread_pool: ThreadPoolExecutor = None
        self.events = Events()
        self.locks = Locks()
        self.signals = Signals()
        self.config = config
        self.color_config: "GidIniConfig" = None
        self.database = database
        self.database.backend = self
        self.update_signaler = update_signaler

        self.record_class_manager = RecordClassManager(backend=self, foreign_key_cache=self.foreign_key_cache)

        self.time_clock = TimeClock(config=self.config, stop_event=self.events.stop)
        self.remote_manager_registry = remote_manager_registry
        AbstractRemoteStorageManager.config = self.config

        self.record_processor = RecordProcessor(backend=self, regex_keeper=SimpleRegexKeeper(), foreign_key_cache=self.foreign_key_cache)
        self.updater = Updater(stop_event=self.events.stop, pause_event=self.events.pause, backend=self, signaler=self.update_signaler)
        self.records_inserter = RecordInserter(config=self.config, backend=self)

        # gui_dependent_on_backend
        self.dependent_objects = set()

        # thread
        self.update_manager: UpdateManager = None

    @property
    def foreign_key_cache(self) -> ForeignKeyCache:
        return self.database.foreign_key_cache

    @property
    def app(self) -> Optional["AntistasiLogbookApplication"]:
        """
        Provides the QtApplication instance, if one exists.

        The running Qt(PySide) Application object is a Singleton(by Qt).

        convenience-method

        Returns:
            `AntistasiLogbookApplication`: The subclassed QApplication-Instance.
        """
        return QApplication.instance()

    @property
    def max_threads(self) -> int:
        max_threads = self.config.get("general", "max_threads")
        return max(self.minimum_thread_amount, max_threads)

    @property
    def thread_pool(self) -> ThreadPoolExecutor:
        """
        Provides the shared thread-pool each part of the Backend(except the `RecordInserter`) uses.

        It is shared to easily be able to limit the max amount of threads via the config.

        Max amount of Threads is 1/3 of the config provided amount

        The thread-pool is created lazily.

        Returns:
            ThreadPoolExecutor: [description]
        """
        if self._thread_pool is None:
            self._thread_pool = ThreadPoolExecutor(max_workers=max(2, self.max_threads - 3), thread_name_prefix="backend")
        return self._thread_pool

    @property
    def inserting_thread_pool(self) -> ThreadPoolExecutor:
        """
        Provides the thread-pool for usage by the `RecordInserter`.

        Is an extra ThreadPool-instance to prevent starvation.

        Max amount of Threads is 2/3 of the config provided amount

        The thread-pool is created lazily.

        Returns:
            ThreadPoolExecutor: [description]
        """
        if self._inserting_thread_pool is None:
            self._inserting_thread_pool = ThreadPoolExecutor(max_workers=3, thread_name_prefix="backend_inserting")
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
        log.debug("Created Parsing Context %r for log-file %r", context, log_file)
        return context

    def get_parser(self) -> Parser:
        parser = Parser(self, record_processor=RecordProcessor(backend=self, regex_keeper=SimpleRegexKeeper(), foreign_key_cache=self.foreign_key_cache), stop_event=self.events.stop)
        parser.record_processor.foreign_key_cache.preload_all()
        log.debug("Created Parser %r", parser)
        return parser

    def register_record_classes(self, record_classes: Iterable[RECORD_CLASS_TYPE]) -> "Backend":
        for record_class in record_classes:
            self.record_class_manager.register_record_class(record_class=record_class, database=self.database)

        return self

    def fill_record_class_manager(self) -> None:
        for record_class in chain(get_all_antistasi_record_classes(), get_all_generic_record_classes()):
            self.record_class_manager.register_record_class(record_class=record_class, database=self.database)
        self.record_class_manager._is_set_up = True
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
        self.database.foreign_key_cache.preload_all()
        self.record_class_manager = RecordClassManager(backend=self, foreign_key_cache=ForeignKeyCache(self.database))
        self.fill_record_class_manager()
        self.record_class_manager.create_record_checker()

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
        try:
            for obj in self.dependent_objects:
                obj.shutdown()
            self.events.stop.set()
            all_futures = []
            log.debug("checking if all ctx are closed")
            while len(self.all_parsing_context) > 0:
                ctx = self.all_parsing_context.pop()
                log.debug("checking ctx %r", ctx)
                open_wait_start_time = time()
                while ctx.is_open is True:
                    sleep(0.1)
                    if int(time() - open_wait_start_time) >= 5:
                        log.critical("timed out waiting for context %r to finish", ctx)
                        break
                all_futures += [i for i in ctx.futures if i.done() is False]
            log.debug("waiting for all futures to finish")
            wait(all_futures, return_when=ALL_COMPLETED, timeout=3.0)
            all_futures.clear()
            if self.update_manager is not None and self.update_manager.is_alive() is True:
                self.update_manager.shutdown()
            self.remote_manager_registry.close()
            self.updater.shutdown()
            self.records_inserter.shutdown()
            self.database.shutdown()
            self.thread_pool.shutdown(cancel_futures=True)
            self.inserting_thread_pool.shutdown(cancel_futures=True)

            gc.collect()
        except Exception as e:
            log.error(e, exc_info=True)

    def move_db(self, new_path: Path):
        # TODO: make this work consistently and not with prayers, also make one general function for moving, backup and backup-compress
        self.shutdown()
        path = self.database.database_path
        self.database.shutdown()
        shutil.move(src=path, dst=new_path)
        self.database.database = make_db_path(new_path)
        self.start_up()

    def start_update_loop(self) -> "Backend":
        if self.update_manager is None:
            self.update_manager = self.get_update_manager()
        self.update_manager.start()
        return self

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(database={self.database!r}, config={self.config!r}, update_signaler={self.update_signaler!r})"


# region[Main_Exec]
if __name__ == '__main__':
    pass
# endregion[Main_Exec]
