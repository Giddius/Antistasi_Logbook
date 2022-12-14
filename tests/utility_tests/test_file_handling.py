import pytest
from pathlib import Path
from antistasi_logbook.utilities.file_handling import FileLineProvider


THIS_FILE_DIR = Path(__file__).parent.absolute()

TEST_DATA_DIR = THIS_FILE_DIR.joinpath("data")


test_file_context_params = [pytest.param(TEST_DATA_DIR.joinpath("simple_text.txt"), id="simple"),
                            pytest.param(TEST_DATA_DIR.joinpath("single_line_text.txt"), id="single_line"),
                            pytest.param(TEST_DATA_DIR.joinpath("three_line_text.txt"), id="three_lines")]


@pytest.mark.parametrize(["file_path"], test_file_context_params)
def test_file_context(file_path: Path):
    all_lines = file_path.read_text(encoding='utf-8', errors='ignore').splitlines()
    collected_lines = []
    line_provider = FileLineProvider(file_path)
    current_line_number = 0
    while line_provider.has_reached_end is False:
        next(line_provider)
        current_line_number += 1
        collected_lines.append(line_provider.current_line.content)
        assert line_provider.current_line.content is not None
        assert line_provider.current_line.start == current_line_number
        assert line_provider.current_line.content == all_lines[current_line_number - 1]
        if current_line_number != 1:
            assert line_provider.previous_line.start == current_line_number - 1
            assert line_provider.previous_line.content == all_lines[current_line_number - 2]

    assert len(all_lines) == line_provider.current_line.start
    assert set(all_lines) == set(collected_lines)


@pytest.mark.parametrize(["file_path"], test_file_context_params)
def test_file_context_lineview(file_path: Path):
    all_lines = file_path.read_text(encoding='utf-8', errors='ignore').splitlines()
    collected_lines = []
    line_provider = FileLineProvider(file_path)
    current_line_number = 0
    while line_provider.has_reached_end is False:
        line_view = next(line_provider)
        collected_lines.append(line_view.current_line.content)
        current_line_number += 1
        assert line_view.current_line.start == current_line_number
        assert line_view.current_line.content == all_lines[current_line_number - 1]
        assert line_view.content == all_lines[current_line_number - 1]
        assert str(line_view) == all_lines[current_line_number - 1]

    assert set(all_lines) == set(collected_lines)


def test_seeking():
    file_path = TEST_DATA_DIR.joinpath("simple_text.txt")
    all_lines = file_path.read_text(encoding='utf-8', errors='ignore').splitlines()
    line_provider = FileLineProvider(file_path)

    line_provider.seek_to_line_number(3)

    assert line_provider.current_line.line_number == 3
    assert line_provider.current_line.content == all_lines[2]

    line_provider.seek_to_line_number(4)

    assert line_provider.current_line.line_number == 4
    assert line_provider.current_line.content == all_lines[3]

    line_provider.seek_to_line_number(1)

    assert line_provider.current_line.line_number == 1
    assert line_provider.current_line.content == all_lines[0]
