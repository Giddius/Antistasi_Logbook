
"""
WiP.

Soon.
"""

# region [Imports]

# * Standard Library Imports ---------------------------------------------------------------------------->
import sys
import threading
from typing import TYPE_CHECKING, Callable, Optional
from pathlib import Path
from datetime import timezone
from traceback import format_tb, format_exception
# * Third Party Imports --------------------------------------------------------------------------------->
from webdav4.client import HTTPError, ResourceNotFound

# * Gid Imports ----------------------------------------------------------------------------------------->
from gidapptools import get_logger

# * Type-Checking Imports --------------------------------------------------------------------------------->
if TYPE_CHECKING:
    from antistasi_logbook.storage.models.models import RemoteStorage
    from antistasi_logbook.utilities.date_time_utilities import DatetimeDuration

# endregion[Imports]

# region [TODO]


# endregion [TODO]

# region [Logging]


# endregion[Logging]

# region [Constants]

THIS_FILE_DIR = Path(__file__).parent.absolute()
log = get_logger(__name__)
# endregion[Constants]


class BaseAntistasiLogbookError(Exception):
    """
    Base Error for antistasi_serverlog_statistics package.
    """


class BaseRemoteStorageError(BaseAntistasiLogbookError):
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


class DurationTimezoneError(BaseAntistasiLogbookError):
    def __init__(self, duration_item: "DatetimeDuration", start_tz: Optional[timezone], end_tz: Optional[timezone], message: str) -> None:
        self.duration_item = duration_item
        self.start_tz = start_tz
        self.end_tz = end_tz
        self.message = message + f", {start_tz=}, {end_tz=}."
        super().__init__(self.message)


class StatsError(BaseAntistasiLogbookError):
    ...


class InsufficientDataPointsError(StatsError):

    def __init__(self, amount_data_points: int, amount_required: int = 2) -> None:
        self.amount_data_points = amount_data_points
        self.amount_required = amount_required
        self.message = f"Not enough Data-Points, Data-Points required: >={self.amount_required}, Data-Points available: {self.amount_data_points}."
        super().__init__(self.message)


EXCEPTION_HANDLER_TYPE = Callable[[BaseException], None]


original_threading_except_hook = threading.excepthook


class DefaultExceptionHandler:

    def __init__(self, manager: "_ExceptionHandlerManager"):
        self.manager = manager

    def handle_exception(self, exception: BaseException):
        # log.error(exception, exc_info=True, stacklevel=3)
        raise exception

    def handle_thread_except_hook(self, args: threading.ExceptHookArgs):
        log.error(args.exc_value, exc_info=True, stacklevel=3)
        original_threading_except_hook(args)

    def handle_except_hook(self, type_, value, traceback):
        # log.error(value, exc_info=True, stacklevel=3)
        sys.__excepthook__(type_, value, traceback)


class MissingLoginAndPasswordHandler(DefaultExceptionHandler):

    def handle_thread_except_hook(self, args: threading.ExceptHookArgs):
        if self.manager.signaler:
            self.manager.signaler.show_error_signal.emit("Unable to login to Remote-Storage! Did you set the Credentials?", args.exc_value)
        self.manager.default_exception_handler.handle_thread_except_hook(args)


class ResourceNotFoundHandler(DefaultExceptionHandler):

    def handle_thread_except_hook(self, args: threading.ExceptHookArgs):
        if self.manager.signaler:
            self.manager.signaler.show_error_signal.emit(str(args.exc_value).rsplit(":", 1)[-1], args.exc_value)
        self.manager.default_exception_handler.handle_thread_except_hook(args)


class HTTPErrorHandler(DefaultExceptionHandler):

    def handle_thread_except_hook(self, args: threading.ExceptHookArgs):
        if self.manager.signaler:
            text = str(args.exc_value)
            if "Unauthorized" in str(args.exc_value):
                text = "Unable to login to Remote-Storage! Did you set the Credentials?"
            self.manager.signaler.show_error_signal.emit(text, args.exc_value)
        self.manager.default_exception_handler.handle_thread_except_hook(args)


class InsufficientDataPointsHandler(DefaultExceptionHandler):

    def handle_except_hook(self, type_, value, traceback):
        if self.manager.signaler:
            self.manager.signaler.show_error_signal.emit(value.message, value)
        self.manager.default_exception_handler.handle_except_hook(type_, value, traceback)


class TypeErrorHandler(DefaultExceptionHandler):

    def handle_except_hook(self, type_, value, traceback):

        if "self.parentChanged()" in '\n'.join(format_tb(traceback)):
            log.debug("suppressed stupid 'pyqtgraph'-error about 'parentChanged'")
            return
        return super().handle_except_hook(type_, value, traceback)

    def handle_thread_except_hook(self, args: threading.ExceptHookArgs):
        if "self.parentChanged()" in '\n'.join(format_tb(args.exc_traceback)):
            log.debug("suppressed stupid 'pyqtgraph'-error about 'parentChanged'")
            return
        return super().handle_thread_except_hook(args)


class _ExceptionHandlerManager:

    def __init__(self) -> None:
        self.signaler = None
        self.default_exception_handler = DefaultExceptionHandler(self)
        self.exception_handler_registry: dict[type[BaseException]:Optional[EXCEPTION_HANDLER_TYPE]] = {MissingLoginAndPasswordError: MissingLoginAndPasswordHandler(self),
                                                                                                       ResourceNotFound: ResourceNotFoundHandler(self),
                                                                                                       HTTPError: HTTPErrorHandler(self),
                                                                                                       InsufficientDataPointsError: InsufficientDataPointsHandler(self),
                                                                                                       TypeError: TypeErrorHandler(self)}

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
