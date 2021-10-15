import os
from yarl import URL
from webdav4.client import Client as WebdavClient
from httpx import Limits, Timeout
USERNAME_KEY = 'NEXTCLOUD_USERNAME'
PASSWORD_KEY = 'NEXTCLOUD_PASSWORD'


def set_nextcloud_credentials(username: str, password: str) -> None:
    if os.getenv(USERNAME_KEY, None) is None:
        os.environ[USERNAME_KEY] = str(username)

    if os.getenv(PASSWORD_KEY, None) is None:
        os.environ[PASSWORD_KEY] = str(password)


def get_nextcloud_options():
    # _options = {"recv_speed": 50 * (1024**2)}
    _options = {}

    if os.getenv(USERNAME_KEY) is not None:
        _options['hostname'] = f"https://antistasi.de/dev_drive/remote.php/dav/files/{os.getenv(USERNAME_KEY)}/"
        _options['login'] = os.getenv(USERNAME_KEY)
        # _options["timeout"] = 600
    else:
        raise RuntimeError('no nextcloud Username set')

    if os.getenv(PASSWORD_KEY) is not None:
        _options['password'] = os.getenv(PASSWORD_KEY)
    else:
        raise RuntimeError('no nextcloud Password set')

    return _options


DEFAULT_BASE_FOLDER = URL('Antistasi_Community_Logs')

DEFAULT_SUB_FOLDER_NAME = 'Server'


DEFAULT_LOG_FOLDER_TEMPLATE = "Antistasi_Community_Logs/{server_folder_name}/Server"


def get_username() -> str:
    return os.getenv(USERNAME_KEY)


def get_webdav_client(username: str = None, password: str = None) -> WebdavClient:
    username = os.getenv(USERNAME_KEY) if username is None else username
    password = os.getenv(PASSWORD_KEY) if password is None else password

    base_url = f"https://antistasi.de/dev_drive/remote.php/dav/files/{username}/"

    return WebdavClient(base_url=base_url, auth=(username, password), retry=True, timeout=Timeout(20), limits=Limits(max_connections=10, max_keepalive_connections=5, keepalive_expiry=20))
