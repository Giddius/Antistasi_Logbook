
import shutil
import os
import sys
from pathlib import Path
from typing import Union, Optional, Iterable, Callable, Any, TYPE_CHECKING


THIS_FILE = Path(__file__).resolve()
THIS_FILE_DIR = THIS_FILE.parent.resolve()

VENV_NAME = '.venv'.casefold()


class NoVenvFoundError(Exception):
    ...


def find_venv(in_folder: Union[str, os.PathLike, Path] = None, level: int = 0) -> Path:
    if level > 3:
        raise NoVenvFoundError(f"Unable to find {VENV_NAME!r} folder.")
    in_folder = Path.cwd().resolve() if in_folder is None else Path(in_folder).resolve()
    for file in in_folder.iterdir():
        if file.is_dir() and file.name.casefold() == VENV_NAME:
            return file
    return find_venv(in_folder.parent, level + 1)


def one_error_handler(func, path, exc_info):
    path = Path(path)
    if path.name.casefold() == 'python.exe':
        print(f'unable to delete {path.as_posix()!r}.')
        return
    raise OSError(exc_info)


def delete_venv():
    try:
        venv_path = find_venv(THIS_FILE_DIR)
        shutil.rmtree(venv_path, ignore_errors=False, onerror=one_error_handler)
    except NoVenvFoundError:
        print('No venv-folder to delete.')
        return


def main(try_round: int = 0):
    try:
        delete_venv()
    except Exception as e:
        if try_round <= 2:
            main(try_round=try_round + 1)
        else:
            sys.exit(e)


if __name__ == '__main__':
    main()
