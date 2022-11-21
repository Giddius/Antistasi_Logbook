# region [Imports]

import pytest
from pathlib import Path
from dateutil.tz import tzoffset
import json
from datetime import datetime, timedelta, timezone
from antistasi_logbook.parsing.meta_log_finder import VersionItem
from hashlib import md5

# endregion [Imports]

# region [Constants]

THIS_FILE_DIR = Path(__file__).parent.absolute()

DATA_DIR = THIS_FILE_DIR.joinpath("data").resolve()

FILE_HASH_INCREMENTAL_THRESHOLD: int = 10485760  # 10mb
# endregion [Constants]


EXAMPLE_LOG_FILES = {example_file.name: example_file.resolve() for example_file in DATA_DIR.iterdir() if example_file.is_file()}


def _check_hash(in_example_file: Path, target_hash: str) -> bool:
    file_hash = md5()
    with in_example_file.open("rb", buffering=FILE_HASH_INCREMENTAL_THRESHOLD) as f:
        for chunk in f:
            file_hash.update(chunk)

    return file_hash.hexdigest() == target_hash


def _load_result_json(in_result_file: Path) -> dict[str, object]:

    with in_result_file.open("r", encoding='utf-8', errors='ignore') as f:
        data = json.load(f)

        try:
            data["version"] = VersionItem.from_string(data["version"]) if data["version"] is not None else None
        except KeyError:
            pass

        try:
            offset_name = data["utc_offset"]["name"]
            offset_delta = timedelta(seconds=data["utc_offset"]["seconds"])
            data["utc_offset"] = tzoffset(offset_name, offset_delta)

        except KeyError:
            pass
        try:
            for item in data["mods"]:

                if item["full_path"] is not None:
                    item["full_path"] = Path(item["full_path"])

        except KeyError:
            pass

        return data


@pytest.fixture
def example_log_file_and_data_1():
    example_file = EXAMPLE_LOG_FILES["example_log_1.txt"]
    example_result_file = EXAMPLE_LOG_FILES[example_file.stem + "_results.json"]
    result_data = _load_result_json(example_result_file)
    if _check_hash(example_file, result_data["source_file_hash"]) is False:
        raise ValueError(f"file {example_file.name!r} has changed and {example_result_file.name!r} needs updating")
    yield example_file, _load_result_json(example_result_file)
