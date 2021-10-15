from pathlib import Path
import re
import sys
import os
import subprocess
import json
import shutil

FUNCTION_REGEX = re.compile(r"^(?P<white>[ \t]*)def \w+\(.*\).*\:$")


PROFILE_DECORATOR_TEMPLATE = "{white}@profile"

STORAGE_JSON_PATH = Path(sys.argv[0]).parent.joinpath('temp_profiling_storage_data.json')
STORAGE_FOLDER_PATH = Path(sys.argv[0]).parent.joinpath('temp_profiling_storage')


def create_temp_folder() -> Path:
    temp_folder = STORAGE_FOLDER_PATH
    temp_folder.mkdir(exist_ok=True, parents=True)
    return temp_folder


def copy_to_temp(in_file: Path, temp_folder: Path) -> Path:
    target = temp_folder.joinpath(in_file.name)
    shutil.copy(in_file, target)
    return target


def check_path(in_path: Path) -> bool:
    return all([in_path.exists(), in_path.is_file(), in_path.suffix.casefold() == '.py'])


def manipulate_file(in_path: Path):
    content = in_path.read_text()
    new_lines = []

    for line in content.splitlines():
        match = FUNCTION_REGEX.match(line)
        if match:
            new_lines.append(PROFILE_DECORATOR_TEMPLATE.format(white=match.group('white')))
        new_lines.append(line)
    in_path.write_text('\n'.join(new_lines), encoding='utf-8', errors='ignore')


def process_file(in_path: Path, temp_folder: Path) -> dict[str, str]:
    stored_file_path = copy_to_temp(in_path, temp_folder=temp_folder)
    manipulate_file(in_path)
    return {'stored_path': stored_file_path.as_posix(), 'original_path': in_path.as_posix()}


def main_modify():
    temp_folder = None
    processed_files = []
    for path in sys.argv[1:]:
        if temp_folder is None:
            temp_folder = create_temp_folder()
        path = Path(path)
        if check_path(path) is False:
            print(f'unable to process path {path.as_posix()!r}')
            continue

        processed_files.append(process_file(path, temp_folder=temp_folder))
    if len(processed_files) > 0:
        data_to_serialize = [temp_folder.as_posix()] + processed_files
        with STORAGE_JSON_PATH.open('w', encoding='utf-8', errors='ignore') as f:
            json.dump(data_to_serialize, f, indent=4, sort_keys=False)
    return


def main_reverse():

    with STORAGE_JSON_PATH.open('r', encoding='utf-8', errors='ignore') as f:
        data = json.load(f)
    temp_folder = Path(data.pop(0)).resolve()
    for item in data:
        stored_path = Path(item['stored_path'])
        original_path = Path(item['original_path'])
        # os.remove(original_path)
        shutil.move(stored_path, original_path)
    os.remove(STORAGE_JSON_PATH)
    os.rmdir(temp_folder)


def main():
    if os.getenv('REVERSE_PROFILE_MODIFICATION', '0') == '1' or sys.argv[1] == '1':
        main_reverse()
    else:
        main_modify()


if __name__ == '__main__':
    main()
