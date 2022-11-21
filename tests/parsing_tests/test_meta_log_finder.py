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
# endregion[Imports]

# region [Constants]

THIS_FILE_DIR = Path(__file__).parent.absolute()

# endregion [Constants]


def test_meta_parsing(example_log_file_and_data_1):
    example_file: Path = example_log_file_and_data_1[0]
    results: dict[str, object] = example_log_file_and_data_1[1]

    with example_file.open("r", encoding='utf-8', errors='ignore') as f:
        text_parts = PairedReader(f, max_chunks=50)
        finder = MetaFinder(regex_keeper=SimpleRegexKeeper())
        while True:
            finder.search(str(text_parts))
            if finder.all_found() is True or text_parts.finished is True:
                break

            text_parts.read_next()

        finder.change_missing_to_none()

    assert results["game_map"] == finder.game_map
    assert results["full_date_time"].local_datetime == finder.full_datetime.local_datetime
    assert results["full_date_time"].utc_datetime == finder.full_datetime.utc_datetime
    assert results["version"] == finder.version
    assert results["campaign_id"] == finder.campaign_id
    assert results["is_new_campaign"] == finder.is_new_campaign
    assert len(finder.mods) == len(set(i["name"] for i in finder.mods))

    assert finder.mods == results["mods"]
