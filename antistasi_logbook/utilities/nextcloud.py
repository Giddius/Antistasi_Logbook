import os
from yarl import URL
from webdav4.client import Client as WebdavClient
from typing import TYPE_CHECKING, Union, Callable, Iterable, Optional, Mapping, Any, IO, TextIO, BinaryIO, Hashable, Generator, Literal, TypeVar, TypedDict, AnyStr
from httpx import Limits, Timeout
from time import sleep
from functools import cached_property, wraps
from contextlib import contextmanager, ContextDecorator
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


TIMEOUT_FUNCTION_TYPE = Callable[[Union[int, float]], Union[int, float]]


def unchanged_timeout(base_timeout: Union[int, float], attempt: int) -> Union[int, float]:
    return base_timeout


def increasing_timeout(base_timeout: Union[int, float], attempt: int) -> Union[int, float]:
    return base_timeout * (attempt + 1)


def exponential_timeout(base_timeout: Union[int, float], attempt: int) -> Union[int, float]:
    return base_timeout ** (attempt + 1)


class Retrier:
    default_timeout = 5.0

    def __init__(self,
                 errors: Iterable[type[BaseException]] = None,
                 allowed_attempts: int = None,
                 timeout: Union[int, float] = None,
                 timeout_function: TIMEOUT_FUNCTION_TYPE = None) -> None:
        self.errors = tuple(errors) or tuple()
        self.allowed_attempts = allowed_attempts or 3
        self.timeout = timeout or self.default_timeout
        self._timeout_function = timeout_function

    def __call__(self, func: Callable) -> Any:
        @wraps(func)
        def _helper_func(*args, attempt: int = 0, **kwargs) -> Any:
            try:
                return func(*args, **kwargs)
            except self.errors as error:
                if attempt > self.allowed_attempts:
                    raise

                seconds_to_sleep = unchanged_timeout(self.timeout, attempt) if self._timeout_function is None else self._timeout_function(self.timeout, attempt)
                msg = f"error: {error!r}, on attempt: {attempt!r}, sleeping {seconds_to_sleep!r} and retrying"
                print('!' * len(msg))
                print(msg)
                print('!' * len(msg))
                sleep(seconds_to_sleep)
                return _helper_func(*args, attempt=attempt + 1, **kwargs)

        return _helper_func
