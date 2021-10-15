import pytest
from unittest.mock import Mock
from antistasi_serverlog_statistic.storage.storage_db import StorageDB
from antistasi_serverlog_statistic.storage import THIS_FILE_DIR as STORAGE_MODULE_DIR
from antistasi_serverlog_statistic.items.base_item import AbstractBaseItem
import inspect
from antistasi_serverlog_statistic.updater import Updater, WebdavManager
from pathlib import Path
import shutil
from typing import Any, Union
from antistasi_serverlog_statistic.updater import Updater
import json
from datetime import datetime, timezone, timedelta
from ..data import FAKE_INFO_DATA, FAKE_LS_DATA, FAKE_LOG_FILES_PATHS
THIS_FILE_DIR = Path(__file__).parent.absolute()


class FAKE_HTTP_CLIENT:

    def close(self):
        pass


class FakeWebdavClient:
    fake_ls_data = FAKE_LS_DATA
    fake_info_data = FAKE_INFO_DATA
    fake_log_files_paths = FAKE_LOG_FILES_PATHS
    http = FAKE_HTTP_CLIENT()

    def ls(self, path: str, detail: bool = True, allow_listing_resource: bool = True) -> list[Union[str, dict[str, Any]]]:
        data = self.fake_ls_data.copy().get(path, [])
        all_data = []
        for item in data:
            all_data.append(item)
        return all_data

    def info(self, path: str) -> dict[str, Any]:
        data = self.fake_info_data.copy().get(path, {})
        return data

    def download_file(self,
                      from_path,
                      to_path,
                      chunk_size: int = None,
                      callback=None) -> None:
        server_name = from_path.parent.parent.name
        file_name = from_path.name
        fake_path = self.fake_log_files_paths[server_name][file_name]
        shutil.copyfile(fake_path, to_path)


@pytest.fixture(scope="session")
def fake_web_dav_client():
    fake_client = FakeWebdavClient()
    yield fake_client


@pytest.fixture(scope="session")
def temp_database():
    db_path = THIS_FILE_DIR.joinpath('temp_storage.db')
    script_folder_path = STORAGE_MODULE_DIR.joinpath("sql_phrases")
    db = StorageDB(db_path=db_path, script_folder_path=script_folder_path)
    yield db
    db_path.unlink(missing_ok=True)


@pytest.fixture(scope="session")
def all_fake_log_file_paths():
    yield FAKE_LOG_FILES_PATHS.copy()


@pytest.fixture(scope="session")
def initialized_updater(temp_database, fake_web_dav_client):
    for item in AbstractBaseItem.__subclasses__():
        if inspect.isabstract(item) is False:
            StorageDB.register_item(item)
    webdav_manager = WebdavManager(log_folder_remote_path="Antistasi_Community_Logs", database=temp_database, client=fake_web_dav_client)
    updater = Updater(30, webdav_manager=webdav_manager, database=temp_database)
    updater._update()
    yield updater
