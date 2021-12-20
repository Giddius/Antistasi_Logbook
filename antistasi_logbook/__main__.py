"""
WiP.

Soon.
"""

# region [Imports]

# * Third Party Imports --------------------------------------------------------------------------------->
from antistasi_logbook import setup

setup()

# * Standard Library Imports ---------------------------------------------------------------------------->
import os
from typing import TYPE_CHECKING
from pathlib import Path

# * Third Party Imports --------------------------------------------------------------------------------->
import click
from dotenv import load_dotenv
from antistasi_logbook.backend import Backend, GidSqliteApswDatabase
from antistasi_logbook.gui.main_window import start_gui
from antistasi_logbook.storage.models.models import RemoteStorage
from antistasi_logbook.storage.models.models import database_proxy

# * Gid Imports ----------------------------------------------------------------------------------------->
from gidapptools import get_logger
from gidapptools.meta_data import get_meta_info, get_meta_paths
from gidapptools.meta_data.interface import get_meta_config

if TYPE_CHECKING:
    # * Gid Imports ----------------------------------------------------------------------------------------->
    from gidapptools.gid_config.interface import GidIniConfig

# endregion[Imports]


# region [TODO]


# endregion [TODO]

# region [Logging]


# endregion[Logging]

# region [Constants]


THIS_FILE_DIR = Path(__file__).parent.absolute()

META_PATHS = get_meta_paths()
META_INFO = get_meta_info()
CONFIG: "GidIniConfig" = get_meta_config().get_config('general')
CONFIG.config.load()
log = get_logger(__name__)
# endregion[Constants]


@click.group(name='antistasi-logbook')
def cli():
    ...


settings_names = []
for section, values in CONFIG.as_dict().items():
    for key, _value in values.items():
        settings_names.append(f"{section}.{key}")


@cli.command(name="settings", help="change the Application settings without the GUI.")
@click.argument("setting_name", type=click.Choice(settings_names))
@click.argument("value")
def settings(setting_name, value):
    section, key = setting_name.split('.')
    CONFIG.set(section_name=section, entry_key=key, entry_value=value)
    current_value = CONFIG.get(section, key)
    click.echo(f"{setting_name} is set to {str(current_value)!r}")


@cli.command(help="Runs a single update of all enabled Server without starting the GUI.")
@click.option('--login', '-l', default=None)
@click.option('--password', '-p', default=None)
def update(login, password):

    def set_auth():
        if login is not None and password is not None:
            item: RemoteStorage = RemoteStorage.get(name='community_webdav')
            item.set_login_and_password(login=login, password=password, store_in_db=False)

    database = GidSqliteApswDatabase(config=CONFIG)

    backend = Backend(database=database, config=CONFIG, database_proxy=database_proxy)
    set_auth()
    try:
        backend.updater()
    finally:
        amount_updated = database.session_meta_data.new_log_files + database.session_meta_data.updated_log_files
        click.echo(f"{amount_updated} log files were updated.")
        backend.shutdown()


def debug_update(login, password):

    def set_auth():
        if login is not None and password is not None:
            item: RemoteStorage = RemoteStorage.get(name='community_webdav')
            item.set_login_and_password(login=login, password=password, store_in_db=False)

    database = GidSqliteApswDatabase(config=CONFIG)

    backend = Backend(database=database, config=CONFIG, database_proxy=database_proxy)
    backend.start_up(overwrite=True)
    set_auth()
    try:
        backend.updater()
    finally:
        amount_updated = database.session_meta_data.new_log_files + database.session_meta_data.updated_log_files
        log.info(f"{amount_updated} log files were updated.")
        backend.shutdown()


@cli.command(help="starts the GUI")
@click.option('--login', '-l', default=None)
@click.option('--password', '-p', default=None)
def gui(login, password):
    start_gui(login, password)


# region[Main_Exec]
if __name__ == '__main__':
    pass
# endregion[Main_Exec]
