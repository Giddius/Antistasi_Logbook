import pytest

from antistasi_logbook.storage.database import GidSqliteQueueDatabase, GidSqliteApswDatabase, GidSqliteDatabase
from antistasi_logbook.backend import Backend
from antistasi_logbook.storage.models.models import RemoteStorage, database as database_proxy
from pathlib import Path
from datetime import datetime, timedelta, timezone
from dateutil.tz import UTC
from time import sleep
from gidapptools.gid_config.interface import GidIniConfig
import shutil
from dotenv import load_dotenv
from pprint import pprint
from tempfile import TemporaryDirectory
from antistasi_logbook.updating.remote_managers import FakeWebdavManager
THIS_FILE_DIR = Path(__file__).parent.absolute()


FROZEN_TIME = datetime(year=2021, month=11, day=9, hour=12, minute=0, second=0, microsecond=0, tzinfo=UTC)

from tests.data import THIS_FILE_DIR as DATA_DIR
load_dotenv(DATA_DIR.joinpath("nextcloud.env"))
BASE_CONFIG_FILE = DATA_DIR.joinpath("config", "general_config_for_tests.ini")
BASE_CONFIGSPEC_FILE = DATA_DIR.joinpath("config", "general_configspec_for_tests.json")


@pytest.fixture
def general_config(tmpdir):

    config_file_path = Path(tmpdir).joinpath(BASE_CONFIG_FILE.name)
    config_spec_file_path = Path(tmpdir).joinpath(BASE_CONFIGSPEC_FILE.name)
    shutil.copy(BASE_CONFIG_FILE, config_file_path)
    shutil.copy(BASE_CONFIGSPEC_FILE, config_spec_file_path)

    config = GidIniConfig(config_file=config_file_path, spec_file=config_spec_file_path)

    config.reload()

    yield config


@pytest.fixture
def general_database(tmpdir, general_config: "GidIniConfig"):

    db = GidSqliteApswDatabase(database_path=Path(tmpdir).joinpath('test_storage.db'), config=general_config)

    yield db


@pytest.fixture
def general_backend(general_database: "GidSqliteDatabase", general_config: "GidIniConfig"):
    backend = Backend(database=general_database, config=general_config, database_proxy=database_proxy)

    FakeWebdavManager.fake_files_folder = DATA_DIR.joinpath("fake_log_files.zip")
    FakeWebdavManager.info_file = DATA_DIR.joinpath("fake_info_data.json")
    FakeWebdavManager.config = general_config
    backend.remote_manager_registry.register_manager_class(FakeWebdavManager, force=True)
    backend.start_up(overwrite=False)
    web_dav_rem = RemoteStorage.get_by_id(1)
    web_dav_rem.set_login_and_password(login="does_not", password="matter", store_in_db=False)
    yield backend
    backend.shutdown()
