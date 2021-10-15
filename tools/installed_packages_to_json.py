import sys
# from gid_scratch._utility import console_print
from pprint import pprint
import re
import json
import os
from pathlib import Path

THIS_FILE_DIR = Path(os.path.dirname(__file__)).absolute()
CREATE_VENV_LOG_FOLDER = THIS_FILE_DIR.joinpath('create_venv_logs')
OUTPUT_FILE = CREATE_VENV_LOG_FOLDER.joinpath('installed_packages.json')


def to_json(in_items: dict[str, str]) -> None:
    data = {k: v for k, v in sorted(in_items.items())}
    with OUTPUT_FILE.open('w', encoding='utf-8') as f:
        json.dump(data, f, sort_keys=True, indent=4)


def find_name_version_pairs(in_data: str) -> dict[str, str]:
    _out = {}
    for line in in_data.splitlines():
        line = line.strip()
        if line:
            name, version = line.split()
            _out[name] = version
    return _out


def clean_header(in_data: str) -> str:
    clean_regex = re.compile(r"\-+\s?\-*")
    cleaned_data = clean_regex.split(in_data, 1)[-1].strip()
    return cleaned_data


def main(in_data: str) -> None:
    data = clean_header(in_data)
    items = find_name_version_pairs(data)
    to_json(in_items=items)


if __name__ == '__main__':
    input_data = sys.stdin.read()
    main(in_data=input_data.strip())
