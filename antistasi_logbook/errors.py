
"""
WiP.

Soon.
"""

# region [Imports]

# * Standard Library Imports ---------------------------------------------------------------------------->
import logging
import sys
from typing import TYPE_CHECKING, Callable, Optional
from pathlib import Path
from datetime import timezone
import threading
if TYPE_CHECKING:
    # * Third Party Imports --------------------------------------------------------------------------------->
    from antistasi_logbook.storage.models.models import RemoteStorage
    from antistasi_logbook.utilities.date_time_utilities import DatetimeDuration

# endregion[Imports]

# region [TODO]


# endregion [TODO]

# region [Logging]


# endregion[Logging]

# region [Constants]

THIS_FILE_DIR = Path(__file__).parent.absolute()

# endregion[Constants]


class BaseAntistasiLogBookError(Exception):
    """
    Base Error for antistasi_serverlog_statistics package.
    """


class BaseRemoteStorageError(BaseAntistasiLogBookError):
    ...


class MissingLoginAndPasswordError(BaseRemoteStorageError):

    def __init__(self, remote_storage_item: "RemoteStorage") -> None:
        self.remote_storage_item = remote_storage_item
        self.remote_storage_name = self.remote_storage_item.name
        self.login = self.remote_storage_item.get_login()
        self.password = self.remote_storage_item.get_password()
        self.base_url = self.remote_storage_item.base_url
        self.msg = self._determine_message()

        super().__init__(self.msg)

    def _determine_message(self) -> str:
        if self.login is None and self.password is None:
            return f"Missing both 'login' and 'password' for 'RemoteStorage': {self.remote_storage_name!r} with base_url {str(self.base_url)!r}."
        if self.login is None:
            return f"Missing 'login' for 'RemoteStorage': {self.remote_storage_name!r} with base_url {str(self.base_url)!r}."
        if self.password is None:
            return f"Missing 'password' for 'RemoteStorage': {self.remote_storage_name!r} with base_url {str(self.base_url)!r}."


class DurationTimezoneError(BaseAntistasiLogBookError):
    def __init__(self, duration_item: "DatetimeDuration", start_tz: Optional[timezone], end_tz: Optional[timezone], message: str) -> None:
        self.duration_item = duration_item
        self.start_tz = start_tz
        self.end_tz = end_tz
        self.message = message + f", {start_tz=}, {end_tz=}."
        super().__init__(self.message)


EXCEPTION_HANDLER_TYPE = Callable[[BaseException], None]


original_threading_except_hook = threading.excepthook


class DefaultExceptionHandler:

    def handle_exception(self, exception: BaseException):
        raise exception

    def handle_thread_except_hook(self, args):
        original_threading_except_hook(args)

    def handle_except_hook(self, type_, value, traceback):
        sys.__excepthook__(type_=type_, value=value, traceback=traceback)


class _ExceptionHandlerManager:

    def __init__(self) -> None:
        self.default_exception_handler = DefaultExceptionHandler()
        self.exception_handler_registry: dict[type[BaseException]:Optional[EXCEPTION_HANDLER_TYPE]] = {}

    def register_handler(self, exception_class: type[BaseException], handler: EXCEPTION_HANDLER_TYPE) -> None:
        self.exception_handler_registry[exception_class] = handler

    def handle_exception(self, exception: BaseException) -> None:
        handler = self.exception_handler_registry.get(type(exception), self.default_exception_handler)
        handler.handle_exception(exception)

    def thread_except_hook(self, args):
        handler = self.exception_handler_registry.get(args.exc_type, self.default_exception_handler)

        handler.handle_thread_except_hook(args=args)

    def except_hook(self, type_, value, traceback):
        handler = self.exception_handler_registry.get(type_, self.default_exception_handler)
        handler.handle_except_hook(type_=type_, value=value, traceback=traceback)


ExceptionHandlerManager = _ExceptionHandlerManager()

threading.excepthook = ExceptionHandlerManager.thread_except_hook
sys.excepthook = ExceptionHandlerManager.except_hook
# region[Main_Exec]
if __name__ == '__main__':
    pass

# endregion[Main_Exec]
