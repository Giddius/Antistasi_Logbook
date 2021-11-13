import pytest
from antistasi_logbook.updating.updater import get_updater, get_update_thread, Updater
from antistasi_logbook.utilities.misc import frozen_time_giver
from antistasi_logbook.storage.database import get_database, GidSqliteQueueDatabase
from antistasi_logbook.storage.models.models import LogFile, LogRecord, Server, AntstasiFunction
from antistasi_logbook.updating.remote_managers import FakeWebdavManager, WebdavManager
from typing import TYPE_CHECKING
from pprint import pprint

if TYPE_CHECKING:
    from gidapptools.gid_config.interface import GidIniConfig


def test_simple_update(general_config: "GidIniConfig", general_database: "GidSqliteQueueDatabase", general_updater: "Updater"):
    general_config.reload()
    general_config.set("webdav", "minimum_download_duration", 0)
    general_config.set("webdav", "delay_between_downloads", 0)
    general_config.set("updater", "max_update_time_frame", "3 days")

    assert general_updater.remote_manager_classes.get("WebdavManager") is not WebdavManager
    assert LogFile.select().count() == 0
    assert LogRecord.select().count() == 0
    assert LogFile.select().where(LogFile.unparsable == True).count() == 0
    for server in Server.select():
        general_updater(server)
    general_updater.close()
    general_database.optimize()
    general_database.vacuum()
    general_database.stop()
    general_database.start()
    amount_collected_log_files = LogFile.select().count()
    amount_collected_log_records = LogRecord.select().count()
    amount_unparsable_log_files = LogFile.select().where(LogFile.unparsable == True).count()

    assert amount_unparsable_log_files == 4
    assert amount_collected_log_files == 16
    assert amount_collected_log_records == 418454
    assert FakeWebdavManager.metrics.downloads_completed == 16
    assert FakeWebdavManager.metrics.downloads_requested == 16
    assert FakeWebdavManager.metrics.instances_created == 5
    assert FakeWebdavManager.metrics.get_files_info_sent == 194

    print(f"{general_database.path.stat().st_size=}")
    assert general_database.path.stat().st_size == pytest.approx(90000000, rel=1e-2)
