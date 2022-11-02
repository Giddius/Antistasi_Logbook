import os
import shutil
import sys
from pathlib import Path

os.chdir(sys.argv[1])

REQUIRED_FILES = ["post_setup_scripts.txt",
                  "pre_setup_scripts.txt",
                  "required_dev.txt",
                  "required_from_github.txt",
                  "required_misc.txt",
                  "required_personal_packages.txt",
                  "required_test.txt", ]

SETTINGS_FOLDER = Path(os.path.abspath(os.path.dirname(__file__))).joinpath('venv_setup_settings')
if SETTINGS_FOLDER.exists() is False:
    SETTINGS_FOLDER.mkdir()
    print(f"Settings Folder '{SETTINGS_FOLDER}' was missing and was created")

for req_file in REQUIRED_FILES:
    req_file = SETTINGS_FOLDER.joinpath(req_file)
    if req_file.is_file() is False:
        with req_file.open(mode='w') as f:
            f.write('')
            print(f"required file '{req_file}' was missing and was created")
    with req_file.open('r') as f:
        lines = filter(lambda x: x != '', f.read().splitlines())
        cleaned_lines = []
        for line in lines:
            if not line.startswith("--force-reinstall") and not line.startswith('--no-cache-dir') and "github.com" not in line:
                mod_line = line.split('==')[0].split('<=')[0].split('>=')[0]
                mod_line = mod_line.split(' ')[-1]
            else:
                mod_line = line
            mod_line = mod_line.strip()
            if all(exist_item.casefold() != mod_line.casefold() for exist_item in cleaned_lines):
                cleaned_lines.append(line)
    with req_file.open('w') as f:
        f.write('\n'.join(sorted(cleaned_lines, key=lambda x: x.casefold())))
