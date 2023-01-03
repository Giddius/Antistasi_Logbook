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

import subprocess
import inspect

from time import sleep, process_time, process_time_ns, perf_counter, perf_counter_ns
from io import BytesIO, StringIO
from abc import ABC, ABCMeta, abstractmethod
from copy import copy, deepcopy
from enum import Enum, Flag, auto, unique
from pprint import pprint, pformat
from pathlib import Path
from string import Formatter, digits, printable, whitespace, punctuation, ascii_letters, ascii_lowercase, ascii_uppercase
from timeit import Timer
from typing import (TYPE_CHECKING, TypeVar, TypeGuard, TypeAlias, Final, TypedDict, Generic, Union, Optional, ForwardRef, final,
                    no_type_check, no_type_check_decorator, overload, get_type_hints, cast, Protocol, runtime_checkable, NoReturn, NewType, Literal, AnyStr, IO, BinaryIO, TextIO, Any)
from collections import Counter, ChainMap, deque, namedtuple, defaultdict
from collections.abc import (AsyncGenerator, AsyncIterable, AsyncIterator, Awaitable, ByteString, Callable, Collection, Container, Coroutine, Generator,
                             Hashable, ItemsView, Iterable, Iterator, KeysView, Mapping, MappingView, MutableMapping, MutableSequence, MutableSet, Reversible, Sequence, Set, Sized, ValuesView)
from zipfile import ZipFile, ZIP_LZMA
from datetime import datetime, timezone, timedelta
from tempfile import TemporaryDirectory
from textwrap import TextWrapper, fill, wrap, dedent, indent, shorten
from functools import wraps, partial, lru_cache, singledispatch, total_ordering, cached_property, cache
from contextlib import contextmanager, asynccontextmanager, nullcontext, closing, ExitStack, suppress
from statistics import mean, mode, stdev, median, variance, pvariance, harmonic_mean, median_grouped
from urllib.parse import urlparse
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, Future, wait, as_completed, ALL_COMPLETED, FIRST_EXCEPTION, FIRST_COMPLETED
from gidapptools.general_helper.import_helper import import_from_name, import_from_file_path

from peewee import Model, Metadata, Field, ForeignKeyField
from graphviz import Source, unflatten
from gidapptools.general_helper.string_helper import StringCase, StringCaseConverter
import jinja2

if sys.version_info >= (3, 11):
    from typing import Self
else:
    from typing_extensions import Self

if TYPE_CHECKING:
    ...

# endregion[Imports]

# region [TODO]


# endregion [TODO]

# region [Logging]


# endregion[Logging]

# region [Constants]

THIS_FILE_DIR = Path(__file__).parent.absolute()

MODELS_FILE_PATH: Path = THIS_FILE_DIR.parent.parent.joinpath("antistasi_logbook", "storage", "models", "models.py").resolve()

# TEMPLATE_PATH: Path = THIS_FILE_DIR.joinpath("db_diagram_template.jinja")
TEMPLATE_PATH: Path = THIS_FILE_DIR.joinpath("_templates", "db_diagram_w_clusters_template.jinja").resolve()


# endregion[Constants]


colors = list({"#565ADB",
               "#56F859",
               "#F97F56",
               "#5CEDFD",
               "#F157FB",
               "#EAFA56",
               "#5B8156",
               "#B2AFBA",
               "#AE5B99",
               "#9FFCA0",
               "#56C6A4",
               "#FCA7FE",
               "#A1C059",
               "#679FFE",
               "#FEC597",
               "#B1E5F5",
               "#A575E9",
               "#EE7FB4",
               "#7387A2",
               "#AB7E56",
               "#57BE5B",
               "#EDFEAD",
               "#59FEB1",
               "#A6F855",
               "#5E5589",
               "#E2BA55",
               "#F95788",
               "#ACA9FE",
               "#E9D4D8",
               "#81C7DB", })

random.shuffle(colors)


green_colors = [i + f'{125:X}' for i in ("#7FFF00",
                                         "#32CD32",
                                         "#00FF00",
                                         "#228B22",
                                         "#008000",
                                         "#006400",
                                         "#9ACD32",
                                         "#00FF7F",
                                         "#00FA9A",
                                         "#90EE90",
                                         "#98FB98",
                                         "#8FBC8F",
                                         "#3CB371",
                                         "#20B2AA",
                                         "#2E8B57",
                                         "#808000",
                                         "#556B2F",
                                         "#6B8E23")]

random.shuffle(green_colors)

# blue_colors = [i + f'{125:X}' for i in ("#F0F8FF",
#                                         "#E6E6FA",
#                                         "#B0E0E6",
#                                         "#ADD8E6",
#                                         "#87CEFA",
#                                         "#87CEEB",
#                                         "#00BFFF",
#                                         "#B0C4DE",
#                                         "#1E90FF",
#                                         "#6495ED",
#                                         "#4682B4",
#                                         "#5F9EA0",
#                                         "#7B68EE",
#                                         "#6A5ACD",
#                                         "#483D8B",
#                                         "#4169E1",
#                                         "#0000FF",
#                                         "#0000CD",
#                                         "#00008B",
#                                         "#000080",
#                                         "#191970",
#                                         "#8A2BE2",
#                                         "#4B0082")]

blue_colors = [i + f'{125:X}' for i in ("#00BFFF",
                                        "#00BFFF",
                                        "#00BFFF",
                                        "#00BFFF",
                                        "#00BFFF",
                                        "#00BFFF",
                                        "#00BFFF",
                                        "#00BFFF",
                                        "#00BFFF",
                                        "#00BFFF",
                                        "#00BFFF")]

random.shuffle(blue_colors)


orange_colors = [i + f'{125:X}' for i in ("#FF7F50",
                                          "#FF6347",
                                          "#FF4500",
                                          #   "#FFD700",
                                          #   "#FFA500",
                                          "#FF8C00")]
random.shuffle(orange_colors)


violet_colors = [i + f'{125:X}' for i in ("#b974b9",
                                          "#DDA0DD",
                                          "#EE82EE",
                                          "#DA70D6",
                                          "#FF00FF",
                                          "#FF00FF",
                                          "#BA55D3",
                                          "#9370DB",
                                          "#8A2BE2",
                                          "#9400D3",
                                          "#9932CC",
                                          "#8B008B",
                                          "#800080",
                                          "#4B0082")]


random.shuffle(violet_colors)


class ColumnNode:

    _default_font_color: str = "#ffffff"
    _default_font: str = "Fira Code"

    _default_typus_font: str = "Fira Code"
    _default_typus_font_color = "#ffffff"
    _default_typus_background_color = "transparent"

    _default_edge_color: str = "#228c47"

    def __init__(self,
                 name: str,
                 field_class: type[Field],
                 field_type: str,
                 is_primary_key: bool = False,
                 is_hidden: bool = False,
                 target_table_name: Optional[str] = None,
                 target_column_name: Optional[str] = None) -> None:
        self.name = name
        self.field_class = field_class
        self.field_type = field_type
        self.is_primary_key = is_primary_key
        self.is_hidden = is_hidden

        self.target_table_name = target_table_name
        self.target_column_name = target_column_name

        self.target_table_node: Optional[Self] = None
        self.target_column_node: Optional[Self] = None

    @cached_property
    def edge_color(self) -> str:
        return self.target_table_node.background_color[:7]

    @cached_property
    def font(self) -> str:
        return self._default_font

    @cached_property
    def font_color(self) -> str:
        return self._default_font_color

    @cached_property
    def typus_font(self) -> str:
        return self._default_typus_font

    @cached_property
    def typus_font_color(self) -> str:
        return self._default_typus_font_color

    @cached_property
    def field_class_name(self) -> str:
        return self.field_class.__name__

    @cached_property
    def typus_background_color(self) -> str:
        return self._default_typus_background_color

    @cached_property
    def is_foreign_key_column(self) -> bool:
        return all([self.is_primary_key is False,
                    self.target_table_name is not None,
                    self.target_column_name is not None,
                    issubclass(self.field_class, ForeignKeyField)])

    def resolve_targets(self, all_tables: dict[str, "TableNode"]) -> None:
        if self.is_foreign_key_column:
            self.target_table_node = all_tables[self.target_table_name]
            self.target_column_node = self.target_table_node.column_map[self.target_column_name]

    @classmethod
    def from_peewee_field(cls, field: Field) -> Self:
        foreign_key_kwargs = {}
        if isinstance(field, ForeignKeyField):
            foreign_key_kwargs = {"target_table_name": field.rel_model.get_meta().table_name,
                                  "target_column_name": field.rel_field.name}

        return cls(name=field.name,
                   field_class=field.__class__,
                   field_type=field.field_type,
                   is_primary_key=field.primary_key,
                   is_hidden=field._hidden,
                   **foreign_key_kwargs)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name={self.name!r}, field_class={self.field_class!r}, field_type={self.field_type!r})"


class TableNode:
    _default_background_color: str = "#e3fafc"
    _default_main_color: str = "#0b7285"
    _default_font_color: str = "#ffffff"
    _default_font: str = "Fira Code Bold"

    def __init__(self, name: str, ) -> None:
        self.name = name
        self._columns: dict[str, ColumnNode] = {}
        self._background_color_selection = None
        self.group = ""
        self.weight = 0

    @cached_property
    def background_color(self) -> str:
        if self._background_color_selection is None:
            return colors.pop(0)

        return self._background_color_selection.pop(0)

    @cached_property
    def main_color(self) -> str:
        return self._default_main_color

    @cached_property
    def font(self) -> str:
        return self._default_font

    @cached_property
    def font_color(self) -> str:
        return self._default_font_color

    @cached_property
    def column_map(self) -> dict[str, ColumnNode]:
        return self._columns

    @cached_property
    def column_list(self) -> list[ColumnNode]:
        return list(self._columns.values())

    @cached_property
    def foreign_key_columns(self) -> list[ColumnNode]:
        return [column for column in self.column_list if column.is_foreign_key_column]

    def _column_sort_func(self, in_column: ColumnNode):
        comments_and_marked_value = 0
        if in_column.name == "comments" or in_column.field_class.__name__ == "CommentsField":
            comments_and_marked_value = 1
        if in_column.name == "marked" or in_column.field_class.__name__ == "MarkedField":
            comments_and_marked_value = 2

        return (1 if in_column.is_hidden else 0,
                0 if in_column.is_primary_key else 1,
                comments_and_marked_value,
                # 1 if in_column.is_foreign_key_column else 0,
                in_column.name.casefold())

    def add_column(self, column: ColumnNode) -> None:
        self._columns[column.name] = column

    def resolve_foreign_key_targets(self, all_tables: dict[str, "TableNode"]) -> None:
        for column in self.column_list:
            column.resolve_targets(all_tables=all_tables)

    def make_label(self) -> str:
        ...

    def make_edges(self) -> list[str]:
        ...

    @classmethod
    def from_peewee_model(cls, model: type[Model]) -> Self:

        instance = cls(name=model.get_meta().table_name)
        for column in model.get_meta().sorted_fields:
            instance.add_column(ColumnNode.from_peewee_field(column))

        return instance

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name={self.name!r})"


class FontData:

    def __init__(self,
                 general_font_name: str = "Fira Code",
                 general_font_size: int = 8,

                 node_font_name: Optional[str] = None,
                 node_font_size: Optional[int] = None,

                 edge_font_name: Optional[str] = None,
                 edge_font_size: Optional[int] = None) -> None:
        self.general_font = general_font_name
        self.general_font_size = general_font_size

        self.node_font = node_font_name or self.general_font
        self.node_font_size = node_font_size or self.general_font_size

        self.edge_font = edge_font_name or self.node_font
        self.edge_font_size = edge_font_size or self.node_font_size


class ColorData:

    def __init__(self,
                 main_color: str) -> None:
        self.main_color = main_color


def get_nodes(models_file_path: Path) -> list[TableNode]:
    models_module = import_from_file_path(models_file_path)

    tables = [TableNode.from_peewee_model(model=model) for model in models_module.get_all_actual_models()]

    table_map = {t.name: t for t in tables}

    for table in tables:
        table.resolve_foreign_key_targets(all_tables=table_map)

    return tables


def is_no_target(in_table_node: TableNode, all_tables: list[TableNode]):
    for table in all_tables:
        for fc in table.foreign_key_columns:
            if fc.target_table_name == in_table_node.name:
                return False
    return True


def make_graph_string(graph_name: str, font_data: FontData, tables: list[TableNode], clusters: dict[str, list[TableNode]], all_tables: list[TableNode]) -> str:
    template = jinja2.Environment(loader=jinja2.BaseLoader()).from_string(TEMPLATE_PATH.read_text(encoding='utf-8', errors='ignore'))

    return template.render(graph_name=graph_name, font_data=font_data, tables=tables, clusters=clusters, background_color="#00000080", all_tables=all_tables)


def save_graph(in_graph_string: str, output_file_path: Path):
    output_file_path.parent.mkdir(parents=True, exist_ok=True)

    graphviz_source = Source(in_graph_string)
    graphviz_source = graphviz_source.unflatten(chain=2)
    # output_file_path.with_suffix(".dot").write_text(in_graph_string, encoding='utf-8', errors='ignore')

    graphviz_source.render(output_file_path,
                           format="svg",
                           cleanup=True,
                           view=False)
    graphviz_source.render(output_file_path.with_suffix(""),
                           format="png",
                           cleanup=True,
                           view=False)


def make_clusters(in_tables: list[TableNode]) -> tuple[dict[str, list[TableNode]], list[TableNode]]:
    clusters = {"LOGRECORD": [],
                "LOGFILE": [],
                "META": [],
                "SERVER": []}

    logrecord_table_names = ("LogRecord", "ArmaFunction", "ArmaFunctionAuthorPrefix", "Message", "RecordClass", "RecordOrigin", "LogLevel")

    logfile_table_names = ("LogFile", "OriginalLogFile", "Mod", "ModSet", "LogFileAndModJoin", "GameMap", "Version", "LogFile_and_Mod_join")

    server_table_names = ("Server", "RemoteStorage")

    rest = []

    for tn in in_tables:
        if tn.name in {"DatabaseMetaData", "MeanUpdateTimePerLogFile", "ModLink"}:
            clusters["META"].append(tn)
            tn._background_color_selection = blue_colors
            tn.group = "META"

        elif tn.name in logrecord_table_names:
            clusters["LOGRECORD"].append(tn)
            tn._background_color_selection = green_colors
            tn.group = "LOGRECORD"
            tn.weight = 100

        elif tn.name in logfile_table_names:
            clusters["LOGFILE"].append(tn)
            tn._background_color_selection = violet_colors
            tn.group = "LOGFILE"
            tn.weight = 80

        elif tn.name in server_table_names:
            clusters["SERVER"].append(tn)
            tn._background_color_selection = orange_colors
            tn.group = "SERVER"
            tn.weight = 50

        else:
            rest.append(tn)
            tn.group = "REST"

    clusters["LOGRECORD"] = sorted(clusters["LOGRECORD"], key=lambda x: logrecord_table_names.index(x.name))
    return clusters, rest


def main(models_file_path: Union[str, os.PathLike], graph_name: str = None):
    models_file_path = Path(models_file_path)
    graph_name = graph_name or "Models"
    font_data = FontData(general_font_name="Helvetica", general_font_size=16)
    tables = get_nodes(models_file_path=models_file_path)
    tables = sorted(tables, key=lambda x: (not is_no_target(x, tables), len(x.foreign_key_columns)), reverse=True)
    all_tables = tables.copy()
    clusters, tables = make_clusters(tables)
    graph_string = make_graph_string(graph_name=graph_name, font_data=font_data, tables=tables, all_tables=all_tables, clusters=clusters)

    save_graph(graph_string, THIS_FILE_DIR.joinpath("_images", "database_graph"))


def from_sphinx_config():
    main(MODELS_FILE_PATH, "Antistasi Logbook Database")


# region[Main_Exec]
if __name__ == '__main__':
    main(MODELS_FILE_PATH, "Antistasi Logbook Database")


# endregion[Main_Exec]
