"""
WiP.

Soon.
"""

# region [Imports]

# * Standard Library Imports ---------------------------------------------------------------------------->
import queue
import apsw
import random
from time import sleep, perf_counter, perf_counter_ns
from typing import TYPE_CHECKING, Any, Optional, Generator, Iterator, Iterable
from pathlib import Path
from datetime import datetime
from threading import Event, Lock, RLock
from collections import defaultdict
from concurrent.futures import ALL_COMPLETED, ThreadPoolExecutor, wait, Future, FIRST_EXCEPTION
import math
import gc
# * Third Party Imports --------------------------------------------------------------------------------->
from dateutil.tz import UTC

# * Gid Imports ----------------------------------------------------------------------------------------->
from gidapptools import get_logger
from gidapptools.gid_signal.interface import get_signal
from gidapptools.general_helper.conversion import number_to_pretty, ns_to_s, human2bytes, bytes2human

# * Local Imports --------------------------------------------------------------------------------------->
from antistasi_logbook.storage.models.models import Server, LogFile, LogRecord, RecordClass, OriginalLogFile, Mod, LogFileAndModJoin, MeanUpdateTimePerLogFile
from antistasi_logbook.updating.remote_managers import remote_manager_registry
from gidapptools.general_helper.timing import get_dummy_profile_decorator_in_globals

# * Type-Checking Imports --------------------------------------------------------------------------------->
if TYPE_CHECKING:
    from antistasi_logbook.backend import Backend
    from antistasi_logbook.gui.misc import UpdaterSignaler
    from antistasi_logbook.storage.database import GidSqliteApswDatabase
    from antistasi_logbook.updating.info_item import InfoItem

# endregion[Imports]

# region [TODO]

# TODO: Refractor whole class

# endregion [TODO]

# region [Logging]


# endregion[Logging]

# region [Constants]

get_dummy_profile_decorator_in_globals()
THIS_FILE_DIR = Path(__file__).parent.absolute()
log = get_logger(__name__)


# FIX THIS ASAP "THESE LOG FILES JUST GET MARKED AS TO UPDATED OVER AND OVER"
HARD_BANNED_LOG_FILES: defaultdict[str, list[str]] = defaultdict(list)
HARD_BANNED_LOG_FILES["testserver_1"].append("arma3server_x64_2022-07-24_11-22-56")
HARD_BANNED_LOG_FILES["testserver_2"].append("arma3server_x64_2022-07-24_11-22-56")
HARD_BANNED_LOG_FILES["mainserver_2"].append("arma3server_x64_2022-09-11_13-08-37")
HARD_BANNED_LOG_FILES["mainserver_1"].append("arma3server_x64_2022-09-11_13-08-37")


# endregion[Constants]


class ThreadSafeCounter:
    __slots__ = ("initial_number", "_value", "_lock")

    def __init__(self, initial_number: int = 0) -> None:
        self.initial_number = initial_number
        self._value = self.initial_number
        self._lock = Lock()

    @property
    def value(self) -> int:
        with self._lock:
            return self._value

    def increment(self, amount: int = 1):
        with self._lock:
            self._value += amount

    def reset(self):
        with self._lock:
            self._value = self.initial_number

    def __str__(self) -> str:
        with self._lock:
            return str(self.value)


class Updater:
    """
    Class to run updates of log_files from the remote drive.

    """
    config_name: str = "updating"
    thread_prefix: str = "updating_threads"
    new_log_file_signal = get_signal("new_log_file")
    updated_log_file_signal = get_signal("updated_log_file")

    is_updating_event: Event = Event()

    __slots__ = ("backend", "stop_event", "pause_event", "_to_close_contexts", "signaler", "record_class_updated_counter")

    def __init__(self,
                 backend: "Backend",
                 stop_event: Event,
                 pause_event: Event,
                 signaler: "UpdaterSignaler" = None) -> None:

        self.backend = backend

        self.stop_event = stop_event
        self.pause_event = pause_event

        self._to_close_contexts = queue.Queue()
        self.signaler = signaler
        self.record_class_updated_counter: ThreadSafeCounter = None

    @property
    def config(self):
        return self.backend.config

    @property
    def parsing_context_factory(self):
        return self.backend.get_parsing_context

    @property
    def database(self) -> "GidSqliteApswDatabase":
        return self.backend.database

    @property
    def thread_pool(self) -> ThreadPoolExecutor:
        return self.backend.thread_pool

    @property
    def max_threads(self) -> int:
        """
        Max amount of threads the thread_pool is allowed to use.

        Currently only has an effect when started.

        Returns:
            int: max amount of threads.
        """
        return self.config.get(self.config_name, "max_updating_threads", default=5)

    @property
    def remove_items_older_than_max_update_time_frame(self) -> bool:
        """
        If log-files that are older than the max update time-frame should be removed from the db.

        If no max_update_time_frame is set, then this is ignored.

        """
        if self.get_cutoff_datetime() is None:
            return False
        return self.config.get(self.config_name, "remove_items_older_than_max_update_time_frame")

    def get_cutoff_datetime(self) -> Optional[datetime]:
        """
        The max_update_time_frame converted to an absolute aware-datetime.

        Uses UTC as timezone.

        If no max_update_time_frame is set, None is returned.

        """
        delta = self.config.get(self.config_name, "max_update_time_frame", default=None)
        if delta is None:
            return None
        return datetime.now(tz=UTC) - delta

    def _create_new_log_file(self, server: "Server", remote_info: "InfoItem") -> LogFile:
        """
        Helper method to create a new `LogFile` instance.

        The new log_file is saved to the database.

        Args:
            server (Server): the `Server`-model instance the log_file belongs to.
            remote_info (InfoItem): The info_item that is received from the `RemoteStorageManager` implementation.

        Returns:
            LogFile: a new instance of the `LogFile`-model
        """
        info_dict = remote_info.as_dict()
        del info_dict["raw_info"]
        del info_dict["content_language"]
        del info_dict["content_type"]
        del info_dict["display_name"]
        del info_dict["type"]
        del info_dict["etag"]

        new_log_file = LogFile(server=server, **info_dict)
        new_log_file.save()
        _ = new_log_file.has_mods

        self.new_log_file_signal.emit(log_file=new_log_file)
        return new_log_file

    def _update_log_file(self, log_file: LogFile, remote_info: "InfoItem") -> LogFile:
        """
        Helper Method to update an existing `LogFile`-model instance, from remote_info.

        The log_file is not updated to the database at that point.

        Args:
            log_file (LogFile): the existing `LogFile`-model instance
            remote_info (InfoItem): The info_item that is received from the `RemoteStorageManager` implementation.

        Returns:
            LogFile: the updated `logFile`-instance.
        """
        log_file.modified_at = remote_info.modified_at
        log_file.size = remote_info.size
        _ = log_file.has_mods
        self.updated_log_file_signal.emit(log_file=log_file)
        return log_file

    def _get_updated_log_files(self, server: "Server"):
        """
        [summary]

        [extended_summary]

        Args:
            server (Server): [description]

        Returns:
            [type]: [description]
        """
        to_update_files = []

        current_log_files = {log_file.name: log_file for log_file in self.database.get_log_files(server=server)}
        for l in current_log_files.values():
            _ = l.has_mods
            l.server = server
        cutoff_datetime = self.get_cutoff_datetime()
        log.debug("cutoff_datetime: %r", cutoff_datetime)

        for remote_info in server.get_remote_files():
            if cutoff_datetime is not None and remote_info.modified_at < cutoff_datetime:
                continue
            # if remote_info.name in HARD_BANNED_LOG_FILES[server.name.casefold()]:
            #     continue
            stored_file: LogFile = current_log_files.get(remote_info.name, None)

            if stored_file is None:

                to_update_files.append(self._create_new_log_file(server=server, remote_info=remote_info))

            elif stored_file.modified_at < remote_info.modified_at or stored_file.size < remote_info.size:

                to_update_files.append(self._update_log_file(log_file=stored_file, remote_info=remote_info))

            elif stored_file.last_parsed_datetime != stored_file.modified_at and stored_file.unparsable is False:

                to_update_files.append(stored_file)

        return sorted(to_update_files, key=lambda x: x.modified_at, reverse=True)

    def _handle_old_log_files(self, server: "Server") -> None:
        if self.remove_items_older_than_max_update_time_frame is False:
            return 0
        cutoff_datetime = self.get_cutoff_datetime()
        if cutoff_datetime is None:
            return 0
        amount_deleted = 0
        tasks = []
        idx = 0
        to_delete = tuple(LogFile.select().where((LogFile.server_id == server.id) & (LogFile.modified_at < cutoff_datetime)).iterator())

        for log_file in to_delete:
            try:
                log.info("removing log-file %r of server %r", log_file, server)

                if log_file.original_file is not None:
                    # tasks.append(self.backend.inserting_thread_pool.submit(log_file.original_file.delete_instance, True))
                    log_file.original_file.delete_instance(True, True)
                # tasks.append(self.backend.inserting_thread_pool.submit(log_file.delete_instance, True))

                log_file.delete_instance(True, True)
                idx += 1

                if idx % 10 == 0:
                    self.backend.inserting_thread_pool.submit(self.database.checkpoint).result()
            except Exception as e:
                log.error(e, exc_info=True)
            # sleep(0.5)
            # amount_deleted += 1
            # if amount_deleted % 10 == 0:
            #     self.database.checkpoint()
            # tasks.append(self.backend.inserting_thread_pool.submit(self.database.checkpoint))
        # self.database.checkpoint()
        wait(tasks, return_when=ALL_COMPLETED)
        return amount_deleted

    def process_log_file(self, log_file: "LogFile", force: bool = False) -> None:
        if force is True:
            log_file.last_parsed_line_number = 0
            log_file.last_parsed_datetime = None
            log_file.version = None
            log_file.utc_offset = None
            log_file.is_new_campaign = None
            log_file.campaign_id = None
            log_file.game_map = None
            log_file.startup_text = None
            log_file.header_text = None
            log_file.max_mem = None
            log_file.is_downloaded = True
            drop_query = LogRecord.delete().where(LogRecord.log_file_id == log_file.id)
            with self.database:
                drop_query.execute()
        context = self.parsing_context_factory(log_file=log_file)
        parser = self.backend.get_parser()
        if force is True:
            context.force = True
        context.done_signal = self.signaler.send_update_increment
        context.log_file_done_signal = self.signaler.send_log_file_finished
        with context:

            log.debug("starting to parse %s", log_file)
            for processed_record in parser(context=context):
                if self.stop_event.is_set() is True:
                    break
                context.insert_record(processed_record)
            context._dump_rest()
        # gc.collect()

    def process(self, server: "Server") -> None:
        log.debug("processing server %r", server)
        tasks = []
        to_update_log_files = self._get_updated_log_files(server=server)
        self.signaler.send_update_info(len(to_update_log_files) * 2, server.name)
        for log_file in to_update_log_files:
            if self.stop_event.is_set() is False:

                sub_task = self.thread_pool.submit(self.process_log_file, log_file=log_file)

                tasks.append(sub_task)
                sleep(random.randint(0, 2) + random.random())

        wait(tasks, return_when=ALL_COMPLETED, timeout=None)

        return len(to_update_log_files)

    def emit_change_update_text(self, text):
        self.signaler.change_update_text.emit(text)

    def emit_amount_record_classes_updated(self, old_amount: int, amount: int, full_amount: int):

        def _do_emit(in_old_amount, in_amount, in_full_amount):
            _amount = in_amount - in_old_amount
            _amount = int(_amount / 10) * 10
            if self.record_class_updated_counter is not None:
                self.record_class_updated_counter.increment(_amount)
                self.signaler.change_update_text.emit(f"Updating Record-Classes --- Checked {self.record_class_updated_counter.value:,} of {in_full_amount:,} Records")
                # self.signaler.send_update_increment(in_amount - in_old_amount)
        _do_emit(old_amount, amount, full_amount)

    def _update_record_classes(self, server: Server = None, log_file: LogFile = None, force: bool = False):

        log.info("updating record classes, Server: %r, LogFile: %r, force: %r", server, log_file, force)
        # batch_size = (32767 // 2) - 1
        batch_size = 5_000
        if log_file is not None:
            batch_size = batch_size

        # report_size = max(round(report_size / 1_000) * 1_000, 1_000)
        report_size = 5_000

        tasks = []
        to_update = []
        old_idx = 0
        idx = 0
        amount_updated_record_classes = 0
        self.backend.record_class_manager.create_record_checker()
        full_amount = self.database.get_amount_iter_all_records(server=server, log_file=log_file, only_missing_record_class=not force)
        log.debug("amount of log-records to check: %r", full_amount)
        if full_amount <= 0:
            return
        # if force is True:
        #     self.signaler.send_update_record_classes_started()
        #     self.signaler.send_update_info(full_amount, f"Updating Record-Classes, to update: {full_amount!r}")
        records_gen = self.database.iter_all_records(server=server, log_file=log_file, only_missing_record_class=not force)

        record_class_determiner = self.backend.record_class_manager.record_class_checker._determine_record_class
        task_creator = self.database.record_inserter.update_record_class
        for record in records_gen:
            record_class = record_class_determiner(record)
            idx += 1

            if idx % report_size == 0:

                if force is True:
                    self.emit_amount_record_classes_updated(old_idx, idx, full_amount)
                    old_idx = idx

            if record.record_class_id is None or record.record_class_id != record_class.id:
                # TODO: make both take the argument in the same order
                task = task_creator(log_record_id=int(record.id), record_class_id=int(record_class.id))
                tasks.append(task)
                amount_updated_record_classes += 1
                if amount_updated_record_classes % 1000 == 0:
                    log.info("already updated %r record classes", amount_updated_record_classes)
                # to_update.append((int(record_class.id), int(record.id)))
                # if len(to_update) >= batch_size:
                #     log.debug("updating %s records with their record class", number_to_pretty(len(to_update)))

                #     task = self.database.record_inserter.many_update_record_class(tuple(to_update))
                #     to_update.clear()
                #     tasks.append(task)
                #     sleep(0.01)

        if len(to_update) > 0:
            log.debug("updating %s records with their record class", number_to_pretty(len(to_update)))
            task = task_creator(list(to_update))
            tasks.append(task)
            to_update.clear()
            sleep(0.01)
        done, not_done = wait(tasks, return_when=FIRST_EXCEPTION)
        if not_done:
            for f in done:
                exception = f.exception()
                if exception is not None:
                    log.error(exception)
        running_tasks = [fu for fu in tasks if fu.done() is False]
        old_len = len(running_tasks)
        while running_tasks:
            if len(running_tasks) < old_len:
                log.info("waiting for %s tasks to finish", number_to_pretty(len(running_tasks)))

            else:
                sleep(0.1)
            old_len = len(running_tasks)
            running_tasks = [fu for fu in tasks if fu.done() is False]

        log.info("finished updating record classes server: %r, log_file: %r, force: %r", server, log_file, force)
        log.info("updated %r record classes", amount_updated_record_classes)
        if force is True:
            self.emit_change_update_text("")
            # self.signaler.send_update_record_classes_finished()

    def before_updates(self):
        self.backend.record_class_manager.create_record_checker()
        self.database.checkpoint()
        log.debug("emiting before_updates_signal")
        self.signaler.send_update_started()

    def after_updates(self):
        log.debug("emiting after_updates_signal")
        self.database.resolve_all_armafunction_extras()
        self.signaler.send_update_finished()
        remote_manager_registry.close()
        self.database.close()

    def update(self) -> None:

        if self.is_updating_event.is_set() is True:
            log.info("update already running, returning!")
            return None, None

        update_start_time = perf_counter_ns()
        self.is_updating_event.set()
        self.before_updates()
        amount_log_files_updated = 0
        update_tasks = []
        try:

            self.database.session_meta_data.update_started()
            for server in self.database.get_all_server():
                if server.is_updatable() is False:
                    continue
                if self.stop_event.is_set() is False:

                    while self.pause_event.is_set() is True:
                        sleep(0.25)
                    log.info("STARTED updating %r", server)
                    new_amount_updated = self.process(server=server)
                    amount_log_files_updated += new_amount_updated
                    # log.debug("released %r amount of DB-memory", bytes2human(apsw.releasememory(1000)))
                    # update_tasks.append(self.backend.thread_pool.submit(self._update_record_classes, server=server))
                    log.info("FINISHED updating server %r", server)
                    update_tasks.append(self.backend.inserting_thread_pool.submit(self.database.checkpoint))
            wait(update_tasks, return_when=ALL_COMPLETED)
            log.debug("All record class update tasks have finished")
            del_tasks = []
            amount_deleted = 0
            for server in self.database.get_all_server():
                if server.is_updatable() is False:
                    continue
                if self.stop_event.is_set() is False:
                    log.info("checking old log_files to delete for server %r", server)
                    del_tasks.append(self.thread_pool.submit(self._handle_old_log_files, server=server))

            wait(del_tasks, return_when=ALL_COMPLETED)

            self.database.session_meta_data.update_finished()
            self.thread_pool.submit(LogFile.refresh_dynamic_for_all_log_files)
        finally:
            self.is_updating_event.clear()
            self.after_updates()
        update_finish_time = perf_counter_ns()
        update_time_taken = ns_to_s(update_finish_time - update_start_time, 3)
        if amount_log_files_updated > 0:
            time_per_log_file = ns_to_s((update_finish_time - update_start_time) / amount_log_files_updated)
            MeanUpdateTimePerLogFile.insert_new_measurement(time_taken_per_log_file=time_per_log_file, amount_updated=amount_log_files_updated)
        else:
            time_per_log_file = 0
        log.info("The update took %r s for %r updated log-files and %r deleted log-files -> %r s per updated log-file", update_time_taken, amount_log_files_updated, amount_deleted, round(time_per_log_file, ndigits=3))
        return amount_log_files_updated, amount_deleted

    def update_all_record_classes(self):
        if self.is_updating_event.is_set():
            log.info("update already running, returning!")
            return
        self.is_updating_event.set()
        try:
            self.record_class_updated_counter = ThreadSafeCounter()
            self._update_record_classes(force=True)
        finally:
            self.is_updating_event.clear()
            self.record_class_updated_counter = None

    def only_update_record_classes(self, server: Server = None, force: bool = False):
        if self.is_updating_event.is_set():
            log.info("update already running, returning!")
            return
        self.is_updating_event.set()
        try:
            self._update_record_classes(server=server, force=force)
        finally:
            self.is_updating_event.clear()

    def __call__(self) -> Any:
        return self.update()

    def shutdown(self) -> None:
        pass


# region[Main_Exec]
if __name__ == '__main__':
    pass

# endregion[Main_Exec]
