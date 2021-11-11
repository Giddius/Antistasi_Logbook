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
from threading import Lock, RLock
from antistasi_logbook.utilities.locks import FILE_LOCKS
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

    @property
    def file_name(self) -> str:
        return f"fn_{self.name}.sqf"

    @property
    def function_name(self) -> str:
        return f"A3A_fnc_{self.name}"


class GameMap(BaseModel):
    full_name = TextField(null=True, unique=True)
    name = TextField(unique=True)
    official = BooleanField(default=False)
    dlc = TextField(null=True)
    map_image_high_resolution = CompressedImageField(null=True)
    map_image_low_resolution = CompressedImageField(null=True)
    coordinates = JSONField(null=True)
    workshop_link = URLField(null=True)
    comments = TextField(null=True)
    marked = BooleanField(default=False)

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
    remote_storage = ForeignKeyField(column_name='remote_storage', default=0, field='id', model=RemoteStorage, lazy_load=True)
    update_enabled = BooleanField(default=False)
    comments = TextField(null=True)
    marked = BooleanField(default=False)
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
    finished = BooleanField(default=False, null=True)
    header_text = CompressedTextField(null=True)
    startup_text = CompressedTextField(null=True)
    last_parsed_line_number = IntegerField(default=0, null=True)
    utc_offset = TzOffsetField(null=True)
    version = VersionField(null=True)
    game_map = ForeignKeyField(column_name='game_map', field='id', model=GameMap, null=True, lazy_load=True)
    is_new_campaign = BooleanField(default=False)
    server = ForeignKeyField(column_name='server', field='id', model=Server, lazy_load=True, backref="log_files")
    unparsable = BooleanField(default=False)
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
            with self.file_lock:
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

    def __str__(self) -> str:
        return f"{self.__class__.__name__}(server={self.server.name!r}, modified_at={self.modified_at.strftime('%Y-%m-%d %H:%M:%S')!r})"


class Mod(BaseModel):
    full_path = PathField(null=True)
    hash = TextField(null=True)
    hash_short = TextField(null=True)
    link = TextField(null=True)
    mod_dir = TextField()
    name = TextField()
    default = BooleanField(default=False)
    official = BooleanField(default=False)
    comments = TextField(null=True)
    marked = BooleanField(default=False)

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
    is_antistasi_record = BooleanField(default=False)
    logged_from = ForeignKeyField(column_name='logged_from', field='id', model=AntstasiFunction, lazy_load=True, null=True)
    log_file = ForeignKeyField(column_name='log_file', field='id', model=LogFile, lazy_load=True, backref="log_records", null=False)
    log_level = ForeignKeyField(column_name='log_level', default=0, field='id', model=LogLevel, null=True, lazy_load=True)
    record_class = ForeignKeyField(column_name='record_class', field='id', model=RecordClass, lazy_load=True)
    comments = TextField(null=True)
    marked = BooleanField(default=False)

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


def setup_db():
    all_models = BaseModel.__subclasses__()
    database.create_tables(all_models)
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
                                     {"id": 185, "name": "arePositionsConnected"}]}
    for model, data in setup_data.items():
        x = model.insert_many(data).on_conflict_ignore()
        database.execute(x)
    sleep(2)
