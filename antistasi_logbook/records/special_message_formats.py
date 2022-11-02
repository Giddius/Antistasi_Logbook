"""
WiP.

Soon.
"""

# region [Imports]

# * Standard Library Imports ---------------------------------------------------------------------------->
from typing import TYPE_CHECKING, Iterable
from pathlib import Path
from functools import partial
from collections import defaultdict

# * Third Party Imports --------------------------------------------------------------------------------->
from sortedcontainers import SortedList

# * Type-Checking Imports --------------------------------------------------------------------------------->
if TYPE_CHECKING:
    from antistasi_logbook.records.base_record import BaseRecord
    from antistasi_logbook.storage.models.models import Server, LogFile

# endregion[Imports]

# region [TODO]


# endregion [TODO]

# region [Logging]


# endregion[Logging]

# region [Constants]

THIS_FILE_DIR = Path(__file__).parent.absolute()

# endregion[Constants]


def discord_format(in_record: "BaseRecord") -> str:
    server = in_record.log_file.server
    log_file = in_record.log_file
    text = f"**__Server:__** `{server.pretty_name}`, **__Log-File:__** `{log_file.pretty_name}`, **__Lines:__** `{in_record.start}`-`{in_record.end}`\n"
    joined_lines = '\n'.join(f"<{ln}> {l}" for ln, l in in_record.log_file.original_file.get_lines_with_line_numbers(start=in_record.start, end=in_record.end))
    text += f"```sqf\n{joined_lines}\n```"
    return text


class DiscordText:
    text_template: str = "**__Server:__** `{server}`, **__Log-File:__** `{log_file}`\n```sqf\n{record_lines}\n```"

    def __init__(self, records: Iterable["BaseRecord"]) -> None:
        self.records = records

    def get_records_map(self) -> defaultdict[tuple["Server", "LogFile"], list["BaseRecord"]]:
        _out = defaultdict(partial(SortedList, key=lambda x: (x.start, x.end)))
        for record in self.records:
            _out[(record.server, record.log_file)].add(record)
        return _out

    def make_text(self) -> str:
        text = ""
        for meta_data, records in self.get_records_map().items():
            record_lines = ""
            last_record_line = None
            for record in records:
                raw_record_lines = record.log_file.original_file.get_lines_with_line_numbers(start=record.start, end=record.end)
                if last_record_line is not None and raw_record_lines[-1][0] != last_record_line + 1:
                    record_lines += '...\n'

                record_lines += '\n'.join(f"<{ln}> {l}" for ln, l in raw_record_lines) + '\n'
                last_record_line = raw_record_lines[-1][0]
            text += self.text_template.format(server=meta_data[0].pretty_name, log_file=meta_data[1].pretty_name, record_lines=record_lines.strip()) + '\n\n'
        return text.strip()

    def __str__(self) -> str:
        return self.make_text()

    def __repr__(self) -> str:
        """
        Basic Repr
        !REPLACE!
        """
        return f'{self.__class__.__name__}'

# region[Main_Exec]


if __name__ == '__main__':
    pass

# endregion[Main_Exec]
