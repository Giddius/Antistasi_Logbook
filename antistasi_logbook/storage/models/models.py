from peewee import Model, TextField, IntegerField, BooleanField, AutoField, DateTimeField, ForeignKeyField, SQL, BareField, SqliteDatabase, Field, DatabaseProxy
from .custom_fields import RemotePathField, PathField, VersionField
from playhouse.sqlite_ext import SqliteExtDatabase
from playhouse.sqliteq import SqliteQueueDatabase
from antistasi_logbook.webdav.webdav_manager import WebdavManager
from antistasi_logbook.webdav.remote_item import RemoteAntistasiLogFolder
database = DatabaseProxy()


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
    comments = TextField(null=True)

    class Meta:
        table_name = 'GameMap'


class RemoteType(BaseModel):
    name = TextField(unique=True)
    base_url = TextField(null=True)
    log_folder = RemotePathField(null=True)
    login = TextField(null=True)
    password = TextField(null=True)

    class Meta:
        table_name = 'RemoteType'
        indexes = (
            (('base_url', 'login', 'password'), True),
        )

    @property
    def manager(self) -> WebdavManager:
        if self.name == "local":
            return None
        return WebdavManager.from_remote_type(base_url=self.base_url, log_folder=self.log_folder, login=self.login, password=self.password)


class Server(BaseModel):
    local_path = PathField(null=True, unique=True)
    name = TextField(unique=True)
    remote_path = RemotePathField(null=True, unique=True)
    remote_type = ForeignKeyField(column_name='remote_type', constraints=[SQL("DEFAULT 0")], field='id', model=RemoteType, lazy_load=True)
    comments = TextField(null=True)

    class Meta:
        table_name = 'Server'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._log_files = None

    @property
    def remote_item(self) -> RemoteAntistasiLogFolder:
        return RemoteAntistasiLogFolder.from_path(manager=self.remote_type.manager, path=self.remote_path)

    def get_log_files(self):
        return list(self.log_files)

    def update(self):
        self._log_files = self.get_log_files()
        finished_log_file_names = {log_file.name for log_file in self._log_files if log_file.finished is True}
        local_log_files = {log_file.name: log_file for log_file in self._log_files if log_file.name not in finished_log_file_names}
        for remote_log_file in reversed(list(self.get_remote_log_files())):
            ...


class LogFile(BaseModel):
    name = TextField()
    remote_path = RemotePathField(unique=True)
    modified_at = DateTimeField()
    size = IntegerField()
    created_at = DateTimeField(null=True)
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
    recorded_at = DateTimeField()
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
