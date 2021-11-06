"""
WiP.

Soon.
"""

# region [Imports]
from antistasi_logbook import setup
setup()

import gc
import os
import re
import sys
import json
import queue
import math
import base64
import pickle
import random
import shelve
import dataclasses
import shutil
import asyncio
import logging
import sqlite3
import platform
import importlib
import subprocess
import unicodedata
import inspect

from time import sleep, process_time, process_time_ns, perf_counter, perf_counter_ns
from io import BytesIO, StringIO
from abc import ABC, ABCMeta, abstractmethod
from copy import copy, deepcopy
from enum import Enum, Flag, auto
from time import time, sleep
from pprint import pprint, pformat
from pathlib import Path
from string import Formatter, digits, printable, whitespace, punctuation, ascii_letters, ascii_lowercase, ascii_uppercase
from timeit import Timer
from typing import TYPE_CHECKING, Union, Callable, Iterable, Optional, Mapping, Any, IO, TextIO, BinaryIO
from zipfile import ZipFile, ZIP_LZMA
from datetime import datetime, timezone, timedelta
from tempfile import TemporaryDirectory
from textwrap import TextWrapper, fill, wrap, dedent, indent, shorten
from functools import wraps, partial, lru_cache, singledispatch, total_ordering, cached_property
from importlib import import_module, invalidate_caches
from contextlib import contextmanager, asynccontextmanager
from statistics import mean, mode, stdev, median, variance, pvariance, harmonic_mean, median_grouped
from collections import Counter, ChainMap, deque, namedtuple, defaultdict
from urllib.parse import urlparse
from importlib.util import find_spec, module_from_spec, spec_from_file_location
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from importlib.machinery import SourceFileLoader
from gidapptools.meta_data import get_meta_info, get_meta_paths
from gidapptools.meta_data.interface import app_meta, get_meta_config
from dotenv import load_dotenv
from gidapptools.general_helper.timing import time_execution
import click
from gidapptools.gid_signal.interface import get_signal
import atexit
from antistasi_logbook.storage.models.models import Server, RemoteStorage
from antistasi_logbook.storage.database import get_database
from antistasi_logbook.updating.updater import get_updater, get_update_thread
if TYPE_CHECKING:
    from gidapptools.gid_config.interface import GidIniConfig
# endregion[Imports]


# region [TODO]


# endregion [TODO]

# region [Logging]


# endregion[Logging]

# region [Constants]


THIS_FILE_DIR = Path(__file__).parent.absolute()

META_PATHS = get_meta_paths()
META_INFO = get_meta_info()
CONFIG: "GidIniConfig" = get_meta_config().get_config('general')
CONFIG.config.load()
# endregion[Constants]


@click.group(name='antistasi-logbook')
def cli():
    ...


@cli.group(name="settings", help="Commands to change the Application settings without the GUI.")
def settings():
    ...


@settings.command(name="set-keep-downloaded-files", help="Changes wether to delete the log files after parsing or to keep it on the hard drive.")
@click.argument("value", type=click.BOOL)
def set_keep_downloaded_files(value):
    config_value = CONFIG.get("downloading", "keep_downloaded_files", default="False")
    if value is not config_value:
        CONFIG.set("downloading", "keep_downloaded_files", value)
    current_value = CONFIG.get("downloading", "keep_downloaded_files", default="False")
    click.echo(f"Setting 'keep_downloaded_files' is now set to {str(current_value)!r}")


@settings.command(name="set-local-storage-folder", help="Sets the local folder where the downloaded log files are stored.use 'UNSET' if you want to revert to the default.")
@click.argument("value", type=click.Path(file_okay=False))
def set_local_storage_folder(value):
    if value == "UNSET":
        value = None
    else:
        value = Path(value)
    CONFIG.set("folder", "local_storage_folder", value)
    current_value = CONFIG.get("folder", "local_storage_folder", default=None)
    if isinstance(current_value, Path):
        current_value = current_value.as_posix()
    click.echo(f"Setting 'local_storage_folder' is now set to {str(current_value)!r}")


@cli.command(help="Runs a single update of all enabled Server without starting the GUI.")
@click.option('--login', '-l', default=None)
@click.option('--password', '-p', default=None)
def update(login, password):
    amount_updated = 0

    def count_amount(log_file) -> None:
        nonlocal amount_updated
        amount_updated += 1

    def set_auth():
        if login is not None and password is not None:
            item: RemoteStorage = RemoteStorage.get(name='community_webdav')
            item.set_login_and_password(login=login, password=password, store_in_db=False)

    log_file_updated_signal = get_signal("log_file_updated")
    log_file_updated_signal.connect(count_amount)
    db = get_database()
    updater = get_updater(database=db)
    set_auth()
    try:
        for server in Server.select():
            updater(server=server)
    finally:
        click.echo(f"{amount_updated} log files were updated.")
        db.optimize()
        db.vacuum()
        db.shutdown()


# region[Main_Exec]
if __name__ == '__main__':
    if getattr(sys, 'frozen', False):
        cli(sys.argv[1:])
# endregion[Main_Exec]
