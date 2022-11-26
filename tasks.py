from invoke import task, Result, Context, Collection
import sqlite3
import os
import logging
from zipfile import ZipFile, ZIP_LZMA

import shutil
from tomlkit.toml_file import TOMLFile
from tomlkit.toml_document import TOMLDocument
from tomlkit.api import loads as toml_loads, dumps as toml_dumps, parse, document
import json
from collections import defaultdict
from dotenv import load_dotenv, find_dotenv, dotenv_values
from webdav4.client import Client as WebdavClient
from tabulate import tabulate
from datetime import datetime, timedelta
import sys
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, wait
import random
from threading import Semaphore
from dateparser import parse as date_parse
from rich import inspect as rinspect
from rich.console import Console as RichConsole
from collections import UserString, UserList, UserDict, deque, ChainMap, Counter
from tempfile import TemporaryDirectory, gettempdir
from time import sleep, time
from itertools import repeat
import re
from rich.rule import Rule
from zipfile import ZipFile, ZIP_LZMA
from gidapptools.general_helper.string_helper import make_attribute_name
import subprocess
from typing import Union, Optional, Iterable, Hashable, Generator, Mapping, MutableMapping, Any
import logging
import xml.etree.ElementTree as et
from pathlib import Path
from pprint import pprint
# import attr
from gid_tasks.project_info.project import Project
from send2trash import send2trash
# from gid_tasks.actions import doc_collection, clean_collection, update_collection
# from gid_tasks._custom_invoke_classes.custom_task_objects import task
# ns = Collection()
# ns.add_collection(doc_collection)
# ns.add_collection(clean_collection)
# ns.add_collection(update_collection)
THIS_FILE_DIR = Path(__file__).parent.absolute()

PROJECT = Project(cwd=THIS_FILE_DIR)
Context.project = PROJECT

loggers = list(logging.Logger.manager.loggerDict)

PATH_TYPE = Union[str, os.PathLike, Path]
CONSOLE = RichConsole(soft_wrap=True)
RULE_CHARS = "▴▾"
RULE = Rule(characters=RULE_CHARS)


def rprint(*args, **kwargs):
    def _handle_mappings(in_item):
        if isinstance(in_item, (Mapping, MutableMapping)):
            return dict(in_item)
        return in_item
    args = [_handle_mappings(item) for item in args]
    CONSOLE.print()
    CONSOLE.print(*args, **kwargs)
    CONSOLE.print()
    CONSOLE.print(RULE)


print = rprint
Context.console = CONSOLE
# CONSOLE.print(RULE)


class PyprojectTomlFile:

    def __init__(self, path: PATH_TYPE) -> None:
        self.path = self._validate_path(path)
        self.document: TOMLDocument = None
        self.read()

    @staticmethod
    def _validate_path(path: PATH_TYPE) -> Path:
        path = Path(path)
        if path.exists() is False:
            raise FileNotFoundError(f"The file {path.as_posix!r} does not exist.")
        if path.is_file() is False:
            raise FileNotFoundError(f"The path {path.as_posix()!r} is not a file.")
        if path.suffix.casefold() != '.toml':
            # TODO: Custom Error!
            raise RuntimeError(f"The file {path.as_posix()!r} is not a toml file.")
        return path

    def read(self) -> None:
        with self.path.open('r', encoding='utf-8', errors='ignore') as f:
            self.document = toml_loads(f.read())

    def write(self) -> None:
        with self.path.open('w', encoding='utf-8', errors='ignore') as f:
            f.write(self.document.as_string())

    def get(self, key, default=None) -> Any:
        return self.document.get(key, default)


class ProjectInfo:
    GIT_EXE = shutil.which('git.exe')

    def __init__(self, project_folder: Path = None) -> None:
        self.project_folder = self.main_dir_from_git() if project_folder is None else Path(project_folder)
        self.pyproject_toml = PyprojectTomlFile(path=self.project_folder.joinpath("pyproject.toml"))
        self.important_folder: dict[str:Path] = {}
        self.important_files: dict[str:Path] = {}
        self.important_scripts: dict[str, str] = {}
        self.load_important_folder()
        self.load_important_files()

    @classmethod
    def main_dir_from_git(cls, cwd: os.PathLike = None) -> Path:
        cwd = Path.cwd() if cwd is None else Path(cwd)
        cmd = subprocess.run([cls.GIT_EXE, "rev-parse", "--show-toplevel"], capture_output=True, text=True, shell=True, check=True, cwd=cwd)
        main_dir = Path(cmd.stdout.rstrip('\n'))
        if main_dir.is_dir() is False:
            raise FileNotFoundError('Unable to locate main dir of project')
        return main_dir

    def load_important_folder(self) -> None:
        folder_to_load = {
            "venv": [".venv"],
            "scripts": [".venv", "scripts"],
            "site_packages": [".venv", "lib", "site-packages"],
            "vscode": [".vscode"],
            "docs": ["docs"],
            "misc": ["misc"],
            "temp": ["temp"],
            "test": ["test"],
            "tools": ["tools"],
            "main_module": [self.pyproject_toml.get('project').get('name')],
            "sql_scripts": [self.pyproject_toml.get('project').get('name'), "storage", "sql_scripts"]
        }
        for k, v in folder_to_load.items():
            folder_path = self.project_folder.joinpath(*v).resolve()
            if folder_path.exists() and folder_path.is_dir():
                self.important_folder[k] = folder_path

    def load_important_files(self) -> None:
        files_to_load = {
            "activate_venv": [".venv", "scripts", "activate.bat"],
            "python": [".venv", "scripts", "python.exe"],
            "main": [self.pyproject_toml.get('project').get('name'), '__main__.py'],
            "log_pipe_create_venv": ["tools", "log_pipe_create_venv.cmd"],
            "autoflake_all": ["tools", "autoflake_all.cmd"],
            "datasette_plugin_metadata": ["tools", "datasette_plugin_metadata.json"],
        }
        for k, v in files_to_load.items():
            file_path = self.project_folder.joinpath(*v).resolve()
            if file_path.exists() and file_path.is_file():
                self.important_files[k] = file_path


PROJECT_INFO = ProjectInfo()
PROJECT_INFO.pyproject_toml.read()


# region [Constants]
MODULE_NAME = "antistasi_logbook"
THIS_FILE_DIR = Path(__file__).parent.absolute()
GIT_EXE = shutil.which('git.exe')

NEXTCLOUD_BASE_FOLDER = "Antistasi_Community_Logs"
NEXTCLOUD_OPTIONS = {"webdav_hostname": "https://antistasi.de/dev_drive/remote.php/dav/files/Giddi",
                     "webdav_login": 'Giddi',
                     'webdav_timeout': 1000,
                     "webdav_password": os.getenv('ANTISTASI_DEV_DRIVE'),
                     #  'recv_speed': 2 * (1024**2)
                     }

TOOLS_FOLDER = THIS_FILE_DIR.joinpath("tools")
TEMP_FOLDER = THIS_FILE_DIR.joinpath('temp')
MISC_FOLDER = THIS_FILE_DIR.joinpath('misc')
DOCS_FOLDER = THIS_FILE_DIR.joinpath('docs')
VENV_FOLDER = THIS_FILE_DIR.joinpath('.venv')
SCRIPTS_FOLDER = VENV_FOLDER.joinpath('scripts')
SITE_PACKAGES_FOLDER = VENV_FOLDER.joinpath("lib", "site-packages")

REPORTS_FOLDER = TOOLS_FOLDER.joinpath('reports')
MAIN_MODULE_FOLDER = THIS_FILE_DIR.joinpath(MODULE_NAME)
LOG_NAME_DATE_TIME_REGEX = re.compile(r"(?P<year>\d\d\d\d).(?P<month>\d+?).(?P<day>\d+).(?P<hour>[012\s]?\d).(?P<minute>[0123456]\d).(?P<second>[0123456]\d)")

IMPORTANT_FOLDER = [TEMP_FOLDER, MISC_FOLDER, DOCS_FOLDER, MAIN_MODULE_FOLDER]

VENV_ACTIVATOR_PATH = SCRIPTS_FOLDER.joinpath("activate.bat")
PWIZ_FILE = SITE_PACKAGES_FOLDER.joinpath("pwiz.py")
DESIGNER_FILES_FOLDER = THIS_FILE_DIR.joinpath("designer_files")
RESOURCES_FILE_FOLDER = DESIGNER_FILES_FOLDER.joinpath("resources")
RESOURCES_FILE = RESOURCES_FILE_FOLDER.joinpath("antistasi_logbook_resources.qrc")
RAW_WIDGETS_FOLDER = MAIN_MODULE_FOLDER.joinpath("gui", "raw_widgets")
# endregion[Constants]


def activator_run(c: Context, command, echo=True, **kwargs) -> Result:
    with c.prefix(str(VENV_ACTIVATOR_PATH)):
        result = c.run(command, echo=echo, **kwargs)
        return result


def loadjson(in_file):
    with open(in_file, 'r', encoding='utf-8', errors='ignore') as jsonfile:
        _out = json.load(jsonfile)
    return _out


def writejson(in_object, in_file, sort_keys=True, indent=4):
    with open(in_file, 'w', encoding='utf-8', errors='ignore') as jsonoutfile:
        json.dump(in_object, jsonoutfile, sort_keys=sort_keys, indent=indent)


def readit(in_file, per_lines=False, in_encoding='utf-8', in_errors=None):

    with open(in_file, 'r', encoding=in_encoding, errors=in_errors) as _rfile:
        _content = _rfile.read()
    if per_lines is True:
        _content = _content.splitlines()

    return _content


def writeit(in_file, in_data, append=False, in_encoding='utf-8', in_errors=None):

    _write_type = 'w' if append is False else 'a'
    with open(in_file, _write_type, encoding=in_encoding, errors=in_errors,) as _wfile:
        _wfile.write(in_data)


def pathmaker(first_segment, *in_path_segments, rev=False):
    _path = first_segment
    _path = os.path.join(_path, *in_path_segments)
    if rev is True or sys.platform not in ['win32', 'linux']:
        return os.path.normpath(_path)
    return os.path.normpath(_path).replace(os.path.sep, '/')


def create_folder(in_path):
    if os.path.isdir(in_path) is False:
        os.makedirs(in_path)


def clean_create_folder(in_path):
    if os.path.isdir(in_path):
        shutil.rmtree(in_path)
    create_folder(in_path)


def main_dir_from_git():
    cmd = subprocess.run([GIT_EXE, "rev-parse", "--show-toplevel"], capture_output=True, text=True, shell=True, check=True)
    main_dir = pathmaker(cmd.stdout).rstrip('\n')
    if os.path.isdir(main_dir) is False:
        raise FileNotFoundError('Unable to locate main dir of project')
    return main_dir


os.chdir(main_dir_from_git())


@task()
def convert_designer_files(c, target_folder=None):
    target_folder = DESIGNER_FILES_FOLDER if target_folder is None else Path(target_folder)
    to_convert: dict[Path:Path] = {}
    for file in DESIGNER_FILES_FOLDER.iterdir():
        if file.is_file() and file.suffix == '.ui':
            to_convert[file] = target_folder.joinpath(file.name).with_suffix('.py')

    exe = "pyside6-uic.exe"
    for src, tgt in to_convert.items():
        print(f"converting file {src!s} to {tgt!s}")
        args = []
        args.append("-g python")
        args.append("-a")
        args.append("--from-imports")
        args.append(str(src))
        cmd = exe + ' ' + ' '.join(args)
        result = activator_run(c, cmd, echo=False, hide=True)
        raw_lines = result.stdout.splitlines()
        while raw_lines[0].startswith('#') or raw_lines[0] == '':
            _ = raw_lines.pop(0)

        raw_text = '\n'.join(raw_lines)
        raw_text = re.sub(r"self\.retranslateUi\(\w+\).*\#\s*retranslateUi", "", raw_text, flags=re.DOTALL)
        raw_text = re.sub(r"from\s+\.\s+import\s\w+", "", raw_text)
        tgt.write_text(raw_text, encoding='utf-8', errors='ignore')

        print(f"FINISHED converting file {src!s} to {tgt!s}")


def _rcc(c, src: Path, tgt: Path):

    command = f"pyside6-rcc.exe --threshold 50 --compress 9 -g python -o {tgt!s} {src!s}"
    print(f"Converting resource file {src.name!r}")
    activator_run(c, command=command, echo=False, hide=True)


def _rcc_list_mapping(c, src: Path):
    command = f"pyside6-rcc.exe --list-mapping {src!s}"
    result = activator_run(c, command=command, echo=False, hide=True)

    return result.stdout


RESOURCE_HEADER_TEXT = """

# region[Imports]

import os
from enum import Enum, auto, Flag
from pathlib import Path
from PySide6.QtGui import QPixmap, QIcon, QImage
from typing import Union, Optional, Iterable, TYPE_CHECKING
from collections import defaultdict
import atexit
import pp
from pprint import pprint, pformat
from gidapptools.gidapptools_qt.resources.resources_helper import ressource_item_factory, ResourceItem, AllResourceItemsMeta
from gidapptools import get_logger
from . import antistasi_logbook_resources

# endregion[Imports]

log = get_logger(__name__)

"""

RESOURCE_ITEM_COLLECTION_TEXT = """
class AllResourceItems(metaclass=AllResourceItemsMeta):
    categories = {category_names}
    missing_items = defaultdict(set)
"""
RESSOURCE_ITEM_COLLECTION_ATTRIBUTE_TEMPLATE = "    {att_name}_{cat_name_lower} = {obj_name}_{cat_name}"


AUTO_GENERATED_HINT = '"""\nThis File was auto-generated\n"""\n\n\n'

RESOURCE_ITEM_COLLECTION_POST_TEXT = r"""

    @classmethod
    def dump_missing(cls):
        missing_items = {k: [i.rsplit('_', 1)[0] for i in v] for k, v in cls.missing_items.items()}

        log.info("Missing Ressource Items:\n%s", pp.fmt(missing_items).replace("'", '"'))


if __debug__ is True:
    atexit.register(AllResourceItems.dump_missing)
"""


def _write_resource_list_mapping(raw_text: str, tgt_file: Path, converted_file_path: Path):

    def _to_txt():
        tgt_file.write_text(raw_text, encoding='utf-8', errors='ignore')

    def _to_py():

        def _make_singular(word: str) -> str:
            if word in {"IMAGES", "GIFS"}:
                return word.removesuffix("S")

            return word
        text_lines = [AUTO_GENERATED_HINT]

        try:
            module_path = tgt_file.relative_to(converted_file_path).with_suffix("").as_posix().replace('/', ".")
        except ValueError:
            module_path = f"{converted_file_path.stem}"

        text_lines.append(RESOURCE_HEADER_TEXT.format(converted_module_path=module_path))

        items = [line.split('\t') for line in raw_text.splitlines() if line]
        all_obj_names = defaultdict(list)
        for qt_path, file_path in items:
            _file_path = Path(file_path)
            obj_name = make_attribute_name(_file_path.stem).upper()
            cat_name = make_attribute_name(qt_path.removeprefix(":/").split("/")[0]).upper()
            cat_name = _make_singular(cat_name)
            all_obj_names[cat_name].append(obj_name)
            text_lines.append(f"{obj_name}_{cat_name} = ressource_item_factory(file_path={_file_path.name!r}, qt_path={qt_path!r})\n")

        text_lines.append(RESOURCE_ITEM_COLLECTION_TEXT.format(category_names="{" + ', '.join(f'{cat!r}'.casefold() for cat in all_obj_names.keys()) + '}'))
        for cat_name, obj_names in all_obj_names.items():
            for obj_name in obj_names:
                text_lines.append(RESSOURCE_ITEM_COLLECTION_ATTRIBUTE_TEMPLATE.format(att_name=obj_name.casefold(), obj_name=obj_name, cat_name=cat_name, cat_name_lower=cat_name.casefold()))
        text_lines.append(RESOURCE_ITEM_COLLECTION_POST_TEXT)
        tgt_file.write_text('\n'.join(text_lines), encoding='utf-8', errors='ignore')

    def _to_md():
        text_lines = []
        rel_conv_path = Path(THIS_FILE_DIR.name).joinpath(converted_file_path.relative_to(THIS_FILE_DIR))
        text_lines.append(f'# {rel_conv_path.name.title()} Items\n')
        text_lines.append(f"## Resource File\n\n`{rel_conv_path.as_posix()}`\n\n")
        text_lines.append("## Items\n\n")
        headers = ["name", "Qt Path", "File path"]
        sorted_items = defaultdict(list)

        def _make_sub_items(_qt_path: str, _file_path: str) -> tuple[str, str, str]:

            _file_path = Path(THIS_FILE_DIR.name).joinpath(Path(_file_path).relative_to(THIS_FILE_DIR))
            _qt_path = Path(_qt_path)
            name = _qt_path.stem
            prefix = '/'.join(_qt_path.parts[1:-1])
            sorted_items[prefix].append((name, _qt_path.as_posix(), _file_path.as_posix()))

        items = [_make_sub_items(*line.split('\t')) for line in raw_text.splitlines() if line]
        for k, v in sorted_items.items():
            text_lines.append(f'### {k.title()}\n\n')
            text_lines.append(tabulate(v, headers=headers, tablefmt="github"))

        tgt_file.write_text('\n'.join(text_lines), encoding='utf-8', errors='ignore')
    typus_map = {'.py': _to_py, '.txt': _to_txt, '.md': _to_md}
    typus_map[tgt_file.suffix.casefold()]()


def collect_resources(folder: Path, target_file: Path):
    def _qresource_section(parent, prefix: str):
        sect = et.Element("qresource")
        sect.set("prefix", prefix)
        parent.append(sect)
        return sect

    def _file_sub_element(parent, in_file: Path):
        file_sub = et.SubElement(parent, "file")
        file_sub.text = in_file.name

    def _collect_files() -> dict[str, Path]:
        _all_files = defaultdict(list)
        for fi in folder.iterdir():
            if fi.is_file() and fi.suffix != ".qrc":
                _all_files[fi.suffix.casefold()].append(fi)
        return _all_files
    all_files = _collect_files()

    root = et.Element("RCC")

    images_sect = _qresource_section(root, "images")
    for ext in [".png", ".svg", ".ico", ".jpg"]:
        for file in sorted(all_files.get(ext, []), key=lambda x: x.stem.casefold()):
            _file_sub_element(images_sect, file)

    gifs_sect = _qresource_section(root, "gifs")
    for ext in [".gif"]:
        for file in sorted(all_files.get(ext, []), key=lambda x: x.stem.casefold()):
            _file_sub_element(gifs_sect, file)

    tree = et.ElementTree(root)
    et.indent(tree, space="\t")
    with target_file.open("wb") as f:
        tree.write(f)


@task()
def convert_resources(c):
    target_folder = MAIN_MODULE_FOLDER.joinpath("gui", "resources")
    target_folder.mkdir(exist_ok=True, parents=True)

    resource_lists_folder = MISC_FOLDER.joinpath("qt_resource_lists")
    resource_lists_folder.mkdir(exist_ok=True, parents=True)
    collect_resources(RESOURCES_FILE_FOLDER, RESOURCES_FILE)
    target_name = RESOURCES_FILE.with_suffix('.py').name
    target = target_folder.joinpath(target_name)
    _rcc(c, RESOURCES_FILE, target)
    mapping_text = _rcc_list_mapping(c, RESOURCES_FILE)
    _write_resource_list_mapping(mapping_text, resource_lists_folder.joinpath(target.stem + '.md'), converted_file_path=target)
    _write_resource_list_mapping(mapping_text, target.with_name(target.stem + '_accessor.py'), converted_file_path=target)


@task()
def remove_reports(c):
    project: Project = c.project

    reports_folder = project.base_folder.joinpath("tools", "reports").resolve()

    if reports_folder.exists() is False:
        CONSOLE.print(f"{reports_folder.as_posix()!r} already removed (does not exist).")
        return
    CONSOLE.print(f"removing {reports_folder.as_posix()!r}")
    send2trash(reports_folder)
    CONSOLE.print(f"succesfully removed {reports_folder.as_posix()!r}")


from gid_tasks.hackler.imports_cleaner import import_clean_project


@task()
def clean_imports(c):
    project: Project = c.project
    list(import_clean_project(project=project))


@task()
def remove_logs(c):
    project: Project = c.project

    logs_folder = project.main_module.base_folder.joinpath("logs").resolve()

    if logs_folder.exists() is False:
        CONSOLE.print(f"{logs_folder.as_posix()!r} already removed (does not exist).")
        return
    CONSOLE.print(f"removing {logs_folder.as_posix()!r}")
    send2trash(logs_folder)
    CONSOLE.print(f"succesfully removed {logs_folder.as_posix()!r}")


@task()
def reset_storage(c):
    project: Project = c.project
    storage_folder = project.main_module.base_folder.joinpath("storage").resolve()

    to_remove = ("original_log_files",
                 "storage.logbook_db",
                 "storage.logbook_db-shm",
                 "storage.logbook_db-wal")

    for name in to_remove:
        path = storage_folder.joinpath(name).resolve()
        if path.exists() is False:
            continue

        CONSOLE.print(f"removing {path.as_posix()!r}")
        send2trash(path)
        CONSOLE.print(f"succesfully removed {path.as_posix()!r}")
