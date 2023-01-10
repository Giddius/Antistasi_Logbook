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
import inspect
# * Third Party Imports --------------------------------------------------------------------------------->
from antistasi_logbook.parsing.record_line import RecordLine
import sys
if sys.version_info >= (3, 11):
    from typing import Self
else:
    from typing_extensions import Self
# endregion [Imports]

# region [TODO]


# endregion [TODO]

# region [Logging]


# endregion [Logging]

# region [Constants]
from gidapptools.general_helper.timing import get_dummy_profile_decorator_in_globals
get_dummy_profile_decorator_in_globals()
THIS_FILE_DIR = Path(__file__).parent.absolute()

# endregion [Constants]


class LineView:
    __slots__ = ("_previous_line", "_current_line", "_next_line", "_reached_end")

    def __init__(self,
                 previous_line: Optional[RecordLine],
                 current_line: Optional[RecordLine],
                 next_line: Optional[RecordLine],
                 reached_end: bool) -> None:
        self._previous_line = previous_line
        self._current_line = current_line
        self._next_line = next_line
        self._reached_end = reached_end

    @property
    def previous_line(self) -> Optional[RecordLine]:
        return self._previous_line

    @property
    def current_line(self) -> Optional[RecordLine]:
        return self._current_line

    @property
    def next_line(self) -> Optional[RecordLine]:
        return self._next_line

    @property
    def reached_end(self) -> Optional[RecordLine]:
        return self._reached_end

    @property
    def content(self) -> Optional[str]:
        return self.current_line.content

    @property
    def start(self) -> Optional[int]:
        return self.current_line.start

    def __str__(self) -> str:
        return self.current_line.content


class FileLineProvider:
    __slots__ = ("file_path", "line_generator", "_line_deque", "_initial_filled", "_file_completed")
    empty_value = RecordLine(None, None)

    def __init__(self, file_path: Union[str, os.PathLike, Path]):
        self.file_path: Path = Path(file_path)
        self.line_generator: Optional[Generator[RecordLine, None, None]] = None
        self._line_deque: deque[Union[RecordLine, None]] = deque([self.empty_value] * 3, maxlen=3)
        self._initial_filled: bool = False
        self._file_completed: bool = False

    def initial_fill(self) -> None:

        if self._initial_filled is True:
            return
        if self.line_generator is None:
            self.line_generator = self._get_new_line_generator()
        self._advance_line()
        self._advance_line()
        self._initial_filled = True

    def _advance_line(self) -> None:
        if self._file_completed is True:
            if self.current_line.is_none is False:
                self._line_deque.append(self.empty_value)

        else:

            try:
                new_line = next(self.line_generator)
                self._line_deque.append(new_line)

            except StopIteration:
                self.line_generator.close()
                self._line_deque.append(self.empty_value)
                self._file_completed = True

    def advance_line(self) -> None:
        if self.line_generator is not None and inspect.getgeneratorstate(self.line_generator) is inspect.GEN_CLOSED:
            raise RuntimeError(f"line_generator of {self!r} is closed.")

        if self._initial_filled is False:
            self.initial_fill()
        else:
            self._advance_line()

    def __next__(self) -> LineView:
        if self.has_reached_end is False:
            self.advance_line()
        return LineView(self.previous_line, self.current_line, self.next_line, self.has_reached_end)

    def _get_new_line_generator(self) -> Generator[RecordLine, None, None]:
        current_line_num: int = 0
        open_file = self.file_path.open("r", encoding='utf-8', errors='ignore')
        try:
            for line in open_file:
                current_line_num += 1
                yield RecordLine(start=current_line_num, content=line.rstrip())
        finally:
            open_file.close()

    def close(self) -> None:
        if self.line_generator is None:
            return
        if inspect.getgeneratorstate(self.line_generator) is not inspect.GEN_CLOSED:
            self.line_generator.close()

    def reset(self) -> Self:
        self.close()
        self.line_generator = None
        self._initial_filled = False
        self.initial_fill()

    def seek_to_line_number(self, line_number: int) -> Self:
        self.initial_fill()

        if line_number == self.current_line.start:
            return self

        if line_number < self.current_line.start:
            self.reset()

        while self.current_line.start < line_number:
            self.advance_line()

        return self

    @property
    def is_empty(self) -> bool:
        return all(i is self.empty_value for i in [self._line_deque[0], self._line_deque[1], self._line_deque[2]])

    @property
    def has_reached_end(self) -> bool:
        return self._file_completed is True and self.next_line.is_none is True

    @property
    def next_line(self) -> RecordLine:

        return self._line_deque[2]

    @property
    def current_line(self) -> RecordLine:

        return self._line_deque[1]

    @property
    def previous_line(self) -> RecordLine:

        return self._line_deque[0]

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(previous_line={self.previous_line!r}, current_line={self.current_line!r}, next_line={self.next_line!r})"


# region [Main_Exec]
if __name__ == '__main__':
    pass
# endregion [Main_Exec]
