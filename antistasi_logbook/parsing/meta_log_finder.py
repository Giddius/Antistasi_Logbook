"""
WiP.

Soon.
"""

# region [Imports]

# * Standard Library Imports ---------------------------------------------------------------------------->
from typing import TYPE_CHECKING, Union, TypedDict, TextIO
from pathlib import Path
from datetime import datetime, timezone, timedelta
from collections import namedtuple
from dateutil.tz import UTC, tzoffset
# * Third Party Imports --------------------------------------------------------------------------------->
from dateutil.tz import UTC
import re
import sys
# * Gid Imports ----------------------------------------------------------------------------------------->
from gidapptools import get_logger
from gidapptools.general_helper.enums import MiscEnum
from gidapptools.general_helper.conversion import str_to_bool
from gidapptools.general_helper.date_time import calculate_utc_offset
from gidapptools.general_helper.timing import get_dummy_profile_decorator_in_globals
from antistasi_logbook.regex_store.regex_keeper import SimpleRegexKeeper
from antistasi_logbook.utilities.paired_reader import PairedReader
# * Local Imports --------------------------------------------------------------------------------------->
from antistasi_logbook.utilities.misc import ModItem, VersionItem
# * Type-Checking Imports --------------------------------------------------------------------------------->
if TYPE_CHECKING:
    from antistasi_logbook.parsing.parsing_context import ParsingContext
if sys.version_info >= (3, 11):
    from typing import Self
else:
    from typing_extensions import Self

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


class RawModData(TypedDict):
    name: str
    mod_dir: str
    default: bool
    official: bool
    origin: str
    mod_hash: Union[str, None]
    mod_hash_short: Union[str, None]
    full_path: Union[Path, None]


def parse_mod_line(in_line: str) -> RawModData:

    def strip_converter(in_string: Union[str, None]) -> Union[str, None]:
        if in_string is None:
            return None
        new_string = in_string.strip()
        if new_string == "":
            return None
        return new_string

    def strip_to_path(data: Union[str, None]) -> Union[Path, None]:
        data = strip_converter(data)
        if data in (None, ""):
            return None
        return Path(data)

    parts = in_line.split('|')
    name, mod_dir, default, official, origin = parts[:5]
    try:
        mod_hash = strip_converter(parts[5])
    except IndexError:
        mod_hash = None

    try:
        mod_hash_short = strip_converter(parts[6])
    except IndexError:
        mod_hash_short = None

    try:
        full_path = strip_to_path(parts[7])
    except IndexError:
        full_path = None

    return RawModData(name=strip_converter(name),
                      mod_dir=strip_converter(mod_dir),
                      default=str_to_bool(default),
                      official=str_to_bool(official),
                      origin=strip_converter(origin),
                      mod_hash=mod_hash, mod_hash_short=mod_hash_short,
                      full_path=full_path)


class MetaFinder:

    __slots__ = ["game_map",
                 "utc_offset",
                 "version",
                 "mods",
                 "campaign_id",
                 "is_new_campaign",
                 "regex_keeper"]

    def __init__(self, regex_keeper: "SimpleRegexKeeper" = None, existing_data: dict[str, object] = None, force: bool = False) -> None:
        self.regex_keeper = regex_keeper or SimpleRegexKeeper()

        if force is True or existing_data is None:
            self.game_map: str = MiscEnum.NOT_FOUND
            self.utc_offset: tzoffset = MiscEnum.NOT_FOUND
            self.version: VersionItem = MiscEnum.NOT_FOUND
            self.mods: list[RawModData] = MiscEnum.NOT_FOUND
            self.campaign_id: int = MiscEnum.NOT_FOUND
            self.is_new_campaign: bool = MiscEnum.NOT_FOUND
        else:
            self.game_map: str = MiscEnum.NOT_FOUND if existing_data.get("has_game_map", False) is False else MiscEnum.DEFAULT
            self.utc_offset: tzoffset = MiscEnum.NOT_FOUND if existing_data.get("utc_offset", None) is None else MiscEnum.DEFAULT
            self.version: VersionItem = MiscEnum.NOT_FOUND if existing_data.get("version", None) is None else MiscEnum.DEFAULT
            self.mods: list[RawModData] = MiscEnum.NOT_FOUND if existing_data.get("has_mods", False) is False else MiscEnum.DEFAULT
            self.campaign_id: int = MiscEnum.NOT_FOUND if existing_data.get("campaign_id", None) is None else MiscEnum.DEFAULT
            self.is_new_campaign: bool = MiscEnum.NOT_FOUND if existing_data.get("is_new_campaign", None) is None else MiscEnum.DEFAULT

    def all_found(self) -> bool:
        return all(i is not MiscEnum.NOT_FOUND for i in [self.game_map, self.utc_offset, self.version, self.campaign_id, self.is_new_campaign, self.mods])

    def _resolve_utc_offset(self, text: str) -> None:
        if match := self.regex_keeper.first_full_datetime.search(text):
            utc_datetime_kwargs = {k: int(v) for k, v in match.groupdict().items() if not k.startswith('local_')}
            local_datetime_kwargs = {k.removeprefix('local_'): int(v) for k, v in match.groupdict().items() if k.startswith('local_')}
            self.utc_offset = calculate_utc_offset(utc_datetime=datetime(tzinfo=UTC, **utc_datetime_kwargs), local_datetime=datetime(tzinfo=UTC, **local_datetime_kwargs), offset_class=tzoffset)

    def _resolve_version(self, text: str) -> None:
        if match := self.regex_keeper.version.search(text):
            version = VersionItem.from_string(match.group("version").strip())

            self.version = version
        elif match := self.regex_keeper.game_file.search(text):
            raw = match.group('game_file')
            version_args = [i for i in raw if i.isnumeric()]
            if version_args:
                while len(version_args) < 3:
                    version_args.append('MISSING')
                try:
                    version = VersionItem(*version_args)

                    self.version = version
                except ValueError:
                    pass

    def _resolve_game_map(self, text: str) -> None:

        if match := self.regex_keeper.game_map.search(text):
            self.game_map = match.group('game_map')

    def _resolve_mods(self, text: str) -> None:

        match = self.regex_keeper.mods.search(text)
        if match:
            mod_lines = match.group('mod_lines').splitlines()

            cleaned_mod_lines = [self.regex_keeper.mod_time_strip.sub("", line, 1) for line in mod_lines if '|' in line and 'modDir' not in line]

            self.mods = [parse_mod_line(cleaned_line) for cleaned_line in cleaned_mod_lines]

    def _resolve_campaign_id(self, text: str) -> None:
        if match := self.regex_keeper.campaign_id.search(text):

            self.campaign_id = int(match.group("campaign_id"))

            if match.group("text_loading") is not None:
                self.is_new_campaign = False
            elif match.group("text_creating") is not None:
                self.is_new_campaign = True

    def search(self, text: str) -> None:
        if self.campaign_id is MiscEnum.NOT_FOUND:
            self._resolve_campaign_id(text)

        if self.game_map is MiscEnum.NOT_FOUND:
            self._resolve_game_map(text)

        if self.version is MiscEnum.NOT_FOUND:

            self._resolve_version(text)

        if self.utc_offset is MiscEnum.NOT_FOUND:
            self._resolve_utc_offset(text)

        if self.mods is MiscEnum.NOT_FOUND:
            self._resolve_mods(text)

    def change_missing_to_none(self) -> None:

        if self.campaign_id is MiscEnum.NOT_FOUND:
            self.campaign_id = None

        if self.is_new_campaign is MiscEnum.NOT_FOUND:
            self.is_new_campaign = None

        if self.game_map is MiscEnum.NOT_FOUND:
            self.game_map = None

        if self.version is MiscEnum.NOT_FOUND:
            self.version = None

        if self.utc_offset is MiscEnum.NOT_FOUND:
            self.utc_offset = None

        if self.mods is MiscEnum.NOT_FOUND:
            self.mods = None

    def parse_file(self, in_file_obj: TextIO) -> Self:
        for text in PairedReader(in_file_obj, max_chunks=50):
            self.search(text)
            if self.all_found() is True:
                break

        self.change_missing_to_none()
        return self


# region[Main_Exec]
if __name__ == '__main__':
    pass

# endregion[Main_Exec]
