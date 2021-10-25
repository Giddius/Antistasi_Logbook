from invoke import task, Result, Context
import sqlite3
import os
import shutil
from tomlkit.toml_file import TOMLFile
from tomlkit.toml_document import TOMLDocument
from tomlkit.api import loads as toml_loads, dumps as toml_dumps, parse, document
import json
from dotenv import load_dotenv, find_dotenv, dotenv_values
from webdav3.client import Client as WebdavClient
from webdav3.exceptions import NoConnection
from datetime import datetime, timedelta
import sys
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, wait
import random
from icecream import ic
from threading import Semaphore
from dateparser import parse as date_parse
from rich import inspect as rinspect
from rich.console import Console as RichConsole
from collections import UserString, UserList, UserDict, deque, ChainMap, Counter
from tempfile import TemporaryDirectory, gettempdir
from time import sleep, time
from itertools import repeat
import re

from zipfile import ZipFile, ZIP_LZMA
from aiodav import Client as AioWebdavClient
import subprocess
from typing import Union, Optional, Iterable, Hashable, Generator, Mapping, MutableMapping, Any
import logging
from pathlib import Path
from pprint import pprint
import attr
loggers = list(logging.Logger.manager.loggerDict)


PATH_TYPE = Union[str, os.PathLike, Path]
CONSOLE = RichConsole(soft_wrap=True)


def rprint(*args, **kwargs):
    def _handle_mappings(in_item):
        if isinstance(in_item, (Mapping, MutableMapping)):
            return dict(in_item)
        return in_item
    args = [_handle_mappings(item) for item in args]
    CONSOLE.print(*args, **kwargs)
    CONSOLE.rule()


print = rprint


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
    except NoConnection:
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
                         "VERSION": "VersionField"}

    def __init__(self, text: str) -> None:
        self.original_text = text
        self.text = str(text)

    def _remove_comment_lines(self) -> None:
        self.text = self.comment_line_regex.sub("", self.text).strip()

    def _replace_imports(self) -> None:
        new_import_lines = ["from peewee import Model, TextField, IntegerField, BooleanField, AutoField, DateTimeField, ForeignKeyField, SQL, BareField, SqliteDatabase, Field, DatabaseProxy",
                            "from .custom_fields import RemotePathField,PathField,VersionField",
                            "from playhouse.sqlite_ext import SqliteExtDatabase",
                            "from playhouse.sqliteq import SqliteQueueDatabase"]
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
