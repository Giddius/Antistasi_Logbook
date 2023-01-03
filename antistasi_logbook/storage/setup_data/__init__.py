
from pathlib import Path
import json
from typing import TYPE_CHECKING, Optional
from functools import wraps
from gidapptools.gid_logger.logger import get_logger
from gidapptools.general_helper.timing import get_dummy_profile_decorator_in_globals

from peewee import chunked, IntegrityError, DoesNotExist
from hashlib import blake2b
from frozendict import frozendict

from antistasi_logbook.data.coordinates import MAP_COORDS_DIR

from antistasi_logbook.data.map_images import MAP_IMAGES_DIR

get_dummy_profile_decorator_in_globals()
if TYPE_CHECKING:
    from antistasi_logbook.storage.database import GidSqliteApswDatabase


SETUP_DATA_FOLDER = Path(__file__).parent.absolute()

log = get_logger(__name__)


def get_setup_data_file_hash(name: str) -> Optional[str]:
    try:
        path = SETUP_DATA_FOLDER.joinpath(name + ".json")
        return blake2b(path.read_bytes()).hexdigest()
    except FileNotFoundError:
        return None


def get_setup_data(name: str, default=None) -> list[dict]:
    try:
        name = name.casefold()
        with SETUP_DATA_FOLDER.joinpath(name + ".json").open("r", encoding='utf-8', errors='ignore') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return default


def setup_tables(db: "GidSqliteApswDatabase"):
    for table in db._models.values():
        pre_exists = table.table_exists()
        table.create_table()
        if pre_exists is False:
            log.debug("created table %r", table._meta.table_name)


def setup_loglevel(db: "GidSqliteApswDatabase"):
    model = db.get_model("loglevel")
    model.create_table()
    data = get_setup_data("loglevel")

    model.insert_many(data).on_conflict_ignore().execute()


def setup_recordorigin(db: "GidSqliteApswDatabase"):
    model = db.get_model("recordorigin")
    model.create_table()
    data = get_setup_data("recordorigin")

    model.insert_many(data).on_conflict_ignore().execute()


def setup_arma_author_prefix(db: "GidSqliteApswDatabase"):
    model = db.get_model("armafunctionauthorprefix")
    model.create_table()

    model.insert_many(get_setup_data("armafunctionauthorprefix")).on_conflict_ignore().execute()


def setup_armafunction(db: "GidSqliteApswDatabase"):
    model = db.get_model("armafunction")
    model.create_table()
    data = get_setup_data("armafunction")

    for item in data:
        sub_model = db.get_model("armafunctionauthorprefix")
        item["author_prefix"] = sub_model.select().where((sub_model.name == item["author_prefix"]["name"]) & (sub_model.full_name == item["author_prefix"]["full_name"]))
    model.insert_many(data).on_conflict_ignore().execute()


def setup_most_common_messages(db: "GidSqliteApswDatabase"):
    model = db.get_model("message")
    model.create_table()
    data = get_setup_data("message") + get_setup_data("message_extra", default=[])

    for data_chunk in chunked(data, 327670 // (2 + 1)):
        model.insert_many(data_chunk).on_conflict_ignore().execute()
    log.debug("inserted (or ignored) %r most_common_message items", len(data))

    db.most_common_messages = frozendict({m.md5_hash: m for m in model.select().where((model.md5_hash << [i["md5_hash"] for i in data]))})


def setup_mod_set(db: "GidSqliteApswDatabase"):
    model = db.get_model("modset")
    model.create_table()
    data = get_setup_data("modset")

    model.insert_many(data).on_conflict_ignore().execute()


def setup_modlink(db: "GidSqliteApswDatabase"):
    model = db.get_model("modlink")
    model.create_table()
    data = get_setup_data("modlink")

    model.insert_many(data).on_conflict_ignore().execute()


def setup_remote_storage(db: "GidSqliteApswDatabase"):
    model = db.get_model("remotestorage")
    model.create_table()
    data = get_setup_data("remotestorage")

    model.insert_many(data).on_conflict_ignore().execute()


def setup_server(db: "GidSqliteApswDatabase"):
    model = db.get_model("server")
    model.create_table()
    data = get_setup_data("server")

    for item in data:
        sub_model = db.get_model("remotestorage")
        item["remote_storage"] = sub_model.select().where(sub_model.name == item.pop("remote_storage_name"))

    model.insert_many(data).on_conflict_ignore().execute()


def setup_game_map(db: "GidSqliteApswDatabase"):
    model = db.get_model("gamemap")
    model.create_table()
    data = get_setup_data("gamemap")

    for item in data:
        if item.get("map_image_low_resolution", None):
            if MAP_IMAGES_DIR.joinpath(item["map_image_low_resolution"]).is_file():
                item["map_image_low_resolution"] = MAP_IMAGES_DIR.joinpath(item["map_image_low_resolution"])
            else:
                item["map_image_low_resolution"] = None

        if item.get("map_image_high_resolution", None):
            if MAP_IMAGES_DIR.joinpath(item["map_image_high_resolution"]).is_file():
                item["map_image_high_resolution"] = MAP_IMAGES_DIR.joinpath(item["map_image_high_resolution"])
            else:
                item["map_image_high_resolution"] = None

        if item.get("coordinates", None):
            coord_path = MAP_COORDS_DIR.joinpath(item["coordinates"])
            if coord_path.is_file():
                with coord_path.open("r", encoding='utf-8', errors='ignore') as f:
                    item["coordinates"] = json.load(f)
            else:
                item["coordinates"] = None

    model.insert_many(data).on_conflict_ignore().execute()


def setup_from_data(db: "GidSqliteApswDatabase"):
    with db:
        setup_tables(db)
        setup_loglevel(db)
        setup_recordorigin(db)
        setup_arma_author_prefix(db)
        setup_armafunction(db)
        setup_most_common_messages(db)
        setup_mod_set(db)
        setup_modlink(db)
        setup_remote_storage(db)
        setup_server(db)
        setup_game_map(db)
