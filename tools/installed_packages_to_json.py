import sys
# from gid_scratch._utility import console_print
from pprint import pprint
import re
import json
import os
from pathlib import Path
import subprocess
try:
    import pipdeptree
    deptree_installed = True
except ImportError:
    deptree_installed = False


THIS_FILE_DIR = Path(os.path.dirname(__file__)).absolute()
CREATE_VENV_LOG_FOLDER = THIS_FILE_DIR.joinpath('create_venv_logs')
OUTPUT_FILE = CREATE_VENV_LOG_FOLDER.joinpath('installed_packages.json')
DEP_TREE_FILE = CREATE_VENV_LOG_FOLDER.joinpath("dependency_tree.json")


def to_json(in_items: dict[str, str]) -> None:

    with OUTPUT_FILE.open('w', encoding='utf-8') as f:
        json.dump(in_items, f, sort_keys=True, indent=4)


def write_dependency_tree() -> None:
    cmd = subprocess.run("pipdeptree --json-tree -a", check=True, capture_output=True, text=True)
    DEP_TREE_FILE.write_text(cmd.stdout, encoding='utf-8', errors='ignore')


def main(in_data: str) -> None:
    items = json.loads(in_data)
    to_json(in_items=items)


if __name__ == '__main__':
    input_data = sys.stdin.read()
    main(in_data=input_data.strip())
