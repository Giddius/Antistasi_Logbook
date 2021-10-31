from peewee import Model, TextField, IntegerField, BooleanField, AutoField, DateTimeField, ForeignKeyField, SQL, BareField, SqliteDatabase, Field, DatabaseProxy
from .custom_fields import RemotePathField, PathField, VersionField, URLField, BetterDateTimeField
from typing import TYPE_CHECKING, Generator, Hashable, Iterable, Optional, TextIO
from pathlib import Path
from io import TextIOWrapper
from gidapptools import get_meta_paths, get_meta_config
from functools import cached_property
from yarl import URL
from contextlib import contextmanager
from rich.console import Console as RichConsole
if TYPE_CHECKING:
    from antistasi_logbook.updating.remote_managers import AbstractRemoteStorageManager, InfoItem
    from gidapptools.gid_config.meta_factory import GidIniConfig


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


class AntstasiFunction(BaseModel):
    name = TextField(unique=True)
    file_name = TextField(null=True, unique=True)

    class Meta:
        table_name = 'AntstasiFunction'


class GameMap(BaseModel):
    full_name = TextField(null=True, unique=True)
    name = TextField(unique=True)
    official = BooleanField(constraints=[SQL("DEFAULT 0")])
    dlc = TextField(null=True)
    map_image_high_resolution_path = PathField(null=True)
    map_image_low_resolution_path = PathField(null=True)
    workshop_link = URLField(null=True)
    comments = TextField(null=True)

    class Meta:
        table_name = 'GameMap'


class RemoteStorage(BaseModel):
    name = TextField(unique=True)
    base_url = URLField(null=True)
    login = TextField(null=True)
    password = TextField(null=True)
    manager_type = TextField()

    class Meta:
        table_name = 'RemoteStorage'
        indexes = (
            (('base_url', 'login', 'password', 'manager_type'), True),
        )


class Server(BaseModel):
    local_path = PathField(null=True, unique=True)
    name = TextField(unique=True)
    remote_path = RemotePathField(null=True, unique=True)
    remote_storage = ForeignKeyField(column_name='remote_storage', constraints=[SQL("DEFAULT 0")], field='id', model=RemoteStorage, lazy_load=True)
    update_enabled = BooleanField(constraints=[SQL("DEFAULT 0")])
    comments = TextField(null=True)
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

            return CONFIG.get("folder", "local_storage_folder", default=META_PATHS.get_new_temp_dir(name=self.name))

        return self.local_path


class LogFile(BaseModel):
    name = TextField()
    remote_path = RemotePathField(unique=True)
    modified_at = BetterDateTimeField()
    size = IntegerField()
    created_at = BetterDateTimeField(null=True)
    finished = BooleanField(constraints=[SQL("DEFAULT 0")], null=True)
    header_text = TextField(null=True)
    last_parsed_line_number = IntegerField(constraints=[SQL("DEFAULT 0")], null=True)
    utc_offset = IntegerField(null=True)
    version = VersionField(null=True)
    game_map = ForeignKeyField(column_name='game_map', field='id', model=GameMap, null=True, lazy_load=True)
    server = ForeignKeyField(column_name='server', field='id', model=Server, lazy_load=True, backref="log_files")
    comments = TextField(null=True)

    class Meta:
        table_name = 'LogFile'
        indexes = (
            (('name', 'server', 'remote_path'), True),
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.is_downloaded = False

    def add_game_map(self, short_name: str) -> None:
        game_map_item = GameMap.get_or_none(GameMap.name == short_name)
        if game_map_item is None:
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
        return self.server.full_local_path.joinpath(self.remote_path.name)

    @property
    def keep_downloaded_files(self) -> bool:
        return CONFIG.get("downloading", "keep_downloaded_files", default=False)

    @contextmanager
    def open(self) -> TextIOWrapper:
        try:
            if self.is_downloaded is False:
                self.server.remote_manager.download_file(self)
            with self.local_path.open('r', encoding='utf-8', errors='ignore') as f:

                yield f
        finally:
            self._cleanup()

    def _cleanup(self) -> None:
        if self.is_downloaded is True and self.keep_downloaded_files is False:
            log.debug(f'deleting local-file of log_file_item [b]{self.name!r}[/b] from path [u]{self.local_path.as_posix()!r}[/u]')
            self.local_path.unlink(missing_ok=True)


class Mod(BaseModel):
    full_path = PathField(null=True, unique=True)
    hash = TextField(null=True, unique=True)
    hash_short = TextField(column_name='hashShort', null=True, unique=True)
    link = TextField(null=True, unique=True)
    mod_dir = TextField(unique=True)
    name = TextField(unique=True)
    default = BooleanField(constraints=[SQL("DEFAULT 0")])
    official = BooleanField(constraints=[SQL("DEFAULT 0")])
    comments = TextField(null=True)

    class Meta:
        table_name = 'Mod'


class LogFileAndModJoin(BaseModel):
    log_file = ForeignKeyField(column_name='log_file_id', field='id', model=LogFile, lazy_load=True)
    mod = ForeignKeyField(column_name='mod_id', field='id', model=Mod, lazy_load=True)

    class Meta:
        table_name = 'LogFile_and_Mod_join'
        indexes = (
            (('log_file', 'mod'), True),
        )
        primary_key = False


class LogLevel(BaseModel):
    name = TextField(unique=True)

    class Meta:
        table_name = 'LogLevel'


class RecordClass(BaseModel):
    name = TextField(unique=True)

    class Meta:
        table_name = 'RecordClass'


class PunishmentAction(BaseModel):
    name = TextField(unique=True)

    class Meta:
        table_name = 'PunishmentAction'


class LogRecord(BaseModel):
    end = IntegerField()
    start = IntegerField()
    message = TextField()
    recorded_at = BetterDateTimeField()
    called_by = TextField(null=True)
    client = TextField(null=True)
    logged_from = TextField(null=True)
    log_file = ForeignKeyField(column_name='log_file', field='id', model=LogFile, lazy_load=True)
    log_level = ForeignKeyField(column_name='log_level', constraints=[SQL("DEFAULT 0")], field='id', model=LogLevel, null=True, lazy_load=True)
    punishment_action = ForeignKeyField(column_name='punishment_action', constraints=[SQL("DEFAULT 0")], field='id', model=PunishmentAction, null=True, lazy_load=True)
    record_class = ForeignKeyField(column_name='record_class', field='id', model=RecordClass, lazy_load=True)
    comments = TextField(null=True)

    class Meta:
        table_name = 'LogRecord'
        indexes = (
            (('start', 'end', 'log_file', 'record_class'), True),
        )


class SqliteSequence(BaseModel):
    name = BareField(null=True)
    seq = BareField(null=True)

    class Meta:
        table_name = 'sqlite_sequence'
        primary_key = False
