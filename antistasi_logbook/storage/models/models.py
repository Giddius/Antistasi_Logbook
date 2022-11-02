# * Standard Library Imports ---------------------------------------------------------------------------->
import re
import json
import os
from io import TextIOWrapper
from time import sleep
from concurrent.futures import ThreadPoolExecutor
from typing import TYPE_CHECKING, Any, Union, Literal, Optional, Generator, Callable, Iterable
from pathlib import Path
from zipfile import ZIP_LZMA, ZipFile
from datetime import datetime, timezone, timedelta
from functools import cached_property, cache, lru_cache
from threading import Lock, RLock
import sys
from operator import add
import hashlib
import peewee
import zlib
import shutil
from contextlib import contextmanager
from statistics import StatisticsError, mean, median
from playhouse.sqlite_ext import Blob, ZeroBlob
from functools import reduce
from collections import defaultdict, namedtuple
from gidapptools.general_helper.conversion import human2bytes
from statistics import stdev, variance, quantiles, correlation, covariance, pstdev
from threading import Event
from concurrent.futures import Future, wait, ALL_COMPLETED
import numpy
import apsw
# * Qt Imports --------------------------------------------------------------------------------------->
from PySide6.QtGui import QColor

# * Third Party Imports --------------------------------------------------------------------------------->
import keyring
from yarl import URL
from peewee import DatabaseProxy, IntegrityError, fn, SQL, JOIN, ModelBase
from tzlocal import get_localzone
from dateutil.tz import UTC
from playhouse.signals import Model as SignalsModel, post_delete, post_save, pre_init, pre_delete, pre_save
from playhouse.apsw_ext import TextField, BooleanField, IntegerField, ForeignKeyField, ManyToManyField, FixedCharField, CharField, DeferredForeignKey, FloatField
from playhouse.sqlite_ext import JSONField

# * Gid Imports ----------------------------------------------------------------------------------------->
from gidapptools import get_logger, get_meta_info, get_meta_paths
from gidapptools.gid_config.interface import GidIniConfig, get_config
from gidapptools.general_helper.timing import get_dummy_profile_decorator_in_globals
from gidapptools.general_helper.enums import MiscEnum

from gidapptools.general_helper.conversion import bytes2human, str_to_bool

# * Local Imports --------------------------------------------------------------------------------------->
from antistasi_logbook import setup
from antistasi_logbook.data.misc import LOG_FILE_DATE_REGEX
from antistasi_logbook.records.enums import RecordFamily
from antistasi_logbook.utilities.misc import VersionItem
from antistasi_logbook.utilities.date_time_utilities import DateTimeFrame
from antistasi_logbook.utilities.locks import FILE_LOCKS
from antistasi_logbook.records.base_record import MessageFormat
from antistasi_logbook.updating.remote_managers import remote_manager_registry
from antistasi_logbook.storage.models.custom_fields import (URLField, PathField, LoginField, MarkedField, VersionField, CommentsField, TzOffsetField,
                                                            RemotePathField, CaselessTextField, AwareTimeStampField, LZMACompressedTextField, CompressedImageField, TextBlobField, LocalImageField)
from antistasi_logbook.utilities.row_instance_cache import RowInstanceCache
import lzma
from antistasi_logbook.utilities.misc import EnumLikeModelCache, all_subclasses_recursively
setup()
# * Standard Library Imports ---------------------------------------------------------------------------->

# * Third Party Imports --------------------------------------------------------------------------------->

# * Gid Imports ----------------------------------------------------------------------------------------->
if sys.version_info >= (3, 11):
    from typing import Self
else:
    from typing_extensions import Self
if TYPE_CHECKING:

    from antistasi_logbook.storage.database import GidSqliteApswDatabase
    from antistasi_logbook.parsing.py_raw_record import RawRecord
    from antistasi_logbook.updating.remote_managers import InfoItem, AbstractRemoteStorageManager
    from antistasi_logbook.records.record_class_manager import RECORD_CLASS_TYPE, RecordClassManager


THIS_FILE_DIR = Path(__file__).parent.absolute()

get_dummy_profile_decorator_in_globals()
META_PATHS = get_meta_paths()

META_INFO = get_meta_info()
log = get_logger(__name__)


database_proxy = DatabaseProxy()


LOCAL_TIMEZONE = get_localzone()


class BaseModel(SignalsModel):

    # non-db attributes
    _column_name_set: set[str] = None
    is_view: bool = False

    class Meta:
        database: "GidSqliteApswDatabase" = database_proxy

    @classmethod
    def has_column_named(cls, name: str) -> bool:
        if cls._column_name_set is None:
            cls._column_name_set = set(cls.get_meta().sorted_field_names)
        return name in cls._column_name_set

    @classmethod
    def get_meta(cls):
        return cls._meta

    @property
    def database(self) -> "GidSqliteApswDatabase":
        return self._meta.database

    @property
    def config(self) -> "GidIniConfig":
        return self._meta.database.backend.config

    @property
    def color_config(self) -> "GidIniConfig":
        return self._meta.database.backend.color_config

    def get_data(self, attr_name: str, default: Any = "") -> Any:
        _out = getattr(self, f"pretty_{attr_name}", MiscEnum.NOTHING)
        if _out is MiscEnum.NOTHING:
            _out = getattr(self, attr_name, default)
        return _out

    def format_datetime(self, date_time: datetime) -> str:
        if self.config.get("time", "use_local_timezone", default=False) is True:
            date_time = date_time.astimezone(tz=LOCAL_TIMEZONE)
        time_format = self.config.get("time", "time_format", default='%Y-%m-%d %H:%M:%S.%f')
        if time_format == "iso":
            return date_time.isoformat()
        if time_format == "local":
            time_format = "%x %X"
        _out = date_time.strftime(time_format)
        if "%f" in time_format:
            _out = _out[:-3]
        return _out

    @property
    def pretty_name(self) -> str:
        return str(self)

    def __getattr__(self, attr_name: str):
        if attr_name.startswith("pretty_"):
            return getattr(self, attr_name.removeprefix("pretty_"))

        try:
            return super().__getattr__(attr_name)
        except AttributeError:
            pass

        raise AttributeError(f"{self.__class__!r} object has no attribute {attr_name!r}", name=attr_name, obj=self)

    def __str__(self) -> str:
        if hasattr(self, "name"):
            return str(self.name)

        return super().__str__()

    def __len__(self):
        return self.__class__.select().count()

    @classmethod
    def get_all_models(cls, include_view_models: bool = True) -> tuple["BaseModel"]:
        if include_view_models is False:
            return tuple(m for m in all_subclasses_recursively(cls) if m.is_view is False)
        elif include_view_models is True:
            return tuple(m for m in all_subclasses_recursively(cls))

    @classmethod
    def get_all_view_models(cls) -> tuple["ViewBaseModel"]:
        return tuple(m for m in all_subclasses_recursively(cls) if m.is_view is True)


database_proxy.attach_callback(lambda _db: setattr(_db, "_base_model", BaseModel))


class ViewBaseModel(BaseModel):
    is_view: bool = True


database_proxy.attach_callback(lambda _db: setattr(_db, "_view_base_model", ViewBaseModel))


class EnumLikeBaseModel(BaseModel):
    _instance_cache: EnumLikeModelCache = None

    def __new__(cls: type[Self], *args, **kwargs) -> Self:

        cls._ensure_instance_cache()
        _id = kwargs.get("id", None)
        instance = cls._instance_cache.get_by_id(_id)

        if instance is None:
            instance = super(EnumLikeBaseModel, cls).__new__(cls)

        return instance

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._instance_cache.add(self)

    @classmethod
    def clear_instance_cache(cls) -> None:
        cls._instance_cache.clear()

    @classmethod
    def _ensure_instance_cache(cls):
        if cls._instance_cache is None:
            cls._instance_cache = EnumLikeModelCache(cls)


class ArmaFunctionAuthorPrefix(EnumLikeBaseModel):
    name = TextField(unique=True, index=True)
    full_name = TextField(unique=True, null=True, index=True)
    local_folder_path = PathField(null=True)
    github_link = URLField(null=True)
    comments = CommentsField(null=True)
    marked = MarkedField()

    class Meta:
        table_name = 'ArmaFunctionAuthorPrefix'
        indexes = (
            (('name', 'full_name'), True),
        )

    @property
    def pretty_name(self) -> str:
        if self.full_name is not None:
            return self.full_name
        return super().pretty_name

    @classmethod
    def get_by_id_cached(cls, pk):

        return super().get_by_id(pk)


class ArmaFunction(BaseModel):
    name = TextField(null=False, index=True)
    author_prefix = ForeignKeyField(column_name='author_prefix', field='id', model=ArmaFunctionAuthorPrefix, lazy_load=True, index=True, verbose_name="Author Prefix")
    link = URLField(null=True)
    local_path = PathField(null=True)
    comments = CommentsField(null=True)
    marked = MarkedField()
    file_name = TextField(null=True, index=True)
    function_name = TextField(null=True, unique=True, index=True)
    show_as: Literal["file_name", "function_name"] = "function_name"

    # non-db attributes
    parsing_regex: re.Pattern = re.compile(r"(?P<author_prefix>[\w_]+)_fnc_(?P<name>.*)")

    class Meta:
        table_name = 'ArmaFunction'
        indexes = (
            (('name', 'author_prefix'), True),
            (("file_name", "author_prefix"), True),
        )

    @classmethod
    @lru_cache(None)
    def get_by_id_cached(cls, pk):
        if pk is None:
            return None
        return super().get_by_id(pk)

    def load_extras(self) -> None:
        if self.file_name is None:
            file_name = self._get_file_name()

            ArmaFunction.update(file_name=file_name).where(ArmaFunction.id == self.id).execute()
            self.file_name = file_name

        if self.function_name is None:
            function_name = self._get_function_name()

            ArmaFunction.update(function_name=function_name).where(ArmaFunction.id == self.id).execute()
            self.function_name = function_name

    def _get_function_name(self) -> Optional[str]:
        try:
            if self.author_prefix.name == "UNKNOWN":
                return self.file_name
            if self.author_prefix.name == "FSM":
                return self.name

            return f"{self.author_prefix.name}_fnc_{self.name}"
        except Exception as error:
            log.critical("Encountered %r while getting function name of %r", error, self)
            return None

    def _get_file_name(self) -> Optional[str]:
        try:
            if self.author_prefix.name == "FSM":
                return f"{self.name}.fsm"

            return f"fn_{self.name}.sqf"
        except Exception as error:
            log.critical("Encountered %r while getting file name of %r", error, self)
            return None

    @classmethod
    def parse_raw_function_name(cls, in_name: str) -> dict[str, Optional[str]]:
        in_name = in_name.strip()
        parsed_data = {"name": None,
                       "author_prefix": None}

        if in_name.endswith(".sqf"):
            parsed_data['name'] = in_name.removeprefix("fn_").removesuffix(".sqf")
            parsed_data['author_prefix'] = "UNKNOWN"
        elif '_' not in in_name:
            parsed_data["author_prefix"] = "FSM"
            parsed_data['name'] = in_name

        else:
            parsed_data |= cls.parsing_regex.match(in_name).groupdict()

        return parsed_data

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name={self.name!r})"

    def __str__(self) -> str:
        self.load_extras()
        if self.show_as == "file_name":
            _out = self.file_name
        elif self.show_as == "function_name":
            _out = self.function_name
        else:
            _out = self.name
        return _out


class GameMap(BaseModel):
    full_name = TextField(null=True, unique=True, index=True, verbose_name="Full Name")
    name = TextField(unique=True, index=True, verbose_name="Internal Name")
    official = BooleanField(default=False, index=True, verbose_name="Official")
    dlc = TextField(null=True, index=True, verbose_name="DLC")
    map_image_high_resolution = LocalImageField(null=True, verbose_name="High Resolution Image")
    map_image_low_resolution = LocalImageField(null=True, verbose_name="Low Resolution Image")
    coordinates = JSONField(null=True, verbose_name="Coordinates-JSON")
    workshop_link = URLField(null=True, verbose_name="Workshop Link")
    comments = CommentsField(null=True)
    marked = MarkedField()

    class Meta:
        table_name = 'GameMap'
        indexes = (
            (('name', 'full_name', 'workshop_link'), True),

        )

    @classmethod
    @lru_cache(None)
    def get_by_id_cached(cls, pk):

        return super().get_by_id(pk)

    def has_low_res_image(self) -> bool:
        return self.map_image_low_resolution is not None

    def has_high_res_image(self) -> bool:
        return self.map_image_high_resolution is not None

    def get_avg_players_per_hour(self) -> dict[str, Union[float, int, datetime]]:
        log_files_query = LogFile.select().where((LogFile.game_map_id == self.id) & (LogFile.unparsable == False))
        record_class = RecordClass.get(name="PerformanceRecord")
        data = []
        all_time_frames = []
        for log_file in log_files_query.iterator():
            data.append((log_file.average_players_per_hour[0], log_file.time_frame.hours, log_file.average_players_per_hour[1]))
            all_time_frames.append(log_file.time_frame)
        if len(data) <= 0:
            return {"avg_players": None, "sample_size_hours": None, "sample_size_data_points": None, "date_time_frame": None, "std_dev": None}

        if len(data) == 1:
            overall_avg = data[0][0]
            std_dev = 0.0

        else:
            overall_avg = float(round(numpy.average([i[0] for i in data], weights=[i[1] for i in data]), 3))
            all_values = []
            for i in data:
                if i[2]:
                    all_values += i[2]
            # std_dev = stdev(all_values)
            std_dev = correlation([i[0] for i in data], [len(i[2]) for i in data])
        date_time_frame = DateTimeFrame(start=min([fr.start for fr in all_time_frames]), end=max([fr.end for fr in all_time_frames]))
        sample_size_hours = sum([i[1] for i in data])
        sample_size_data_points = sum(tf.seconds // 10 for tf in all_time_frames)
        return {"avg_players": overall_avg, "sample_size_hours": sample_size_hours, "sample_size_data_points": sample_size_data_points, "date_time_frame": date_time_frame, "std_dev": std_dev}

    def get_avg_players_per_hour_per_mod_set(self) -> dict[str, Union[float, int, datetime]]:
        log_files_query = LogFile.select().where((LogFile.game_map_id == self.id) & (LogFile.unparsable == False))
        record_class = RecordClass.get(name="PerformanceRecord")
        data = {m.name: [] for m in ModSet.select()}
        all_time_frames = []
        for log_file in log_files_query.iterator():
            if log_file.mod_set is None:
                continue
            data[str(log_file.mod_set)].append((log_file.average_players_per_hour[0], log_file.time_frame.hours, log_file.average_players_per_hour[1]))
            all_time_frames.append(log_file.time_frame)
        data = dict(data)
        for mod_set_name in data:
            _sub_data = data[mod_set_name]
            if len(_sub_data) < 1:
                data[mod_set_name] = 0.0

            elif len(_sub_data) == 1:
                data[mod_set_name] = _sub_data[0][0]

            else:
                data[mod_set_name] = float(round(numpy.average([i[0] for i in _sub_data], weights=[i[1] for i in _sub_data]), 3))

        return data

    def _get_avg_players_per_hour(self) -> dict[str, Union[float, int, datetime]]:

        log_files_query = LogFile.select().where((LogFile.game_map_id == self.id))
        record_class = RecordClass.get(name="PerformanceRecord")
        query = LogRecord.select(LogRecord.message, LogRecord.recorded_at).where((LogRecord.log_file << log_files_query)).where((LogRecord.record_class_id == record_class.id))
        player_data = defaultdict(list)
        performance_record_class = record_class.record_class

        # log.debug("SQL for 'get_avg_players_per_hour' of %r: %r", self, query.sql())
        _all_timestamps = []
        sql_phrase = """SELECT "t1"."message", "t1"."recorded_at" FROM "LogRecord" AS "t1" WHERE (("t1"."record_class" = ?) AND ("t1"."log_file" IN (SELECT "t2"."id" FROM "LogFile" AS "t2" WHERE (("t2"."unparsable" = ?) AND ("t2"."game_map" = ?)))))"""
        # cursor = self.database.cursor()

        # for (message, recorded_at) in self.database.execute_sql(sql_phrase, (record_class.id, 0, self.id)):
        # for message, recorded_at in list(cursor.execute(sql_phrase, (record_class.id, self.id))):
        sample_size = 0
        for message, recorded_at in list(self.database.execute(query)):
            sample_size += 1
            recorded_at = LogRecord.recorded_at.python_value(recorded_at)
            stats = performance_record_class.parse(message)

            players: int = stats["Players"]
            _all_timestamps.append(recorded_at)

            timestamp: datetime = recorded_at.replace(microsecond=0, second=0, minute=0)

            player_data[timestamp].append(players)

        if len(player_data) <= 0 or len(_all_timestamps) <= 1:
            return {"avg_players": None, "sample_size_hours": None, "sample_size_data_points": None, "date_time_frame": None}
        date_time_frame = DateTimeFrame(start=min(_all_timestamps), end=max(_all_timestamps))
        avg_player_data = {}
        for k, v in player_data.items():
            if len(v) > 1:
                avg_player_data[k] = mean(v)
            else:
                avg_player_data[k] = v[0]

        return {"avg_players": round(mean(avg_player_data.values()), 3), "sample_size_hours": sample_size, "sample_size_data_points": sample_size, "date_time_frame": date_time_frame}

    def __str__(self):
        return str(self.full_name)


class RemoteStorage(BaseModel):
    name = TextField(unique=True, index=True)
    base_url = URLField(null=True)
    login = LoginField(null=True)
    manager_type = TextField(index=True)
    credentials_required = BooleanField(default=False)

    class Meta:
        table_name = 'RemoteStorage'
        indexes = (
            (('base_url', 'login', 'manager_type'), True),
        )

    @classmethod
    @lru_cache(None)
    def get_by_id_cached(cls, pk):

        return super().get_by_id(pk)

    def get_password(self) -> Optional[str]:
        return keyring.get_password(self.name, self.login)

    def get_login(self) -> Optional[str]:
        return self.login

    def set_login_and_password(self, login: str, password: str) -> None:
        self.__class__.update(login=login).where(self.__class__.id == self.id).execute()

        keyring.set_password(self.name, login, password)
        self.login = list(self.__class__.select(self.__class__.login).where(self.__class__.id == self.id).tuples().iterator())[0]

    def as_remote_manager(self) -> "AbstractRemoteStorageManager":
        manager = remote_manager_registry.get_remote_manager(self)
        return manager

    def __str__(self):
        return ' '.join(self.name.split('_')).title()


class Server(BaseModel):
    name = TextField(unique=True, index=True, verbose_name="Name", help_text="The Name of the Server")
    remote_path = RemotePathField(null=True, unique=True, verbose_name="Remote Path", help_text="The Path in the Remote Storage containing the log files")
    remote_storage = ForeignKeyField(column_name='remote_storage', default=0, field='id', model=RemoteStorage, lazy_load=True, index=True, verbose_name="Remote Storage")
    update_enabled = BooleanField(default=False, verbose_name="Update", help_text="If this Server should update", index=True)
    ip = TextField(null=True, verbose_name="IP Address", help_text="IP Adress of the Server")
    port = IntegerField(null=True, verbose_name="Port", help_text="Port the Server uses")
    comments = CommentsField(null=True)
    marked = MarkedField()

    # non-db attributes
    archive_lock = RLock()

    class Meta:
        table_name = 'Server'
        indexes = (
            (('ip', 'port'), True),
        )

    @classmethod
    @lru_cache(None)
    def get_by_id_cached(cls, pk):

        return super().get_by_id(pk)

    @property
    def background_color(self):
        return self.color_config.get("server", self.name, default=None)

    @property
    def pretty_name(self) -> str:
        return self.name.replace('_', ' ').title()

    @property
    def pretty_remote_path(self) -> str:
        return self.remote_path.as_posix()

    @property
    def remote_manager(self) -> "AbstractRemoteStorageManager":
        return self.remote_storage.as_remote_manager()

    def is_updatable(self) -> bool:
        if self.update_enabled is False:
            return False
        if self.remote_storage.manager_type == "LocalManager":
            return False
        return True

    def get_remote_files(self) -> Generator["InfoItem", None, None]:
        yield from self.remote_manager.get_files(self.remote_path)

    def get_amount_log_files(self) -> int:
        return LogFile.select().where(LogFile.server_id == self.id).count(self.database)

    @property
    def full_local_path(self) -> Path:

        local_path = META_PATHS.get_new_temp_dir(name=self.name, exists_ok=True)

        local_path.mkdir(exist_ok=True, parents=True)
        return local_path

    @property
    def archive_path(self) -> Path:
        archive_path = META_PATHS.cache_dir.joinpath(self.name + '.zip')
        archive_path.parent.mkdir(parents=True, exist_ok=True)
        return archive_path

    def add_log_file_to_archive(self, log_file: "LogFile"):
        with self.archive_lock:
            with ZipFile(self.archive_path, "a", compression=ZIP_LZMA) as zippy:
                zippy.write(log_file.local_path, log_file.local_path.name)

    def get_log_file_from_archive(self, log_file: "LogFile") -> Path:
        with self.archive_lock:
            with ZipFile(self.archive_path, "r", compression=ZIP_LZMA) as zippy:
                with zippy.open(log_file.local_path.name, "r") as a_f:
                    with log_file.local_path.open("wb") as l_f:
                        for chunk in a_f:
                            l_f.write(chunk)
        return log_file.local_path

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name={self.name!r}, remote_storage={self.remote_storage.name!r}, update_enabled={self.update_enabled!r})"

    def __str__(self) -> str:
        return self.name


class Version(BaseModel):
    full = VersionField(unique=True, verbose_name="Full Version", index=True)
    major = IntegerField(verbose_name="Major", index=True)
    minor = IntegerField(verbose_name="Minor", index=True)
    patch = IntegerField(verbose_name="Patch", null=True, index=True)
    extra = TextField(null=True, verbose_name="Extra", index=True)
    comments = CommentsField(null=True)
    marked = MarkedField()

    class Meta:
        table_name = 'Version'
        indexes = (
            (('major', 'minor', 'patch', 'extra'), True),

        )

    @classmethod
    @lru_cache(None)
    def get_by_id_cached(cls, pk):

        return super().get_by_id(pk)

    @classmethod
    def add_or_get_version(cls, version: "VersionItem") -> "Version":
        if version is None:
            return

        extra = version.extra
        if isinstance(extra, int):
            extra = str(extra)
        Version.insert(full=version, major=version.major, minor=version.minor, patch=version.patch, extra=version.extra).on_conflict_ignore().execute()

        return tuple(Version.select().where(Version.full == version))[0]

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(full={self.full!r}, major={self.major!r}, minor={self.minor!r}, patch={self.patch!r}, extra={self.extra!r}, marked={self.marked!r})"

    def __str__(self) -> str:
        return str(self.full)


class OriginalLogFile(BaseModel):
    name = TextField(unique=False, null=False, index=True)
    server = ForeignKeyField(model=Server, backref=False, field="id", lazy_load=True, verbose_name="Server")
    text_hash = FixedCharField(max_length=32, unique=True, null=False, index=True)

    # non-db attributes
    hash_algorithm = hashlib.md5
    compress_algorithm = lzma

    class Meta:
        table_name = 'OriginalLogFile'
        indexes = (
            (("name", "server"), True),
        )

    @classmethod
    @lru_cache(None)
    def get_by_id_cached(cls, pk):

        return super().get_by_id(pk)

    def unpack_to_temp_file(self) -> Path:
        temp_folder = META_PATHS.get_new_temp_dir(name=self.server.name)
        full_temp_path = temp_folder.joinpath(f"{self.name}.txt")
        decompressed_data = self.compress_algorithm.decompress(self.file_path.read_bytes())
        full_temp_path.write_text(decompressed_data.decode(encoding='utf-8', errors='ignore'))
        return full_temp_path

    @classmethod
    def get_save_folder(cls) -> Path:
        _out: Path = cls._meta.database.database_path.parent.joinpath("original_log_files")
        _out.mkdir(exist_ok=True, parents=True)
        return _out

    @classmethod
    def make_file_path(cls, server_name: str, file_name: str) -> Path:
        file_name = file_name.rsplit(".", 1)[0]
        file_path = cls.get_save_folder().joinpath(server_name, file_name).with_suffix(".compressed")

        file_path.parent.mkdir(parents=True, exist_ok=True)
        return file_path

    @property
    def text(self) -> str:
        temp_file_path = self.unpack_to_temp_file()
        return temp_file_path.read_text(encoding='utf-8', errors='ignore')

    @property
    def file_path(self) -> Path:
        file_path = self.make_file_path(server_name=self.server.name, file_name=self.name)

        return file_path

    @property
    def lines(self) -> tuple[int, str]:
        return tuple(enumerate(self.text.splitlines()))

    def compress_and_store_file(self, in_file_path: Path) -> Path:
        new_file_path = self.make_file_path(server_name=self.server.name, file_name=self.name)
        with new_file_path.open("wb") as f:
            f.write(self.compress_algorithm.compress(in_file_path.read_bytes()))
        return new_file_path

    @classmethod
    def init_from_file(cls, file_path: os.PathLike, server: Server) -> "OriginalLogFile":
        file_path = Path(file_path)
        text_bytes = file_path.read_bytes()

        instance = cls(text_hash=cls.create_text_hash(text_bytes), name=file_path.stem, server=server)
        # cls._meta.database.backend.inserting_thread_pool.submit(instance.compress_and_store_file,in_file_path=file_path)
        instance.compress_and_store_file(in_file_path=file_path)
        return instance

    @classmethod
    def create_text_hash(cls, text_or_bytes: Union[str, bytes]) -> str:
        if isinstance(text_or_bytes, str):
            text_or_bytes = text_or_bytes.encode(encoding='utf-8', errors='ignore')
        return cls.hash_algorithm(text_or_bytes).hexdigest()

    def modify_update_from_file(self, file_path: os.PathLike) -> "OriginalLogFile":
        file_path = Path(file_path)
        self.text_hash = self.create_text_hash(file_path.read_bytes())
        # self._meta.database.backend.inserting_thread_pool.submit(self.compress_and_store_file,in_file_path=file_path)
        self.compress_and_store_file(in_file_path=file_path)
        return self

    def to_file(self) -> Path:
        path = self.unpack_to_temp_file()

        return path

    def __iter__(self):
        for line_number, line in self.lines:
            yield line

    def get_lines(self, start: int, end: int) -> tuple[str]:
        only_lines = [i[1] for i in self.lines]
        if end == start:
            return tuple([only_lines[end - 1]])
        corrected_start = start - 1
        corrected_end = end
        return tuple(only_lines[corrected_start:corrected_end])

    def get_lines_with_line_numbers(self, start: int, end: int) -> tuple[tuple[int, str]]:
        if end == start:
            return ((end, [i[1] for i in self.lines][end - 1]),)
        corrected_start = start - 1
        corrected_end = end

        return tuple(self.lines[corrected_start:corrected_end])

    def delete_instance(self, *args, **kwargs):
        self.get_meta().database.backend.inserting_thread_pool.submit(self.file_path.unlink, missing_ok=True)
        return super().delete_instance(*args, **kwargs)


class ModSet(BaseModel):
    name = TextField(unique=True, verbose_name="Mod-Set Name")
    mod_names = JSONField(unique=True, verbose_name="Mod names")

    class Meta:
        table_name = 'ModSet'

    @classmethod
    @lru_cache(None)
    def get_by_id_cached(cls, pk):

        return super().get_by_id(pk)

    @property
    def background_color(self) -> QColor:
        if "vanilla" in self.name.casefold():
            return QColor(243, 229, 171, 155)

        if "rhs" in self.name.casefold():
            return QColor(220, 50, 50, 155)

        if "3cb" in self.name.casefold():
            return QColor(50, 50, 235, 155)


class LogFile(BaseModel):
    name = TextField(index=True, verbose_name="Name")
    remote_path = RemotePathField(unique=True, verbose_name="Remote Path")
    modified_at = AwareTimeStampField(index=True, verbose_name="Modified at")
    size = IntegerField(verbose_name="Size")
    created_at = AwareTimeStampField(null=True, index=True, verbose_name="Created at")
    header_text = LZMACompressedTextField(null=True, verbose_name="Header Text")
    startup_text = LZMACompressedTextField(null=True, verbose_name="Startup Text")
    last_parsed_line_number = IntegerField(default=0, null=True, verbose_name="Last Parsed Line Number")
    utc_offset = TzOffsetField(null=True, verbose_name="UTC Offset")
    version = ForeignKeyField(null=True, model=Version, field="id", column_name="version", lazy_load=True, index=True, verbose_name="Version")
    game_map = ForeignKeyField(column_name='game_map', field='id', model=GameMap, null=True, lazy_load=True, index=True, verbose_name="Game-Map")
    is_new_campaign = BooleanField(null=True, index=True, verbose_name="New Campaign")
    campaign_id = IntegerField(null=True, index=True, verbose_name="Campaign Id")
    server = ForeignKeyField(column_name='server', field='id', model=Server, lazy_load=True, backref="log_files", index=True, verbose_name="Server")
    unparsable = BooleanField(default=False, index=True, verbose_name="Unparsable")
    last_parsed_datetime = AwareTimeStampField(null=True, verbose_name="Last Parsed Datetime")
    max_mem = IntegerField(verbose_name="Max Memory", null=True)
    original_file = ForeignKeyField(model=OriginalLogFile, field="id", column_name="original_file", lazy_load=True, backref="log_file", null=True, on_delete="CASCADE", index=True)
    manually_added = BooleanField(null=False, default=False, verbose_name="Manually added", index=True)
    mod_set = ForeignKeyField(null=True, model=ModSet, field="id", column_name="mod_set", lazy_load=True, index=True, verbose_name="Mod-Set")
    amount_headless_clients = IntegerField(null=True, unique=False, index=False, verbose_name="Headless Clients")
    amount_log_records = IntegerField(null=True, index=False, unique=False, verbose_name="Log-Records")
    amount_errors = IntegerField(null=True, index=False, unique=False, verbose_name="Errors")
    amount_warnings = IntegerField(null=True, index=False, unique=False, verbose_name="Warnings")
    comments = CommentsField(null=True)
    marked = MarkedField()

    class Meta:
        table_name = 'LogFile'

        indexes = (
            (("name", "server", "created_at"), True),
            (("name", "server", "remote_path"), True),
            (("unparsable", "modified_at", "server", "version", "game_map", "original_file"), False)
        )

    @classmethod
    @lru_cache(None)
    def get_by_id_cached(cls, pk):

        return super().get_by_id(pk)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.is_downloaded: bool = False

    def ensure_dynamic_columns(self, force: bool = False, update_db: bool = True) -> dict[str, Union[int, ModSet]]:

        update_data = {}

        if self.mod_set is None or force is True:
            self.mod_set = self.determine_mod_set()
            update_data["mod_set"] = self.mod_set

        if self.amount_headless_clients is None or force is True:
            self.amount_headless_clients = self.determine_amount_headless_clients()
            update_data["amount_headless_clients"] = self.amount_headless_clients

        if self.amount_log_records is None or force is True:
            self.amount_log_records = self.determine_amount_log_records()
            update_data["amount_log_records"] = self.amount_log_records

        if self.amount_errors is None or force is True:
            self.amount_errors = self.determine_amount_errors()
            update_data["amount_errors"] = self.amount_errors

        if self.amount_warnings is None or force is True:
            self.amount_warnings = self.determine_amount_warnings()
            update_data["amount_warnings"] = self.amount_warnings

        if update_data and update_db is True:
            with self.database.connection_context():
                LogFile.update(**update_data).where((LogFile.id == self.id)).execute()

        update_data["id"] = self.id
        return update_data

    @classmethod
    def refresh_dynamic_for_all_log_files(cls, log_files: Iterable["LogFile"] = None):
        while RecordClass.record_class_manager is None:
            sleep(1)
        if log_files is None:
            log_files = LogFile.select().iterator()

        all_update_data = list(cls._meta.database.backend.inserting_thread_pool.map(lambda x: x.ensure_dynamic_columns(force=True, update_db=False), log_files))
        # all_update_data = [l.ensure_dynamic_columns(force=True, update_db=True) for l in log_files]

    def determine_mod_set(self) -> Optional["ModSet"]:
        own_mod_names = frozenset([m.cleaned_name for m in Mod.select().join(LogFileAndModJoin).join(LogFile).where(LogFile.id == self.id).iterator()])
        mod_set_value = None
        for mod_set in sorted(ModSet.select().iterator(), key=lambda x: len(x.mod_names), reverse=True):
            if len(mod_set.mod_names) > len(own_mod_names):
                continue
            if all(mod_name in own_mod_names for mod_name in mod_set.mod_names):
                mod_set_value = mod_set
                break
        return mod_set_value

    @cached_property
    def amount_headless_clients_disconnected(self) -> int:
        record_class_disconnected = RecordClass.get(name="GenericHeadlessClientDisconnected")

        # disconnected = LogRecord.select().where((LogRecord.log_file_id == self.id) & (LogRecord.record_class_id == record_class_disconnected.id)).count()
        disconnected = set()
        for message in LogRecord.select(Message.text).join_from(LogRecord, Message, on=(LogRecord.message_item == Message.md5_hash), join_type=JOIN.LEFT_OUTER).where((LogRecord.log_file_id == self.id) & (LogRecord.record_class_id == record_class_disconnected.id)).tuples().iterator():
            message = Message.text.python_value(message[0])
            disconnected.add(record_class_disconnected.record_class.parse(message)["client_number"])

        return len(disconnected)

    @cached_property
    def amount_headless_clients_connected(self) -> int:
        record_class_connected = RecordClass.get(name="GenericHeadlessClientConnected")

        connected = set()
        for message in LogRecord.select(Message.text).join_from(LogRecord, Message, on=(LogRecord.message_item == Message.md5_hash), join_type=JOIN.LEFT_OUTER).where((LogRecord.log_file_id == self.id) & (LogRecord.record_class_id == record_class_connected.id)).tuples().iterator():
            message = Message.text.python_value(message[0])

            connected.add(record_class_connected.record_class.parse(message)["client_number"])
        return len(connected)

    def determine_amount_headless_clients(self) -> int:

        record_class_connected = RecordClass.get(name="GenericHeadlessClientConnected")
        # connected = LogRecord.select().where((LogRecord.log_file_id == self.id) & (LogRecord.record_class_id == record_class_connected.id)).count()
        connected = set()
        for message in LogRecord.select(Message.text).join_from(LogRecord, Message, on=(LogRecord.message_item == Message.md5_hash), join_type=JOIN.LEFT_OUTER).where((LogRecord.log_file_id == self.id) & (LogRecord.record_class_id == record_class_connected.id)).tuples().iterator():

            message = Message.text.python_value(message[0])
            connected.add(record_class_connected.record_class.parse(message)["client_number"])

        record_class_disconnected = RecordClass.get(name="GenericHeadlessClientDisconnected")

        # disconnected = LogRecord.select().where((LogRecord.log_file_id == self.id) & (LogRecord.record_class_id == record_class_disconnected.id)).count()
        disconnected = set()
        for message in LogRecord.select(Message.text).join_from(LogRecord, Message, on=(LogRecord.message_item == Message.md5_hash), join_type=JOIN.LEFT_OUTER).where((LogRecord.log_file_id == self.id) & (LogRecord.record_class_id == record_class_disconnected.id)).tuples().iterator():
            message = Message.text.python_value(message[0])
            disconnected.add(record_class_disconnected.record_class.parse(message)["client_number"])
        difference = connected.difference(disconnected)

        return len(difference)

    @cached_property
    def time_frame(self) -> DateTimeFrame:
        # query = LogRecord.select(fn.Min(LogRecord.recorded_at), fn.Max(LogRecord.recorded_at)).where((LogRecord.log_file_id == self.id))
        query_string = """SELECT Min("recorded_at"), Max("recorded_at") FROM "LogRecord" WHERE ("log_file" = ?)"""
        cursor = self.database.connection().execute(query_string, (self.id,))
        min_date_time, max_date_time = cursor.fetchone()
        min_date_time = LogRecord.recorded_at.python_value(min_date_time)
        max_date_time = LogRecord.recorded_at.python_value(max_date_time)
        result = DateTimeFrame(min_date_time, max_date_time)
        cursor.close()
        return result

    @cached_property
    def pretty_time_frame(self) -> str:
        time_frame = self.time_frame
        return f"{self.format_datetime(time_frame.start)} until {self.format_datetime(time_frame.end)}"

    @cached_property
    def pretty_server(self) -> str:
        return self.server.pretty_name

    @cached_property
    def pretty_utc_offset(self) -> str:
        _offset = self.utc_offset
        offset_hours = _offset._offset.total_seconds() / 3600

        return f"UTC{offset_hours:+}"

    def determine_amount_log_records(self) -> int:
        query_string = """SELECT COUNT(*) FROM "LogRecord" WHERE ("log_file" = ?)"""
        return self.database.connection().execute(query_string, (self.id,)).fetchone()[0]

    def determine_amount_errors(self) -> int:
        query_string = """SELECT COUNT(*) FROM "LogRecord" WHERE (("log_file" = ?) AND ("log_level" = ?))"""
        return self.database.connection().execute(query_string, (self.id, 5)).fetchone()[0]

    def determine_amount_warnings(self) -> int:
        query_string = """SELECT count(*) FROM "LogRecord" WHERE (("log_file" = ?) AND ("log_level" = ?))"""

        return self.database.connection().execute(query_string, (self.id, 3)).fetchone()[0]

    @cached_property
    def pretty_size(self) -> str:
        if self.size is not None:
            return bytes2human(self.size)

    @cached_property
    def pretty_modified_at(self) -> str:
        if self.modified_at is not None:
            return self.format_datetime(self.modified_at)

    @cached_property
    def pretty_created_at(self) -> str:
        if self.created_at is not None:
            return self.format_datetime(self.created_at)

    @cached_property
    def file_lock(self) -> Lock:
        return FILE_LOCKS.get_file_lock(self)

    @cached_property
    def average_players_per_hour(self) -> int:

        self.database.connect(reuse_if_open=True)
        performance_record_class = RecordClass.get(name="PerformanceRecord")
        generic_performance_record_class = RecordClass.get(name="PerfProfilingRecord")
        ideal_entries_per_hour = (60 * 60) // 10

        def _handle_record(in_message, in_recorded_at, in_record_class_id) -> tuple[datetime, int]:
            in_message = Message.text.python_value(in_message)
            _timestamp: datetime = LogRecord.recorded_at.python_value(in_recorded_at).replace(microsecond=0, second=0, minute=0)
            # _timestamp: datetime = in_recorded_at.replace(microsecond=0, second=0, minute=0)

            if in_record_class_id == performance_record_class.id:
                stats = performance_record_class.record_class.parse(in_message)
                _players: int = stats["Players"]

            elif in_record_class_id == generic_performance_record_class.id:
                stats = generic_performance_record_class.record_class.parse(in_message)
                _players = stats["Players"]

            return _timestamp, _players

        def _insert_zero_player_values(in_raw_data: dict[datetime, list[int]]) -> dict[datetime, list[int]]:
            _raw_data = dict(in_raw_data)
            for _timestamp, player_data in in_raw_data.items():
                if len(player_data) < ideal_entries_per_hour:
                    difference = ideal_entries_per_hour - len(player_data)
                    _raw_data[_timestamp].extend(0 for _ in range(difference))
            return _raw_data

        def _average_hours(in_raw_data: dict[datetime, list[int]]) -> dict[datetime, int]:
            averaged_data = {}
            for k, v in in_raw_data.items():
                if len(v) > 1:
                    averaged_data[k] = mean(v)
                else:
                    averaged_data[k] = v[0]
            return averaged_data

        def _all_values(in_raw_data: dict[datetime, list[int]]) -> list[int]:
            all_values = []
            for k, v in in_raw_data.items():
                all_values += v
            return all_values

        query = LogRecord.select(Message.text, LogRecord.recorded_at, LogRecord.record_class_id).join_from(LogRecord, Message, on=(LogRecord.message_item == Message.md5_hash)).where((LogRecord.log_file_id == self.id) & ((LogRecord.record_class_id == performance_record_class.id) | (LogRecord.record_class_id == generic_performance_record_class.id))).order_by(-LogRecord.recorded_at)
        hour_data = defaultdict(list)

        for message, raw_recorded_at, record_class_id in list(self.database.connection().execute(*query.sql()).fetchall()):
            timestamp, players = _handle_record(message, raw_recorded_at, record_class_id)
            hour_data[timestamp].append(players)
        if len(hour_data) <= 0:
            return 0, []
        hour_data = _insert_zero_player_values(hour_data)

        average_hour_data = _average_hours(hour_data)

        return round(sum(average_hour_data.values()) / len(hour_data), 3), _all_values(hour_data)

    @classmethod
    def amount_log_files(cls) -> int:
        return LogFile.select(LogFile.id).count(cls._meta.database, True)

    @classmethod
    def average_file_size_per_log_file(cls) -> int:
        amount_log_files = cls.amount_log_files()
        db_file_size = cls._meta.database.database_file_size
        try:
            return db_file_size // amount_log_files
        except ZeroDivisionError:
            return 5242880  # 5mb

    def is_fully_parsed(self) -> bool:
        if self.last_parsed_datetime is None:
            return False
        return self.last_parsed_datetime == self.modified_at

    def has_game_map(self) -> bool:
        return self.game_map_id is not None

    def has_server(self) -> bool:
        return self.server_id is not None

    @cached_property
    def has_mods(self) -> bool:

        self.database.connect(reuse_if_open=True)

        has_mods_value = LogFileAndModJoin.select().where(LogFileAndModJoin.log_file_id == self.id).count()

        return has_mods_value > 0

    def get_marked_records(self) -> list["LogRecord"]:
        self.database.connect(reuse_if_open=True)
        return [i.to_record_class() for i in LogRecord.select().where((LogRecord.log_file_id == self.id) & (LogRecord.marked == True)).iterator()]

    def get_campaign_stats(self) -> tuple[list[dict[str, Any]], tuple["LogFile"]]:
        self.database.connect(True)
        all_stats: list[dict[str, Any]] = []
        log_files_query = LogFile.select().where(LogFile.campaign_id == self.campaign_id).iterator()
        all_log_files = tuple(log_files_query)
        for log_file in all_log_files:
            all_stats += log_file.get_stats()

        return all_stats, all_log_files

    def get_stats(self):
        all_stats: list[dict[str, Any]] = []
        self.database.connect(True)
        record_class = RecordClass.get(name="PerformanceRecord")
        record_class_2 = RecordClass.get(name="PerfProfilingRecord")
        query = LogRecord.select(Message.text, LogRecord.recorded_at, LogRecord.record_class_id).join_from(LogRecord, Message, on=(LogRecord.message_item == Message.md5_hash)).where(LogRecord.log_file_id == self.id).where((LogRecord.record_class_id == record_class.id) | (LogRecord.record_class_id == record_class_2.id)).order_by(-LogRecord.recorded_at)

        for (message, recorded_at, _record_class_id) in self.database.execute(query):
            recorded_at = LogRecord.recorded_at.python_value(recorded_at)
            message = Message.text.python_value(message)
            if _record_class_id == record_class.id:
                conc_record_class = record_class.record_class
                item_stats = conc_record_class.parse(message) | {"timestamp": recorded_at}
                item_stats["Players"] = item_stats["Players"] - self.amount_headless_clients
            elif _record_class_id == record_class_2.id:
                conc_record_class = record_class_2.record_class
                item_stats = conc_record_class.parse(message) | {"timestamp": recorded_at}

            all_stats.append(item_stats)

        return all_stats

    @cached_property
    def name_datetime(self) -> Optional[datetime]:
        if match := LOG_FILE_DATE_REGEX.search(self.name):
            datetime_kwargs = {k: int(v) for k, v in match.groupdict().items()}
            return datetime(tzinfo=UTC, **datetime_kwargs)

    def set_last_parsed_line_number(self, line_number: int) -> None:
        if line_number <= self.last_parsed_line_number:
            return
        log.debug("setting 'last_parsed_line_number' for %s to %r", self, line_number)
        changed = LogFile.update(last_parsed_line_number=line_number).where(LogFile.id == self.id).iterator().execute(self.get_meta().database)
        log.debug("changed=%r", changed)
        self.last_parsed_line_number = line_number

    @ cached_property
    def download_url(self) -> Optional[URL]:
        try:
            return self.server.remote_manager.full_base_url / self.remote_path.as_posix()
        except AttributeError:
            return None

    @ cached_property
    def local_path(self) -> Path:
        if self.server.name == "NO_SERVER":
            return Path(self.remote_path)
        return self.server.full_local_path.joinpath(self.remote_path.name)

    def download(self, fallback_to_stored_file: bool = False) -> Path:
        try:
            path = self.server.remote_manager.download_file(self)
            return path
        except Exception as e:
            log.warning("unable to download log-file %r because of %r", self, e)
            log.error(e, exc_info=True)
            if self.original_file is not None and fallback_to_stored_file is True:
                return self.original_file.to_file()
            else:
                raise

    @ contextmanager
    def open(self, cleanup: bool = True) -> TextIOWrapper:
        try:
            if self.is_downloaded is False:
                self.download()

            with self.local_path.open('r', encoding='utf-8', errors='ignore') as f:
                yield f
        except Exception as e:
            log.error(e, exc_info=True)
            raise e
        finally:
            if cleanup is True:
                self._cleanup()

    def store_original_log_file(self) -> Future:
        if self.is_downloaded is False:
            self.download()
        if self.original_file is None:
            log.debug("creating new orginal log file for logfile %r, because logfile.original_file=%r", self, self.original_file)
            _future = self.database.backend.records_inserter.insert_original_log_file(self.local_path, log_file=self)
        else:
            log.debug("updating original log file for log file %r, because it already exists", self)
            _future = self.database.backend.records_inserter.update_original_log_file(self.original_file, self.local_path)

        return _future

    def _cleanup(self) -> None:

        def _remove_file(fu: Future):
            self.local_path.unlink(missing_ok=True)
            self.is_downloaded = False
            log.debug('deleted local-file of log_file_item %r from path %r', self.name, self.local_path.as_posix())

        log.debug("cleaning up LogFile %r", self)
        if self.is_downloaded is True:
            original_file_future = self.store_original_log_file()
            original_file_future.add_done_callback(_remove_file)

    def get_mods(self) -> Optional[list["Mod"]]:
        self.database.connect(reuse_if_open=True)
        query = Mod.select().join(LogFileAndModJoin).join(LogFile).where(LogFile.id == self.id)
        _out = list(query)
        if not _out:
            return None

        return _out

    def delete_instance(self, *args, **kwargs):
        _out = super().delete_instance(*args, **kwargs)
        log.debug("deleted %r", self)
        return _out

    def __rich__(self):
        return f"[u b blue]{self.server.name}/{self.name}[/u b blue]"

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name={self.name!r}, server={self.server.name!r}, modified_at={self.modified_at.strftime('%Y-%m-%d %H:%M:%S')!r})"

    def __str__(self) -> str:
        return f"{self.name}"


class ModLink(BaseModel):
    cleaned_mod_name = TextField(unique=True)
    link = URLField(unique=True)

    class Meta:
        table_name = 'ModLink'
        indexes = (
            (("cleaned_mod_name", "link"), True),
        )

    @classmethod
    @lru_cache(None)
    def get_by_id_cached(cls, pk):

        return super().get_by_id(pk)


class Mod(BaseModel):
    full_path = PathField(null=True)
    mod_hash = FixedCharField(null=True, max_length=40)
    mod_hash_short = CharField(null=True, max_length=10)
    mod_dir = CharField(max_length=100)
    name = TextField(index=True)
    default = BooleanField(default=False)
    official = BooleanField(default=False)
    comments = CommentsField(null=True)
    marked = MarkedField()

    version_regex = re.compile(r"(\s*\-\s*)?v?\s*[\d\.]*$")
    get_or_create_lock = RLock()

    class Meta:
        table_name = 'Mod'
        indexes = (
            (('name', 'mod_dir', 'mod_hash', 'full_path'), True),
        )

    @classmethod
    @lru_cache(None)
    def get_by_id_cached(cls, pk):

        return super().get_by_id(pk)

    @property
    def link(self):
        try:
            _out = list(ModLink.select().where(ModLink.cleaned_mod_name == self.cleaned_name))[0]
            if _out is not None:

                return _out.link
        except IndexError:
            return None

    @property
    def cleaned_name(self) -> str:
        cleaned_name = str(self.name)
        cleaned_name = cleaned_name.strip().strip('@')
        cleaned_name = self.version_regex.sub("", cleaned_name)
        cleaned_name = cleaned_name.strip().casefold()

        return cleaned_name

    def get_all_variants(self) -> tuple["Mod"]:
        all_mods = Mod.select()
        return tuple(mod for mod in all_mods if mod.cleaned_name == self.cleaned_name)

    def get_log_files(self) -> tuple[LogFile]:
        query = LogFile.select().join(LogFileAndModJoin).join(Mod).where(Mod.id == self.id)
        log_files = tuple(query)

        return log_files

    def __str__(self):
        return self.name

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name={self.name!r}, default={self.default!r}, official={self.official!r}, mod_dir={self.mod_dir!r}, mod_hash_short={self.mod_hash_short!r}, mod_hash={self.mod_hash}, full_path={self.full_path.as_posix()!r})"

    @property
    def pretty_name(self) -> str:
        return self.name.removeprefix('@')

    @ classmethod
    def from_text_line(cls, line: str) -> tuple["Mod", bool]:

        def strip_converter(in_string: Union[str, None]) -> str:
            if in_string is None:
                return in_string
            return in_string.strip()

        def strip_to_path(data):
            data = strip_converter(data)
            if data is None:
                return data
            return Path(data)

        parts = line.split('|')
        name, mod_dir, default, official, origin = parts[:5]
        optional_kwargs = {}
        if len(parts) > 5:
            optional_kwargs['mod_hash'] = strip_converter(parts[5])
            optional_kwargs["mod_hash_short"] = strip_converter(parts[6])
            optional_kwargs["full_path"] = strip_to_path(parts[7])
        with cls.get_or_create_lock:
            try:
                mod = Mod.get(name=strip_converter(name), mod_dir=strip_converter(mod_dir), default=str_to_bool(default), official=str_to_bool(official), **optional_kwargs)
                created = False
                return mod, created
            except peewee.DoesNotExist:
                created = True
                try:
                    Mod.insert(name=strip_converter(name), mod_dir=strip_converter(mod_dir), default=str_to_bool(default), official=str_to_bool(official), **optional_kwargs).execute()
                except peewee.IntegrityError:
                    created = False
                mod = Mod.get(name=strip_converter(name), mod_dir=strip_converter(mod_dir), default=str_to_bool(default), official=str_to_bool(official), **optional_kwargs)
        return mod, created


class LogFileAndModJoin(BaseModel):
    log_file = ForeignKeyField(model=LogFile, lazy_load=True, backref="mods", index=False, unique=False, on_delete="CASCADE")
    mod = ForeignKeyField(model=Mod, lazy_load=True, backref="log_files", index=False, unique=False)

    class Meta:
        table_name = 'LogFile_and_Mod_join'
        index = (
            (("log_file", "mod"), True)
        )
        primary_key = False

    @ property
    def name(self) -> str:
        return self.mod.name


class LogLevel(EnumLikeBaseModel):
    name = TextField(unique=True, index=True)
    comments = CommentsField(null=True)

    @property
    def background_color(self) -> QColor:
        return self.color_config.get("log_level", self.name, default=None)

    @classmethod
    def get_by_id_cached(cls, pk):

        instance = cls._instance_cache.get_by_id(pk)
        if instance is None:
            return super().get_by_id(pk)

    class Meta:
        table_name = 'LogLevel'

    def __str__(self) -> str:
        return str(self.name)


class RecordClass(BaseModel):
    name = TextField(unique=True, index=True)
    comments = CommentsField(null=True)
    marked = MarkedField()

    # non-db attributes
    record_class_manager: "RecordClassManager" = None

    class Meta:
        table_name = 'RecordClass'

    @classmethod
    @lru_cache(None)
    def get_by_id_cached(cls, pk):

        return super().get_by_id(pk)

    @property
    def background_color(self) -> "QColor":
        return self.record_class.background_color

    @property
    def amount_stored(self) -> int:
        return LogRecord.select().where(LogRecord.record_class == self).count()

    @property
    def specificity(self) -> int:
        return self.record_class.___specificity___

    @property
    def pretty_record_family(self):
        return str(self.record_family).removeprefix("RecordFamily.")

    @property
    def record_family(self):
        return self.record_class.___record_family___

    @cached_property
    def record_class(self) -> "RECORD_CLASS_TYPE":

        return self.record_class_manager.get_by_name(self.name)

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name={self.name!r})"


class RecordOrigin(BaseModel):
    name = TextField(unique=True, verbose_name="Name", index=True)
    identifier = CaselessTextField(unique=True, verbose_name="Identifier", index=True)
    is_default = BooleanField(default=False, verbose_name="Is Default Origin", index=True)
    comments = CommentsField(null=True)
    marked = MarkedField()

    origin_instances: dict[Union[str, int], "RecordOrigin"] = {}

    class Meta:
        table_name = 'RecordOrigin'
        constraints = [SQL('UNIQUE(name, identifier)')]

    def __new__(cls: type[Self], *args, **kwargs) -> Self:
        name = kwargs.get("name", None)
        _id = kwargs.get("id", None)
        key = name if name is not None else _id
        instance = cls.origin_instances.get(key, None)
        if instance is None:
            instance = super(RecordOrigin, cls).__new__(cls)
        return instance

    def _add_to_instances(self) -> None:
        if self.name is not None and self.name not in self.__class__.origin_instances:
            self.__class__.origin_instances[self.name] = self
        if self.id is not None and self.id not in self.__class__.origin_instances:
            self.__class__.origin_instances[self.id] = self

    @classmethod
    def clear_instance_cache(cls) -> None:
        cls.origin_instances.clear()

    @classmethod
    @lru_cache(None)
    def get_by_id_cached(cls, pk):

        return super().get_by_id(pk)

    @property
    def pretty_name(self) -> str:
        return sys.inter(self.name)

    def check(self, raw_record: "RawRecord") -> bool:
        return self.identifier in raw_record.content.casefold()

    @property
    def record_family(self) -> RecordFamily:
        return RecordFamily.from_record_origin(self)


class Message(BaseModel):
    md5_hash = FixedCharField(max_length=32, unique=True, null=False, index=True)
    text = TextBlobField(unique=False, null=False, index=False)

    class Meta:
        table_name = 'Message'
        primary_key = False

    @classmethod
    def get_by_id_cached(cls, pk: str):
        try:
            return cls._meta.database.most_common_messages[pk]
        except KeyError:
            return cls._get_by_id_cached(pk)

    @classmethod
    @lru_cache(maxsize=10_000)
    def _get_by_id_cached(cls, pk: str):
        return cls.get(md5_hash=pk)

    @classmethod
    def hash_text(cls, in_text: str) -> str:
        return hashlib.md5(in_text.encode(encoding='utf-8', errors='ignore')).hexdigest()

    def __str__(self) -> str:
        return sys.intern(self.text)


class LogRecord(BaseModel):
    start = IntegerField(help_text="Start Line number of the Record", verbose_name="Start", index=False)
    end = IntegerField(help_text="End Line number of the Record", verbose_name="End", index=False)
    message_item = FixedCharField(max_length=32, help_text="Message part of the Record", verbose_name="Message", null=False, unique=False, _hidden=True, index=False)
    recorded_at = AwareTimeStampField(verbose_name="Recorded at", index=False)
    called_by = ForeignKeyField(column_name='called_by', field='id', model=ArmaFunction, backref="log_records_called_by", lazy_load=True, null=True, verbose_name="Called by", index=False)
    origin = ForeignKeyField(column_name="origin", field="id", model=RecordOrigin, backref="records", lazy_load=True, verbose_name="Origin", default=0, index=False)
    logged_from = ForeignKeyField(column_name='logged_from', field='id', model=ArmaFunction, backref="log_records_logged_from", lazy_load=True, null=True, verbose_name="Logged from", index=False)
    log_file = ForeignKeyField(column_name='log_file', field='id', model=LogFile, lazy_load=True, backref="log_records", null=False, verbose_name="Log-File", index=True, on_delete="CASCADE")
    log_level = ForeignKeyField(column_name='log_level', default=0, field='id', model=LogLevel, null=True, lazy_load=True, verbose_name="Log-Level", index=False)
    record_class = ForeignKeyField(column_name='record_class', field='id', model=RecordClass, lazy_load=True, verbose_name="Record Class", null=True, index=False)
    marked = MarkedField(index=False)

    # non-db attributes
    message_size_hint = None

    class Meta:
        table_name = 'LogRecord'
        indexes = (
            (("start", "end", "log_file", "log_level", "record_class"), False),
        )

    @classmethod
    @lru_cache(None)
    def get_by_id_cached(cls, pk):

        return super().get_by_id(pk)

    @classmethod
    def amount_log_records(cls) -> int:
        return cls._meta.database.connection().execute('SELECT COUNT(*) from "LogRecord"').fetchone()[0]

    @property
    def server(self) -> Server:
        return Server.get_by_id_cached(self.log_file.server_id)

    @property
    def message(self) -> str:
        try:
            message_obj = self._message
            return message_obj.text
        except AttributeError:
            return sys.intern(next((i[0] for i in Message.select(Message.text).where((Message.md5_hash == self.message_item)).tuples().iterator())))

    @ property
    def pretty_log_level(self) -> str:
        if self.log_level.name == "NO_LEVEL":
            return None
        return self.log_level

    @ property
    def pretty_recorded_at(self) -> str:
        return self.format_datetime(self.recorded_at)

    def to_record_class(self) -> "RECORD_CLASS_TYPE":

        # if self.record_class_id == self.database.base_record_id:
        #     return self
        return self.record_class.record_class.from_db_item(self)

    def get_formated_message(self, msg_format: "MessageFormat" = MessageFormat.PRETTY) -> str:
        return self.message

    @ property
    def pretty_message(self) -> str:
        return self.get_formated_message(MessageFormat.PRETTY)

    def __str__(self) -> str:
        return f"{self.recorded_at.isoformat(sep=' ')} {self.message}"


class MeanUpdateTimePerLogFile(BaseModel):
    recorded_at = AwareTimeStampField(null=False, unique=True)
    time_taken_per_log_file = FloatField(null=False)
    amount_updated = IntegerField(null=False)

    row_limit: int = 3

    class Meta:
        table_name = 'MeanUpdateTimePerLogFile'

    @ classmethod
    def limit_stored_instances(cls) -> None:
        if len(cls.select(cls.id)) <= cls.row_limit:
            return

        for idx, inst_id in enumerate(list(cls.select(cls.id).order_by(cls.recorded_at.desc()))):
            if idx <= (cls.row_limit - 1):
                continue
            cls.delete_by_id(inst_id)

    @classmethod
    def insert_new_measurement(cls, time_taken_per_log_file: Union[float, timedelta], amount_updated: int):
        if amount_updated <= 0:
            return

        now = datetime.now(tz=timezone.utc)
        if isinstance(time_taken_per_log_file, timedelta):
            time_taken_per_log_file = time_taken_per_log_file.total_seconds()

        cls.insert(recorded_at=now, time_taken_per_log_file=time_taken_per_log_file, amount_updated=amount_updated).execute()
        cls.limit_stored_instances()


class DatabaseMetaData(BaseModel):
    started_at = AwareTimeStampField(index=True)
    app_version = VersionField(index=True)
    new_log_files = IntegerField(default=0)
    updated_log_files = IntegerField(default=0)
    added_log_records = IntegerField(default=0)
    errored = TextField(null=True)
    last_update_started_at = AwareTimeStampField(null=True, index=True)
    last_update_finished_at = AwareTimeStampField(null=True, index=True)

    # non-db attributes
    database_meta_lock = RLock()
    amount_old_meta_data_items: int = 50

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.stored_last_update_finished_at: datetime = MiscEnum.NOTHING

    class Meta:
        table_name = 'DatabaseMetaData'

    @ classmethod
    def get_user_version(cls) -> int:
        return cls._meta.database.user_version

    @ classmethod
    def increment_user_version(cls):
        db: "GidSqliteApswDatabase" = cls._meta.database
        db.pragma("user_version", cls.get_user_version() + 1)
        log.debug("incremented user_version to %r", cls.get_user_version())

    @ classmethod
    def get_amount_meta_data_items(cls):
        return DatabaseMetaData.select(DatabaseMetaData.id).count(cls._meta.database, True)

    @ classmethod
    def new_session(cls, started_at: datetime = None, app_version: Version = None) -> "DatabaseMetaData":
        started_at = datetime.now(tz=UTC) if started_at is None else started_at
        app_version = META_INFO.version if app_version is None else app_version
        item = cls(started_at=started_at, app_version=app_version)
        with cls._meta.database.write_lock:
            with cls._meta.database:
                item.save()
            cls.increment_user_version()
        cls.limit_stored_instances()
        return item

    @ classmethod
    def limit_stored_instances(cls) -> None:
        amount = DatabaseMetaData.select(fn.COUNT(DatabaseMetaData)).scalar()
        log.debug("amount: %r", amount)
        while amount > cls.amount_old_meta_data_items:
            oldest = [i for i in DatabaseMetaData.select().order_by(DatabaseMetaData.started_at).limit(1).execute()]
            for i in oldest:
                with cls._meta.database.write_lock:
                    with cls._meta.database:
                        DatabaseMetaData.delete_by_id(i.id)
                        log.debug("removed DatabaseMetaData started at: %r", i.started_at)
            amount = DatabaseMetaData.select(fn.COUNT(DatabaseMetaData)).scalar()

    @classmethod
    def get_average_size_per_log_file(cls) -> int:
        amount_log_files = LogFile.amount_log_files()
        db_file_size = cls._meta.database.database_file_size
        try:
            return db_file_size // amount_log_files
        except ZeroDivisionError:
            return 5242880  # 5mb

    @property
    def mean_update_time_per_log_file(self) -> timedelta:
        values = []
        weights = []
        for time_taken_per_log_file, amount_updated in MeanUpdateTimePerLogFile.select(MeanUpdateTimePerLogFile.time_taken_per_log_file, MeanUpdateTimePerLogFile.amount_updated).tuples().iterator():
            values.append(time_taken_per_log_file)
            weights.append(amount_updated)

        if len(values) == 0:
            values = [15.0]

        if len(weights) == 0:
            weights = [1]

        raw_update_time = numpy.average(values, weights=weights)

        return timedelta(seconds=round(raw_update_time, ndigits=3))

    def get_absolute_last_update_finished_at(self) -> datetime:
        if self.stored_last_update_finished_at is not MiscEnum.NOTHING:
            return self.stored_last_update_finished_at
        if self.last_update_finished_at is None:
            self.last_update_finished_at = DatabaseMetaData.select(DatabaseMetaData.last_update_finished_at).where(DatabaseMetaData.last_update_finished_at != None).order_by(-DatabaseMetaData.last_update_finished_at).scalar()
        self.stored_last_update_finished_at = self.last_update_finished_at
        return self.stored_last_update_finished_at

    def count_log_files(self, server: "Server" = None) -> int:
        if server is None:
            return LogFile.select().count()
        return LogFile.select().where(LogFile.server == server).count()

    def count_log_records(self, log_file: "LogFile" = None, server: "Server" = None) -> int:
        if log_file is None and server is None:
            return LogRecord.select().count()

        if log_file is None and server is not None:
            return LogRecord.select().where(LogRecord.log_file.server == server).count()

        if log_file is not None and server is None:
            return LogRecord.select().where(LogRecord.log_file == log_file).count()

    def increment_new_log_file(self, **kwargs) -> None:
        with self.database_meta_lock:
            amount = kwargs.get("amount", 1)
            self.new_log_files += amount

    def increment_updated_log_file(self, **kwargs) -> None:
        with self.database_meta_lock:
            amount = kwargs.get("amount", 1)
            self.updated_log_files += amount

    def increment_added_log_records(self, **kwargs) -> None:
        with self.database_meta_lock:
            amount = kwargs.get("amount", 1)
            self.added_log_records += amount

    def update_started(self) -> None:
        now = datetime.now(tz=timezone.utc)
        self.last_update_started_at = now
        with self.database.connection_context():
            DatabaseMetaData.update(last_update_started_at=now).where(DatabaseMetaData.id == self.id).execute()

    def update_finished(self) -> None:
        now = datetime.now(tz=timezone.utc)
        self.last_update_finished_at = now
        self.stored_last_update_finished_at = self.last_update_finished_at
        with self.database.connection_context():
            DatabaseMetaData.update(last_update_finished_at=now).where(DatabaseMetaData.id == self.id).execute()


def setup_db(database: "GidSqliteApswDatabase"):
    from antistasi_logbook.data.map_images import MAP_IMAGES_DIR
    from antistasi_logbook.data.coordinates import MAP_COORDS_DIR
    database_proxy.initialize(database)

    all_models = [m for m in BaseModel.__subclasses__() if m.is_view is False]
    database._models = {m.__name__.casefold(): m for m in all_models}
    setup_data = {



        GameMap: [{'dlc': None,
                   'full_name': 'Altis',
                   'name': 'Altis',
                   'official': 1,
                   'workshop_link': None,
                   "map_image_low_resolution": MAP_IMAGES_DIR.joinpath("altis_thumbnail.png")},
                  {'dlc': 'Apex',
                   'full_name': 'Tanoa',
                   'name': 'Tanoa',
                   'official': 1,
                   'workshop_link': None,
                   "map_image_low_resolution": MAP_IMAGES_DIR.joinpath("tanoa_thumbnail.png"),
                   "map_image_high_resolution": MAP_IMAGES_DIR.joinpath("tanoa_huge.png")},
                  {'dlc': 'Contact',
                   'full_name': 'Livonia',
                   'name': 'Enoch',
                   'official': 1,
                   'workshop_link': None,
                   "map_image_low_resolution": None},
                  {'dlc': 'Malden',
                   'full_name': 'Malden',
                   'name': 'Malden',
                   'official': 1,
                   'workshop_link': None,
                   "map_image_low_resolution": MAP_IMAGES_DIR.joinpath("malden_thumbnail.png"),
                   "map_image_high_resolution": MAP_IMAGES_DIR.joinpath("malden_huge.png")},
                  {'dlc': None,
                   'full_name': 'Takistan',
                   'name': 'takistan',
                   'official': 0,
                   'workshop_link': None,
                   "map_image_low_resolution": MAP_IMAGES_DIR.joinpath("takistan_thumbnail.png"),
                   "map_image_high_resolution": MAP_IMAGES_DIR.joinpath("takistan_huge.png")},
                  {'dlc': None,
                   'full_name': 'Virolahti',
                   'name': 'vt7',
                   'official': 0,
                   'workshop_link': 'https://steamcommunity.com/workshop/filedetails/?id=1926513010',
                   "map_image_low_resolution": MAP_IMAGES_DIR.joinpath("virolahti_thumbnail.png")},
                  {'dlc': None,
                   'full_name': 'Sahrani',
                   'name': 'sara',
                   'official': 0,
                   'workshop_link': 'https://steamcommunity.com/sharedfiles/filedetails/?id=583544987',
                   "map_image_low_resolution": MAP_IMAGES_DIR.joinpath("sahrani_thumbnail.png"),
                   "map_image_high_resolution": MAP_IMAGES_DIR.joinpath("sara_huge.png")},
                  {'dlc': None,
                   'full_name': 'Chernarus Winter',
                   'name': 'Chernarus_Winter',
                   'official': 0,
                   'workshop_link': 'https://steamcommunity.com/sharedfiles/filedetails/?id=583544987',
                   "map_image_low_resolution": MAP_IMAGES_DIR.joinpath("cherno_winter_thumbnail.png"),
                   "map_image_high_resolution": MAP_IMAGES_DIR.joinpath("chernarus_winter_huge.png"),
                   "coordinates": json.loads(MAP_COORDS_DIR.joinpath("chernarus_winter_pos.json").read_text(encoding='utf-8', errors='ignore'))},
                  {'dlc': None,
                   'full_name': 'Chernarus Summer',
                   'name': 'chernarus_summer',
                   'official': 0,
                   'workshop_link': 'https://steamcommunity.com/sharedfiles/filedetails/?id=583544987',
                   "map_image_low_resolution": MAP_IMAGES_DIR.joinpath("cherno_summer_thumbnail.png"),
                   "map_image_high_resolution": MAP_IMAGES_DIR.joinpath("chernarus_summer_huge.png"),
                   "coordinates": json.loads(MAP_COORDS_DIR.joinpath("chernarus_winter_pos.json").read_text(encoding='utf-8', errors='ignore'))},
                  {'dlc': None,
                   'full_name': 'Anizay',
                   'name': 'tem_anizay',
                   'official': 0,
                   'workshop_link': 'https://steamcommunity.com/workshop/filedetails/?id=1537973181',
                   "map_image_low_resolution": MAP_IMAGES_DIR.joinpath("anizay_thumbnail.png")},
                  {'dlc': None,
                   'full_name': 'Tembelan',
                   'name': 'Tembelan',
                   'official': 0,
                   'workshop_link': 'https://steamcommunity.com/workshop/filedetails/?id=1252091296',
                   "map_image_low_resolution": MAP_IMAGES_DIR.joinpath("tembelan_thumbnail.png")},
                  {'dlc': 'S.O.G. Prairie Fire',
                   'full_name': 'Cam Lao Nam',
                   'name': 'cam_lao_nam',
                   'official': 1,
                   'workshop_link': None,
                   "map_image_low_resolution": None},
                  {'dlc': 'S.O.G. Prairie Fire',
                   'full_name': 'Khe Sanh',
                   'name': 'vn_khe_sanh',
                   'official': 1,
                   'workshop_link': None,
                   "map_image_low_resolution": None}],

    }

    database.create_tables(all_models)

    for model, data in setup_data.items():
        if model == GameMap:
            base_data = {'dlc': None,
                         'full_name': None,
                         'name': None,
                         'official': 1,
                         'workshop_link': None,
                         "map_image_low_resolution": None,
                         "map_image_high_resolution": None,
                         "coordinates": None}
            data = [base_data.copy() | d for d in data]
        model.insert_many(data).on_conflict_ignore().execute()
