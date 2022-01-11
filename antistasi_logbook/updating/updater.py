"""
WiP.

Soon.
"""

# region [Imports]

# * Standard Library Imports ---------------------------------------------------------------------------->
import queue
import random
from time import sleep
from typing import TYPE_CHECKING, Any, Callable, Optional
from pathlib import Path
from datetime import datetime, timezone
from threading import Event
from concurrent.futures import ALL_COMPLETED, ThreadPoolExecutor, wait

# * Third Party Imports --------------------------------------------------------------------------------->
from dateutil.tz import UTC
from antistasi_logbook.storage.models.models import Server, LogFile, LogRecord, RecordClass
from antistasi_logbook.updating.remote_managers import remote_manager_registry

# * Gid Imports ----------------------------------------------------------------------------------------->
from gidapptools import get_logger
from gidapptools.gid_signal.interface import get_signal

if TYPE_CHECKING:
    # * Third Party Imports --------------------------------------------------------------------------------->
    from antistasi_logbook.gui.misc import UpdaterSignaler
    from antistasi_logbook.backend import Backend
    from antistasi_logbook.storage.database import GidSqliteApswDatabase
    from antistasi_logbook.updating.info_item import InfoItem
    from antistasi_logbook.parsing.parsing_context import LogParsingContext

    # * Gid Imports ----------------------------------------------------------------------------------------->
    from gidapptools.gid_config.interface import GidIniConfig

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


class Updater:
    """
    Class to run updates of log_files from the remote drive.

    """
    config_name: str = "updating"
    thread_prefix: str = "updating_threads"
    new_log_file_signal = get_signal("new_log_file")
    updated_log_file_signal = get_signal("updated_log_file")

    is_updating_event: Event = Event()

    __slots__ = ("backend", "stop_event", "pause_event", "_to_close_contexts", "signaler")

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
    def parser(self):
        return self.backend.parser

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
        return self.config.get(self.config_name, "remove_items_older_than_max_update_time_frame", default=False)

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
        new_log_file = LogFile(server=server, **remote_info.as_dict())
        new_log_file.save()
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
        cutoff_datetime = self.get_cutoff_datetime()

        for remote_info in server.get_remote_files():
            if cutoff_datetime is not None and remote_info.modified_at < cutoff_datetime:
                continue
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
        for log_file in server.log_files.select().where(LogFile.modified_at < cutoff_datetime):
            log.info("removing log-file %r of server %r", log_file, server)

            log_file.delete_instance(True)
            amount_deleted += 1
        return amount_deleted

    def process(self, server: "Server") -> None:

        def _do(_log_file: "LogFile"):
            sleep(random.uniform(0.1, 2.0))
            self.signaler.send_update_increment()
            if self.stop_event.is_set() is False:
                context = self.parsing_context_factory(log_file=_log_file)
                context.done_signal = self.signaler.send_update_increment
                with context:

                    log.debug("starting to parse %s", _log_file)
                    for processed_record in self.parser(context=context):
                        if self.stop_event.is_set() is True:
                            break
                        context.insert_record(processed_record)
                    context._dump_rest()

        tasks = []
        to_update_log_files = self._get_updated_log_files(server=server)
        self.signaler.send_update_info(len(to_update_log_files) * 3, server.name)
        for log_file in to_update_log_files:
            if self.stop_event.is_set() is False:
                sub_task = self.thread_pool.submit(_do, _log_file=log_file)
                tasks.append(sub_task)

        wait(tasks, return_when=ALL_COMPLETED, timeout=None)

    @profile
    def update_record_classes(self, server: Server = None, force: bool = False):

        def _find_record_class(_record: "LogRecord") -> tuple["LogRecord", "RecordClass"]:
            _record_class = self.database.record_processor.determine_record_class(_record)
            return _record, _record_class

        log.info("updating record classes")
        # batch_size = (32767 // 2) - 1
        batch_size = 100_000
        tasks = []
        to_update = []

        for record, record_class in self.thread_pool.map(_find_record_class, self.database.iter_all_records(server=server, only_missing_record_class=not force)):

            if record.record_class_id == record_class.id:
                continue

            to_update.append((record_class.id, record.id))
            if len(to_update) == batch_size:
                log.debug("updating %r records with their record class", len(to_update))
                task = self.database.record_inserter.many_update_record_class(list(to_update))
                tasks.append(task)

                to_update.clear()
        if len(to_update) > 0:
            log.debug("updating %r records with their record class", len(to_update))
            task = self.database.record_inserter.many_update_record_class(list(to_update))
            tasks.append(task)
            to_update.clear()
        wait(tasks, return_when=ALL_COMPLETED)

    def before_updates(self):
        log.debug("emiting before_updates_signal")
        self.signaler.send_update_started()

    def after_updates(self):
        log.debug("emiting after_updates_signal")
        self.signaler.send_update_finished()
        remote_manager_registry.close()

    def update(self) -> None:

        if self.is_updating_event.is_set() is True:
            return
        self.is_updating_event.set()
        self.before_updates()
        tasks = []
        try:

            self.database.session_meta_data.last_update_started_at = datetime.now(tz=timezone.utc)
            for server in self.database.get_all_server():
                if server.is_updatable() is False:
                    continue
                if self.stop_event.is_set() is False:

                    while self.pause_event.is_set() is True:
                        sleep(0.25)
                    log.info("STARTED updating %r", server)
                    self.process(server=server)
                    tasks.append(self.thread_pool.submit(self.update_record_classes, server=server))
                    log.info("FINISHED updating server %r", server)

            log.debug("waiting for %r tasks to finish", len(tasks))
            wait(tasks, return_when=ALL_COMPLETED)

            log.debug("All record class update tasks have finished")
            amount_deleted = 0
            for server in self.database.get_all_server():
                if server.is_updatable() is False:
                    continue
                if self.stop_event.is_set() is False:
                    log.info("checking old log_files to delete for server %r", server)
                    amount_deleted += self._handle_old_log_files(server=server)

            if amount_deleted > 0:
                if self.stop_event.is_set() is False:
                    self.database.vacuum()
                    self.database.optimize()

            self.database.session_meta_data.last_update_finished_at = datetime.now(tz=timezone.utc)

        finally:
            self.is_updating_event.clear()
            self.after_updates()

    def __call__(self) -> Any:
        return self.update()

    def shutdown(self) -> None:
        pass


# region[Main_Exec]
if __name__ == '__main__':
    pass

# endregion[Main_Exec]
