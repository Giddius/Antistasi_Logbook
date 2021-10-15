import pytest
from antistasi_serverlog_statistic.updater import Updater, WebdavManager
from antistasi_serverlog_statistic.items.base_item import AbstractBaseItem
import inspect
from typing import TYPE_CHECKING
from pathlib import Path
from ..data import FAKE_LOG_FILES_PATHS
if TYPE_CHECKING:
    from antistasi_serverlog_statistic.storage.storage_db import StorageDB
    from antistasi_serverlog_statistic.updater import Updater

found_log_files_result_dict = {}
for k, v in FAKE_LOG_FILES_PATHS.items():
    found_log_files_result_dict[k] = []
    for sk, sv in v.items():
        found_log_files_result_dict[k].append(sv.stem)

found_log_files_parameter = {}
for name in ["Mainserver_1", "Mainserver_2", "Testserver_1", "Testserver_2", "Testserver_3", "Eventserver"]:
    found_log_files_parameter[name] = found_log_files_result_dict.get(name)

found_log_files_run_names = list(found_log_files_parameter)
found_log_files_args = [(k, v) for k, v in found_log_files_parameter.items()]


@pytest.mark.parametrize("in_server_name, expected_names", found_log_files_args, ids=found_log_files_run_names)
def test_found_log_files(initialized_updater: "Updater", in_server_name, expected_names):
    assert set(initialized_updater.webdav_manager.get_server_folder().get(in_server_name).log_files) == set(expected_names)
