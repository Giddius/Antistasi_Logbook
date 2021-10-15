"""
WiP.

Soon.
"""

# region [Imports]
import antistasi_serverlog_statistic

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
from gidapptools.meta_data import get_meta_info, get_meta_paths, get_meta_item
from gidapptools.meta_data.interface import app_meta
from dotenv import load_dotenv
from gidapptools.general_helper.timing import time_execution
from antistasi_serverlog_statistic.webdav.webdav_manager import WebdavManager
from antistasi_serverlog_statistic.items.base_item import AbstractBaseItem

from antistasi_serverlog_statistic.storage.storage_db import StorageDB
from antistasi_serverlog_statistic.updater import Updater
import atexit
# endregion[Imports]


# region [TODO]


# endregion [TODO]

# region [Logging]


# endregion[Logging]

# region [Constants]


THIS_FILE_DIR = Path(__file__).parent.absolute()

META_PATHS = get_meta_paths()
META_INFO = get_meta_info()
# endregion[Constants]


class NoThreadPoolExecutor:

    def map(self, func, items):
        return map(func, items)

    def shutdown(self):
        return


def main():
    load_dotenv(r"D:\Dropbox\hobby\Modding\Programs\Github\My_Repos\Antistasi_ServerLog_Statistic\antistasi_serverlog_statistic\nextcloud.env")
    for item in AbstractBaseItem.__subclasses__():
        if inspect.isabstract(item) is False:
            StorageDB.register_item(item)
    db = StorageDB()

    web_dav = WebdavManager(log_folder_remote_path="Antistasi_Community_Logs", database=db)
    updater = Updater(timedelta(seconds=10000), db, web_dav, thread_pool=ThreadPoolExecutor(100))
    # updater.start()
    updater._update()
    run_for = 600
    steps = 5
    sleep_amount = run_for / steps
    start_t = time()
    theoretical_end_time = start_t + run_for
    with time_execution(f"should be {run_for} s"):
        for i in range(steps):
            # if i == 3:
            #     print(f"{'!|!'*50}\ntriggering update\n{'!|!'*50}")
            #     updater.update()
            sleep(sleep_amount)
            print(f"sleept for {sleep_amount} s\n| remaining time: {run_for-((i+1)*sleep_amount)} s |\n{'-'*25}")
            print(f"{updater.is_alive()=}")
        updater.close()


# region[Main_Exec]
if __name__ == '__main__':
    main()
# endregion[Main_Exec]
