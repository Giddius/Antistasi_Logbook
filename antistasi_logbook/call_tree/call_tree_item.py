"""
WiP.

Soon.
"""

# region [Imports]

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
import inspect

from time import sleep, process_time, process_time_ns, perf_counter, perf_counter_ns
from io import BytesIO, StringIO
from abc import ABC, ABCMeta, abstractmethod
from copy import copy, deepcopy
from enum import Enum, Flag, auto, unique
from time import time, sleep
from pprint import pprint, pformat
from pathlib import Path
from string import Formatter, digits, printable, whitespace, punctuation, ascii_letters, ascii_lowercase, ascii_uppercase
from timeit import Timer
from typing import TYPE_CHECKING, Union, Callable, Iterable, Optional, Mapping, Any, IO, TextIO, BinaryIO, Hashable, Generator, Literal, TypeVar, TypedDict, AnyStr
from zipfile import ZipFile, ZIP_LZMA
from datetime import datetime, timezone, timedelta
from tempfile import TemporaryDirectory
from textwrap import TextWrapper, fill, wrap, dedent, indent, shorten
from functools import wraps, partial, lru_cache, singledispatch, total_ordering, cached_property
from importlib import import_module, invalidate_caches
from contextlib import contextmanager, asynccontextmanager, nullcontext, closing, ExitStack, suppress
from statistics import mean, mode, stdev, median, variance, pvariance, harmonic_mean, median_grouped
from collections import Counter, ChainMap, deque, namedtuple, defaultdict
from urllib.parse import urlparse
from importlib.util import find_spec, module_from_spec, spec_from_file_location
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from importlib.machinery import SourceFileLoader

from antistasi_logbook.storage.models.models import LogFile, AntstasiFunction, LogRecord

from gidapptools import get_logger
import networkx as nx
import matplotlib.pyplot as plt
# endregion[Imports]

# region [TODO]

# TODO: This is Proof-of-Concept!

# endregion [TODO]

# region [Logging]


# endregion[Logging]

# region [Constants]

from gidapptools.general_helper.timing import get_dummy_profile_decorator_in_globals
get_dummy_profile_decorator_in_globals()
THIS_FILE_DIR = Path(__file__).parent.absolute()
log = get_logger(__name__)

# endregion[Constants]


class CallTreeNode:

    def __init__(self, function: AntstasiFunction):
        self.function = function
        self.amount_called = 0
        self.amount_called_by = 0
        self.nodes_called: set["CallTreeNode"] = set()
        self.called_by_nodes: set["CallTreeNode"] = set()

    def add_called_node(self, node):
        self.amount_called += 1
        self.nodes_called.add(node)

    def add_called_by_node(self, node):
        self.amount_called_by += 1
        self.called_by_nodes.add(node)

    def __hash__(self) -> int:
        return hash(self.function.id)


class CallTree:

    def __init__(self, log_file: LogFile) -> None:
        self.log_file = log_file
        self.root = nx.DiGraph(nodesep=10.0)
        self.init_server_node = None
        self.label_dict = {}

    def populate(self):
        all_records = tuple(LogRecord.select().where((LogRecord.log_file_id == self.log_file.id) & (LogRecord.logged_from != None) & (LogRecord.called_by != None)).order_by(LogRecord.recorded_at))
        all_functions = {r.logged_from for r in all_records}.union({r.called_by for r in all_records})
        nodes = {f.name: CallTreeNode(f) for f in all_functions}

        for record in all_records:
            logged_from_node = nodes[record.logged_from.name]
            called_by_node = nodes[record.called_by.name]
            logged_from_node.add_called_by_node(called_by_node)
            called_by_node.add_called_node(logged_from_node)
        add_list = []
        all_again = set()
        for name, node in nodes.items():
            all_again.add(node)
            if name.casefold().split('_')[-1] == "initserver":
                self.init_server_node = node
            for calling_node in node.called_by_nodes:
                all_again.add(calling_node)
                add_list.append((calling_node, node, node.amount_called_by + calling_node.amount_called))
            for called_node in node.nodes_called:
                all_again.add(called_node)
                add_list.append((node, called_node, called_node.amount_called_by + node.amount_called))

        self.root.add_weighted_edges_from(add_list)
        for node in nodes.values():
            self.label_dict[node] = f"{node.function.pretty_name}\n{node.amount_called_by!r}"
            self.root.add_node(node, label=f"{node.function.pretty_name}: {node.amount_called_by!r}")


# region[Main_Exec]
if __name__ == '__main__':
    pass

# endregion[Main_Exec]
