import pytest
from antistasi_logbook.updating.updater import Updater
from antistasi_logbook.utilities.path_utilities import RemotePath
from antistasi_logbook.utilities.misc import frozen_time_giver, Version
from antistasi_logbook.storage.database import GidSqliteApswDatabase
from antistasi_logbook.storage.models.models import LogFile, LogRecord, Server, AntstasiFunction, RecordClass, LogLevel
from antistasi_logbook.updating.remote_managers import FakeWebdavManager, WebdavManager
from gidapptools import get_logger
from gidapptools.general_helper.timing import time_execution
import antistasi_logbook
from typing import TYPE_CHECKING
from pprint import pprint
from pathlib import Path
from datetime import datetime
import json
from time import sleep
from playhouse.shortcuts import model_to_dict, dict_to_model
import random
import time_machine
if TYPE_CHECKING:
    from gidapptools.gid_config.interface import GidIniConfig
    from antistasi_logbook.backend import Backend


THIS_FILE_DIR = Path(__file__).parent.absolute()

import antistasi_logbook.storage.database
antistasi_logbook.setup()
log = get_logger(__name__)


def test_simple_update(general_backend: "Backend"):
    with time_machine.travel(FakeWebdavManager.for_datetime_of, tick=True):
        general_backend.config.reload()
        general_backend.config.set("webdav", "minimum_download_duration", 0)
        general_backend.config.set("webdav", "delay_between_downloads", 0)
        general_backend.config.set("updating", "max_update_time_frame", "3 days")
        general_backend.config.config.save()
        assert general_backend.remote_manager_registry.registered_managers.get("WebdavManager") is not WebdavManager
        assert LogFile.select().count() == 0
        assert LogRecord.select().count() == 0
        assert LogFile.select().where(LogFile.unparsable == True).count() == 0
        with time_execution("updating_log_files", condition=True, output=log.critical):
            general_backend.updater()
        with time_execution("querying data", condition=True, output=log.critical):
            amount_collected_log_files = LogFile.select().count()
            amount_collected_log_records = LogRecord.select().count()
            amount_unparsable_log_files = LogFile.select().where(LogFile.unparsable == True).count()

        stored_log_file_models_file = THIS_FILE_DIR.joinpath("random_log_files.json")

        # all_log_files = LogFile.select()
        # with stored_log_file_models_file.open('w', encoding='utf-8', errors='ignore') as f:
        #     only_fields = (LogFile.name, LogFile.modified_at, LogFile.last_parsed_line_number, LogFile.remote_path, LogFile.version,
        #                    LogFile.unparsable, LogFile.is_new_campaign, LogFile.size, LogFile.campaign_id, LogFile.last_parsed_datetime, LogFile.server)
        #     json.dump([model_to_dict(i, exclude=[LogFile.header_text,LogFile.startup_text]) for i in all_log_files], f, default=str, indent=4, sort_keys=False)

        stored_log_files = json.loads(stored_log_file_models_file.read_text(encoding='utf-8', errors='ignore'))

        for x in stored_log_files:
            name = x.get("name")
            modified_at = datetime.fromisoformat(x.get("modified_at"))
            last_parsed_line_number = x.get("last_parsed_line_number")
            remote_path = RemotePath(x.get("remote_path"))
            version = Version.from_string(x.get("version"))
            unparsable = x.get("unparsable")
            is_new_campaign = x.get("is_new_campaign")
            campaign_id = x.get("campaign_id")
            last_parsed_datetime = datetime.fromisoformat(x.get("last_parsed_datetime"))
            size = x.get("size")
            log_file_model = LogFile.get_or_none(name=name, remote_path=remote_path)
            assert log_file_model is not None
            assert log_file_model.modified_at == modified_at
            assert log_file_model.last_parsed_line_number == last_parsed_line_number
            assert log_file_model.version == version
            assert log_file_model.unparsable == unparsable
            assert log_file_model.is_new_campaign == is_new_campaign
            assert log_file_model.size == size
            assert log_file_model.last_parsed_datetime == last_parsed_datetime
            assert log_file_model.campaign_id == campaign_id

        all_log_files = LogFile.select()

        for log_file in all_log_files:
            if log_file.unparsable is True:
                assert log_file.last_parsed_line_number == 0
            if log_file.last_parsed_line_number == 0:
                assert log_file.unparsable is True

        stored_record_models_file = THIS_FILE_DIR.joinpath("random_records.json")

        fixed_check_log_records_file = THIS_FILE_DIR.joinpath("fixed_check_record.json")

        # random_records = random.choices(LogRecord.select(), k=amount_collected_log_records // 250)
        # with stored_record_models_file.open('w', encoding='utf-8', errors='ignore') as f:
        #     only_fields = (LogRecord.message, LogRecord.recorded_at, LogRecord.start, LogRecord.end, LogRecord.is_antistasi_record, LogRecord.record_class.name)
        #     json.dump([model_to_dict(i, exclude=[LogRecord.log_file]) for i in random_records], f, default=str, indent=4, sort_keys=False)

        stored_models = json.loads(stored_record_models_file.read_text(encoding='utf-8', errors='ignore')) + json.loads(fixed_check_log_records_file.read_text(encoding='utf-8', errors='ignore'))

        for i in stored_models:

            message = i.get('message')

            recorded_at = datetime.fromisoformat(i.get("recorded_at"))

            start = i.get("start")

            end = i.get("end")

            called_by = i.get("called_by")
            if called_by is not None:
                called_by = called_by.get("name")

            logged_from = i.get("logged_from")
            if logged_from is not None:
                logged_from = logged_from.get("name")

            record_class = i.get("record_class").get("name")

            log_level = i.get("log_level").get("name")

            is_antistasi_record = i.get("is_antistasi_record")

            marked = i.get("marked")

            log_record_model = LogRecord.get_or_none(message=message, recorded_at=recorded_at, start=start, end=end, is_antistasi_record=is_antistasi_record)
            if log_record_model is None:
                print(f"{message=}")
                print(f"{is_antistasi_record=}")
            else:

                assert marked == log_record_model.marked

                assert log_level == log_record_model.log_level.name

                # assert record_class == log_record_model.record_class.name

                if log_record_model.called_by is not None:
                    assert called_by == log_record_model.called_by.name
                else:
                    assert called_by == log_record_model.called_by

                if log_record_model.logged_from is not None:
                    assert logged_from == log_record_model.logged_from.name
                else:
                    assert logged_from == log_record_model.logged_from

                if log_record_model.is_antistasi_record is True:
                    assert log_record_model.logged_from is not None

        all_log_records = LogRecord.select()

        for log_record in all_log_records:
            if log_record.is_antistasi_record is True:
                assert log_record.logged_from is not None

        assert any('["UK3CB_BAF_FV432_Mk3_GPMG_Green_DPMT",4.46059]' in rec.message for rec in all_log_records)

        assert FakeWebdavManager.metrics.downloads_completed == 16
        assert FakeWebdavManager.metrics.downloads_requested == 16
        assert FakeWebdavManager.metrics.instances_created == 1
        assert FakeWebdavManager.metrics.get_files_info_sent == 194
        assert amount_collected_log_files == 16
        assert amount_collected_log_records == 418466
        assert amount_unparsable_log_files == 4

        log.info(f"{general_backend.database.session_meta_data.new_log_files=}")
        log.info(f"{general_backend.database.session_meta_data.updated_log_files=}")
        log.info(f"{general_backend.database.session_meta_data.added_log_records=}")
        general_backend.updater()
