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

# endregion[Imports]

# region [TODO]


# endregion [TODO]

# region [Logging]


# endregion[Logging]

# region [Constants]

THIS_FILE_DIR = Path(__file__).parent.absolute()

# endregion[Constants]


class LineData:

    __slots__ = ("_start", "_content")

    def __init__(self, start: Optional[int], content: Optional[str]) -> None:
        self._start = start
        self._content = content

    @property
    def start(self) -> Optional[int]:
        return self._start

    @property
    def line_number(self) -> Optional[int]:
        return self._start

    @property
    def content(self) -> Optional[str]:
        return self._content

    @property
    def is_none(self) -> bool:
        return self.start is None and self.content is None

    def __eq__(self, o: object) -> bool:
        if isinstance(o, self.__class__):
            return self.content == o.content and self.start == o.content
        return NotImplemented

    def __str__(self) -> str:
        return self.start

    def __repr__(self):
        return str(self.start) + " " + str(self.content)


class LineView:

    def __init__(self,
                 previous_line: LineData,
                 current_line: LineData,
                 next_line: LineData,
                 reached_end: bool) -> None:
        self.previous_line = previous_line
        self.current_line = current_line
        self.next_line = next_line
        self.reached_end = reached_end

    @property
    def content(self) -> Optional[str]:
        return self.current_line.content

    @property
    def start(self) -> Optional[int]:
        return self.current_line.start

    def __str__(self) -> str:
        return self.current_line.content


class FileLineProvider:
    empty_value = LineData(None, None)

    def __init__(self, file_path: Union[str, os.PathLike, Path]):
        self.file_path: Path = Path(file_path)
        self.line_generator: Optional[Generator[LineData, None, None]] = None
        self._line_deque: deque[Union[LineData, None]] = deque([self.empty_value] * 3, maxlen=3)
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
                self._line_deque.append(next(self.line_generator))

            except StopIteration:
                self.line_generator.close()
                self._line_deque.append(self.empty_value)
                self._file_completed = True

    def advance_line(self) -> None:
        if self._initial_filled is False:
            self.initial_fill()
        else:
            self._advance_line()

    def __next__(self) -> LineView:
        if self.has_reached_end is False:
            self.advance_line()
        return LineView(self.previous_line, self.current_line, self.next_line, self.has_reached_end)

    def _get_new_line_generator(self) -> Generator[LineData, None, None]:
        current_line_number = 0
        with self.file_path.open("r", encoding='utf-8', errors='ignore') as f:
            for line in f:
                current_line_number += 1
                yield RecordLine(start=current_line_number, content=line.rstrip("\n\r"))

    def close(self) -> None:
        if self.line_generator is None:
            return
        if inspect.getgeneratorstate(self.line_generator) is not inspect.GEN_CLOSED:
            self.line_generator.close()
        self.line_generator = None

    @property
    def is_empty(self) -> bool:
        return all(i is self.empty_value for i in [self._line_deque[0], self._line_deque[1], self._line_deque[2]])

    @property
    def has_reached_end(self) -> bool:
        return self._file_completed is True and self.next_line.is_none is True

    @property
    def next_line(self) -> LineData:

        return self._line_deque[2]

    @property
    def current_line(self) -> LineData:

        return self._line_deque[1]

    @property
    def previous_line(self) -> LineData:

        return self._line_deque[0]

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(previous_line={self.previous_line!r}, current_line={self.current_line!r}, next_line={self.next_line!r})"


# region[Main_Exec]
if __name__ == '__main__':
    pass
# endregion[Main_Exec]
