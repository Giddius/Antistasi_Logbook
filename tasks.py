from invoke import task
import os
import shutil
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
from rich import print as rprint, inspect as rinspect
from time import sleep, time
from itertools import repeat
import re
from zipfile import ZipFile, ZIP_LZMA
from aiodav import Client as AioWebdavClient
import subprocess
import logging
from pathlib import Path

loggers = list(logging.Logger.manager.loggerDict)


# region [Constants]
MODULE_NAME = "antistasi_serverlog_statistic"
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

REPORTS_FOLDER = TOOLS_FOLDER.joinpath('reports')
MAIN_MODULE_FOLDER = THIS_FILE_DIR.joinpath(MODULE_NAME)
LOG_NAME_DATE_TIME_REGEX = re.compile(r"(?P<year>\d\d\d\d).(?P<month>\d+?).(?P<day>\d+).(?P<hour>[012\s]?\d).(?P<minute>[0123456]\d).(?P<second>[0123456]\d)")

IMPORTANT_FOLDER = [TEMP_FOLDER, MISC_FOLDER, DOCS_FOLDER, MAIN_MODULE_FOLDER]
# endregion[Constants]


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
for folder_path in IMPORTANT_FOLDER:
    create_folder(folder_path)


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
