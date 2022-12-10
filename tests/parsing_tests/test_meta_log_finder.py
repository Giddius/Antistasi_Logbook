# region [Imports]

import pytest
from pytest import param
from pytest_lazyfixture import lazy_fixture

from pathlib import Path
from datetime import datetime, timedelta, timezone
from antistasi_logbook.parsing.meta_log_finder import MetaFinder
from antistasi_logbook.utilities.paired_reader import PairedReader
from antistasi_logbook.regex_store.regex_keeper import SimpleRegexKeeper
from pprint import pprint
from time import perf_counter
# endregion[Imports]

# region [Constants]

THIS_FILE_DIR = Path(__file__).parent.absolute()

# endregion [Constants]
test_meta_parsing_params = [
    param(lazy_fixture(f"example_log_file_and_data_{data_num}"), id=str(data_num)) for data_num in (1, 2)
]


@pytest.mark.parametrize(["in_log_file_and_data"], test_meta_parsing_params)
def test_meta_parsing(in_log_file_and_data):
    example_file: Path = in_log_file_and_data[0]
    results: dict[str, object] = in_log_file_and_data[1]

    with example_file.open("r", encoding='utf-8', errors='ignore') as f:
        finder = MetaFinder().parse_file(f)

    assert results["game_map"] == finder.game_map
    assert results["version"] == finder.version
    assert results["campaign_id"] == finder.campaign_id
    assert results["is_new_campaign"] == finder.is_new_campaign
    assert results["utc_offset"] == finder.utc_offset

    for item in results["mods"]:
        assert item in finder.mods
