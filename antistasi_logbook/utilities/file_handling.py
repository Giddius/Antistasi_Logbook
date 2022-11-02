"""
WiP.

Soon.
"""

# region [Imports]

# * Standard Library Imports ---------------------------------------------------------------------------->
import os
from typing import Union, Optional
from pathlib import Path
from collections import deque
from collections.abc import Generator

# * Third Party Imports --------------------------------------------------------------------------------->
import attrs

# endregion[Imports]

# region [TODO]


# endregion [TODO]

# region [Logging]


# endregion[Logging]

# region [Constants]

THIS_FILE_DIR = Path(__file__).parent.absolute()

# endregion[Constants]


@attrs.define(frozen=True, slots=True, weakref_slot=True)
class LineData:
    number: int
    text: str

    @property
    def is_none(self) -> bool:
        return self.number is None and self.text is None

    def __getitem__(self, index: int):
        if not isinstance(index, int):
            raise TypeError(f"index must be an integer not {type(index)!r}.")

        if index == 0:
            return self.number
        if index == 1:
            return self.text

        raise IndexError(f"index {index!r} not found in {self!r}.")

    def __str__(self) -> str:
        return self.text

    def __eq__(self, o: object) -> bool:
        if isinstance(o, self.__class__):
            return self.text == o.text and self.number == o.number
        return NotImplemented


class FileLineView(deque):
    empty_value = LineData(None, None)

    def __init__(self, line_generator: Generator[LineData, None, None]):
        super().__init__([self.empty_value] * 3, maxlen=3)
        self.line_generator = line_generator
        self._initial_filled: bool = False

    def initial_fill(self) -> None:
        if self._initial_filled is True:
            return
        self.advance_line()
        self.advance_line()
        self._initial_filled = True

    def advance_line(self):
        if self.is_empty is False and self[1] is self.empty_value and self[2] is self.empty_value:
            return
        try:
            self.append(next(self.line_generator))

        except StopIteration:
            self.line_generator.close()
            self.append(self.empty_value)

    @property
    def is_empty(self) -> bool:
        return all(i is self.empty_value for i in [self[0], self[1], self[2]])

    @property
    def has_reached_end(self) -> bool:
        return self.is_empty is False and self.current_line is self.empty_value and self.next_line is self.empty_value

    @property
    def next_line(self) -> Optional[str]:
        if self._initial_filled is False:
            self.initial_fill()
        return self[2]

    @property
    def current_line(self) -> Optional[str]:
        if self._initial_filled is False:
            self.initial_fill()
        return self[1]

    @property
    def previous_line(self) -> Optional[str]:
        if self._initial_filled is False:
            self.initial_fill()
        return self[0]

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(previous_line={self.previous_line!r}, current_line={self.current_line!r}, next_line={self.next_line!r})"


class FileContext:

    def __init__(self, file_path: Union[str, os.PathLike]) -> None:
        self.file_path = Path(file_path).resolve()
        self.file_line_view = FileLineView(self._get_line_generator())

    def _get_line_generator(self) -> Generator[LineData, None, None]:
        current_line_number = 0
        with self.file_path.open("r", encoding='utf-8', errors='ignore') as f:
            for line in f:
                current_line_number += 1
                yield LineData(current_line_number, line.rstrip("\n\r"))


# region[Main_Exec]
if __name__ == '__main__':
    pass
# endregion[Main_Exec]
