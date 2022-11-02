"""
WiP.

Soon.
"""

# region [Imports]

# * Standard Library Imports ---------------------------------------------------------------------------->
import re
from typing import ClassVar
from pathlib import Path

# * Third Party Imports --------------------------------------------------------------------------------->
import attr

# * Gid Imports ----------------------------------------------------------------------------------------->
from gidapptools.general_helper.string_helper import string_strip

# endregion[Imports]

# region [TODO]


# endregion [TODO]

# region [Logging]


# endregion[Logging]

# region [Constants]

THIS_FILE_DIR = Path(__file__).parent.absolute()

# endregion[Constants]


@attr.s(frozen=True, kw_only=True, slots=True, weakref_slot=True, auto_attribs=True, auto_detect=True)
class RawSQLPhrase:
    phrase: str = attr.ib(converter=string_strip)
    value_names: tuple[str] = attr.ib()
    value_names_regex: ClassVar = re.compile(r"\((?P<value_names>[\"\w\,\s]+)\)\s*VALUES")

    @value_names.default
    def _parse_value_names(self) -> tuple[str]:
        raw_value_names = self.value_names_regex.search(self.phrase).group("value_names")
        value_names = [name.strip().strip('"') for name in raw_value_names.split(",")]
        return tuple(value_names)

    @property
    def batch_size(self) -> int:
        return 327670 // (len(self.value_names) + 2)


# region[Main_Exec]
if __name__ == '__main__':
    pass

# endregion[Main_Exec]
