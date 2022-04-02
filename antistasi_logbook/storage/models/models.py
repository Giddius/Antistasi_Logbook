# * Standard Library Imports ---------------------------------------------------------------------------->
import re
import json
from io import TextIOWrapper
from time import sleep
from typing import TYPE_CHECKING, Any, Union, Literal, Optional, Generator
from pathlib import Path
from zipfile import ZIP_LZMA, ZipFile
from datetime import datetime, timezone
from functools import cached_property
from threading import Lock, RLock
from contextlib import contextmanager
from statistics import StatisticsError, mean
from collections import defaultdict
from concurrent.futures import Future

# * Qt Imports --------------------------------------------------------------------------------------->
from PySide6.QtGui import QColor

# * Third Party Imports --------------------------------------------------------------------------------->
import keyring
from yarl import URL
from peewee import DatabaseProxy, IntegrityError, fn
from tzlocal import get_localzone
from dateutil.tz import UTC
from playhouse.signals import Model
from playhouse.apsw_ext import TextField, BooleanField, IntegerField, ForeignKeyField
from playhouse.sqlite_ext import JSONField

# * Gid Imports ----------------------------------------------------------------------------------------->
from gidapptools import get_logger, get_meta_info, get_meta_paths, get_meta_config
from gidapptools.general_helper.timing import get_dummy_profile_decorator_in_globals
from gidapptools.general_helper.enums import MiscEnum

from gidapptools.general_helper.conversion import bytes2human

# * Local Imports --------------------------------------------------------------------------------------->
from antistasi_logbook import setup
from antistasi_logbook.data.misc import LOG_FILE_DATE_REGEX
from antistasi_logbook.records.enums import RecordFamily
from antistasi_logbook.utilities.misc import VersionItem
from antistasi_logbook.utilities.locks import FILE_LOCKS
from antistasi_logbook.records.abstract_record import MessageFormat
from antistasi_logbook.updating.remote_managers import remote_manager_registry
from antistasi_logbook.storage.models.custom_fields import (URLField, PathField, LoginField, MarkedField, VersionField, CommentsField, TzOffsetField,
                                                            RemotePathField, CaselessTextField, AwareTimeStampField, CompressedTextField, CompressedImageField)
from antistasi_logbook.utilities.date_time_utilities import DateTimeFrame

setup()
# * Standard Library Imports ---------------------------------------------------------------------------->

# * Third Party Imports --------------------------------------------------------------------------------->

# * Gid Imports ----------------------------------------------------------------------------------------->

if TYPE_CHECKING:
    from gidapptools.gid_config.meta_factory import GidIniConfig

    from antistasi_logbook.storage.database import GidSqliteApswDatabase
    from antistasi_logbook.parsing.raw_record import RawRecord
    from antistasi_logbook.updating.remote_managers import InfoItem, AbstractRemoteStorageManager
    from antistasi_logbook.records.record_class_manager import RECORD_CLASS_TYPE, RecordClassManager


THIS_FILE_DIR = Path(__file__).parent.absolute()

get_dummy_profile_decorator_in_globals()
META_PATHS = get_meta_paths()
CONFIG: "GidIniConfig" = get_meta_config().get_config('general')
META_INFO = get_meta_info()
log = get_logger(__name__)


database_proxy = DatabaseProxy()


LOCAL_TIMEZONE = get_localzone()


class BaseModel(Model):
    _column_name_set: set[str] = None

    class Meta:
        database: "GidSqliteApswDatabase" = database_proxy

    # @classmethod
    # def create_or_get(cls, **kwargs) -> "BaseModel":
    #     try:
    #         return cls.create(**kwargs)
    #     except IntegrityError:
    #         return cls.get(*[getattr(cls, k) == v for k, v in kwargs.items()])

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
        return self._meta.database.config

    @cached_property
    def color_config(self) -> "GidIniConfig":
        return get_meta_config().get_config("color")

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

    def __str__(self) -> str:
        if hasattr(self, "name"):
            return str(self.name)

        return super().__str__()


class ArmaFunctionAuthorPrefix(BaseModel):
    name = TextField(unique=True)
    full_name = TextField(unique=True, null=True)
    local_folder_path = PathField(null=True)
    github_link = URLField(null=True)
    comments = CommentsField(null=True)
    marked = MarkedField()

    class Meta:
        table_name = 'ArmaFunctionAuthorPrefix'

    @property
    def pretty_name(self) -> str:
        if self.full_name is not None:
            return self.full_name
        return super().pretty_name


class ArmaFunction(BaseModel):
    name = TextField()
    author_prefix = ForeignKeyField(column_name='author_prefix', field='id', model=ArmaFunctionAuthorPrefix, lazy_load=True, index=True, verbose_name="Author Prefix")
    link = URLField(null=True)
    local_path = PathField(null=True)
    comments = CommentsField(null=True)
    marked = MarkedField()
    show_as: Literal["file_name", "function_name"] = "function_name"
    parsing_regex: re.Pattern = re.compile(r"(?P<author_prefix>[\w_]+)_fnc_(?P<name>.*)")

    class Meta:
        table_name = 'ArmaFunction'
        indexes = (
            (('name', 'author_prefix'), True),
        )

    @cached_property
    def file_name(self) -> str:
        if self.author_prefix.name == "FSM":
            return f"{self.name}.fsm"

        return f"fn_{self.name}.sqf"

    @cached_property
    def function_name(self) -> str:
        if self.author_prefix.name == "UNKNOWN":
            return self.file_name
        if self.author_prefix.name == "FSM":
            return self.name

        return f"{self.author_prefix}_fnc_{self.name}"

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

    def __str__(self) -> str:
        if self.show_as == "file_name":
            return self.file_name
        elif self.show_as == "function_name":
            return self.function_name
        else:
            return self.name


class GameMap(BaseModel):
    full_name = TextField(null=True, unique=True, index=True, verbose_name="Full Name")
    name = TextField(unique=True, index=True, verbose_name="Internal Name")
    official = BooleanField(default=False, index=True, verbose_name="Official")
    dlc = TextField(null=True, index=True, verbose_name="DLC")
    map_image_high_resolution = CompressedImageField(null=True, verbose_name="High Resolution Image")
    map_image_low_resolution = CompressedImageField(null=True, verbose_name="Low Resolution Image")
    coordinates = JSONField(null=True, verbose_name="Coordinates-JSON")
    workshop_link = URLField(null=True, verbose_name="Workshop Link")
    comments = CommentsField(null=True)
    marked = MarkedField()

    class Meta:
        table_name = 'GameMap'

    def get_avg_players_per_hour(self) -> dict[str, Union[float, int, datetime]]:

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
        for message, recorded_at in list(self.database.execute(query)):

            recorded_at = LogRecord.recorded_at.python_value(recorded_at)
            stats = performance_record_class.parse(message)

            players: int = stats["Players"]
            _all_timestamps.append(recorded_at)

            timestamp: datetime = recorded_at.replace(microsecond=0, second=0, minute=0)

            player_data[timestamp].append(players)

        if len(player_data) <= 0:
            return {"avg_players": None, "sample_size": None, "min_timestamp": None, "max_timestamp": None}

        avg_player_data = {}
        for k, v in player_data.items():
            if len(v) > 1:
                avg_player_data[k] = mean(v)
            else:
                avg_player_data[k] = v[0]

        return {"avg_players": round(mean(avg_player_data.values()), 3), "sample_size": len(avg_player_data), "min_timestamp": min(_all_timestamps), "max_timestamp": max(_all_timestamps)}

    def __str__(self):
        return self.full_name


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

    def get_password(self) -> Optional[str]:
        return keyring.get_password(self.name, self.login)

    def get_login(self) -> Optional[str]:
        return self.login

    def set_login_and_password(self, login: str, password: str) -> None:
        self.login = login
        self.save()

        keyring.set_password(self.name, self.login, password)

    def as_remote_manager(self) -> "AbstractRemoteStorageManager":
        manager = remote_manager_registry.get_remote_manager(self)
        return manager

    def __str__(self):
        return ' '.join(self.name.split('_')).title()


class Server(BaseModel):
    name = TextField(unique=True, index=True, verbose_name="Name", help_text="The Name of the Server")
    remote_path = RemotePathField(null=True, unique=True, verbose_name="Remote Path", help_text="The Path in the Remote Storage containing the log files")
    remote_storage = ForeignKeyField(column_name='remote_storage', default=0, field='id', model=RemoteStorage, lazy_load=True, index=True, verbose_name="Remote Storage")
    update_enabled = BooleanField(default=False, verbose_name="Update", help_text="If this Server should update")
    ip = TextField(null=True, verbose_name="IP Address", help_text="IP Adress of the Server")
    port = IntegerField(null=True, verbose_name="Port", help_text="Port the Server uses")
    comments = CommentsField(null=True)
    marked = MarkedField()
    archive_lock = RLock()

    class Meta:
        table_name = 'Server'

    @cached_property
    def background_color(self):
        return self.color_config.get("server", self.name, default=None)

    @cached_property
    def pretty_name(self) -> str:
        return self.name.replace('_', ' ').title()

    @cached_property
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

    @cached_property
    def full_local_path(self) -> Path:

        local_path = META_PATHS.get_new_temp_dir(name=self.name)

        local_path.mkdir(exist_ok=True, parents=True)
        return local_path

    @cached_property
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
    full = VersionField(unique=True, verbose_name="Full Version")
    major = IntegerField(verbose_name="Major")
    minor = IntegerField(verbose_name="Minor")
    patch = IntegerField(verbose_name="Patch", null=True)
    extra = TextField(null=True, verbose_name="Extra")
    comments = CommentsField(null=True)
    marked = MarkedField()

    class Meta:
        table_name = 'Version'

    @classmethod
    def add_or_get_version(cls, version: "VersionItem"):
        if version is None:
            return
        with cls.get_meta().database.write_lock:
            with cls.get_meta().database:
                extra = version.extra
                if isinstance(extra, int):
                    extra = str(extra)
                try:
                    return Version.create(full=version, major=version.major, minor=version.minor, patch=version.patch, extra=version.extra)
                except IntegrityError:
                    return Version.get(full=version)

    def __str__(self) -> str:
        return str(self.full)


class OriginalLogFile(BaseModel):
    text = CompressedTextField(compression_level=9, unique=True)

    class Meta:
        table_name = 'OriginalLogFile'

    @cached_property
    def temp_path(self) -> Path:

        temp_path = META_PATHS.temp_dir.joinpath(self.log_file[0].server.name, self.log_file[0].name + '.txt')
        temp_path.parent.mkdir(parents=True, exist_ok=True)
        return temp_path

    def to_file(self) -> Path:
        path = self.temp_path
        path.write_text(self.text, encoding='utf-8', errors='ignore')
        return path


class LogFile(BaseModel):
    name = TextField(index=True, verbose_name="Name")
    remote_path = RemotePathField(unique=True, verbose_name="Remote Path")
    modified_at = AwareTimeStampField(index=True, utc=True, verbose_name="Modified at")
    size = IntegerField(verbose_name="Size")
    created_at = AwareTimeStampField(null=True, utc=True, index=True, verbose_name="Created at")
    header_text = CompressedTextField(null=True, verbose_name="Header Text")
    startup_text = CompressedTextField(null=True, verbose_name="Startup Text")
    last_parsed_line_number = IntegerField(default=0, null=True, verbose_name="Last Parsed Line Number")
    utc_offset = TzOffsetField(null=True, verbose_name="UTC Offset")
    version = ForeignKeyField(null=True, model=Version, field="id", column_name="version", lazy_load=True, index=False, verbose_name="Version")
    game_map = ForeignKeyField(column_name='game_map', field='id', model=GameMap, null=True, lazy_load=True, index=True, verbose_name="Game-Map")
    is_new_campaign = BooleanField(null=True, index=True, verbose_name="New Campaign")
    campaign_id = IntegerField(null=True, index=True, verbose_name="Campaign Id")
    server = ForeignKeyField(column_name='server', field='id', model=Server, lazy_load=True, backref="log_files", index=True, verbose_name="Server")
    unparsable = BooleanField(default=False, index=True, verbose_name="Unparsable")
    last_parsed_datetime = AwareTimeStampField(null=True, utc=True, verbose_name="Last Parsed Datetime")
    max_mem = IntegerField(verbose_name="Max Memory", null=True)
    original_file = ForeignKeyField(model=OriginalLogFile, field="id", column_name="original_file", lazy_load=True, backref="log_file", null=True, on_delete="SET NULL")
    comments = CommentsField(null=True)
    marked = MarkedField()

    class Meta:
        table_name = 'LogFile'
        indexes = (
            (('name', 'server', 'remote_path'), True),

        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.is_downloaded: bool = False

    @cached_property
    def time_frame(self) -> DateTimeFrame:
        # query = LogRecord.select(fn.Min(LogRecord.recorded_at), fn.Max(LogRecord.recorded_at)).where((LogRecord.log_file_id == self.id))
        query_string = """SELECT Min("t1"."recorded_at"), Max("t1"."recorded_at") FROM "LogRecord" AS "t1" WHERE ("t1"."log_file" = ?)"""
        cursor = self.database.execute_sql(query_string, (self.id,))
        min_date_time, max_date_time = cursor.fetchone()
        min_date_time = LogRecord.recorded_at.python_value(min_date_time)
        max_date_time = LogRecord.recorded_at.python_value(max_date_time)
        return DateTimeFrame(min_date_time, max_date_time)

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

    @cached_property
    def amount_log_records(self) -> int:
        # query = LogRecord.select(fn.count(LogRecord.id)).where(LogRecord.log_file_id == self.id)
        query_string = """SELECT count("t1"."id") FROM "LogRecord" AS "t1" WHERE ("t1"."log_file" = ?)"""

        cursor = self.database.execute_sql(query_string, (self.id,))
        return cursor.fetchone()[0]

    @cached_property
    def amount_errors(self) -> int:
        error_log_level = self.database.foreign_key_cache.all_log_levels.get("ERROR")
        # query = LogRecord.select(fn.count(LogRecord.id)).where((LogRecord.log_file_id == self.id) & (LogRecord.log_level_id == error_log_level.id))
        query_string = """SELECT count("t1"."id") FROM "LogRecord" AS "t1" WHERE (("t1"."log_file" = ?) AND ("t1"."log_level" = ?))"""
        cursor = self.database.execute_sql(query_string, (self.id, error_log_level.id))
        return cursor.fetchone()[0]

    @cached_property
    def amount_warnings(self) -> int:
        warning_log_level = self.database.foreign_key_cache.all_log_levels.get("WARNING")
        # query = LogRecord.select(fn.count(LogRecord.id)).where((LogRecord.log_file_id == self.id) & (LogRecord.log_level_id == warning_log_level.id))
        query_string = """SELECT count("t1"."id") FROM "LogRecord" AS "t1" WHERE (("t1"."log_file" = ?) AND ("t1"."log_level" = ?))"""

        cursor = self.database.execute_sql(query_string, (self.id, warning_log_level.id))
        return cursor.fetchone()[0]

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

    def is_fully_parsed(self) -> bool:
        if self.last_parsed_datetime is None:
            return False
        return self.last_parsed_datetime == self.modified_at

    def has_game_map(self) -> bool:
        return self.game_map_id is not None

    def has_server(self) -> bool:
        return self.server_id is not None

    def has_mods(self) -> bool:
        with self.database.connection_context() as ctx:
            return LogFileAndModJoin.select(LogFileAndModJoin.mod_id).where(LogFileAndModJoin.log_file == self).count() > 0

    def get_marked_records(self) -> list["LogRecord"]:
        with self.database:
            return [i.to_record_class() for i in LogRecord.select().where((LogRecord.log_file_id == self.id) & (LogRecord.marked == True))]

    def get_campaign_stats(self) -> tuple[list[dict[str, Any]], tuple["LogFile"]]:
        self.database.connect(True)
        all_stats: list[dict[str, Any]] = []
        record_class = RecordClass.get(name="PerformanceRecord")
        conc_record_class = record_class.record_class
        log_files_query = LogFile.select().where(LogFile.campaign_id == self.campaign_id)
        all_log_files = tuple(log_files_query)
        query = LogRecord.select(LogRecord.message, LogRecord.recorded_at).where(LogRecord.log_file_id << log_files_query).where(LogRecord.record_class_id == record_class.id).order_by(-LogRecord.recorded_at)
        for (message, recorded_at) in self.database.execute(query):
            recorded_at = LogRecord.recorded_at.python_value(recorded_at)
            item_stats = conc_record_class.parse(message) | {"timestamp": recorded_at}
            all_stats.append(item_stats)
        self.database.close()
        return all_stats, all_log_files

    def get_stats(self):
        all_stats: list[dict[str, Any]] = []
        self.database.connect(True)
        record_class = RecordClass.get(name="PerformanceRecord")
        query = LogRecord.select(LogRecord.message, LogRecord.recorded_at).where(LogRecord.log_file_id == self.id).where(LogRecord.record_class_id == record_class.id).order_by(-LogRecord.recorded_at)
        conc_record_class = record_class.record_class
        for (message, recorded_at) in self.database.execute(query):
            recorded_at = LogRecord.recorded_at.python_value(recorded_at)
            item_stats = conc_record_class.parse(message) | {"timestamp": recorded_at}
            all_stats.append(item_stats)
        self.database.close()
        return all_stats

    def get_resource_check_stats(self):
        all_stats: list[dict[str, Any]] = []
        self.database.connect(True)
        record_class = RecordClass.get(name="ResourceCheckRecord")
        query = LogRecord.select(LogRecord.message, LogRecord.recorded_at).where(LogRecord.log_file_id == self.id).where(LogRecord.record_class_id == record_class.id).order_by(-LogRecord.recorded_at)
        conc_record_class = record_class.record_class
        for (message, recorded_at) in self.database.execute(query):
            recorded_at = LogRecord.recorded_at.python_value(recorded_at)
            item_stats = conc_record_class.parse(message) | {"timestamp": recorded_at}

            if "PARSING ERROR" not in item_stats.keys():
                all_stats.append(item_stats)
        self.database.close()
        return all_stats

    @property
    def name_datetime(self) -> Optional[datetime]:
        if match := LOG_FILE_DATE_REGEX.search(self.name):
            datetime_kwargs = {k: int(v) for k, v in match.groupdict().items()}
            return datetime(tzinfo=UTC, **datetime_kwargs)

    def set_last_parsed_line_number(self, line_number: int) -> None:
        if line_number <= self.last_parsed_line_number:
            return
        log.debug("setting 'last_parsed_line_number' for %s to %r", self, line_number)
        changed = LogFile.update(last_parsed_line_number=line_number).where(LogFile.id == self.id).execute(self.get_meta().database)
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

    def download(self) -> Path:
        try:
            return self.server.remote_manager.download_file(self)
        except Exception as e:
            log.warning("unable to download log-file %r because of %r", self, e)
            log.error(e, exc_info=True)
            if self.original_file is not None:
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
        finally:
            if cleanup is True:
                self._cleanup()

    def store_original_log_file(self):

        if self.original_file is None:
            log.debug("creating new orginal log file for logfile %r, because logfile.original_file=%r", self, self.original_file)
            with self.database.write_lock:
                with self.database:
                    text = self.local_path.read_text(encoding='utf-8', errors='ignore')
                    try:
                        original_file = OriginalLogFile.create(text=text)
                    except IntegrityError as e:
                        log.critical("error %r while creating OriginalLogFile for LogFile %r", e, self)
                        original_file = OriginalLogFile.get(text=text)
                    self.update(original_file=original_file).where(LogFile.id == self.id).execute()
        else:
            with self.database.write_lock:
                with self.database:
                    log.debug("updating original log file for log file %r, because it already exists", self)
                    OriginalLogFile.update(text=self.local_path.read_text(encoding='utf-8', errors='ignore')).where(OriginalLogFile.id == self.original_file.id).execute()

    def _cleanup(self) -> None:
        log.debug("cleaning up LogFile %r", self)
        if self.is_downloaded is True:
            self.store_original_log_file()
            self.local_path.unlink(missing_ok=True)
            log.debug('deleted local-file of log_file_item %r from path %r', self.name, self.local_path.as_posix())
            self.is_downloaded = False

    def get_mods(self) -> Optional[list["Mod"]]:
        with self.database.connection_context() as ctx:
            _out = [mod.mod for mod in self.mods]
            if not _out:
                return None
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


class Mod(BaseModel):
    full_path = PathField(null=True)
    mod_hash = TextField(null=True)
    mod_hash_short = TextField(null=True)
    mod_dir = TextField()
    name = TextField(index=True)
    default = BooleanField(default=False, index=True)
    official = BooleanField(default=False, index=True)
    comments = CommentsField(null=True)
    marked = MarkedField()
    version_regex = re.compile(r"(\s*\-\s*)?v?\s*[\d\.]*$")

    class Meta:
        table_name = 'Mod'
        indexes = (
            (('name', 'mod_dir', "full_path", "mod_hash", "mod_hash_short"), True),
        )

    @property
    def link(self):
        try:
            _out = list(ModLink.select().where(ModLink.cleaned_mod_name == self.cleaned_name))[0]
            if _out is not None:

                return _out.link
        except IndexError:
            return None

    @cached_property
    def cleaned_name(self) -> str:
        cleaned_name = str(self.name)
        cleaned_name = cleaned_name.strip().strip('@')
        cleaned_name = self.version_regex.sub("", cleaned_name)
        cleaned_name = cleaned_name.strip().casefold()

        return cleaned_name

    def get_log_files(self) -> tuple[LogFile]:
        joiners = LogFileAndModJoin.select().where(LogFileAndModJoin.mod_id == self.id)
        log_files = [LogFile.get_by_id(i.log_file_id) for i in joiners]
        return tuple(log_files)

    def __str__(self):
        return self.name

    @cached_property
    def pretty_name(self) -> str:
        return self.name.removeprefix('@')


class LogFileAndModJoin(BaseModel):
    log_file = ForeignKeyField(column_name='log_file_id', field='id', model=LogFile, lazy_load=True, backref="mods")
    mod = ForeignKeyField(column_name='mod_id', field='id', model=Mod, lazy_load=True, backref="log_files")

    class Meta:
        table_name = 'LogFile_and_Mod_join'
        indexes = (
            (('log_file', 'mod'), True),
        )
        primary_key = False

    @ property
    def name(self) -> str:
        return self.mod.name


class LogLevel(BaseModel):
    name = TextField(unique=True)
    comments = CommentsField(null=True)

    @cached_property
    def background_color(self) -> QColor:
        return self.color_config.get("log_level", self.name, default=None)

    class Meta:
        table_name = 'LogLevel'

    def __str__(self) -> str:
        return f"{self.name}"


class RecordClass(BaseModel):
    record_class_manager: "RecordClassManager" = None
    name = TextField(unique=True, index=True)
    comments = CommentsField(null=True)
    marked = MarkedField()
    _record_class: "RECORD_CLASS_TYPE" = None

    class Meta:
        table_name = 'RecordClass'

    @property
    def background_color(self) -> "QColor":
        return self.record_class.background_color

    @cached_property
    def amount_stored(self) -> int:
        return LogRecord.select().where(LogRecord.record_class == self).count()

    @cached_property
    def specificity(self) -> int:
        return self.record_class.___specificity___

    @cached_property
    def pretty_record_family(self):
        return str(self.record_family).removeprefix("RecordFamily.")

    @cached_property
    def record_family(self):
        return self.record_class.___record_family___

    @property
    def record_class(self) -> "RECORD_CLASS_TYPE":
        if self._record_class is None:
            self._record_class = self.record_class_manager.get_by_name(self.name)
        return self._record_class

    def __str__(self) -> str:
        return self.name


class RecordOrigin(BaseModel):
    name = TextField(unique=True, verbose_name="Name", index=True)
    identifier = CaselessTextField(unique=True, verbose_name="Identifier", index=True)
    is_default = BooleanField(default=False, verbose_name="Is Default Origin")
    comments = CommentsField(null=True)
    marked = MarkedField()

    class Meta:
        table_name = 'RecordOrigin'

    def check(self, raw_record: "RawRecord") -> bool:
        return self.identifier in raw_record.content.casefold()

    @cached_property
    def record_family(self) -> RecordFamily:
        return RecordFamily.from_record_origin(self)


class LogRecord(BaseModel):
    start = IntegerField(help_text="Start Line number of the Record", verbose_name="Start")
    end = IntegerField(help_text="End Line number of the Record", verbose_name="End")
    message = TextField(help_text="Message part of the Record", verbose_name="Message")
    recorded_at = AwareTimeStampField(index=True, utc=True, verbose_name="Recorded at")
    called_by = ForeignKeyField(column_name='called_by', field='id', model=ArmaFunction, backref="log_records_called_by", lazy_load=True, null=True, verbose_name="Called by", index=True)
    origin = ForeignKeyField(column_name="origin", field="id", model=RecordOrigin, backref="records", lazy_load=True, verbose_name="Origin", default=0, index=True)
    logged_from = ForeignKeyField(column_name='logged_from', field='id', model=ArmaFunction, backref="log_records_logged_from", lazy_load=True, null=True, verbose_name="Logged from", index=True)
    log_file = ForeignKeyField(column_name='log_file', field='id', model=LogFile, lazy_load=True, backref="log_records", null=False, verbose_name="Log-File", index=True)
    log_level = ForeignKeyField(column_name='log_level', default=0, field='id', model=LogLevel, null=True, lazy_load=True, verbose_name="Log-Level")
    record_class = ForeignKeyField(column_name='record_class', field='id', model=RecordClass, lazy_load=True, verbose_name="Record Class", null=True, index=True)
    marked = MarkedField(index=False)

    message_size_hint = None

    class Meta:
        table_name = 'LogRecord'
        indexes = (
            (('start', 'end', 'log_file'), True),
            (("log_file", "log_level"), False),
            (("log_file", "record_class"), False),
            (("log_file", "logged_from"), False),
            (("log_file", "record_class", "logged_from"), False),
            (("record_class", "logged_from"), False),
            (("log_file", "called_by"), False),
            (("log_file", "origin"), False)
        )

    @profile
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @classmethod
    def amount_log_records(cls) -> int:
        return LogRecord.select(LogRecord.id).count(cls._meta.database, True)

    @cached_property
    def pretty_log_level(self) -> str:
        if self.log_level.name == "NO_LEVEL":
            return None
        return self.log_level

    @cached_property
    def pretty_recorded_at(self) -> str:
        return self.format_datetime(self.recorded_at)

    def to_record_class(self) -> "RECORD_CLASS_TYPE":

        # if self.record_class_id == self.database.base_record_id:
        #     return self
        return self.record_class.record_class.from_db_item(self)

    def get_formated_message(self, msg_format: "MessageFormat" = MessageFormat.PRETTY) -> str:
        return self.message

    @cached_property
    def pretty_message(self) -> str:
        return self.get_formated_message(MessageFormat.PRETTY)

    def __str__(self) -> str:
        return f"{self.recorded_at.isoformat(sep=' ')} {self.message}"


DATABASE_META_LOCK = RLock()


class DatabaseMetaData(BaseModel):
    started_at = AwareTimeStampField(utc=True)
    app_version = VersionField()
    new_log_files = IntegerField(default=0)
    updated_log_files = IntegerField(default=0)
    added_log_records = IntegerField(default=0)
    errored = TextField(null=True)
    last_update_started_at = AwareTimeStampField(null=True, utc=True)
    last_update_finished_at = AwareTimeStampField(null=True, utc=True)
    stored_last_update_finished_at: datetime = MiscEnum.NOTHING

    class Meta:
        table_name = 'DatabaseMetaData'

    @classmethod
    def get_amount_meta_data_items(cls):
        return DatabaseMetaData.select(DatabaseMetaData.id).count(cls._meta.database, True)

    @classmethod
    def new_session(cls, started_at: datetime = None, app_version: Version = None) -> "DatabaseMetaData":
        started_at = datetime.now(tz=UTC) if started_at is None else started_at
        app_version = META_INFO.version if app_version is None else app_version
        item = cls(started_at=started_at, app_version=app_version)
        with cls._meta.database.write_lock:
            with cls._meta.database:
                item.save()
        cls.limit_stored_instances()
        return item

    @classmethod
    def limit_stored_instances(cls) -> None:
        while cls.get_amount_meta_data_items() > 100:
            oldest = DatabaseMetaData.select().order_by(DatabaseMetaData.started_at)[0]
            with cls._meta.database.write_lock:
                with cls._meta.database:
                    DatabaseMetaData.delete_by_id(oldest.id)
                    log.debug("removed DatabaseMetaData started at: %r", oldest.started_at)

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
        with DATABASE_META_LOCK:
            amount = kwargs.get("amount", 1)
            self.new_log_files += amount

    def increment_updated_log_file(self, **kwargs) -> None:
        with DATABASE_META_LOCK:
            amount = kwargs.get("amount", 1)
            self.updated_log_files += amount

    def increment_added_log_records(self, **kwargs) -> None:
        with DATABASE_META_LOCK:
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

    all_models = BaseModel.__subclasses__()

    setup_data = {RemoteStorage: [{"name": "local_files", "id": 0, "base_url": "--LOCAL--", "manager_type": "LocalManager", "credentials_required": False},
                                  {"name": "community_webdav", "id": 1, "base_url": "https://antistasi.de", "manager_type": "WebdavManager", "credentials_required": True}],
                  RecordOrigin: [{"id": 0, "name": "Generic", "identifier": "generic", "is_default": True},
                  {"id": 1, "name": "Antistasi", "identifier": "| antistasi |", "is_default": False}],
                  LogLevel: [{"id": 0, "name": "NO_LEVEL"},
                             {"id": 1, "name": "DEBUG"},
                             {"id": 2, "name": "INFO"},
                             {"id": 3, "name": "WARNING"},
                             {"id": 4, "name": "CRITICAL"},
                             {"id": 5, "name": "ERROR"}],

                  Server: [{'name': 'NO_SERVER',
                           'remote_path': None,
                            'remote_storage': 0,
                            'update_enabled': 0,
                            "ip": None,
                            "port": None},
                           {'name': 'Mainserver_1',
                            'remote_path': 'Antistasi_Community_Logs/Mainserver_1/Server/',
                            'remote_storage': 1,
                            'update_enabled': 1,
                            "ip": "38.133.154.60",
                            "port": 2312},
                           {'name': 'Mainserver_2',
                            'remote_path': 'Antistasi_Community_Logs/Mainserver_2/Server/',
                            'remote_storage': 1,
                            'update_enabled': 1,
                            "ip": "38.133.154.60",
                            "port": 2322},
                           {'name': 'Testserver_1',
                            'remote_path': 'Antistasi_Community_Logs/Testserver_1/Server/',
                            'remote_storage': 1,
                            'update_enabled': 1,
                            "ip": "38.133.154.60",
                            "port": 2342},
                           {'name': 'Testserver_2',
                            'remote_path': 'Antistasi_Community_Logs/Testserver_2/Server/',
                            'remote_storage': 1,
                            'update_enabled': 1,
                            "ip": "38.133.154.60",
                            "port": 2352},
                           {'name': 'Testserver_3',
                            'remote_path': 'Antistasi_Community_Logs/Testserver_3/Server/',
                            'remote_storage': 1,
                            'update_enabled': 1,
                            "ip": None,
                            "port": None}],

                  GameMap: [{'dlc': None,
                             'full_name': 'Altis',
                            'name': 'Altis',
                             'official': 1,
                             'workshop_link': None,
                             "map_image_low_resolution": MAP_IMAGES_DIR.joinpath("altis_thumbnail.png").read_bytes()},
                            {'dlc': 'Apex',
                            'full_name': 'Tanoa',
                             'name': 'Tanoa',
                             'official': 1,
                             'workshop_link': None,
                             "map_image_low_resolution": MAP_IMAGES_DIR.joinpath("tanoa_thumbnail.png").read_bytes()},
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
                             "map_image_low_resolution": MAP_IMAGES_DIR.joinpath("malden_thumbnail.png").read_bytes()},
                            {'dlc': None,
                            'full_name': 'Takistan',
                             'name': 'takistan',
                             'official': 0,
                             'workshop_link': None,
                             "map_image_low_resolution": MAP_IMAGES_DIR.joinpath("takistan_thumbnail.png").read_bytes()},
                            {'dlc': None,
                            'full_name': 'Virolahti',
                             'name': 'vt7',
                             'official': 0,
                             'workshop_link': 'https://steamcommunity.com/workshop/filedetails/?id=1926513010',
                             "map_image_low_resolution": MAP_IMAGES_DIR.joinpath("virolahti_thumbnail.png").read_bytes()},
                            {'dlc': None,
                            'full_name': 'Sahrani',
                             'name': 'sara',
                             'official': 0,
                             'workshop_link': 'https://steamcommunity.com/sharedfiles/filedetails/?id=583544987',
                             "map_image_low_resolution": MAP_IMAGES_DIR.joinpath("sahrani_thumbnail.png").read_bytes()},
                            {'dlc': None,
                            'full_name': 'Chernarus Winter',
                             'name': 'Chernarus_Winter',
                             'official': 0,
                             'workshop_link': 'https://steamcommunity.com/sharedfiles/filedetails/?id=583544987',
                             "map_image_low_resolution": MAP_IMAGES_DIR.joinpath("cherno_winter_thumbnail.png").read_bytes(),
                             "coordinates": json.loads(MAP_COORDS_DIR.joinpath("chernarus_winter_pos.json").read_text(encoding='utf-8', errors='ignore'))},
                            {'dlc': None,
                            'full_name': 'Chernarus Summer',
                             'name': 'chernarus_summer',
                             'official': 0,
                             'workshop_link': 'https://steamcommunity.com/sharedfiles/filedetails/?id=583544987',
                             "map_image_low_resolution": MAP_IMAGES_DIR.joinpath("cherno_summer_thumbnail.png").read_bytes(),
                             "coordinates": json.loads(MAP_COORDS_DIR.joinpath("chernarus_winter_pos.json").read_text(encoding='utf-8', errors='ignore'))},
                            {'dlc': None,
                            'full_name': 'Anizay',
                             'name': 'tem_anizay',
                             'official': 0,
                             'workshop_link': 'https://steamcommunity.com/workshop/filedetails/?id=1537973181',
                             "map_image_low_resolution": MAP_IMAGES_DIR.joinpath("anizay_thumbnail.png").read_bytes()},
                            {'dlc': None,
                            'full_name': 'Tembelan',
                             'name': 'Tembelan',
                             'official': 0,
                             'workshop_link': 'https://steamcommunity.com/workshop/filedetails/?id=1252091296',
                             "map_image_low_resolution": MAP_IMAGES_DIR.joinpath("tembelan_thumbnail.png").read_bytes()},
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
                  ModLink: [{"cleaned_mod_name": "vet_unflipping", "link": "https://steamcommunity.com/sharedfiles/filedetails/?id=1703187116"},
                  {"cleaned_mod_name": "gruppe adler trenches", "link": "https://steamcommunity.com/workshop/filedetails/?id=1224892496"},
                  {"cleaned_mod_name": "zeus enhanced", "link": "https://steamcommunity.com/sharedfiles/filedetails/?id=1779063631"},
                  {"cleaned_mod_name": "tfar", "link": "https://steamcommunity.com/sharedfiles/filedetails/?id=894678801"},
                  {"cleaned_mod_name": "enhanced movement", "link": "https://steamcommunity.com/sharedfiles/filedetails/?l=german&id=333310405"},
                  {"cleaned_mod_name": "community base addons", "link": "https://steamcommunity.com/workshop/filedetails/?id=450814997"},
                  {"cleaned_mod_name": "advanced combat environment", "link": "https://steamcommunity.com/workshop/filedetails/?id=463939057"},
                  {"cleaned_mod_name": "rhs: united states forces", "link": "https://steamcommunity.com/sharedfiles/filedetails/?id=843577117"},
                  {"cleaned_mod_name": "rhs: gref", "link": "https://steamcommunity.com/workshop/filedetails/?id=843593391"},
                  {"cleaned_mod_name": "rhs: armed forces of the russian federation", "link": "https://steamcommunity.com/workshop/filedetails/?id=843425103"},
                  {"cleaned_mod_name": "zeusenhancedace3compatibility", "link": "https://steamcommunity.com/sharedfiles/filedetails/?id=2018593688"},
                  {"cleaned_mod_name": "acecompatrhsgref", "link": "https://steamcommunity.com/sharedfiles/filedetails/?id=884966711"},
                  {"cleaned_mod_name": "acecompatrhsarmedforcesoftherussianfederation", "link": "https://steamcommunity.com/sharedfiles/filedetails/?id=773131200"},
                  {"cleaned_mod_name": "acecompatrhsunitedstatesarmedforces", "link": "https://steamcommunity.com/sharedfiles/filedetails/?id=773125288"},
                  {"cleaned_mod_name": "taskforceenforcer", "link": "https://github.com/Sparker95/TaskForceEnforcer"},
                  {"cleaned_mod_name": "rksl attachments pack", "link": "https://steamcommunity.com/workshop/filedetails/?id=1661066023"}],
                  ArmaFunctionAuthorPrefix: [{"id": 1, "name": "UNKNOWN", "full_name": "Unknown", "github_link": None},
                  {"id": 2, "name": "FSM", "full_name": "Finite State Machine", "github_link": None},
        {"id": 3, "name": "A3A", "full_name": "Antistasi", "github_link": "https://github.com/official-antistasi-community/A3-Antistasi/tree/unstable"},
        {"id": 4, "name": "JN", "full_name": "Jeroen Arsenal", "github_link": "https://github.com/official-antistasi-community/A3-Antistasi/tree/unstable"},
        {"id": 5, "name": "HR_GRG", "full_name": "Hakon Garage", "github_link": "https://github.com/official-antistasi-community/A3-Antistasi/tree/unstable"}],
        ArmaFunction: [
        {'author_prefix': 1, 'id': 1, 'link': None, 'name': 'init'},
        {'author_prefix': 3, 'id': 2, 'link': None, 'name': 'initServer'},
        {'author_prefix': 3, 'id': 3, 'link': None, 'name': 'initParams'},
        {'author_prefix': 3, 'id': 4, 'link': None, 'name': 'initFuncs'},
        {'author_prefix': 4, 'id': 5, 'link': None, 'name': 'arsenal_init'},
        {'author_prefix': 3, 'id': 6, 'link': None, 'name': 'initVar'},
        {'author_prefix': 3, 'id': 7, 'link': None, 'name': 'initVarCommon'},
        {'author_prefix': 3, 'id': 8, 'link': None, 'name': 'initVarServer'},
        {'author_prefix': 3, 'id': 9, 'link': None, 'name': 'initDisabledMods'},
        {
            'author_prefix': 3,
            'id': 10,
            'link': None,
            'name': 'compatibilityLoadFaction',
        },
        {'author_prefix': 3, 'id': 11, 'link': None, 'name': 'registerUnitType'},
        {'author_prefix': 3, 'id': 12, 'link': None, 'name': 'aceModCompat'},
        {'author_prefix': 3, 'id': 13, 'link': None, 'name': 'initVarClient'},
        {
            'author_prefix': 3,
            'id': 14,
            'link': None,
            'name': 'initACEUnconsciousHandler',
        },
        {'author_prefix': 3, 'id': 15, 'link': None, 'name': 'loadNavGrid'},
        {'author_prefix': 3, 'id': 16, 'link': None, 'name': 'initZones'},
        {'author_prefix': 3, 'id': 17, 'link': None, 'name': 'initSpawnPlaces'},
        {'author_prefix': 3, 'id': 18, 'link': None, 'name': 'initGarrisons'},
        {'author_prefix': 3, 'id': 19, 'link': None, 'name': 'addHC'},
        {'author_prefix': 3, 'id': 20, 'link': None, 'name': 'loadServer'},
        {'author_prefix': 3, 'id': 21, 'link': None, 'name': 'returnSavedStat'},
        {'author_prefix': 3, 'id': 22, 'link': None, 'name': 'getStatVariable'},
        {'author_prefix': 3, 'id': 23, 'link': None, 'name': 'loadStat'},
        {'author_prefix': 3, 'id': 24, 'link': None, 'name': 'updatePreference'},
        {'author_prefix': 3, 'id': 25, 'link': None, 'name': 'tierCheck'},
        {'author_prefix': 3, 'id': 26, 'link': None, 'name': 'initPetros'},
        {'author_prefix': 3, 'id': 27, 'link': None, 'name': 'createPetros'},
        {'author_prefix': 1, 'id': 28, 'link': None, 'name': 'advancedTowingInit'},
        {'author_prefix': 1, 'id': 29, 'link': None, 'name': 'initServer'},
        {'author_prefix': 3, 'id': 30, 'link': None, 'name': 'assignBossIfNone'},
        {'author_prefix': 3, 'id': 31, 'link': None, 'name': 'loadPlayer'},
        {'author_prefix': 3, 'id': 32, 'link': None, 'name': 'logPerformance'},
        {'author_prefix': 3, 'id': 33, 'link': None, 'name': 'scheduler'},
        {'author_prefix': 3, 'id': 34, 'link': None, 'name': 'distance'},
        {'author_prefix': 5, 'id': 35, 'link': None, 'name': 'removeFromPool'},
        {'author_prefix': 5, 'id': 36, 'link': None, 'name': 'addVehicle'},
        {'author_prefix': 3, 'id': 37, 'link': None, 'name': 'onPlayerDisconnect'},
        {'author_prefix': 3, 'id': 38, 'link': None, 'name': 'savePlayer'},
        {'author_prefix': 3, 'id': 39, 'link': None, 'name': 'theBossTransfer'},
        {'author_prefix': 3, 'id': 40, 'link': None, 'name': 'punishment_FF'},
        {'author_prefix': 3, 'id': 41, 'link': None, 'name': 'punishment'},
        {'author_prefix': 3, 'id': 42, 'link': None, 'name': 'economicsAI'},
        {'author_prefix': 3, 'id': 43, 'link': None, 'name': 'resourcecheck'},
        {'author_prefix': 3, 'id': 44, 'link': None, 'name': 'rebelAttack'},
        {'author_prefix': 3, 'id': 45, 'link': None, 'name': 'promotePlayer'},
        {'author_prefix': 3, 'id': 46, 'link': None, 'name': 'reinforcementsAI'},
        {'author_prefix': 3, 'id': 47, 'link': None, 'name': 'AAFroadPatrol'},
        {'author_prefix': 3, 'id': 48, 'link': None, 'name': 'createAIAction'},
        {'author_prefix': 3, 'id': 49, 'link': None, 'name': 'wavedCA'},
        {'author_prefix': 3, 'id': 50, 'link': None, 'name': 'retrievePlayerStat'},
        {'author_prefix': 3, 'id': 51, 'link': None, 'name': 'resetPlayer'},
        {'author_prefix': 3, 'id': 52, 'link': None, 'name': 'WPCreate'},
        {'author_prefix': 3, 'id': 53, 'link': None, 'name': 'findPath'},
        {'author_prefix': 3, 'id': 54, 'link': None, 'name': 'chooseSupport'},
        {'author_prefix': 3, 'id': 55, 'link': None, 'name': 'AIreactOnKill'},
        {'author_prefix': 1, 'id': 56, 'link': None, 'name': 'AIVEHinit'},
        {
            'author_prefix': 3,
            'id': 57,
            'link': None,
            'name': 'vehKilledOrCaptured',
        },
        {'author_prefix': 3, 'id': 58, 'link': None, 'name': 'postmortem'},
        {'author_prefix': 3, 'id': 59, 'link': None, 'name': 'AIVEHinit'},
        {'author_prefix': 3, 'id': 60, 'link': None, 'name': 'supportAvailable'},
        {'author_prefix': 3, 'id': 61, 'link': None, 'name': 'sendSupport'},
        {'author_prefix': 3, 'id': 62, 'link': None, 'name': 'createSupport'},
        {'author_prefix': 3, 'id': 63, 'link': None, 'name': 'SUP_mortar'},
        {'author_prefix': 3, 'id': 64, 'link': None, 'name': 'saveLoop'},
        {
            'author_prefix': 3,
            'id': 65,
            'link': None,
            'name': 'theBossToggleEligibility',
        },
        {'author_prefix': 3, 'id': 66, 'link': None, 'name': 'patrolReinf'},
        {'author_prefix': 3, 'id': 67, 'link': None, 'name': 'selectReinfUnits'},
        {'author_prefix': 3, 'id': 68, 'link': None, 'name': 'replenishGarrison'},
        {'author_prefix': 3, 'id': 69, 'link': None, 'name': 'createConvoy'},
        {'author_prefix': 3, 'id': 70, 'link': None, 'name': 'findSpawnPosition'},
        {'author_prefix': 3, 'id': 71, 'link': None, 'name': 'milBuildings'},
        {'author_prefix': 3, 'id': 72, 'link': None, 'name': 'placeIntel'},
        {
            'author_prefix': 3,
            'id': 73,
            'link': None,
            'name': 'makePlayerBossIfEligible',
        },
        {'author_prefix': 3, 'id': 74, 'link': None, 'name': 'createAIOutposts'},
        {'author_prefix': 3, 'id': 75, 'link': None, 'name': 'unlockEquipment'},
        {'author_prefix': 3, 'id': 76, 'link': None, 'name': 'arsenalManage'},
        {'author_prefix': 3, 'id': 77, 'link': None, 'name': 'attackDrillAI'},
        {'author_prefix': 3, 'id': 78, 'link': None, 'name': 'callForSupport'},
        {'author_prefix': 3, 'id': 79, 'link': None, 'name': 'findBaseForQRF'},
        {'author_prefix': 3, 'id': 80, 'link': None, 'name': 'freeSpawnPositions'},
        {'author_prefix': 3, 'id': 81, 'link': None, 'name': 'SUP_QRF'},
        {
            'author_prefix': 3,
            'id': 82,
            'link': None,
            'name': 'getVehiclePoolForQRFs',
        },
        {
            'author_prefix': 3,
            'id': 83,
            'link': None,
            'name': 'spawnVehicleAtMarker',
        },
        {
            'author_prefix': 3,
            'id': 84,
            'link': None,
            'name': 'createVehicleQRFBehaviour',
        },
        {
            'author_prefix': 3,
            'id': 85,
            'link': None,
            'name': 'createAttackVehicle',
        },
        {'author_prefix': 3, 'id': 86, 'link': None, 'name': 'vehiclePrice'},
        {'author_prefix': 3, 'id': 87, 'link': None, 'name': 'SUP_QRFRoutine'},
        {'author_prefix': 3, 'id': 88, 'link': None, 'name': 'SUP_mortarRoutine'},
        {'author_prefix': 3, 'id': 89, 'link': None, 'name': 'endSupport'},
        {'author_prefix': 3, 'id': 90, 'link': None, 'name': 'spawnConvoy'},
        {'author_prefix': 3, 'id': 91, 'link': None, 'name': 'convoyMovement'},
        {'author_prefix': 3, 'id': 92, 'link': None, 'name': 'spawnConvoyLine'},
        {
            'author_prefix': 3,
            'id': 93,
            'link': None,
            'name': 'splitVehicleCrewIntoOwnGroups',
        },
        {'author_prefix': 3, 'id': 94, 'link': None, 'name': 'garbageCleaner'},
        {'author_prefix': 3, 'id': 95, 'link': None, 'name': 'convoy'},
        {'author_prefix': 3, 'id': 96, 'link': None, 'name': 'missionRequest'},
        {
            'author_prefix': 3,
            'id': 97,
            'link': None,
            'name': 'findAirportForAirstrike',
        },
        {'author_prefix': 3, 'id': 98, 'link': None, 'name': 'SUP_CAS'},
        {'author_prefix': 3, 'id': 99, 'link': None, 'name': 'despawnConvoy'},
        {'author_prefix': 3, 'id': 100, 'link': None, 'name': 'zoneCheck'},
        {'author_prefix': 3, 'id': 101, 'link': None, 'name': 'findPathPrecheck'},
        {'author_prefix': 3, 'id': 102, 'link': None, 'name': 'SUP_airstrike'},
        {'author_prefix': 1, 'id': 103, 'link': None, 'name': 'rebelAttack'},
        {'author_prefix': 3, 'id': 104, 'link': None, 'name': 'markerChange'},
        {'author_prefix': 3, 'id': 105, 'link': None, 'name': 'setPlaneLoadout'},
        {'author_prefix': 3, 'id': 106, 'link': None, 'name': 'SUP_CASRoutine'},
        {'author_prefix': 3, 'id': 107, 'link': None, 'name': 'SUP_CASRun'},
        {'author_prefix': 5, 'id': 108, 'link': None, 'name': 'toggleLock'},
        {'author_prefix': 3, 'id': 109, 'link': None, 'name': 'paradrop'},
        {'author_prefix': 3, 'id': 110, 'link': None, 'name': 'SUP_QRFAvailable'},
        {
            'author_prefix': 3,
            'id': 111,
            'link': None,
            'name': 'SUP_airstrikeRoutine',
        },
        {'author_prefix': 3, 'id': 112, 'link': None, 'name': 'airbomb'},
        {'author_prefix': 3, 'id': 113, 'link': None, 'name': 'addSupportTarget'},
        {'author_prefix': 3, 'id': 114, 'link': None, 'name': 'SUP_ASF'},
        {
            'author_prefix': 3,
            'id': 115,
            'link': None,
            'name': 'spawnDebuggingLoop',
        },
        {
            'author_prefix': 3,
            'id': 116,
            'link': None,
            'name': 'punishment_checkStatus',
        },
        {
            'author_prefix': 1,
            'id': 117,
            'link': None,
            'name': 'punishment_sentence_server',
        },
        {'author_prefix': 3, 'id': 118, 'link': None, 'name': 'createAIResources'},
        {
            'author_prefix': 3,
            'id': 119,
            'link': None,
            'name': 'punishment_release',
        },
        {'author_prefix': 3, 'id': 120, 'link': None, 'name': 'mrkWIN'},
        {'author_prefix': 3, 'id': 121, 'link': None, 'name': 'singleAttack'},
        {
            'author_prefix': 3,
            'id': 122,
            'link': None,
            'name': 'vehicleConvoyTravel',
        },
        {'author_prefix': 3, 'id': 123, 'link': None, 'name': 'invaderPunish'},
        {
            'author_prefix': 3,
            'id': 124,
            'link': None,
            'name': 'occupantInvaderUnitKilledEH',
        },
        {'author_prefix': 3, 'id': 125, 'link': None, 'name': 'rebuildRadioTower'},
        {
            'author_prefix': 3,
            'id': 126,
            'link': None,
            'name': 'getVehiclePoolForAttacks',
        },
        {'author_prefix': 3, 'id': 127, 'link': None, 'name': 'SUP_ASFRoutine'},
        {'author_prefix': 2, 'id': 128, 'link': None, 'name': 'ConvoyTravel'},
        {
            'author_prefix': 3,
            'id': 129,
            'link': None,
            'name': 'startBreachVehicle',
        },
        {'author_prefix': 2, 'id': 130, 'link': None, 'name': 'ConvoyTravelAir'},
        {'author_prefix': 3, 'id': 131, 'link': None, 'name': 'minefieldAAF'},
        {'author_prefix': 3, 'id': 132, 'link': None, 'name': 'SUP_SAM'},
        {'author_prefix': 3, 'id': 133, 'link': None, 'name': 'createAICities'},
        {'author_prefix': 3, 'id': 134, 'link': None, 'name': 'airspaceControl'},
        {
            'author_prefix': 3,
            'id': 135,
            'link': None,
            'name': 'getNearestNavPoint',
        },
        {
            'author_prefix': 3,
            'id': 136,
            'link': None,
            'name': 'arePositionsConnected',
        },
        {'author_prefix': 3, 'id': 137, 'link': None, 'name': 'createAIcontrols'},
        {'author_prefix': 3, 'id': 138, 'link': None, 'name': 'DES_Heli'},
        {'author_prefix': 3, 'id': 139, 'link': None, 'name': 'onConvoyArrival'},
        {'author_prefix': 3, 'id': 140, 'link': None, 'name': 'LOG_Supplies'},
        {'author_prefix': 3, 'id': 141, 'link': None, 'name': 'taskUpdate'},
        {'author_prefix': 1, 'id': 142, 'link': None, 'name': 'CIVinit'},
        {'author_prefix': 3, 'id': 143, 'link': None, 'name': 'logistics_unload'},
        {'author_prefix': 3, 'id': 144, 'link': None, 'name': 'HQGameOptions'},
        {'author_prefix': 3, 'id': 145, 'link': None, 'name': 'fillLootCrate'},
        {'author_prefix': 3, 'id': 146, 'link': None, 'name': 'SUP_SAMRoutine'},
        {'author_prefix': 3, 'id': 147, 'link': None, 'name': 'createAIAirplane'},
        {'author_prefix': 3, 'id': 148, 'link': None, 'name': 'cleanserVeh'},
        {'author_prefix': 3, 'id': 149, 'link': None, 'name': 'roadblockFight'},
        {'author_prefix': 3, 'id': 150, 'link': None, 'name': 'NATOinit'},
        {'author_prefix': 5, 'id': 151, 'link': None, 'name': 'getCatIndex'},
        {'author_prefix': 3, 'id': 152, 'link': None, 'name': 'LOG_Salvage'},
        {'author_prefix': 3, 'id': 153, 'link': None, 'name': 'surrenderAction'},
        {'author_prefix': 3, 'id': 154, 'link': None, 'name': 'citySupportChange'},
        {'author_prefix': 3, 'id': 155, 'link': None, 'name': 'RES_Refugees'},
        {
            'author_prefix': 3,
            'id': 156,
            'link': None,
            'name': 'punishment_FF_addEH',
        },
        {'author_prefix': 3, 'id': 157, 'link': None, 'name': 'initPreJIP'},
        {'author_prefix': 2, 'id': 158, 'link': None, 'name': 'preInit'},
        {'author_prefix': 3, 'id': 159, 'link': None, 'name': 'init'},
        {'author_prefix': 3, 'id': 160, 'link': None, 'name': 'detector'},
        {'author_prefix': 3, 'id': 161, 'link': None, 'name': 'selector'},
        {
            'author_prefix': 3,
            'id': 162,
            'link': None,
            'name': 'TV_verifyLoadoutsData',
        },
        {'author_prefix': 3, 'id': 163, 'link': None, 'name': 'TV_verifyAssets'},
        {
            'author_prefix': 3,
            'id': 164,
            'link': None,
            'name': 'compileMissionAssets',
        },
        {'author_prefix': 3, 'id': 165, 'link': None, 'name': 'spawnGroup'},
        {'author_prefix': 3, 'id': 166, 'link': None, 'name': 'createOutpostsFIA'},
        {
            'author_prefix': 3,
            'id': 167,
            'link': None,
            'name': 'punishment_oceanGulag',
        },
        {'author_prefix': 3, 'id': 168, 'link': None, 'name': 'LOG_Ammo'},
        {
            'author_prefix': 3,
            'id': 169,
            'link': None,
            'name': 'compatabilityLoadFaction',
        },
        {'author_prefix': 3, 'id': 170, 'link': None, 'name': 'AS_Traitor'}]}
    with database:
        database.create_tables(all_models)
    for model, data in setup_data.items():
        if model == GameMap:
            base_data = {'dlc': None,
                         'full_name': 'Altis',
                         'name': 'Altis',
                         'official': 1,
                         'workshop_link': None,
                         "map_image_low_resolution": None,
                         "map_image_high_resolution": None,
                         "coordinates": None}
            data = [base_data.copy() | d for d in data]
        x = model.insert_many(data).on_conflict_ignore()
        with database:
            x.execute()
    sleep(0.5)
