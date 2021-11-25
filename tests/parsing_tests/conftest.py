from antistasi_logbook.parsing.parsing_context import LogParsingContext, LineCache, LINE_ITERATOR_TYPE, RecordLine
from antistasi_logbook.parsing.parser import RawRecord, Parser, SimpleRegexKeeper
from pathlib import Path
import pytest
from contextlib import contextmanager
from typing import Any, TextIO, Mapping
from io import TextIOWrapper

THIS_FILE_DIR = Path(__file__).parent.absolute()


class FakeLogFileWrapper:

    def __init__(self, log_file: Path, data: Mapping[str, Any] = None) -> None:
        self.log_file = log_file
        self.data = {} if data is None else data

    @property
    def utc_offset(self) -> bool:
        return self.full_datetime is not None

    def __getattr__(self, name: str) -> Any:
        if hasattr(self.log_file, name):
            return getattr(self.log_file, name)

        return self.data.get(name)

    def has_game_map(self) -> bool:
        return self.game_map is not None

    def has_mods(self) -> bool:
        return self.mods is not None


class FakeParsingContext:

    def __init__(self, log_file: Path) -> None:
        self._log_file = FakeLogFileWrapper(log_file=log_file)
        self.line_cache = LineCache()
        self._line_iterator: LINE_ITERATOR_TYPE = None
        self._current_line: RecordLine = None
        self._current_line_number = 0

    @contextmanager
    def open(self, cleanup: bool = True) -> TextIO:
        with self._log_file.open(encoding='utf-8', errors='ignore') as f:
            yield f

    def _get_line_iterator(self) -> LINE_ITERATOR_TYPE:
        line_number = 0
        with self._log_file.open(encoding='utf-8', errors='ignore') as f:
            for line in f:
                line_number += 1
                line = line.rstrip()
                self._current_line_number = line_number
                yield RecordLine(content=line, start=line_number)

    @property
    def line_iterator(self) -> LINE_ITERATOR_TYPE:
        if self._line_iterator is None:
            self._line_iterator = self._get_line_iterator()
        return self._line_iterator

    @property
    def current_line(self) -> "RecordLine":
        if self._current_line is None:
            self.advance_line()

        return self._current_line

    def advance_line(self) -> None:
        self._current_line = next(self.line_iterator, ...)

    def close(self) -> None:
        if self._line_iterator is not None:
            self._line_iterator.close()

    def __enter__(self) -> "LogParsingContext":
        return self

    def __exit__(self, exception_type: type = None, exception_value: BaseException = None, traceback: Any = None) -> None:
        self.close()


@pytest.fixture
def fake_parsing_context_class():
    yield FakeParsingContext


def create_entry_result_data(log_file: Path):
    parser = Parser(database=None, regex_keeper=SimpleRegexKeeper())
    with FakeParsingContext(log_file=log_file) as context:
        result = list(parser.parse_entries(context=context))

    with open(THIS_FILE_DIR.joinpath(f"{log_file.stem}_auto_param_data.py"), 'w', encoding='utf-8', errors='ignore') as f:
        f.write("from antistasi_logbook.parsing.parser import Parser, SimpleRegexKeeper, RawRecord, RecordLine\n\n")
        idxes = []
        for idx, r in enumerate(result):
            f.write(f"""_{idx} = RawRecord([""" + ',\n\t\t'.join(repr(item) for item in r.lines) + """])\n\n\n""")
            idxes.append(f"_{idx}")
        f.write("all_records = [" + ',\n'.join(idxes) + "]\n\n\n")
        f.write("""if __name__ == '__main__':
    pass""")


if __name__ == '__main__':
    create_entry_result_data(THIS_FILE_DIR.joinpath("multiline_records_file_2.txt"))
