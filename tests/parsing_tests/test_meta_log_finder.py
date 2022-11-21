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
        finder = MetaFinder().parse_file(f)

    assert results["game_map"] == finder.game_map
    assert results["version"] == finder.version
    assert results["campaign_id"] == finder.campaign_id
    assert results["is_new_campaign"] == finder.is_new_campaign
    assert results["utc_offset"] == finder.utc_offset
    assert results["mods"] == finder.mods
