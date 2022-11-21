import pytest
from pathlib import Path
from antistasi_logbook.utilities.file_handling import FileContext


THIS_FILE_DIR = Path(__file__).parent.absolute()

TEST_DATA_DIR = THIS_FILE_DIR.joinpath("data")


test_file_context_params = [pytest.param(TEST_DATA_DIR.joinpath("simple_text.txt"), id="simple"),
                            pytest.param(TEST_DATA_DIR.joinpath("single_line_text.txt"), id="single_line"),
                            pytest.param(TEST_DATA_DIR.joinpath("three_line_text.txt"), id="three_lines")]


@pytest.mark.parametrize(["file_path"], test_file_context_params)
def test_file_context(file_path: Path):
    all_lines = file_path.read_text(encoding='utf-8', errors='ignore').splitlines()

    context = FileContext(file_path=file_path)
    line_view = context.file_line_view
    assert line_view.has_reached_end is False

    assert line_view.previous_line is line_view.empty_value
    assert line_view.current_line[1] == all_lines[0]

    curr_line_num: int = 0
    for i in range(len(all_lines)):
        line_view.advance_line()
        curr_line_num += 1

        assert line_view.previous_line[1] == all_lines[curr_line_num - 1]

        if i == len(all_lines) - 2:
            assert line_view.next_line is line_view.empty_value
            assert line_view.current_line[1] == all_lines[-1]

        elif i == len(all_lines) - 1:
            assert line_view.next_line is line_view.empty_value
            assert line_view.current_line is line_view.empty_value
            assert line_view.previous_line[1] == all_lines[-1]

        else:
            assert line_view.current_line[1] == all_lines[curr_line_num]
            assert line_view.next_line[1] == all_lines[curr_line_num + 1]

    assert line_view.has_reached_end is True
