from peewee import Model, TextField, IntegerField, BooleanField, AutoField, DateTimeField, ForeignKeyField, SQL, BareField, SqliteDatabase, Field, DatabaseProxy
from .custom_fields import RemotePathField, PathField, VersionField, URLField

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
    comments = TextField(null=True)

    class Meta:
        table_name = 'Server'


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
    server = ForeignKeyField(column_name='server', field='id', model=Server, lazy_load=True)
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
