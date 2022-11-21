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
CONSOLE.print(RULE)


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


@task
def checky(c):
    try:
        NEXTCLOUD_CLIENT = WebdavClient(NEXTCLOUD_OPTIONS)
        print(NEXTCLOUD_CLIENT.list(NEXTCLOUD_BASE_FOLDER))
    finally:
        NEXTCLOUD_CLIENT.session.close()


def download_log_file(paths, try_num=1):
    try:
        client = WebdavClient(NEXTCLOUD_OPTIONS)
        client.download_sync(remote_path=paths[0], local_path=paths[1])
        sleep(random.uniform(0.1, 3.0))
        client.session.close()
    except Exception:
        if try_num <= 10:
            print(f'retrying because of NoConnection Error, try_number: {try_num}')
            sleep(random.randint(5, 10))
            download_log_file(paths, try_num + 1)
        else:
            raise
    finally:
        client.session.close()


def _date_time_from_name(path):
    matched_data = LOG_NAME_DATE_TIME_REGEX.search(os.path.basename(path))
    if matched_data:
        date_time_string = f"{matched_data.group('year')}-{matched_data.group('month')}-{matched_data.group('day')} {matched_data.group('hour')}:{matched_data.group('minute')}:{matched_data.group('second')}"
        date_time = datetime.strptime(date_time_string, "%Y-%m-%d %H:%M:%S")
        return date_time
    else:
        raise RuntimeError(f'unable to find date_time_string in {os.path.basename(path)}')


@task
def get_logs(c, low_filter_date="2021.january.01"):
    NEXTCLOUD_CLIENT = WebdavClient(NEXTCLOUD_OPTIONS)
    try:
        to_download = []
        logs_base_folder = os.path.join(TEMP_FOLDER, 'antistasi_logs')
        clean_create_folder(logs_base_folder)
        server_to_get = ['Mainserver_1', 'Mainserver_2', "Testserver_1", "Testserver_2", "Testserver_3"]
        sub_folder_to_get = 'Server'
        filter_date = date_parse(low_filter_date, settings={'TIMEZONE': 'UTC'}) if low_filter_date is not None else low_filter_date
        if filter_date is not None:
            rprint(f"Getting all logs modified after {filter_date.strftime('%Y-%m-%d_%H-%M-%S')}")
        for server in server_to_get:
            remote_path = f"{NEXTCLOUD_BASE_FOLDER}/{server}/{sub_folder_to_get}"
            local_path = pathmaker(logs_base_folder, server)
            clean_create_folder(local_path)
            for file in NEXTCLOUD_CLIENT.list(remote_path, get_info=True):

                if file.get('isdir') is False:
                    log_file_remote_path = f"{remote_path}/{os.path.basename(file.get('path'))}"
                    log_file_local_path = pathmaker(local_path, os.path.basename(file.get("path")))
                    file_date = _date_time_from_name(file.get('path'))

                    if filter_date is None:
                        to_download.append([log_file_remote_path, log_file_local_path])
                    elif file_date >= filter_date:
                        to_download.append([log_file_remote_path, log_file_local_path])
        with ThreadPoolExecutor(20) as pool:
            random.shuffle(to_download)
            random.shuffle(to_download)
            list(pool.map(download_log_file, to_download))
    finally:
        NEXTCLOUD_CLIENT.session.close()


@task
def archive_reports(c):
    def _make_archive_name():
        datetime_format = "%Y-%m-%d_%H-%M-%S"
        all_dates = []
        for dirname, folderlist, filelist in os.walk(REPORTS_FOLDER):
            for file in filelist:
                date_part = file.split(']', 1)[0].strip('[')
                date = datetime.strptime(date_part, datetime_format)
                all_dates.append(date)

        first_date = min(all_dates)
        last_date = max(all_dates)
        name = first_date.strftime(datetime_format) + '--' + last_date.strftime(datetime_format) + '.zip'
        return name
    archive_folder = TOOLS_FOLDER.joinpath("archived_reports")
    archive_folder.mkdir(exist_ok=True, parents=True)
    archive_name = _make_archive_name()
    archive_path = archive_folder.joinpath(archive_name)
    with ZipFile(archive_path, 'w', compression=ZIP_LZMA) as zippy:
        for dirname, folderlist, filelist in os.walk(REPORTS_FOLDER):
            for file in filelist:
                file_path = Path(dirname, file)
                zippy.write(file_path, file_path.relative_to(REPORTS_FOLDER))
    for item in REPORTS_FOLDER.iterdir():
        if item.is_dir():
            shutil.rmtree(item)


class ModelsCode:
    comment_line_regex = re.compile(r"^\#.*", re.MULTILINE)
    unknown_field_regex = re.compile(r"^\s+(?P<attr_name>\w+)\s*\=\s*UnknownField\((?P<field_kwargs>(\w+\=\w+\,?\s?)+)\)\s*\#\s*(?P<unknown_type>[A-z]+)", re.MULTILINE)
    extra_field_types = {"REMOTEPATH": "RemotePathField",
                         "PATH": "PathField",
                         "VERSION": "VersionField",
                         "URL": "URLField"}

    def __init__(self, text: str) -> None:
        self.original_text = text
        self.text = str(text)

    def _remove_comment_lines(self) -> None:
        self.text = self.comment_line_regex.sub("", self.text).strip()

    def _replace_imports(self) -> None:
        new_import_lines = ["from peewee import Model, TextField, IntegerField, BooleanField, AutoField, DateTimeField, ForeignKeyField, SQL, BareField, SqliteDatabase, Field, DatabaseProxy",
                            "from .custom_fields import RemotePathField, PathField, VersionField, URLField"]
        self.text = self.text.replace("from peewee import *", '\n'.join(new_import_lines))

    def _replace_db_instance(self) -> None:
        new_db_instance_line = "database = DatabaseProxy()"
        db_instance_regex = re.compile(r"database \= SqliteDatabase\(\'.*\'\)")
        self.text = db_instance_regex.sub(new_db_instance_line, self.text)

    def _remove_unknown_field_class(self) -> None:
        class_text = """
class UnknownField(object):
    def __init__(self, *_, **__): pass
    """.strip()
        self.text = self.text.replace(class_text, "")

    def _replace_unknow_field_types(self) -> None:
        def _sub_function(match: re.Match) -> str:
            attr_name = match.group('attr_name')
            unknown_type_name = self.extra_field_types.get(match.group("unknown_type"))
            field_kwargs = match.group("field_kwargs")
            indentation = ' ' * 4
            _out = f"{indentation}{attr_name} = {unknown_type_name}({field_kwargs})"

            return _out

        self.text = self.unknown_field_regex.sub(_sub_function, self.text)

    def _add_lazy_loading(self) -> None:
        new_text = []
        for idx, line in enumerate(self.text.splitlines()):

            if idx > 3 and "ForeignKeyField" in line:

                line = line.rstrip(')') + ', lazy_load=True)'
            new_text.append(line)
        self.text = '\n'.join(new_text)

    def process(self) -> None:
        self._remove_comment_lines()
        self._replace_imports()
        self._replace_db_instance()
        self._remove_unknown_field_class()
        self._replace_unknow_field_types()
        self._add_lazy_loading()

    def __str__(self) -> str:
        return self.text


@task
def create_models(c, db_file=None):

    target_dir = THIS_FILE_DIR
    target_dir.mkdir(exist_ok=True, parents=True)
    db_file = target_dir.joinpath('storage.db')

    conn = sqlite3.connect(str(db_file), timeout=5)
    for file in PROJECT_INFO.important_folder.get('sql_scripts').iterdir():
        if file.is_file() and file.suffix.casefold() == '.sql':
            cursor = conn.cursor()
            cursor.executescript(file.read_text(encoding='utf-8', errors='ignore'))
            cursor.close()
    conn.close()

    try:
        with c.prefix(str(PROJECT_INFO.important_files.get('activate_venv'))):
            command = f"pwiz -e sqlite -i -o {str(db_file)}"
            result: Result = c.run(command, echo=False, hide=True, asynchronous=False)

        text = ModelsCode(str(result.stdout))

        text.process()
        out_file: Path = PROJECT_INFO.important_folder.get("main_module").joinpath("storage").joinpath("models").joinpath("models.py")
        out_file.write_text(str(text), encoding='utf-8', errors='ignore')

    finally:

        os.remove(str(db_file))


@task(name="convert-designer-files")
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


@task(name="convert-resources")
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
def build_onefile(c):
    pyinstaller_script = THIS_FILE_DIR.joinpath("tools", "quick_pyinstaller_noconsole.bat")
    spec_file = THIS_FILE_DIR.joinpath("tools", "Antistasi_Logbook_onefile.spec")
    activator_run(c, f"{str(pyinstaller_script)} {str(spec_file)}")


@task()
def build_onedir(c):
    pyinstaller_script = THIS_FILE_DIR.joinpath("tools", "quick_pyinstaller_noconsole.bat")
    spec_file = THIS_FILE_DIR.joinpath("tools", "Antistasi_Logbook.spec")
    activator_run(c, f"{str(pyinstaller_script)} {str(spec_file)}")


# from gidapptools.gid_scribe.markdown.document import MarkdownDocument, MarkdownHeadline, MarkdownImage, MarkdownCodeBlock, MarkdownRawText, MarkdownSimpleList
from gidapptools.general_helper.string_helper import StringCaseConverter, StringCase


# @task()
# def make_readme(c):
#     project: Project = c.project
#     top_headline = project.general_project_data["name"]
#     top_headline = StringCaseConverter.convert_to(top_headline, StringCase.TITLE)
#     top_image = THIS_FILE_DIR.joinpath("docs", "images", "app_icon.png")
#     readme_document = MarkdownDocument(THIS_FILE_DIR.joinpath("README.md"), top_headline=top_headline, top_image=top_image)
#     fact_list = MarkdownSimpleList(ordered=False)
#     fact_list.add_entry(f"**__Version:__** `{project.version!s}`")

#     readme_document.add_part(fact_list)
#     readme_document.to_file()


@task()
def remove_reports(c):
    project: Project = c.project

    reports_folder = project.base_folder.joinpath("tools", "reports").resolve()

    if reports_folder.exists() is False:
        print(f"{reports_folder.as_posix()!r} already removed (does not exist).")
        return
    print(f"removing {reports_folder.as_posix()!r}")
    send2trash(reports_folder)
    print(f"succesfully removed {reports_folder.as_posix()!r}")


from gid_tasks.hackler.imports_cleaner import import_clean_project


@task
def clean_imports(c):
    project: Project = c.project
    list(import_clean_project(project=project))


@task()
def remove_logs(c):
    project: Project = c.project

    logs_folder = project.main_module.base_folder.joinpath("logs").resolve()

    if logs_folder.exists() is False:
        print(f"{logs_folder.as_posix()!r} already removed (does not exist).")
        return
    print(f"removing {logs_folder.as_posix()!r}")
    send2trash(logs_folder)
    print(f"succesfully removed {logs_folder.as_posix()!r}")


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

        print(f"removing {path.as_posix()!r}")
        send2trash(path)
        print(f"succesfully removed {path.as_posix()!r}")
