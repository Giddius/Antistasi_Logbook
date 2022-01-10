"""
WiP.

Soon.
"""

# region [Imports]

# * Standard Library Imports ---------------------------------------------------------------------------->
from gidapptools.general_helper.timing import get_dummy_profile_decorator_in_globals
from gidapptools import get_logger, get_meta_paths, get_meta_config
from antistasi_logbook.utilities.path_utilities import RemotePath, url_to_path
from antistasi_logbook.utilities.nextcloud import Retrier, exponential_timeout
from antistasi_logbook.updating.info_item import InfoItem
from antistasi_logbook.utilities.locks import MinDurationSemaphore
from antistasi_logbook.utilities.enums import RemoteItemType
from antistasi_logbook.errors import MissingLoginAndPasswordError
from webdav4.client import Client as WebdavClient
from dateutil.tz import UTC
from httpx import Limits
import httpx
import yarl
from threading import Lock, RLock
from datetime import datetime, timedelta
from zipfile import ZipFile
from pathlib import Path
from typing import TYPE_CHECKING, Iterable, Optional, Generator
from abc import ABC, abstractmethod
import os
import json
import shutil

# * Third Party Imports --------------------------------------------------------------------------------->
from antistasi_logbook import setup

setup()
# * Standard Library Imports ---------------------------------------------------------------------------->

# * Third Party Imports --------------------------------------------------------------------------------->

# * Gid Imports ----------------------------------------------------------------------------------------->

if TYPE_CHECKING:

    # * Third Party Imports --------------------------------------------------------------------------------->
    from antistasi_logbook.storage.models.models import LogFile, RemoteStorage

    # * Gid Imports ----------------------------------------------------------------------------------------->
    from gidapptools.meta_data.interface import MetaPaths
    from gidapptools.gid_config.meta_factory import GidIniConfig

# endregion[Imports]

# region [TODO]


# endregion [TODO]

# region [Logging]


# endregion[Logging]

# region [Constants]
get_dummy_profile_decorator_in_globals()
THIS_FILE_DIR = Path(__file__).parent.absolute()

META_PATHS: "MetaPaths" = get_meta_paths()
CONFIG: "GidIniConfig" = get_meta_config().get_config('general')
log = get_logger(__name__)
# endregion[Constants]


class RemoteManagerRegistry:
    cache_lock = RLock()

    def __init__(self) -> None:
        self.registered_managers: dict[str, type["AbstractRemoteStorageManager"]] = {}
        self.manager_cache: dict[str, "AbstractRemoteStorageManager"] = {}

    def register_manager_class(self, manager_class: type["AbstractRemoteStorageManager"], force: bool = False) -> "RemoteManagerRegistry":
        name = manager_class.___remote_manager_name___
        if name in self.registered_managers and force is False:
            return
        self.registered_managers[name] = manager_class
        return self

    def register_many_manager_classes(self, manager_classes: Iterable[type["AbstractRemoteStorageManager"]], force: bool = False) -> "RemoteManagerRegistry":
        for manager_class in manager_classes:
            self.register_manager_class(manager_class=manager_class, force=force)
        return self

    def get_remote_manager(self, remote_storage_item: "RemoteStorage") -> "AbstractRemoteStorageManager":
        with self.cache_lock:
            manager = self.manager_cache.get(remote_storage_item.name, None)
            if manager is None:
                manager_class = self.registered_managers[remote_storage_item.manager_type]
                manager = manager_class.from_remote_storage_item(remote_storage_item)
                self.manager_cache[remote_storage_item.name] = manager
        return manager

    def register_decorator(self, force: bool = False, condition: bool = True):
        def _inner(klass):
            if condition:
                self.register_manager_class(klass, force=force)
            return klass
        return _inner

    def close(self) -> "RemoteManagerRegistry":
        with self.cache_lock:
            for manager in self.manager_cache.values():
                manager.close()
            self.manager_cache.clear()
        return self


remote_manager_registry = RemoteManagerRegistry()


class AbstractRemoteStorageManager(ABC):
    config: "GidIniConfig" = CONFIG

    def __init__(self, base_url: yarl.URL = None, login: str = None, password: str = None) -> None:
        self.base_url = base_url
        self.login = login
        self.password = password

    @abstractmethod
    def get_files(self, folder_path: RemotePath) -> Generator:
        ...

    @abstractmethod
    def get_info(self, file_path: RemotePath) -> InfoItem:
        ...

    @abstractmethod
    def download_file(self, log_file: "LogFile") -> "LogFile":
        ...

    @classmethod
    def _validate_remote_storage_item(cls, remote_storage_item: "RemoteStorage") -> None:
        pass

    @classmethod
    def from_remote_storage_item(cls, remote_storage_item: "RemoteStorage") -> "AbstractRemoteStorageManager":
        cls._validate_remote_storage_item(remote_storage_item=remote_storage_item)
        return cls(base_url=remote_storage_item.base_url, login=remote_storage_item.get_login(), password=remote_storage_item.get_password())

    @classmethod
    @property
    def ___remote_manager_name___(cls) -> str:
        return cls.__name__

    def close(self) -> None:
        pass

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(base_url={self.base_url!r})"


@remote_manager_registry.register_decorator()
class LocalManager(AbstractRemoteStorageManager):
    config: "GidIniConfig" = CONFIG

    def __init__(self, base_url: yarl.URL, login: str, password: str) -> None:
        super().__init__(base_url=base_url, login=login, password=password)
        try:
            self.path = url_to_path(self.base_url)
        except AssertionError:
            self.path = Path.cwd()

    def get_files(self, folder_path: Path) -> Generator:
        return (self.get_info(file) for file in folder_path.iterdir() if file.is_file())

    def get_info(self, file_path: Path) -> InfoItem:
        stat = file_path.stat()
        info = {"size": stat.st_size,
                "created_at": stat.st_ctime,
                "modified_at": stat.st_mtime,
                "name": file_path.stem}
        return info

    def download_file(self, log_file: "LogFile") -> "LogFile":
        return log_file

    def close(self) -> None:
        pass


@remote_manager_registry.register_decorator()
class WebdavManager(AbstractRemoteStorageManager):
    config: "GidIniConfig" = CONFIG
    _extra_base_url_parts = ["dev_drive", "remote.php", "dav", "files"]

    download_semaphores: dict[yarl.URL, MinDurationSemaphore] = {}
    config_name = 'webdav'

    def __init__(self, base_url: yarl.URL, login: str, password: str) -> None:
        super().__init__(base_url=base_url, login=login, password=password)
        self.full_base_url = self._make_full_base_url()
        self._client: WebdavClient = None
        self.download_semaphore = self._get_download_semaphore()
        self.config.config.changed_signal.connect(self.reset_client)

    @classmethod
    def _validate_remote_storage_item(cls, remote_storage_item: "RemoteStorage") -> None:
        super()._validate_remote_storage_item(remote_storage_item)
        if any(x is None for x in [remote_storage_item.get_login(), remote_storage_item.get_password()]):
            raise MissingLoginAndPasswordError(remote_storage_item=remote_storage_item)

    def _get_download_semaphore(self) -> MinDurationSemaphore:
        download_semaphore = self.download_semaphores.get(self.full_base_url)
        if download_semaphore is None:
            delay = self.config.get(self.config_name, "delay_between_downloads", default=timedelta())
            minimum_duration = CONFIG.get(self.config_name, "minimum_download_duration", default=timedelta())
            download_semaphore = MinDurationSemaphore(self.max_connections, minimum_duration=minimum_duration, delay=delay)

            self.download_semaphores[self.full_base_url] = download_semaphore
        return download_semaphore

    def reset_client(self, config: "GidIniConfig") -> None:
        log.debug("client reset called")
        self._client = None

    @property
    def max_connections(self) -> Optional[int]:
        return CONFIG.get(self.config_name, "max_concurrent_connections", default=100)

    def _get_new_client(self) -> WebdavClient:
        return WebdavClient(base_url=str(self.full_base_url),
                            auth=(self.login, self.password),
                            retry=True,
                            timeout=httpx.Timeout(300, pool=None),
                            limits=Limits(max_connections=self.max_connections, max_keepalive_connections=self.max_connections // 2, keepalive_expiry=30))

    @property
    def client(self) -> WebdavClient:
        if any([self.login is None, self.password is None]):
            # Todo: Custom Error
            raise RuntimeError(f"login and password can not be None for {self.__class__.__name__!r}.")

        if self._client is None:
            self._client = self._get_new_client()
        return self._client

    def _make_full_base_url(self) -> yarl.URL:
        extra_parts = '/'.join([str(part) for part in self._extra_base_url_parts if part not in self.base_url.parts])
        base_url = self.base_url / extra_parts / self.login
        return base_url

    def get_files(self, folder_path: RemotePath) -> Generator:
        for item in self.client.ls(folder_path):
            info = InfoItem.from_webdav_info(item)

            if info.type is RemoteItemType.DIRECTORY:
                continue
            # dump_to_info_dump(info)
            yield info

    def get_info(self, file_path: RemotePath) -> InfoItem:
        info = self.client.info(file_path)
        _out = InfoItem.from_webdav_info(info)
        return _out

    @Retrier([httpx.ReadError, httpx.RemoteProtocolError], allowed_attempts=3, timeout=5, timeout_function=exponential_timeout)
    def download_file(self, log_file: "LogFile") -> "LogFile":
        local_path = log_file.local_path
        chunk_size = self.config.get("downloading", "chunk_size", default=None)

        log.info("downloading %s", log_file)
        result = self.client.http.get(str(log_file.download_url), auth=(self.login, self.password))
        with local_path.open("wb") as f:
            for chunk in result.iter_bytes(chunk_size=chunk_size):
                f.write(chunk)
        log_file.is_downloaded = True
        log.info("finished downloading %s", log_file)
        return local_path

    def close(self) -> None:
        if self._client is not None:
            log.debug("closing %r", self)
            self._client.http.close()
            self._client = None

    def restart_client(self) -> None:
        if self._client is not None:
            self.close()
            self._client = self._get_new_client()


class FakeManagerMetrics:

    def __init__(self) -> None:
        self.increment_lock = Lock()
        self.instances_created = 0
        self.get_files_requests = 0
        self.get_files_info_sent = 0
        self.get_info_requested = 0
        self.get_info_sent = 0
        self.downloads_requested = 0
        self.downloads_completed = 0

    def increment_instances_created(self, amount: int = 1) -> None:
        with self.increment_lock:
            self.instances_created += amount

    def increment_get_files_requests(self, amount: int = 1) -> None:
        with self.increment_lock:
            self.get_files_requests += amount

    def increment_get_files_info_sent(self, amount: int = 1) -> None:
        with self.increment_lock:
            self.get_files_info_sent += amount

    def increment_get_info_requested(self, amount: int = 1) -> None:
        with self.increment_lock:
            self.get_info_requested += amount

    def increment_get_info_sent(self, amount: int = 1) -> None:
        with self.increment_lock:
            self.get_info_sent += amount

    def increment_downloads_requested(self, amount: int = 1) -> None:
        with self.increment_lock:
            self.downloads_requested += amount

    def increment_downloads_completed(self, amount: int = 1) -> None:
        with self.increment_lock:
            self.downloads_completed += amount

    def reset(self) -> None:
        with self.increment_lock:
            self.instances_created = 0
            self.get_files_requests = 0
            self.get_files_info_sent = 0
            self.get_info_requested = 0
            self.get_info_sent = 0
            self.downloads_requested = 0
            self.downloads_completed = 0


@remote_manager_registry.register_decorator(force=True, condition=os.getenv("USE_FAKE_WEBDAV", "0") == "1")
class FakeWebdavManager(AbstractRemoteStorageManager):
    fake_files_folder: Path = None
    info_file: Path = None
    _info_data: dict[RemotePath, InfoItem] = None
    download_semaphores: dict[yarl.URL, MinDurationSemaphore] = {}
    config: "GidIniConfig" = CONFIG
    config_name = 'webdav'
    metrics = FakeManagerMetrics()
    for_datetime_of: datetime = datetime(year=2021, month=11, day=9, hour=12, minute=0, second=0, microsecond=0, tzinfo=UTC)

    def __init__(self, base_url: yarl.URL = None, login: str = None, password: str = None) -> None:
        self.metrics.increment_instances_created()
        super().__init__(base_url=base_url, login=login, password=password)
        self.full_base_url = self._make_full_base_url()
        self.download_semaphore = self._get_download_semaphore()
        self.is_unpacked = False
        if self.fake_files_folder.suffix in {".zip", ".7z"}:
            tgt = self.fake_files_folder.parent
            with ZipFile(self.fake_files_folder, 'r') as zippy:
                zippy.extractall(tgt)
                self.fake_files_folder = tgt.joinpath(self.fake_files_folder.stem)
                self.is_unpacked = True

    @property
    def max_connections(self) -> Optional[int]:
        return self.config.get(self.config_name, "max_concurrent_connections", default=100)

    def _get_download_semaphore(self) -> MinDurationSemaphore:
        download_semaphore = self.download_semaphores.get(self.full_base_url)
        if download_semaphore is None:
            delay = self.config.get(self.config_name, "delay_between_downloads", default=timedelta())
            minimum_duration = self.config.get(self.config_name, "minimum_download_duration", default=timedelta())

            download_semaphore = MinDurationSemaphore(self.max_connections, minimum_duration=minimum_duration, delay=delay)

            self.download_semaphores[self.full_base_url] = download_semaphore
        return download_semaphore

    def _make_full_base_url(self) -> yarl.URL:
        _extra_base_url_parts = WebdavManager._extra_base_url_parts.copy()
        extra_parts = '/'.join([str(part) for part in _extra_base_url_parts if part not in self.base_url.parts])
        base_url = self.base_url / extra_parts / self.login
        return base_url

    @classmethod
    def get_info_data(cls) -> dict[RemotePath, InfoItem]:
        raw_data = json.loads(cls.info_file.read_text(encoding='utf-8', errors='ignore'))
        _items: list[InfoItem.schema] = []
        for item in raw_data:
            _items.append(InfoItem.schema.load(item))
        _items = [InfoItem.from_schema_item(i) for i in _items]
        _out = {item.remote_path: item for item in _items}
        for item in _items:
            if item.remote_path.parent not in _out:
                _out[item.remote_path.parent] = []
            _out[item.remote_path.parent].append(item)
        return _out

    @classmethod
    @property
    def info_data(cls):
        if cls._info_data is None:
            cls._info_data = cls.get_info_data()
        return cls._info_data

    def get_info(self, file_path: RemotePath) -> InfoItem:
        self.metrics.increment_get_info_requested()
        _out = self.info_data.get(file_path)
        self.metrics.increment_get_info_sent()
        return _out

    def get_files(self, folder_path: RemotePath) -> Generator:
        self.metrics.increment_get_files_requests()
        for item in self.info_data.get(folder_path):
            yield item
            self.metrics.increment_get_files_info_sent()

    def download_file(self, log_file: "LogFile") -> "LogFile":
        self.metrics.increment_downloads_requested()
        local_path = log_file.local_path
        to_get_file = self.fake_files_folder.joinpath(log_file.server.name).joinpath(log_file.name).with_suffix('.txt')

        log.info(f"downloading %r", log_file)
        with local_path.open('wb') as tf:
            with to_get_file.open('rb') as sf:
                for chunk in sf:
                    tf.write(chunk)

        self.metrics.increment_downloads_completed()
        log_file.is_downloaded = True

        return local_path

    def close(self) -> None:
        if self.is_unpacked is True:
            shutil.rmtree(self.fake_files_folder)

    @classmethod
    @property
    def ___remote_manager_name___(cls) -> str:
        return WebdavManager.__name__

    def __repr__(self) -> str:
        return repr(self.__class__.__name__)

        # region[Main_Exec]


if __name__ == '__main__':
    pass

# endregion[Main_Exec]
