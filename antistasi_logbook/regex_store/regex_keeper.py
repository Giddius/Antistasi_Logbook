"""
WiP.

Soon.
"""

# region [Imports]

# * Standard Library Imports ---------------------------------------------------------------------------->
import re
from typing import TYPE_CHECKING
from pathlib import Path

# * Type-Checking Imports --------------------------------------------------------------------------------->
if TYPE_CHECKING:
    pass

# endregion[Imports]

# region [TODO]


# endregion [TODO]

# region [Logging]


# endregion[Logging]

# region [Constants]

THIS_FILE_DIR = Path(__file__).parent.absolute()

# endregion[Constants]


class SimpleRegexKeeper:
    """
    Stores all compiled Regexes for parsing.

    """

    __slots__ = ("only_time",
                 "version",
                 "local_datetime",
                 "continued_record",
                 "generic_record",
                 "full_datetime",
                 "called_by",
                 "game_map",
                 "game_file",
                 "mods",
                 "mod_time_strip",
                 "campaign_id",
                 "first_full_datetime",
                 "fault_error_start",
                 "mod_start_indicator",
                 "mod_end_indicator")

    def __init__(self) -> None:

        self.only_time = re.compile(r"[1-2\s]\d\:[0-6]\d\:[0-6]\d(?=\s)")

        self.local_datetime = re.compile(r"\d{4}/[01]\d/[0-3]\d\,\s[0-2]\d\:[0-6]\d\:[0-6]\d(?=\s)")

        self.continued_record = re.compile(r"\d{4}/[01]\d/[0-3]\d\,\s[0-2]\d\:[0-6]\d\:[0-6]\d" + r"\s+(?P<content>\>{3}\s*.*)")

        self.generic_record = re.compile(r"""(?P<year>\d{4})/(?P<month>[01]\d)/(?P<day>[0-3]\d)\,\s(?P<hour>[0-2]\d)\:(?P<minute>[0-6]\d)\:(?P<second>[0-6]\d)\s(?P<message>.*)""")

        self.full_datetime = re.compile(r"\d{4}/[01]\d/[0-3]\d\,\s[0-2]\d\:[0-6]\d\:[0-6]\d\s(?P<year>\d{4})\-(?P<month>[01]\d)\-(?P<day>[0-3]\d)\s(?P<hour>[0-2]\d)\:(?P<minute>[0-6]\d)\:(?P<second>[0-6]\d)\:(?P<microsecond>\d{3})\s")

        self.called_by = re.compile(r"(.*)(?:\s\|\s*Called\sBy\:\s*)([^\s\|]+)(.*)")

        self.game_map = re.compile(r"\sMission world\:\s*(?P<game_map>.*)")
        self.game_file = re.compile(r"\s+Mission file\:\s*(?P<game_file>.*)")
        self.version = re.compile(r"\s*MP server version:\s*(?P<version>.*)")
        self.campaign_id = re.compile(r"((?P<text_loading>Loading last campaign ID)|(?P<text_creating>Creating new campaign with ID))\s*(?P<campaign_id>\d+)")
        self.mod_start_indicator = re.compile(r"\=+\sList\sof\smods\s\=+")
        self.mod_end_indicator = re.compile(r"\={25,}")
        self.mods = re.compile(r"""^([0-2\s]?\d)
                                          [^\d]
                                          ([0-6]\d)
                                          [^\d]
                                          ([0-6]\d)
                                          \s?\={25,}\sList\sof\smods\s\={25,}
                                          \n
                                          (?P<mod_lines>(^([0-2\s]?\d)
                                                          [^\d]
                                                          ([0-6]\d)
                                                          [^\d]
                                                          ([0-6]\d)
                                                          \s(?!\=).*\n)
                                                          +
                                          )
                                          ^([0-2\s]?\d)
                                          [^\d]
                                          ([0-6]\d)
                                          [^\d]
                                          ([0-6]\d)
                                          \s?\={25,}""", re.VERBOSE | re.MULTILINE)

        self.mod_time_strip = re.compile(r"""^([0-2\s]?\d)
                                                    [^\d]
                                                    ([0-6]\d)
                                                    [^\d]
                                                    ([0-6]\d)""", re.VERBOSE)
        self.first_full_datetime = re.compile(r"""^
                                         (?P<local_year>\d{4})
                                         /
                                         (?P<local_month>[01]\d)
                                         /
                                         (?P<local_day>[0-3]\d)
                                         \,\s+
                                         (?P<local_hour>[0-2]\d)
                                         \:
                                         (?P<local_minute>[0-6]\d)
                                         \:
                                         (?P<local_second>[0-6]\d)
                                         \s
                                         (?P<year>\d{4})
                                         \-
                                         (?P<month>[01]\d)
                                         \-
                                         (?P<day>[0-3]\d)
                                         \s
                                         (?P<hour>[0-2]\d)
                                         \:
                                         (?P<minute>[0-6]\d)
                                         \:
                                         (?P<second>[0-6]\d)
                                         \:
                                         (?P<microsecond>\d{3})
                                         (?=\s)""", re.VERBOSE | re.MULTILINE)

        self.fault_error_start = re.compile(r"\s*\=*\s*\-*\s*Exception code\:.*", re.DOTALL)


# region[Main_Exec]
if __name__ == '__main__':
    pass
# endregion[Main_Exec]
