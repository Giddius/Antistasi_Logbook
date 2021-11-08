from antistasi_logbook import setup
setup()
import os
from peewee import TextField, IntegerField, BooleanField, AutoField, DateTimeField, ForeignKeyField, SQL, BareField, SqliteDatabase, Field, DatabaseProxy, IntegrityError
from playhouse.signals import Model
from playhouse.sqlite_ext import JSONField, JSONPath
from antistasi_logbook.storage.models.custom_fields import RemotePathField, PathField, VersionField, URLField, BetterDateTimeField, TzOffsetField, CompressedTextField, CompressedImageField, LoginField, PasswordField
from typing import TYPE_CHECKING, Generator, Hashable, Iterable, Optional, TextIO, Union
from pathlib import Path
from io import TextIOWrapper
from gidapptools import get_meta_paths, get_meta_config
from functools import cached_property
from statistics import mean
import shutil
from concurrent.futures import ProcessPoolExecutor
from yarl import URL
from datetime import datetime, timedelta, timezone
from dateutil.tz import tzoffset, tzlocal, gettz, datetime_ambiguous, resolve_imaginary, datetime_exists, UTC
from dateutil.tzwin import tzres, tzwin, tzwinlocal
from contextlib import contextmanager
from rich.console import Console as RichConsole
from antistasi_logbook.utilities.misc import Version
from antistasi_logbook.data.misc import LOG_FILE_DATE_REGEX
from dateutil.tz import tzoffset, UTC

from time import sleep
if TYPE_CHECKING:
    from antistasi_logbook.updating.remote_managers import AbstractRemoteStorageManager, InfoItem
    from gidapptools.gid_config.meta_factory import GidIniConfig
    from antistasi_logbook.parsing.record_class_manager import RECORD_CLASS_TYPE


CONSOLE = RichConsole(soft_wrap=True)


def dprint(*args, **kwargs):
    CONSOLE.print(*args, **kwargs)
    CONSOLE.rule()


print = dprint


class FakeLogger:
    def __init__(self) -> None:
        self.debug = dprint
        self.info = dprint
        self.warning = dprint
        self.error = dprint
        self.critical = dprint


database = DatabaseProxy()
META_PATHS = get_meta_paths()
CONFIG: "GidIniConfig" = get_meta_config().get_config('general')
log = FakeLogger()


class BaseModel(Model):
    class Meta:
        database = database

    @classmethod
    def create_or_get(cls, **kwargs) -> "BaseModel":
        try:
            return cls.create(**kwargs)
        except IntegrityError:
            return cls.get(*[getattr(cls, k) == v for k, v in kwargs.items()])

    @classmethod
    def get_meta(cls):
        return cls._meta


class AntstasiFunction(BaseModel):
    name = TextField(unique=True)

    class Meta:
        table_name = 'AntstasiFunction'

    @staticmethod
    def clean_name(in_name: str) -> str:
        cleaned_name = in_name.strip()
        cleaned_name = cleaned_name.removeprefix("A3A_fnc_")
        cleaned_name = cleaned_name.removeprefix("fn_")
        cleaned_name = cleaned_name.removesuffix('.sqf')

        return cleaned_name

    @property
    def file_name(self) -> str:
        return f"fn_{self.name}.sqf"

    @property
    def function_name(self) -> str:
        return f"A3A_fnc_{self.name}"


class GameMap(BaseModel):
    full_name = TextField(null=True, unique=True)
    name = TextField(unique=True)
    official = BooleanField(constraints=[SQL("DEFAULT 0")])
    dlc = TextField(null=True)
    map_image_high_resolution = CompressedImageField(null=True)
    map_image_low_resolution = CompressedImageField(null=True)
    coordinates = JSONField(null=True)
    workshop_link = URLField(null=True)
    comments = TextField(null=True)
    marked = BooleanField(constraints=[SQL("DEFAULT 0")])

    class Meta:
        table_name = 'GameMap'


class RemoteStorage(BaseModel):
    name = TextField(unique=True)
    base_url = URLField(null=True)
    _login = LoginField(null=True)
    _password = PasswordField(null=True)
    manager_type = TextField()

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
            self.save()
        else:
            os.environ[self.login_env_var_name] = login
            os.environ[self.password_env_var_name] = password


class Server(BaseModel):
    local_path = PathField(null=True, unique=True)
    name = TextField(unique=True)
    remote_path = RemotePathField(null=True, unique=True)
    remote_storage = ForeignKeyField(column_name='remote_storage', constraints=[SQL("DEFAULT 0")], field='id', model=RemoteStorage, lazy_load=True)
    update_enabled = BooleanField(constraints=[SQL("DEFAULT 0")])
    comments = TextField(null=True)
    marked = BooleanField(constraints=[SQL("DEFAULT 0")])
    remote_manager_cache: dict[str, "AbstractRemoteStorageManager"] = {}

    class Meta:
        table_name = 'Server'

    @property
    def remote_manager(self) -> "AbstractRemoteStorageManager":
        return self.remote_manager_cache[self.remote_storage.name]

    def ensure_remote_manager(self, remote_manager: "AbstractRemoteStorageManager") -> None:
        self.remote_manager_cache[self.remote_storage.name] = remote_manager

    def is_updatable(self) -> bool:
        if self.update_enabled is False:
            return False
        if self.remote_storage.manager_type == "LocalManager":
            return False
        return True

    def get_remote_files(self, remote_manager: "AbstractRemoteStorageManager") -> Generator["InfoItem", None, None]:
        yield from remote_manager.get_files(self.remote_path)

    def get_current_log_files(self) -> dict[str, "LogFile"]:
        _out = {}
        for log_file in self.log_files:
            _out[log_file.name] = log_file
        return _out

    @cached_property
    def full_local_path(self) -> Path:
        if self.local_path is None:

            local_path = CONFIG.get("folder", "local_storage_folder", default=None)
            if local_path is None:
                local_path = META_PATHS.get_new_temp_dir(name=self.name)
            else:
                local_path = local_path.joinpath(self.name)

        else:
            local_path = self.local_path
        local_path.mkdir(exist_ok=True, parents=True)
        return local_path


class LogFile(BaseModel):
    name = TextField()
    remote_path = RemotePathField(unique=True)
    modified_at = BetterDateTimeField()
    size = IntegerField()
    created_at = BetterDateTimeField(null=True)
    finished = BooleanField(constraints=[SQL("DEFAULT 0")], null=True)
    header_text = CompressedTextField(null=True)
    startup_text = CompressedTextField(null=True)
    last_parsed_line_number = IntegerField(constraints=[SQL("DEFAULT 0")], null=True)
    utc_offset = TzOffsetField(null=True)
    version = VersionField(null=True)
    game_map = ForeignKeyField(column_name='game_map', field='id', model=GameMap, null=True, lazy_load=True)
    is_new_campaign = BooleanField(default=False)
    server = ForeignKeyField(column_name='server', field='id', model=Server, lazy_load=True, backref="log_files")
    unparsable = BooleanField(constraints=[SQL("DEFAULT 0")])
    comments = TextField(null=True)
    marked = BooleanField(constraints=[SQL("DEFAULT 0")])

    class Meta:
        table_name = 'LogFile'
        indexes = (
            (('name', 'server', 'remote_path'), True),
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.is_downloaded = False

    def get_mean_players(self) -> Optional[int]:
        def _get_players(record: "LogRecord") -> float:
            item = record.to_record_class()
            return item.stats.get("Players")
        r_class = RecordClass.get(name="PerformanceRecord")
        players = []
        for record in LogRecord.select().where((LogRecord.log_file == self) & (LogRecord.record_class == r_class)):
            players.append(record.to_record_class().stats["Players"])

        if players:
            return round(mean(players), 2)

    @property
    def name_datetime(self) -> Optional[datetime]:
        if match := LOG_FILE_DATE_REGEX.search(self.name):
            datetime_kwargs = {k: int(v) for k, v in match.groupdict().items()}
            return datetime(tzinfo=UTC, **datetime_kwargs)

    def set_first_datetime(self, full_datetime: Optional[tuple[datetime, datetime]]) -> None:
        if full_datetime is None:
            self.utc_offset = full_datetime
            return
        difference_seconds = (full_datetime[0] - full_datetime[1]).total_seconds()
        offset_timedelta = timedelta(hours=difference_seconds // (60 * 60))
        if offset_timedelta.days > 0:
            offset_timedelta = timedelta(hours=(difference_seconds // (60 * 60)) - 24)

        offset = tzoffset(self.name, offset_timedelta)
        self.created_at = self.name_datetime.astimezone(offset)
        self.utc_offset = offset

    def set_version(self, version: Union[str, "Version", tuple]) -> None:
        if isinstance(version, Version) or version is None:
            self.version = version

        elif isinstance(version, str):
            self.version = Version.from_string(version)

        elif isinstance(version, tuple):
            self.version = Version(*version)

    def set_game_map(self, short_name: str) -> None:
        if short_name is None:
            return

        try:
            game_map_item = GameMap.select().where(GameMap.name == short_name)[0]
        except IndexError:
            game_map_item = GameMap(name=short_name, full_name=f"PLACE_HOLDER {short_name}")
            game_map_item.save()

        self.game_map = game_map_item

    @cached_property
    def download_url(self) -> Optional[URL]:
        try:
            return self.server.remote_manager.full_base_url / self.remote_path.as_posix()
        except AttributeError:
            return None

    @cached_property
    def local_path(self) -> Path:
        if self.server.name == "NO_SERVER":
            return Path(self.remote_path)
        return self.server.full_local_path.joinpath(self.remote_path.name)

    @property
    def keep_downloaded_files(self) -> bool:
        return CONFIG.get("downloading", "keep_downloaded_files", default=False)

    def download(self) -> Path:
        return self.server.remote_manager.download_file(self)

    @contextmanager
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
            log.debug(f'deleted local-file of log_file_item [b]{self.name!r}[/b] from path [u]{self.local_path.as_posix()!r}[/u]')
            self.is_downloaded = False

    def get_mods(self) -> Optional[list["Mod"]]:
        _out = [mod.mod for mod in self.mods]
        if not _out:
            return None
        return _out

    def __rich__(self):
        return f"[u b green]{self.server.name}/{self.name}[/u b green]"


class Mod(BaseModel):
    full_path = PathField(null=True)
    hash = TextField(null=True)
    hash_short = TextField(null=True)
    link = TextField(null=True)
    mod_dir = TextField()
    name = TextField()
    default = BooleanField(constraints=[SQL("DEFAULT 0")])
    official = BooleanField(constraints=[SQL("DEFAULT 0")])
    comments = TextField(null=True)
    marked = BooleanField(constraints=[SQL("DEFAULT 0")])

    class Meta:
        table_name = 'Mod'
        indexes = (
            (('name', 'mod_dir', "full_path", "hash", "hash_short"), True),
        )


class LogFileAndModJoin(BaseModel):
    log_file = ForeignKeyField(column_name='log_file_id', field='id', model=LogFile, lazy_load=True, backref="mods")
    mod = ForeignKeyField(column_name='mod_id', field='id', model=Mod, lazy_load=True, backref="log_files")

    class Meta:
        table_name = 'LogFile_and_Mod_join'
        indexes = (
            (('log_file', 'mod'), True),
        )
        primary_key = False

    @property
    def name(self) -> str:
        return self.mod.name


class LogLevel(BaseModel):
    name = TextField(unique=True)

    class Meta:
        table_name = 'LogLevel'


class RecordClass(BaseModel):
    name = TextField(unique=True)

    class Meta:
        table_name = 'RecordClass'

    @cached_property
    def record_class(self) -> "RECORD_CLASS_TYPE":
        return self._meta.database.record_class_manager.get_by_name(self.name)


class LogRecord(BaseModel):
    start = IntegerField()
    end = IntegerField()
    message = TextField()
    recorded_at = BetterDateTimeField()
    called_by = ForeignKeyField(column_name='called_by', field='id', model=AntstasiFunction, lazy_load=True, null=True)
    client = TextField(null=True)
    is_antistasi_record = BooleanField(constraints=[SQL("DEFAULT 0")])
    logged_from = ForeignKeyField(column_name='logged_from', field='id', model=AntstasiFunction, lazy_load=True, null=True)
    log_file = ForeignKeyField(column_name='log_file', field='id', model=LogFile, lazy_load=True, backref="log_records", null=False)
    log_level = ForeignKeyField(column_name='log_level', constraints=[SQL("DEFAULT 0")], field='id', model=LogLevel, null=True, lazy_load=True)
    record_class = ForeignKeyField(column_name='record_class', field='id', model=RecordClass, lazy_load=True)
    comments = TextField(null=True)
    marked = BooleanField(constraints=[SQL("DEFAULT 0")])

    class Meta:
        table_name = 'LogRecord'
        indexes = (
            (('start', 'end', 'log_file', 'record_class'), True),
        )

    def to_record_class(self) -> "RECORD_CLASS_TYPE":
        return self.record_class.record_class(self)


class SqliteSequence(BaseModel):
    name = BareField(null=True)
    seq = BareField(null=True)

    class Meta:
        table_name = 'sqlite_sequence'
        primary_key = False
