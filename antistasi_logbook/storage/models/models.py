# * Standard Library Imports ---------------------------------------------------------------------------->
import os
import re
import json
from io import TextIOWrapper
from time import sleep
from typing import TYPE_CHECKING, Any, Literal, Optional, Generator
from pathlib import Path
from datetime import datetime
from functools import cached_property
from threading import Lock, RLock
from contextlib import contextmanager

# * Third Party Imports --------------------------------------------------------------------------------->
from yarl import URL
from peewee import DatabaseProxy, IntegrityError, fn
from tzlocal import get_localzone
from dateutil.tz import UTC
from playhouse.signals import Model
from playhouse.apsw_ext import TextField, BooleanField, IntegerField, ForeignKeyField
from playhouse.sqlite_ext import JSONField
from gidapptools.general_helper.enums import MiscEnum
# * Qt Imports --------------------------------------------------------------------------------------->
from PySide6.QtGui import QColor

# * Gid Imports ----------------------------------------------------------------------------------------->
from gidapptools import get_logger, get_meta_info, get_meta_paths, get_meta_config
from gidapptools.general_helper.timing import get_dummy_profile_decorator_in_globals
from gidapptools.general_helper.conversion import bytes2human

# * Local Imports --------------------------------------------------------------------------------------->
from antistasi_logbook import setup
from antistasi_logbook.data.misc import LOG_FILE_DATE_REGEX
from antistasi_logbook.utilities.misc import VersionItem
from antistasi_logbook.utilities.locks import FILE_LOCKS
from antistasi_logbook.records.abstract_record import MessageFormat
from antistasi_logbook.updating.remote_managers import remote_manager_registry
from antistasi_logbook.storage.models.custom_fields import (URLField, PathField, LoginField, MarkedField, VersionField, CommentsField, PasswordField, TzOffsetField,
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


get_dummy_profile_decorator_in_globals()

THIS_FILE_DIR = Path(__file__).parent.absolute()


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

    @classmethod
    def create_or_get(cls, **kwargs) -> "BaseModel":
        try:
            return cls.create(**kwargs)
        except IntegrityError:
            return cls.get(*[getattr(cls, k) == v for k, v in kwargs.items()])

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

    @profile
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


class AntstasiFunction(BaseModel):
    name = TextField(unique=True)
    link = URLField(null=True)
    local_path = PathField(null=True)
    comments = CommentsField()
    marked = MarkedField()
    show_as: Literal["file_name", "function_name"] = "function_name"

    class Meta:
        table_name = 'AntstasiFunction'

    @cached_property
    def file_name(self) -> str:
        return f"fn_{self.name}.sqf"

    @cached_property
    def function_name(self) -> str:
        return f"A3A_fnc_{self.name}"

    @staticmethod
    def clean_antistasi_function_name(in_name: str) -> str:
        return in_name.strip().removeprefix("A3A_fnc_").removeprefix("fn_").removesuffix('.sqf')

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
    comments = CommentsField()
    marked = MarkedField()

    class Meta:
        table_name = 'GameMap'

    def __str__(self):
        return self.full_name


class RemoteStorage(BaseModel):
    name = TextField(unique=True, index=True)
    base_url = URLField(null=True)
    _login = LoginField(null=True)
    _password = PasswordField(null=True)
    manager_type = TextField(index=True)
    credentials_required = BooleanField(default=False)

    class Meta:
        table_name = 'RemoteStorage'
        indexes = (
            (('base_url', '_login', '_password', 'manager_type'), True),
        )

    @property
    def password_env_var_name(self) -> str:
        return f"{self.name}_password"

    @property
    def login_env_var_name(self) -> str:
        return f"{self.name}_login"

    def get_password(self) -> Optional[str]:
        if self._password is None:
            return os.getenv(self.password_env_var_name, None)

        return self._password

    def get_login(self) -> Optional[str]:
        if self._login is None:
            return os.getenv(self.login_env_var_name, None)

        return self._login

    def set_login_and_password(self, login: str, password: str, store_in_db: bool = True) -> None:

        if store_in_db is True:
            self._login = login
            self._password = password
            with self.database.write_lock:
                with self.database:
                    self.save()
        else:
            os.environ[self.login_env_var_name] = login
            os.environ[self.password_env_var_name] = password

    def as_remote_manager(self) -> "AbstractRemoteStorageManager":
        manager = remote_manager_registry.get_remote_manager(self)
        return manager

    def __str__(self):
        return ' '.join(self.name.split('_')).title()


class Server(BaseModel):
    local_path = PathField(null=True, unique=True, verbose_name="Local Path", help_text="Location where Log-Files of this server are downloaded to")
    name = TextField(unique=True, index=True, verbose_name="Name", help_text="The Name of the Server")
    remote_path = RemotePathField(null=True, unique=True, verbose_name="Remote Path", help_text="The Path in the Remote Storage containing the log files")
    remote_storage = ForeignKeyField(column_name='remote_storage', default=0, field='id', model=RemoteStorage, lazy_load=True, index=True, verbose_name="Remote Storage")
    update_enabled = BooleanField(default=False, verbose_name="Update", help_text="If this Server should update")
    ip = TextField(null=True, verbose_name="IP Address", help_text="IP Adress of the Server")
    port = IntegerField(null=True, verbose_name="Port", help_text="Port the Server uses")
    comments = CommentsField()
    marked = MarkedField()

    class Meta:
        table_name = 'Server'

    @cached_property
    @profile
    def background_color(self):
        return self.color_config.get("server", self.name, default=None)

    @cached_property
    @profile
    def pretty_name(self) -> str:
        return self.name.replace('_', ' ').title()

    @cached_property
    @profile
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

    def get_amount_log_files(self)->int:
        with self.database.connection_context() as ctx:
            return LogFile.select().where(LogFile.server_id == self.id).count()

    @cached_property
    def full_local_path(self) -> Path:
        if self.local_path is None:

            local_path = self.config.get("folder", "local_storage_folder", default=None)
            if local_path is None:
                local_path = META_PATHS.get_new_temp_dir(name=self.name)
            else:
                local_path = local_path.joinpath(self.name)

        else:
            local_path = self.local_path
        local_path.mkdir(exist_ok=True, parents=True)
        return local_path

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name={self.name!r}, remote_storage={self.remote_storage.name!r}, update_enabled={self.update_enabled!r})"

    def __str__(self) -> str:
        return self.name


class Version(BaseModel):
    full = VersionField(unique=True, verbose_name="Full Version")
    major = IntegerField(verbose_name="Major")
    minor = IntegerField(verbose_name="Minor")
    patch = IntegerField(verbose_name="Patch")
    extra = TextField(null=True, verbose_name="Extra")
    comments = CommentsField()
    marked = MarkedField()

    class Meta:
        table_name = 'Version'

    @classmethod
    def add_or_get_version(cls, version: "VersionItem"):
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
    version = ForeignKeyField(null=True, model=Version, field="id", column_name="version", lazy_load=True, index=True, verbose_name="Version")
    game_map = ForeignKeyField(column_name='game_map', field='id', model=GameMap, null=True, lazy_load=True, index=True, verbose_name="Game-Map")
    is_new_campaign = BooleanField(null=True, index=True, verbose_name="New Campaign")
    campaign_id = IntegerField(null=True, index=True, verbose_name="Campaign Id")
    server = ForeignKeyField(column_name='server', field='id', model=Server, lazy_load=True, backref="log_files", index=True, verbose_name="Server")
    unparsable = BooleanField(default=False, index=True, verbose_name="Unparsable")
    last_parsed_datetime = AwareTimeStampField(null=True, utc=True, verbose_name="Last Parsed Datetime")
    max_mem = IntegerField(verbose_name="Max Memory", null=True)
    comments = CommentsField()
    marked = MarkedField()

    class Meta:
        table_name = 'LogFile'
        indexes = (
            (('name', 'server', 'remote_path'), True),
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.is_downloaded = False

    @cached_property
    @profile
    def time_frame(self) -> DateTimeFrame:
        min_date_time, max_date_time = LogRecord.select(fn.Min(LogRecord.recorded_at), fn.Max(LogRecord.recorded_at)).where(LogRecord.log_file_id == self.id).scalar(as_tuple=True)
        return DateTimeFrame(min_date_time, max_date_time)

    @cached_property
    @profile
    def pretty_server(self) -> str:
        return self.server.pretty_name

    @cached_property
    @profile
    def pretty_utc_offset(self) -> str:
        offset = self.utc_offset
        offset_hours = offset._offset.total_seconds() / 3600

        return f"UTC{offset_hours:+}"

    @cached_property
    @profile
    def amount_log_records(self) -> int:
        return LogRecord.select().where(LogRecord.log_file_id == self.id).count()

    @cached_property
    @profile
    def amount_errors(self) -> int:
        return LogRecord.select().where((LogRecord.log_file_id == self.id) & (LogRecord.log_level_id == self.database.foreign_key_cache.all_log_levels.get("ERROR").id)).count()

    @cached_property
    @profile
    def amount_warnings(self) -> int:
        return LogRecord.select().where((LogRecord.log_file_id == self.id) & (LogRecord.log_level_id == self.database.foreign_key_cache.all_log_levels.get("WARNING").id)).count()

    @cached_property
    @profile
    def pretty_size(self) -> str:
        if self.size is not None:
            return bytes2human(self.size)

    @cached_property
    @profile
    def pretty_modified_at(self) -> str:
        if self.modified_at is not None:
            return self.format_datetime(self.modified_at)

    @cached_property
    @profile
    def pretty_created_at(self) -> str:
        if self.created_at is not None:
            return self.format_datetime(self.created_at)

    @cached_property
    @profile
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
        return LogFileAndModJoin.select(LogFileAndModJoin.mod_id).where(LogFileAndModJoin.log_file == self).count() > 0

    def get_marked_records(self) -> list["LogRecord"]:
        with self.database:
            return [i.to_record_class() for i in LogRecord.select().where((LogRecord.log_file_id == self.id) & (LogRecord.marked == True))]

    def get_stats(self):
        all_stats: list[dict[str, Any]] = []
        self.database.connect(True)
        query = LogRecord.select().where(LogRecord.log_file_id == self.id).where(LogRecord.record_class_id == RecordClass.get(name="PerformanceRecord").id).order_by(-LogRecord.recorded_at)
        for item_data in query.dicts().iterator():
            record_class = RecordClass.record_class_manager.get_by_id(item_data["record_class"])
            item = record_class.from_model_dict(item_data, log_file=self)
            all_stats.append(item.stats)
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
        log.debug(f"{changed=}")
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

    @ property
    def keep_downloaded_files(self) -> bool:
        return self.config.get("downloading", "keep_downloaded_files", default=False)

    def download(self) -> Path:
        return self.server.remote_manager.download_file(self)

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

    def _cleanup(self) -> None:
        if self.is_downloaded is True and self.keep_downloaded_files is False:

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
        return f"{self.__class__.__name__}(server={self.server.name!r}, modified_at={self.modified_at.strftime('%Y-%m-%d %H:%M:%S')!r})"

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
    comments = CommentsField()
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
    comments = CommentsField()

    @cached_property
    def background_color(self) -> QColor:
        return self.color_config.get("log_level", self.name, default=None)

    class Meta:
        table_name = 'LogLevel'

    def __str__(self) -> str:
        return f"{self.name}"


class RecordClass(BaseModel):
    name = TextField(unique=True)
    record_class_manager: "RecordClassManager" = None
    comments = CommentsField()
    marked = MarkedField()

    class Meta:
        table_name = 'RecordClass'

    @property
    def specificity(self) -> int:
        return self.record_class.___specificity___

    @property
    def pretty_record_family(self):
        return str(self.record_family).removeprefix("RecordFamily.")

    @property
    def record_family(self):
        return self.record_class.___record_family___

    @ property
    def record_class(self) -> "RECORD_CLASS_TYPE":
        return self.record_class_manager.get_by_name(self.name)

    def __str__(self) -> str:
        return self.name


class RecordOrigin(BaseModel):
    name = TextField(unique=True, verbose_name="Name")
    identifier = CaselessTextField(unique=True, verbose_name="Identifier")
    is_default = BooleanField(default=False, verbose_name="Is Default Origin")
    comments = CommentsField()
    marked = MarkedField()

    class Meta:
        table_name = 'RecordOrigin'

    def check(self, raw_record: "RawRecord") -> bool:
        return self.identifier in raw_record.content.casefold()


class LogRecord(BaseModel):
    start = IntegerField(help_text="Start Line number of the Record", verbose_name="Start")
    end = IntegerField(help_text="End Line number of the Record", verbose_name="End")
    message = TextField(help_text="Message part of the Record", verbose_name="Message")
    recorded_at = AwareTimeStampField(index=True, utc=True, verbose_name="Recorded at")
    called_by = ForeignKeyField(column_name='called_by', field='id', model=AntstasiFunction, backref="log_records_called_by", lazy_load=True, null=True, index=True, verbose_name="Called by")
    origin = ForeignKeyField(column_name="origin", field="id", model=RecordOrigin, backref="records", lazy_load=True, verbose_name="Origin", default=0)
    logged_from = ForeignKeyField(column_name='logged_from', field='id', model=AntstasiFunction, backref="log_records_logged_from", lazy_load=True, null=True, index=True, verbose_name="Logged from")
    log_file = ForeignKeyField(column_name='log_file', field='id', model=LogFile, lazy_load=True, backref="log_records", null=False, verbose_name="Log-File", index=True)
    log_level = ForeignKeyField(column_name='log_level', default=0, field='id', model=LogLevel, null=True, lazy_load=True, index=True, verbose_name="Log-Level")
    record_class = ForeignKeyField(column_name='record_class', field='id', model=RecordClass, lazy_load=True, index=True, verbose_name="Record Class", null=True)
    marked = MarkedField()
    ___has_multiline_message___: bool = False
    message_size_hint = None

    class Meta:
        table_name = 'LogRecord'
        indexes = (
            (('start', 'end', 'log_file'), True),
        )

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
        if self.is_antistasi_record is True:
            called_by = '| ' + f'Called By: {self.called_by.function_name}'.ljust(40) + ' |' if self.called_by is not None else "|"
            logged_from = f"File: {self.logged_from.function_name}".ljust(40)
            return f"{self.recorded_at.isoformat(sep=' ')} | Antistasi | {self.log_level.name.title().center(11)} | {logged_from} {called_by} {self.message}"

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

    class Meta:
        table_name = 'DatabaseMetaData'

    @classmethod
    def new_session(cls, started_at: datetime = None, app_version: Version = None) -> "DatabaseMetaData":
        started_at = datetime.now(tz=UTC) if started_at is None else started_at
        app_version = VersionItem.from_string(META_INFO.version) if app_version is None else app_version
        item = cls(started_at=started_at, app_version=app_version)
        with cls._meta.database.write_lock:
            with cls._meta.database:
                item.save()

        return item

    def get_absolute_last_update_finished_at(self) -> datetime:
        with self.database.connection_context() as ctx:
            item = DatabaseMetaData.select(DatabaseMetaData.last_update_finished_at).where(DatabaseMetaData.last_update_finished_at != None).order_by(-DatabaseMetaData.last_update_finished_at).scalar()

            if self.last_update_finished_at is None:
                return item
            if item is None:
                return self.last_update_finished_at
            if item < self.last_update_finished_at:
                return self.last_update_finished_at

            return item

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


def migration(database: "GidSqliteApswDatabase"):
    from playhouse.migrate import SqliteMigrator, migrate
    from playhouse.reflection import Introspector
    migrator = SqliteMigrator(database=database)
    introspector = Introspector.from_database(database)
    operations = []
    existing_models = introspector.generate_models()
    all_models = BaseModel.__subclasses__()
    for model in all_models:
        table = model._meta.table_name.removesuffix("__tmp__")
        existing_model = existing_models[table]

        for field_name, field_obj in model._meta.fields.items():
            if field_name in {"id"}:
                continue
            if field_obj.null is False and field_obj.default is None:
                continue
            if field_name not in existing_model._meta.fields:
                log.debug("adding column named %r to %r", field_name, table)
                migrate(migrator.add_column(table=table, column_name=field_name, field=field_obj))

        for existing_field_name in existing_model._meta.fields:
            if existing_field_name not in model._meta.fields:
                migrate(migrator.drop_column(table=table, column_name=existing_field_name))

    # migrate(*operations)


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

                  Server: [{'local_path': None,
                            'name': 'NO_SERVER',
                           'remote_path': None,
                            'remote_storage': 0,
                            'update_enabled': 0,
                            "ip": None,
                            "port": None},
                           {'local_path': None,
                           'name': 'Mainserver_1',
                            'remote_path': 'Antistasi_Community_Logs/Mainserver_1/Server/',
                            'remote_storage': 1,
                            'update_enabled': 1,
                            "ip": "38.133.154.60",
                            "port": 2312},
                           {'local_path': None,
                           'name': 'Mainserver_2',
                            'remote_path': 'Antistasi_Community_Logs/Mainserver_2/Server/',
                            'remote_storage': 1,
                            'update_enabled': 1,
                            "ip": "38.133.154.60",
                            "port": 2322},
                           {'local_path': None,
                           'name': 'Testserver_1',
                            'remote_path': 'Antistasi_Community_Logs/Testserver_1/Server/',
                            'remote_storage': 1,
                            'update_enabled': 1,
                            "ip": "38.133.154.60",
                            "port": 2342},
                           {'local_path': None,
                           'name': 'Testserver_2',
                            'remote_path': 'Antistasi_Community_Logs/Testserver_2/Server/',
                            'remote_storage': 1,
                            'update_enabled': 1,
                            "ip": "38.133.154.60",
                            "port": 2352},
                           {'local_path': None,
                           'name': 'Testserver_3',
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
                             'name': 'Chernarus_Summer',
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
                  AntstasiFunction: [{'id': 1, 'name': 'init'},
                                     {'id': 2, 'name': 'initServer'},
                                     {'id': 3, 'name': 'initParams'},
                                     {'id': 4, 'name': 'initFuncs'},
                                     {'id': 5, 'name': 'JN_fnc_arsenal_init'},
                                     {'id': 6, 'name': 'initVar'},
                                     {'id': 7, 'name': 'initVarCommon'},
                                     {'id': 8, 'name': 'initVarServer'},
                                     {'id': 9, 'name': 'initDisabledMods'},
                                     {'id': 10, 'name': 'compatibilityLoadFaction'},
                                     {'id': 11, 'name': 'registerUnitType'},
                                     {'id': 12, 'name': 'aceModCompat'},
                                     {'id': 13, 'name': 'initVarClient'},
                                     {'id': 14, 'name': 'initACEUnconsciousHandler'},
                                     {'id': 15, 'name': 'loadNavGrid'},
                                     {'id': 16, 'name': 'initZones'},
                                     {'id': 17, 'name': 'initSpawnPlaces'},
                                     {'id': 18, 'name': 'initGarrisons'},
                                     {'id': 19, 'name': 'loadServer'},
                                     {'id': 20, 'name': 'returnSavedStat'},
                                     {'id': 21, 'name': 'getStatVariable'},
                                     {'id': 22, 'name': 'loadStat'},
                                     {'id': 23, 'name': 'updatePreference'},
                                     {'id': 24, 'name': 'tierCheck'},
                                     {'id': 25, 'name': 'initPetros'},
                                     {'id': 26, 'name': 'createPetros'},
                                     {'id': 27, 'name': 'assignBossIfNone'},
                                     {'id': 28, 'name': 'loadPlayer'},
                                     {'id': 29, 'name': 'addHC'},
                                     {'id': 30, 'name': 'advancedTowingInit'},
                                     {'id': 31, 'name': 'logPerformance'},
                                     {'id': 32, 'name': 'initServer'},
                                     {'id': 33, 'name': 'onPlayerDisconnect'},
                                     {'id': 34, 'name': 'savePlayer'},
                                     {'id': 35, 'name': 'vehKilledOrCaptured'},
                                     {'id': 36, 'name': 'postmortem'},
                                     {'id': 37, 'name': 'scheduler'},
                                     {'id': 38, 'name': 'distance'},
                                     {'id': 39, 'name': 'theBossToggleEligibility'},
                                     {'id': 40, 'name': 'retrievePlayerStat'},
                                     {'id': 41, 'name': 'resetPlayer'},
                                     {'id': 42, 'name': 'HR_GRG_fnc_addVehicle'},
                                     {'id': 43, 'name': 'punishment_FF'},
                                     {'id': 44, 'name': 'HR_GRG_fnc_removeFromPool'},
                                     {'id': 45, 'name': 'HR_GRG_fnc_toggleLock'},
                                     {'id': 46, 'name': 'unlockEquipment'},
                                     {'id': 47, 'name': 'arsenalManage'},
                                     {'id': 48, 'name': 'economicsAI'},
                                     {'id': 49, 'name': 'resourcecheck'},
                                     {'id': 50, 'name': 'promotePlayer'},
                                     {'id': 51, 'name': 'reinforcementsAI'},
                                     {'id': 52, 'name': 'AAFroadPatrol'},
                                     {'id': 53, 'name': 'createAIAction'},
                                     {'id': 54, 'name': 'selectReinfUnits'},
                                     {'id': 55, 'name': 'createConvoy'},
                                     {'id': 56, 'name': 'findSpawnPosition'},
                                     {'id': 57, 'name': 'milBuildings'},
                                     {'id': 58, 'name': 'placeIntel'},
                                     {'id': 59, 'name': 'createAIOutposts'},
                                     {'id': 60, 'name': 'convoyMovement'},
                                     {'id': 61, 'name': 'rebelAttack'},
                                     {'id': 62, 'name': 'rebelAttack'},
                                     {'id': 63, 'name': 'markerChange'},
                                     {'id': 64, 'name': 'freeSpawnPositions'},
                                     {'id': 65, 'name': 'punishment'},
                                     {'id': 66, 'name': 'supportAvailable'},
                                     {'id': 67, 'name': 'sendSupport'},
                                     {'id': 68, 'name': 'createSupport'},
                                     {'id': 69, 'name': 'SUP_mortar'},
                                     {'id': 70, 'name': 'chooseSupport'},
                                     {'id': 71, 'name': 'AIreactOnKill'},
                                     {'id': 72, 'name': 'findBaseForQRF'},
                                     {'id': 73, 'name': 'SUP_QRF'},
                                     {'id': 74, 'name': 'getVehiclePoolForQRFs'},
                                     {'id': 75, 'name': 'spawnVehicleAtMarker'},
                                     {'id': 76, 'name': 'endSupport'},
                                     {'id': 77, 'name': 'findAirportForAirstrike'},
                                     {'id': 78, 'name': 'SUP_ASF'},
                                     {'id': 79, 'name': 'addSupportTarget'},
                                     {'id': 80, 'name': 'zoneCheck'},
                                     {'id': 81, 'name': 'AIVEHinit'},
                                     {'id': 82, 'name': 'createAIResources'},
                                     {'id': 83, 'name': 'saveLoop'},
                                     {'id': 84, 'name': 'vehiclePrice'},
                                     {'id': 85, 'name': 'patrolReinf'},
                                     {'id': 86, 'name': 'SUP_mortarRoutine'},
                                     {'id': 87, 'name': 'theBossTransfer'},
                                     {'id': 88, 'name': 'setPlaneLoadout'},
                                     {'id': 89, 'name': 'SUP_ASFRoutine'},
                                     {'id': 90, 'name': 'createAttackVehicle'},
                                     {'id': 91, 'name': 'SUP_QRFRoutine'},
                                     {'id': 92, 'name': 'spawnConvoy'},
                                     {'id': 93, 'name': 'spawnConvoyLine'},
                                     {'id': 94, 'name': 'despawnConvoy'},
                                     {'id': 95, 'name': 'ConvoyTravelAir'},
                                     {'id': 96, 'name': 'paradrop'},
                                     {'id': 97, 'name': 'SUP_airstrike'},
                                     {'id': 98, 'name': 'findPathPrecheck'},
                                     {'id': 99, 'name': 'findPath'},
                                     {'id': 100, 'name': 'airspaceControl'},
                                     {'id': 101, 'name': 'callForSupport'},
                                     {'id': 102, 'name': 'SUP_airstrikeRoutine'},
                                     {'id': 103, 'name': 'convoy'},
                                     {'id': 104, 'name': 'airbomb'},
                                     {'id': 105, 'name': 'mrkWIN'},
                                     {'id': 106, 'name': 'occupantInvaderUnitKilledEH'},
                                     {'id': 107, 'name': 'singleAttack'},
                                     {'id': 108, 'name': 'getVehiclePoolForAttacks'},
                                     {'id': 109, 'name': 'SUP_QRFAvailable'},
                                     {'id': 110, 'name': 'wavedCA'},
                                     {'id': 111, 'name': 'garbageCleaner'},
                                     {'id': 112, 'name': 'missionRequest'},
                                     {'id': 113, 'name': 'minefieldAAF'},
                                     {'id': 114, 'name': 'attackDrillAI'},
                                     {'id': 115, 'name': 'invaderPunish'},
                                     {'id': 116, 'name': 'vehicleConvoyTravel'},
                                     {'id': 117, 'name': 'SUP_CAS'},
                                     {'id': 118, 'name': 'splitVehicleCrewIntoOwnGroups'},
                                     {'id': 119, 'name': 'makePlayerBossIfEligible'},
                                     {'id': 120, 'name': 'replenishGarrison'},
                                     {'id': 121, 'name': 'HQGameOptions'},
                                     {'id': 122, 'name': 'vehicleConvoyTravel'},
                                     {'id': 123, 'name': 'WPCreate'},
                                     {'id': 124, 'name': 'createVehicleQRFBehaviour'},
                                     {'id': 125, 'name': 'AIVEHinit'},
                                     {'id': 126, 'name': 'SUP_CASRoutine'},
                                     {'id': 127, 'name': 'SUP_CASRun'},
                                     {'id': 128, 'name': 'startBreachVehicle'},
                                     {'id': 129, 'name': 'spawnDebuggingLoop'},
                                     {'id': 130, 'name': 'SUP_SAM'},
                                     {'id': 131, 'name': 'cleanserVeh'},
                                     {'id': 132, 'name': 'SUP_SAMRoutine'},
                                     {'id': 133, 'name': 'punishment_release'},
                                     {'id': 134, 'name': 'logistics_unload'},
                                     {'id': 135, 'name': 'rebuildRadioTower'},
                                     {'id': 136, 'name': 'roadblockFight'},
                                     {'id': 137, 'name': 'HR_GRG_fnc_getCatIndex'},
                                     {'id': 138, 'name': 'punishment_sentence_server'},
                                     {'id': 139, 'name': 'punishment_checkStatus'},
                                     {'id': 140, 'name': 'taskUpdate'},
                                     {'id': 141, 'name': 'punishment_FF_addEH'},
                                     {'id': 142, 'name': 'askHelp'},
                                     {'id': 143, 'name': 'unconscious'},
                                     {'id': 144, 'name': 'handleDamage'},
                                     {'id': 145, 'name': 'unconsciousAAF'},
                                     {'id': 146, 'name': 'createCIV'},
                                     {'id': 147, 'name': 'initPreJIP'},
                                     {'id': 148, 'name': 'preInit'},
                                     {'id': 149, 'name': 'init'},
                                     {'id': 150, 'name': 'detector'},
                                     {'id': 151, 'name': 'selector'},
                                     {'id': 152, 'name': 'TV_verifyLoadoutsData'},
                                     {'id': 153, 'name': 'TV_verifyAssets'},
                                     {'id': 154, 'name': 'compileMissionAssets'},
                                     {'id': 155, 'name': 'createAIcontrols'},
                                     {'id': 156, 'name': 'createAICities'},
                                     {'id': 157, 'name': 'createAIAirplane'},
                                     {'id': 158, 'name': 'spawnGroup'},
                                     {'id': 159, 'name': 'fillLootCrate'},
                                     {'id': 160, 'name': 'getNearestNavPoint'},
                                     {'id': 171, 'name': 'HR_GRG_fnc_loadSaveData'},
                                     {'id': 172, 'name': 'compatabilityLoadFaction'},
                                     {'id': 173, 'name': 'spawnHCGroup'},
                                     {'id': 174, 'name': 'AS_Traitor'},
                                     {'id': 175, 'name': 'LOG_Supplies'},
                                     {'id': 176, 'name': 'DES_Heli'},
                                     {'id': 177, 'name': 'LOG_Salvage'},
                                     {'id': 178, 'name': 'ConvoyTravel'},
                                     {"id": 179, "name": "RES_Refugees"},
                                     {'id': 180, 'name': "NATOinit"},
                                     {'id': 181, 'name': "chooseAttackType"},
                                     {"id": 182, "name": "CIVinit"},
                                     {"id": 183, "name": "onConvoyArrival"},
                                     {"id": 184, "name": "surrenderAction"},
                                     {"id": 185, "name": "arePositionsConnected"},
                                     {"id": 186, "name": "moveHQObject"}]}
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
