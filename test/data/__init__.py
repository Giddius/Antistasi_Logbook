from pathlib import Path
import json
from typing import Any
from datetime import datetime, timezone, timedelta
THIS_FILE_DIR = Path(__file__).parent.absolute()


FAKE_INFO_DATA_FILE = THIS_FILE_DIR.joinpath("fake_info_data.json")

FAKE_LS_DATA_FILE = THIS_FILE_DIR.joinpath("fake_ls_data.json")

FAKE_LOG_FILES_FOLDER = THIS_FILE_DIR.joinpath("fake_log_files")


def get_fake_info_data() -> dict[str, dict[str, Any]]:
    with FAKE_INFO_DATA_FILE.open(encoding='utf-8', errors='ignore') as f:
        data = json.load(f)
    modified_data = {}
    for path_string, values in data.items():
        modified_data[path_string] = {}
        for key, value in values.items():
            if key == "modified":
                value = datetime.fromisoformat(value)

            modified_data[path_string][key] = value
    return modified_data


def get_fake_ls_data() -> dict[str, list[dict[str, Any]]]:
    with FAKE_LS_DATA_FILE.open(encoding='utf-8', errors='ignore') as f:
        data = json.load(f)
    modified_data = {}
    for path_string, values in data.items():
        modified_data[path_string] = []
        for item in values:
            item['modified'] = datetime.fromisoformat(item["modified"])
            modified_data[path_string].append(item)
    return modified_data


def get_fake_log_files_paths() -> dict[str, Path]:
    data = {}
    for folder in FAKE_LOG_FILES_FOLDER.iterdir():
        if folder.is_dir() is False:
            continue
        data[folder.name] = {}
        for file in folder.iterdir():
            if file.is_file() is False or file.suffix != '.txt':
                continue
            data[folder.name][file.name] = file

    return data


FAKE_INFO_DATA = get_fake_info_data()


FAKE_LS_DATA = get_fake_ls_data()


FAKE_LOG_FILES_PATHS = get_fake_log_files_paths()
