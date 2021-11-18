import pytest
from antistasi_logbook.updating.updater import get_updater, get_update_thread, Updater
from antistasi_logbook.utilities.misc import frozen_time_giver
from antistasi_logbook.storage.database import get_database, GidSqliteQueueDatabase
from antistasi_logbook.storage.models.models import LogFile, LogRecord, Server, AntstasiFunction
from antistasi_logbook.updating.remote_managers import FakeWebdavManager, WebdavManager
from typing import TYPE_CHECKING
from pprint import pprint
from pathlib import Path
from datetime import datetime
import json
from time import sleep
from playhouse.shortcuts import model_to_dict, dict_to_model
import random
if TYPE_CHECKING:
    from gidapptools.gid_config.interface import GidIniConfig


THIS_FILE_DIR = Path(__file__).parent.absolute()


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
    general_updater.parser.record_process_worker.inserter.wait()
    for log_file in LogFile.select():
        log_file.set_last_parsed_line_number()
    general_updater.close()

    general_database.stop()

    general_database.start()

    amount_collected_log_files = LogFile.select().count()
    amount_collected_log_records = LogRecord.select().count()
    amount_unparsable_log_files = LogFile.select().where(LogFile.unparsable == True).count()
    amount_log_files_with_records = LogFile.select().where((LogFile.log_records != []) & (LogFile.log_records != None)).count()
    print(f"{amount_collected_log_files=}")
    print(f"{amount_collected_log_records=}")
    print(f"{amount_unparsable_log_files=}")
    print(f"{amount_log_files_with_records=}")

    stored_record_models_file = THIS_FILE_DIR.joinpath("random_records.json")

    random_records = random.choices(LogRecord.select(), k=amount_collected_log_records // 500)
    with stored_record_models_file.open('w', encoding='utf-8', errors='ignore') as f:
        only_fields = (LogRecord.message, LogRecord.recorded_at, LogRecord.start, LogRecord.end, LogRecord.is_antistasi_record)
        json.dump([model_to_dict(i, only=only_fields) for i in random_records], f, default=str, indent=4, sort_keys=False)

    stored_models = json.loads(stored_record_models_file.read_text(encoding='utf-8', errors='ignore'))

    for i in stored_models:

        message = i.get('message')
        recorded_at = datetime.fromisoformat(i.get("recorded_at"))
        start = i.get("start")
        end = i.get("end")

        is_antistasi_record = i.get("is_antistasi_record")
        model = LogRecord.get(message=message, recorded_at=recorded_at, start=start, end=end, is_antistasi_record=is_antistasi_record)
        assert model is not None
        try:
            print(model)
        except AttributeError:
            print(f"{model.is_antistasi_record=}")
            print(f"{model.message=}")
            print(f"{model.log_file=}")
            print(f"{model.log_file.server.name=}")
            print(f"{model.logged_from=}")
            raise
    assert FakeWebdavManager.metrics.downloads_completed == 16
    assert FakeWebdavManager.metrics.downloads_requested == 16
    assert FakeWebdavManager.metrics.instances_created == 5
    assert FakeWebdavManager.metrics.get_files_info_sent == 194
    assert amount_collected_log_files == 16
    assert amount_collected_log_records == 418466
    assert amount_unparsable_log_files == 4
