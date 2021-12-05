from antistasi_logbook import setup
setup()
import os
from peewee import TextField, IntegerField, BooleanField, AutoField, DateTimeField, ForeignKeyField, SQL, BareField, SqliteDatabase, Field, DatabaseProxy, IntegrityError, fn
from playhouse.signals import Model
from playhouse.sqlite_ext import JSONField, JSONPath
from playhouse.shortcuts import model_to_dict

from antistasi_logbook.storage.models.custom_fields import RemotePathField, PathField, VersionField, URLField, BetterDateTimeField, TzOffsetField, CompressedTextField, CompressedImageField, LoginField, PasswordField
from typing import TYPE_CHECKING, Generator, Hashable, Iterable, Optional, TextIO, Union
from pathlib import Path
from io import TextIOWrapper

from functools import cached_property
from statistics import mean
import shutil
from concurrent.futures import ProcessPoolExecutor
from yarl import URL
from playhouse.reflection import print_table_sql, get_table_sql
from datetime import datetime, timedelta, timezone
from dateutil.tz import tzoffset, tzlocal, gettz, datetime_ambiguous, resolve_imaginary, datetime_exists, UTC
from dateutil.tzwin import tzres, tzwin, tzwinlocal
from contextlib import contextmanager
from rich.console import Console as RichConsole
from threading import Lock, RLock
from antistasi_logbook.utilities.locks import FILE_LOCKS
from antistasi_logbook.utilities.misc import Version
from pprint import pformat
from antistasi_logbook.data.misc import LOG_FILE_DATE_REGEX
from dateutil.tz import tzoffset, UTC
from playhouse.sqlite_changelog import ChangeLog
from playhouse.apsw_ext import BooleanField, DateTimeField, CharField, IntegerField

from time import sleep
from antistasi_logbook.updating.remote_managers import remote_manager_registry

if TYPE_CHECKING:
    from antistasi_logbook.updating.remote_managers import AbstractRemoteStorageManager, InfoItem
    from gidapptools.gid_config.meta_factory import GidIniConfig
    from antistasi_logbook.records.record_class_manager import RECORD_CLASS_TYPE, RecordClassManager
    from antistasi_logbook.storage.database import GidSqliteApswDatabase

from gidapptools import get_logger, get_meta_info, get_meta_paths, get_meta_config

from gidapptools.general_helper.timing import get_dummy_profile_decorator_in_globals
get_dummy_profile_decorator_in_globals()

THIS_FILE_DIR = Path(__file__).parent.absolute()


META_PATHS = get_meta_paths()
CONFIG: "GidIniConfig" = get_meta_config().get_config('general')
META_INFO = get_meta_info()
log = get_logger(__name__)


database_proxy = DatabaseProxy()


class BaseModel(Model):
    class Meta:
        database = database_proxy

    @classmethod
    def create_or_get(cls, **kwargs) -> "BaseModel":
        try:
            return cls.create(**kwargs)
        except IntegrityError:
            return cls.get(*[getattr(cls, k) == v for k, v in kwargs.items()])

    @classmethod
    def get_meta(cls):
        return cls._meta

    @property
    def config(self) -> "GidIniConfig":
        return self._meta.database.config


class AntstasiFunction(BaseModel):
    name = TextField(unique=True)

    class Meta:
        table_name = 'AntstasiFunction'

    @property
    def file_name(self) -> str:
        return f"fn_{self.name}.sqf"

    @property
    def function_name(self) -> str:
        return f"A3A_fnc_{self.name}"

    @staticmethod
    def clean_antistasi_function_name(in_name: str) -> str:
        return in_name.strip().removeprefix("A3A_fnc_").removeprefix("fn_").removesuffix('.sqf')


class GameMap(BaseModel):
    full_name = TextField(null=True, unique=True, index=True)
    name = TextField(unique=True, index=True)
    official = BooleanField(default=False, index=True)
    dlc = TextField(null=True, index=True)
    map_image_high_resolution = CompressedImageField(null=True)
    map_image_low_resolution = CompressedImageField(null=True)
    coordinates = JSONField(null=True)
    workshop_link = URLField(null=True)
    comments = TextField(null=True)
    marked = BooleanField(default=False, index=True)

    class Meta:
        table_name = 'GameMap'


class RemoteStorage(BaseModel):
    name = TextField(unique=True, index=True)
    base_url = URLField(null=True)
    _login = LoginField(null=True)
    _password = PasswordField(null=True)
    manager_type = TextField(index=True)

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

    def as_remote_manager(self) -> "AbstractRemoteStorageManager":
        manager = remote_manager_registry.get_remote_manager(self)
        return manager


class Server(BaseModel):
    local_path = PathField(null=True, unique=True)
    name = TextField(unique=True, index=True)
    remote_path = RemotePathField(null=True, unique=True)
    remote_storage = ForeignKeyField(column_name='remote_storage', default=0, field='id', model=RemoteStorage, lazy_load=True, index=True)
    update_enabled = BooleanField(default=False)
    comments = TextField(null=True)
    marked = BooleanField(default=False, index=True)

    class Meta:
        table_name = 'Server'

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
        return f"{self.__class__.__name__}(name={self.name!r}, remote_storage={self.remote_storage.name!r}, update_enabled={self.update_enabled!r}, remote_manager={self.remote_manager!r})"

    def __str__(self) -> str:
        return self.name


class LogFile(BaseModel):
    name = TextField(index=True)
    remote_path = RemotePathField(unique=True)
    modified_at = BetterDateTimeField(index=True)
    size = IntegerField()
    created_at = BetterDateTimeField(null=True, index=True)
    header_text = CompressedTextField(null=True)
    startup_text = CompressedTextField(null=True)
    last_parsed_line_number = IntegerField(default=0, null=True)
    utc_offset = TzOffsetField(null=True)
    version = VersionField(null=True, index=True)
    game_map = ForeignKeyField(column_name='game_map', field='id', model=GameMap, null=True, lazy_load=True, index=True)
    is_new_campaign = BooleanField(null=True, index=True)
    campaign_id = IntegerField(null=True, index=True)
    server = ForeignKeyField(column_name='server', field='id', model=Server, lazy_load=True, backref="log_files", index=True)
    unparsable = BooleanField(default=False, index=True)
    last_parsed_datetime = BetterDateTimeField(null=True)
    comments = TextField(null=True)
    marked = BooleanField(default=False)

    class Meta:
        table_name = 'LogFile'
        indexes = (
            (('name', 'server', 'remote_path'), True),
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.is_downloaded = False

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
        return LogFileAndModJoin.select(LogFileAndModJoin.mod_id).where(LogFileAndModJoin.log_file == self).count() > 0

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
        _out = [mod.mod for mod in self.mods]
        if not _out:
            return None
        return _out

    def __rich__(self):
        return f"[u b blue]{self.server.name}/{self.name}[/u b blue]"

    def __repr__(self) -> str:
        return str(self)

    def __str__(self) -> str:
        return f"{self.__class__.__name__}(server={self.server.name!r}, modified_at={self.modified_at.strftime('%Y-%m-%d %H:%M:%S')!r})"


class Mod(BaseModel):
    full_path = PathField(null=True)
    mod_hash = TextField(null=True)
    mod_hash_short = TextField(null=True)
    link = TextField(null=True)
    mod_dir = TextField()
    name = TextField(index=True)
    default = BooleanField(default=False, index=True)
    official = BooleanField(default=False, index=True)
    comments = TextField(null=True)
    marked = BooleanField(default=False, index=True)

    class Meta:
        table_name = 'Mod'
        indexes = (
            (('name', 'mod_dir', "full_path", "mod_hash", "mod_hash_short"), True),
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

    @ property
    def name(self) -> str:
        return self.mod.name


class LogLevel(BaseModel):
    name = TextField(unique=True)

    class Meta:
        table_name = 'LogLevel'

    def __str__(self) -> str:
        return f"{self.name}"


class RecordClass(BaseModel):
    name = TextField(unique=True)
    record_class_manager: "RecordClassManager" = None

    class Meta:
        table_name = 'RecordClass'

    @ cached_property
    def record_class(self) -> "RECORD_CLASS_TYPE":
        return self.record_class_manager.get_by_name(self.name)


class LogRecord(BaseModel):
    start = IntegerField()
    end = IntegerField()
    message = TextField()
    recorded_at = BetterDateTimeField(index=True)
    called_by = ForeignKeyField(column_name='called_by', field='id', model=AntstasiFunction, backref="log_records_called_by", lazy_load=True, null=True, index=True)
    is_antistasi_record = BooleanField(default=False, index=True)
    logged_from = ForeignKeyField(column_name='logged_from', field='id', model=AntstasiFunction, backref="log_records_logged_from", lazy_load=True, null=True, index=True)
    log_file = ForeignKeyField(column_name='log_file', field='id', model=LogFile, lazy_load=True, backref="log_records", null=False)
    log_level = ForeignKeyField(column_name='log_level', default=0, field='id', model=LogLevel, null=True, lazy_load=True, index=True)
    record_class = ForeignKeyField(column_name='record_class', field='id', model=RecordClass, lazy_load=True, index=True)
    marked = BooleanField(default=False, index=True)

    class Meta:
        table_name = 'LogRecord'
        indexes = (
            (('start', 'end', 'log_file'), True),
        )

    def to_record_class(self) -> "RECORD_CLASS_TYPE":
        return self.record_class.record_class(self)

    def __str__(self) -> str:
        if self.is_antistasi_record is True:
            called_by = '| ' + f'Called By: {self.called_by.function_name}'.ljust(40) + ' |' if self.called_by is not None else "|"
            logged_from = f"File: {self.logged_from.function_name}".ljust(40)
            return f"{self.recorded_at.isoformat(sep=' ')} | Antistasi | {self.log_level.name.title().center(11)} | {logged_from} {called_by} {self.message}"

        return f"{self.recorded_at.isoformat(sep=' ')} {self.message}"


DATABASE_META_LOCK = RLock()


class DatabaseMetaData(BaseModel):
    started_at = BetterDateTimeField()
    app_version = VersionField()
    new_log_files = IntegerField(default=0)
    updated_log_files = IntegerField(default=0)
    added_log_records = IntegerField(default=0)
    errored = TextField(null=True)

    class Meta:
        table_name = 'DatabaseMetaData'

    @classmethod
    def new_session(cls, started_at: datetime = None, app_version: Version = None) -> "DatabaseMetaData":
        started_at = datetime.now(tz=UTC) if started_at is None else started_at
        app_version = Version.from_string(META_INFO.version) if app_version is None else app_version
        item = cls(started_at=started_at, app_version=app_version)
        with cls._meta.database:
            item.save()
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


def setup_db(database: "GidSqliteApswDatabase"):
    database_proxy.initialize(database)

    all_models = BaseModel.__subclasses__()

    setup_data = {RemoteStorage: [{"name": "local_files", "id": 0, "base_url": "--LOCAL--", "manager_type": "LocalManager"},
                                  {"name": "community_webdav", "id": 1, "base_url": "https://antistasi.de", "manager_type": "WebdavManager"}],

                  LogLevel: [{"id": 0, "name": "NO_LEVEL"},
                             {"id": 1, "name": "DEBUG"},
                             {"id": 2, "name": "INFO"},
                             {"id": 3, "name": "WARNING"},
                             {"id": 4, "name": "CRITICAL"},
                             {"id": 5, "name": "ERROR"}],

                  Server: [{'local_path': None,
                            'name': 'NO_SERVER',
                           'remote_path': 'NO_PATH',
                            'remote_storage': 0,
                            'update_enabled': 0},
                           {'local_path': None,
                           'name': 'Mainserver_1',
                            'remote_path': 'Antistasi_Community_Logs/Mainserver_1/Server/',
                            'remote_storage': 1,
                            'update_enabled': 1},
                           {'local_path': None,
                           'name': 'Mainserver_2',
                            'remote_path': 'Antistasi_Community_Logs/Mainserver_2/Server/',
                            'remote_storage': 1,
                            'update_enabled': 1},
                           {'local_path': None,
                           'name': 'Testserver_1',
                            'remote_path': 'Antistasi_Community_Logs/Testserver_1/Server/',
                            'remote_storage': 1,
                            'update_enabled': 1},
                           {'local_path': None,
                           'name': 'Testserver_2',
                            'remote_path': 'Antistasi_Community_Logs/Testserver_2/Server/',
                            'remote_storage': 1,
                            'update_enabled': 1},
                           {'local_path': None,
                           'name': 'Testserver_3',
                            'remote_path': 'Antistasi_Community_Logs/Testserver_3/Server/',
                            'remote_storage': 1,
                            'update_enabled': 1},
                           {'local_path': None,
                           'name': 'Eventserver',
                            'remote_path': 'Antistasi_Community_Logs/Eventserver/Server/',
                            'remote_storage': 1,
                            'update_enabled': 0}],

                  GameMap: [{'dlc': None,
                             'full_name': 'Altis',
                            'name': 'Altis',
                             'official': 1,
                             'workshop_link': None},
                            {'dlc': 'Apex',
                            'full_name': 'Tanoa',
                             'name': 'Tanoa',
                             'official': 1,
                             'workshop_link': None},
                            {'dlc': 'Contact',
                            'full_name': 'Livonia',
                             'name': 'Enoch',
                             'official': 1,
                             'workshop_link': None},
                            {'dlc': 'Malden',
                            'full_name': 'Malden',
                             'name': 'Malden',
                             'official': 1,
                             'workshop_link': None},
                            {'dlc': None,
                            'full_name': 'Takistan',
                             'name': 'takistan',
                             'official': 0,
                             'workshop_link': None},
                            {'dlc': None,
                            'full_name': 'Virolahti',
                             'name': 'vt7',
                             'official': 0,
                             'workshop_link': 'https://steamcommunity.com/workshop/filedetails/?id=1926513010'},
                            {'dlc': None,
                            'full_name': 'Sahrani',
                             'name': 'sara',
                             'official': 0,
                             'workshop_link': 'https://steamcommunity.com/sharedfiles/filedetails/?id=583544987'},
                            {'dlc': None,
                            'full_name': 'Chernarus Winter',
                             'name': 'Chernarus_Winter',
                             'official': 0,
                             'workshop_link': 'https://steamcommunity.com/sharedfiles/filedetails/?id=583544987'},
                            {'dlc': None,
                            'full_name': 'Anizay',
                             'name': 'tem_anizay',
                             'official': 0,
                             'workshop_link': 'https://steamcommunity.com/workshop/filedetails/?id=1537973181'},
                            {'dlc': None,
                            'full_name': 'Tembelan',
                             'name': 'Tembelan',
                             'official': 0,
                             'workshop_link': 'https://steamcommunity.com/workshop/filedetails/?id=1252091296'},
                            {'dlc': 'S.O.G. Prairie Fire',
                            'full_name': 'Cam Lao Nam',
                             'name': 'cam_lao_nam',
                             'official': 1,
                             'workshop_link': None},
                            {'dlc': 'S.O.G. Prairie Fire',
                            'full_name': 'Khe Sanh',
                             'name': 'vn_khe_sanh',
                             'official': 1,
                             'workshop_link': None}],

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
        x = model.insert_many(data).on_conflict_ignore()
        with database:
            x.execute()
    sleep(0.5)
