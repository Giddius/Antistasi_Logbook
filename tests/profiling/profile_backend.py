import antistasi_logbook
antistasi_logbook.setup()
from antistasi_logbook.backend import Backend, GidSqliteApswDatabase, get_meta_config
from antistasi_logbook.storage.models.models import RemoteStorage, LogFile, LogRecord
import os
from gidapptools.general_helper.timing import time_func, time_execution
from peewee import Query, Select
from pathlib import Path


@time_func(condition=True, also_pretty=True)
def main():
    config = get_meta_config().get_config('general')
    old_value = config.get("updating", "max_update_time_frame", default=None)
    config.set("updating", "max_update_time_frame", "10 days")
    db = GidSqliteApswDatabase(config=config)
    b = Backend(database=db, config=config)

    b.start_up(True)
    import dotenv
    dotenv.load_dotenv(r"D:\Dropbox\hobby\Modding\Programs\Github\My_Repos\Antistasi_Logbook\antistasi_logbook\nextcloud.env")
    with db:
        RemoteStorage.get(name="community_webdav").set_login_and_password(login=os.getenv("NEXTCLOUD_USERNAME"), password=os.getenv("NEXTCLOUD_PASSWORD"), store_in_db=False)
    b.updater()
    with db:
        print(f"{LogFile.select().count()=}")
        print(f"{LogRecord.select().count()=}")
    b.shutdown()
    config.set("updating", "max_update_time_frame", old_value)


if __name__ == '__main__':
    main()
