"""
WiP.

Soon.
"""

# region [Imports]

# * Standard Library Imports ---------------------------------------------------------------------------->
from typing import TYPE_CHECKING, Any, TextIO
from pathlib import Path
from threading import Event
from time import sleep
# * Gid Imports ----------------------------------------------------------------------------------------->
from gidapptools import get_logger
from gidapptools.general_helper.timing import get_dummy_profile_decorator_in_globals
from gidapptools.general_helper.conversion import human2bytes, bytes2human
from collections import deque
from queue import Queue, LifoQueue, SimpleQueue, PriorityQueue
# * Local Imports --------------------------------------------------------------------------------------->
from antistasi_logbook.parsing.py_raw_record import RawRecord
from antistasi_logbook.parsing.meta_log_finder import MetaFinder
from antistasi_logbook.parsing.parsing_context import RecordLine, LogParsingContext
from antistasi_logbook.parsing.record_processor import RecordProcessor
from antistasi_logbook.regex_store.regex_keeper import SimpleRegexKeeper
from antistasi_logbook.utilities.paired_reader import PairedReader
# * Type-Checking Imports --------------------------------------------------------------------------------->
if TYPE_CHECKING:
    from antistasi_logbook.backend import Backend

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


class Parser:
    """
    Parses all Parsable data from the log file, the actual log_records are parsed by the `record_processor`.

    """
    log_file_data_scan_chunk_increase = 256000  # 250 kb
    log_file_data_scan_chunk_initial = 256000

    __slots__ = ("backend", "regex_keeper", "stop_event", "record_processor")

    def __init__(self, backend: "Backend", record_processor: "RecordProcessor", stop_event: Event) -> None:
        self.backend = backend
        self.regex_keeper = SimpleRegexKeeper()
        self.stop_event = stop_event
        self.record_processor = record_processor

    def _get_log_file_meta_data(self, file_item: TextIO, existing_data: dict[str, object] = None, force: bool = False) -> "MetaFinder":

        text_parts = PairedReader(file_item, max_chunks=50)
        regex_keeper = self.regex_keeper.__class__()

        finder = MetaFinder(existing_data=existing_data, regex_keeper=regex_keeper, force=force)

        while True:
            finder.search(str(text_parts))
            if finder.all_found() is True or text_parts.finished is True:
                break

            text_parts.read_next()

        log.debug("added %r parts (len: %r), bytes: %r (%r)", text_parts.chunks_read, len(text_parts), text_parts.bytes_read, bytes2human(text_parts.bytes_read))
        finder.change_missing_to_none()

        return finder

    def _parse_header_text(self, context: LogParsingContext) -> None:

        while not self.regex_keeper.only_time.match(context.current_line.content):
            context.line_cache.append(context.current_line)
            context.advance_line()
        return context.line_cache.dump()

    def _parse_startup_entries(self, context: LogParsingContext) -> None:

        while not self.regex_keeper.local_datetime.match(context.current_line.content):
            context.line_cache.append(context.current_line)
            context.advance_line()
        return context.line_cache.dump()

    def parse_entries(self, context: LogParsingContext) -> None:
        while context.current_line is not ... and not self.stop_event.is_set():
            if self.regex_keeper.local_datetime.match(context.current_line.content):
                if match := self.regex_keeper.continued_record.match(context.current_line.content):
                    context.line_cache.append(RecordLine(content=match.group('content'), start=context.current_line.start))
                    context.advance_line()
                    continue

                if context.line_cache.is_empty is False:
                    yield RawRecord(context.line_cache.dump())

            context.line_cache.append(context.current_line)
            context.advance_line()
        rest_lines = context.line_cache.dump()
        if rest_lines:

            yield RawRecord(rest_lines)

    def __call__(self, context: "LogParsingContext") -> Any:

        # if self.stop_event.is_set():
        #     return
        log.info("Parsing meta-data for %r", context._log_file)
        with context.open(cleanup=False) as file:
            context.set_found_meta_data(self._get_log_file_meta_data(file_item=file, force=context.force, existing_data=context.get_existing_meta_data()))
        if context.unparsable is True:
            log.info("Log file %r is unparseable", context._log_file)
            return
        if self.stop_event.is_set():
            return
        if context._log_file.header_text is None:
            log.info("Parsing header-text for %r", context._log_file)
            context.set_header_text(self._parse_header_text(context))

        if self.stop_event.is_set():
            return
        if context._log_file.startup_text is None:
            log.info("Parsing startup-entries for %r", context._log_file)
            context.set_startup_text(self._parse_startup_entries(context))

        if self.stop_event.is_set():
            return
        log.info("Parsing entries for %r", context._log_file)
        for raw_record in self.parse_entries(context):

            processed_record = self.record_processor(raw_record=raw_record, utc_offset=context.log_file_data["utc_offset"])
            yield processed_record


# region[Main_Exec]
if __name__ == '__main__':
    pass

# endregion[Main_Exec]
