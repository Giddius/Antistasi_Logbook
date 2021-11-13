import pytest

from antistasi_logbook.storage.database import get_database, GidSqliteQueueDatabase
from antistasi_logbook.updating.updater import get_updater, get_update_thread
from antistasi_logbook.utilities.misc import frozen_time_giver
from antistasi_logbook.storage.models.models import RemoteStorage
from pathlib import Path
from datetime import datetime, timedelta, timezone
from dateutil.tz import UTC
from time import sleep
from gidapptools.gid_config.interface import GidIniConfig
import shutil
from dotenv import load_dotenv
from pprint import pprint
from tempfile import TemporaryDirectory
THIS_FILE_DIR = Path(__file__).parent.absolute()


FROZEN_TIME = datetime(year=2021, month=11, day=9, hour=12, minute=0, second=0, microsecond=0, tzinfo=UTC)

from tests.data import THIS_FILE_DIR as DATA_DIR
load_dotenv(DATA_DIR.joinpath("nextcloud.env"))
BASE_CONFIG_FILE = DATA_DIR.joinpath("config", "general_config_for_tests.ini")
BASE_CONFIGSPEC_FILE = DATA_DIR.joinpath("config", "general_configspec_for_tests.json")


@pytest.fixture
def general_config():
    tmpdir = TemporaryDirectory()
    config_file_path = Path(tmpdir.name).joinpath(BASE_CONFIG_FILE.name)
    config_spec_file_path = Path(tmpdir.name).joinpath(BASE_CONFIGSPEC_FILE.name)
    shutil.copy(BASE_CONFIG_FILE, config_file_path)
    shutil.copy(BASE_CONFIGSPEC_FILE, config_spec_file_path)

    config = GidIniConfig(config_file=config_file_path, spec_file=config_spec_file_path)

    config.reload()

    yield config
    tmpdir.cleanup()


@pytest.fixture
def general_database(tmpdir, general_config: "GidIniConfig"):

    db = get_database(database_path=Path(tmpdir).joinpath('test_storage.db'), overwrite_db=True, config=general_config)
    web_dav_rem = RemoteStorage.get_by_id(1)
    web_dav_rem.set_login_and_password(login="does_not", password="matter", store_in_db=False)
    yield db
    db.shutdown()


@pytest.fixture
def general_updater(general_database: "GidSqliteQueueDatabase", general_config: "GidIniConfig"):

    updater = get_updater(database=general_database, use_fake_webdav_manager=True, get_now=frozen_time_giver(FROZEN_TIME), config=general_config)
    yield updater
