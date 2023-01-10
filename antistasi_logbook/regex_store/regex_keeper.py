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

# endregion [Imports]

# region [TODO]


# endregion [TODO]

# region [Logging]


# endregion [Logging]

# region [Constants]

THIS_FILE_DIR = Path(__file__).parent.absolute()

# endregion [Constants]

ONLY_TIME = re.compile(r"[1-2\s]\d\:[0-6]\d\:[0-6]\d(?=\s)")

LOCAL_DATETIME = re.compile(r"\d{4}/[01]\d/[0-3]\d\,\s+[0-2]*\d\:[0-6]\d\:[0-6]\d(?=\s)")

CONTINUED_RECORD = re.compile(r"\d{4}/[01]\d/[0-3]\d\,\s[0-2]\d\:[0-6]\d\:[0-6]\d" + r"\s+(?P<content>\>{3}\s*.*)")

GENERIC_RECORD = re.compile(r"""(?P<year>\d{4})/(?P<month>[01]\d)/(?P<day>[0-3]\d)\,\s+(?P<hour>[0-2]*\d)\:(?P<minute>[0-6]\d)\:(?P<second>[0-6]\d)\s(?P<message>.*)""")

FULL_DATETIME = re.compile(r"""\d{4}/[01]\d/[0-3]\d\,\s+[0-2]*\d\:[0-6]\d\:[0-6]\d
                                \s
                                (?P<year>\d{4})\-(?P<month>[01]\d)\-(?P<day>[0-3]\d)
                                \s
                                (?P<hour>[0-2]\d)\:(?P<minute>[0-6]\d)\:(?P<second>[0-6]\d)\:(?P<microsecond>\d{3})
                                \s""", re.VERBOSE)

CALLED_BY = re.compile(r"(.*)(?:\s\|\s*Called\sBy\:\s*)([^\s\|]+)(.*)")

GAME_MAP = re.compile(r"\sMission world\:\s*(?P<game_map>.*)")

GAME_FILE = re.compile(r"\s+Mission file\:\s*(?P<game_file>.*)")

VERSION = re.compile(r"\s*((MP server version)|(Server version)):\s*(?P<version>.*?)(?=\s|$)")

CAMPAIGN_ID = re.compile(r"((?P<text_loading>(Loading last campaign ID)|(Loading campaign with ID))|(?P<text_creating>Creating new campaign with ID))\s*(?P<campaign_id>\d+)")


MOD_START_INDICATOR = re.compile(r"\=+\sList\sof\smods\s\=+")

MOD_END_INDICATOR = re.compile(r"\={25,}")

MODS = re.compile(r"""^([0-2\s]?\d)
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

MOD_TIME_STRIP = re.compile(r"""^([0-2\s]?\d)
                                                    [^\d]
                                                    ([0-6]\d)
                                                    [^\d]
                                                    ([0-6]\d)""", re.VERBOSE)
FIRST_FULL_DATETIME = re.compile(r"""^
                                    (?P<local_year>\d{4})
                                    /
                                    (?P<local_month>[01]\d)
                                    /
                                    (?P<local_day>[0-3]\d)
                                    \,\s+
                                    (?P<local_hour>[0-2]*\d)
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

FAULT_ERROR_START = re.compile(r"\s*\=*\s*\-*\s*Exception code\:.*", re.DOTALL)


class SimpleRegexKeeper:
    """
    Stores all compiled Regexes for parsing.

    Info:
        The reason for this being a class, is so different regex-pattern collections can be used dynamically.

        The reason for copying each regex is for possible multiprocessing (unknown if needed but does not add to much overhead anyway)

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
                 "mod_end_indicator",
                 "alternative_campaign_id")

    def __init__(self) -> None:

        self.only_time = ONLY_TIME.__copy__()

        self.local_datetime = LOCAL_DATETIME.__copy__()

        self.continued_record = CONTINUED_RECORD.__copy__()

        self.generic_record = GENERIC_RECORD.__copy__()

        self.full_datetime = FULL_DATETIME.__copy__()

        self.called_by = CALLED_BY.__copy__()

        self.game_map = GAME_MAP.__copy__()

        self.game_file = GAME_FILE.__copy__()

        self.version = VERSION.__copy__()

        self.campaign_id = CAMPAIGN_ID.__copy__()

        self.mod_start_indicator = MOD_START_INDICATOR.__copy__()

        self.mod_end_indicator = MOD_END_INDICATOR.__copy__()

        self.mods = MODS.__copy__()

        self.mod_time_strip = MOD_TIME_STRIP.__copy__()

        self.first_full_datetime = FIRST_FULL_DATETIME.__copy__()

        self.fault_error_start = FAULT_ERROR_START.__copy__()


# region [Main_Exec]
if __name__ == '__main__':
    pass
# endregion [Main_Exec]
