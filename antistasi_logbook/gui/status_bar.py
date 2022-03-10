"""
WiP.

Soon.
"""

# region [Imports]

# * Standard Library Imports ---------------------------------------------------------------------------->
from time import sleep
from typing import TYPE_CHECKING
from pathlib import Path
from datetime import datetime, timedelta
from threading import Thread

# * Qt Imports --------------------------------------------------------------------------------------->
import PySide6
from PySide6 import QtCore
from PySide6.QtCore import Qt, Slot, Signal, QObject
from PySide6.QtWidgets import QLabel, QStatusBar, QApplication, QProgressBar

# * Third Party Imports --------------------------------------------------------------------------------->
from dateutil.tz import UTC

# * Gid Imports ----------------------------------------------------------------------------------------->
from gidapptools import get_logger
from gidapptools.general_helper.conversion import seconds2human

# * Type-Checking Imports --------------------------------------------------------------------------------->
if TYPE_CHECKING:
    from antistasi_logbook.gui.application import AntistasiLogbookApplication
    from antistasi_logbook.gui.main_window import Backend, AntistasiLogbookMainWindow

# endregion[Imports]

# region [TODO]


# endregion [TODO]

# region [Logging]


# endregion[Logging]

# region [Constants]
from gidapptools.general_helper.timing import get_dummy_profile_decorator_in_globals

THIS_FILE_DIR = Path(__file__).parent.absolute()
log = get_logger(__name__)
# endregion[Constants]


class StupidSignaler(QObject):
    finished = Signal()

    def emit_finished(self):
        self.finished.emit()


class FuncRunner(Thread):

    def __init__(self, label: "LastUpdatedLabel",) -> None:
        super().__init__()
        self.signaler = StupidSignaler()
        self.label = label

    def run(self) -> None:
        self.label._refresh_text_helper()
        self.signaler.emit_finished()


class ErrorMessageClearer(Thread):

    def __init__(self, status_bar, clear_timeout) -> None:
        super().__init__()
        self.status_bar = status_bar
        self.clear_timeout = clear_timeout

    def run(self):
        sleep(self.clear_timeout)
        self.status_bar.clear_error()


class LastUpdatedLabel(QLabel):
    min_unit_progression_table = {timedelta(seconds=0): "second",
                                  timedelta(minutes=5): "minute",
                                  timedelta(hours=5): "hour",
                                  timedelta(days=5): "day",
                                  timedelta(weeks=5): "week"}

    def __init__(self, status_bar: "LogbookStatusBar", parent=None) -> None:
        super().__init__(parent=parent)
        self.status_bar = status_bar
        self.timer_id: int = None
        self.refresh_interval: int = 1000 * 1
        self.min_unit = "second"
        self.last_triggered: datetime = None
        self.label_text: str = None
        self.is_running = False
        self.start()

    def set_refresh_interval(self, new_interval: int) -> None:
        if new_interval == self.refresh_interval:
            return
        self.refresh_interval = new_interval
        self.start_timer()

    @property
    def last_update_finished_at(self) -> "datetime":
        return self.status_bar.backend.session_meta_data.get_absolute_last_update_finished_at()

    def start(self) -> None:
        if self.is_running is False:
            self.refresh_text()
            self.start_timer()
            self.is_running = True

    def _thread_finished(self):

        self.setText(self.label_text)
        self.update()

    def _refresh_text_helper(self):
        if self.last_update_finished_at is None:
            self.label_text = "Never Updated"
        else:
            delta = self._time_since_last_update_finished()
            try:
                min_unit = [v for k, v in self.min_unit_progression_table.items() if k <= delta][-1]
                delta_text = seconds2human(delta.total_seconds(), min_unit=min_unit)
                self.label_text = f"Last update finished {delta_text} ago"
            except IndexError:
                log.error("indexerror with self.last_update_finished_at = %r, now = %r, now-self.last_update_finished_at = %r", self.last_update_finished_at.isoformat(sep=" "), datetime.now(tz=UTC).isoformat(sep=" "), delta)
                self.label_text = "Never Updated"

    def refresh_text(self) -> None:
        self._refresh_text_helper()
        self._thread_finished()
        # if self.running_thread is not None:
        #     return
        # self.running_thread = FuncRunner(self)
        # self.running_thread.signaler.finished.connect(self._thread_finished)
        # self.running_thread.start()

    def start_timer(self) -> None:
        log.debug("Starting timer for %r", self)
        if self.timer_id is not None:
            self.killTimer(self.timer_id)
        self.timer_id = self.startTimer(self.refresh_interval, Qt.VeryCoarseTimer)

    def _time_since_last_update_finished(self) -> timedelta:
        now = datetime.now(tz=UTC)
        return now - self.last_update_finished_at

    def timerEvent(self, event: PySide6.QtCore.QTimerEvent) -> None:
        if event.timerId() == self.timer_id:
            self.last_triggered = datetime.now(tz=UTC)
            self.refresh_text()

    def shutdown(self):
        if self.timer_id is not None:
            self.killTimer(self.timer_id)
            self.timer_id = None
        self.is_running = False
        self.status_bar.backend.database.close()

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(status_bar={self.status_bar!r})"

    def __str__(self) -> str:
        last_triggered = f"last_triggered={self.last_triggered.strftime('%Y-%m-%d %H:%M:%S UTC')!r}" if self.last_triggered is not None else f"last_triggered={self.last_triggered!r}"
        return f"{self.__class__.__name__}(interval={self.refresh_interval/1000}s, {last_triggered})"


class LogbookStatusBar(QStatusBar):
    change_status_bar_color = Signal(bool)
    request_clear_error = Signal()

    def __init__(self, main_window: "AntistasiLogbookMainWindow") -> None:
        super().__init__(parent=main_window)
        self.main_window = main_window
        self.last_updated_label: LastUpdatedLabel = None
        self.update_running_label: QLabel = None
        self.update_progress: QProgressBar = None
        self.timer: int = None

    @property
    def app(self) -> "AntistasiLogbookApplication":
        return QApplication.instance()

    @property
    def backend(self) -> "Backend":
        return self.main_window.backend

    def setup(self) -> None:

        self.setup_labels()
        self.update_progress = QProgressBar()
        self.insertWidget(2, self.update_progress, 2)
        self.update_progress.hide()
        self.change_status_bar_color.connect(self.set_showing_error)
        self.request_clear_error.connect(self.clearMessage)

    def setup_labels(self) -> None:
        if self.last_updated_label is None:
            self.last_updated_label = LastUpdatedLabel(self)
            self.insertWidget(0, self.last_updated_label, 1)
        if self.update_running_label is None:
            self.update_running_label = QLabel()
            self.update_running_label.setText("Updating...")
            self.update_running_label.hide()
            self.insertWidget(1, self.update_running_label, 1)

        # self.last_updated_label.start()
        self.current_label = self.last_updated_label

    def switch_labels(self, update_start: bool) -> None:
        if update_start is True:
            self.last_updated_label.hide()
            self.last_updated_label.shutdown()
            self.update_running_label.show()
            self.update_progress.show()
        else:
            self.update_running_label.hide()
            self.update_progress.hide()
            self.last_updated_label.start()
            self.last_updated_label.show()

    @Slot(int, str)
    def start_progress_bar(self, max_amount: int, server_name: str):
        self.update_progress.reset()
        self.update_progress.setMaximum(max_amount)
        self.update_running_label.setText(f"Updating Server {server_name.title()}")

    def set_showing_error(self, value: bool = False):

        self.setProperty("showing_error", value)
        self.style().unpolish(self)

        self.style().polish(self)

    def clear_error(self, future):
        self.change_status_bar_color.emit(False)
        self.request_clear_error.emit()

    @Slot(str, BaseException)
    def show_error(self, message: str, exception: BaseException):
        self.set_showing_error(True)
        timeout = 10 * 1000
        self.showMessage(message, timeout)
        t = self.app.gui_thread_pool.submit(sleep, timeout / 1000)
        t.add_done_callback(self.clear_error)

    def set_update_text(self, text: str):
        if text:
            self.showMessage(text)
        else:
            self.clearMessage()

    def increment_progress_bar(self):
        self.update_progress.setValue(self.update_progress.value() + 1)

    def shutdown(self):
        self.last_updated_label.shutdown()
        self.backend.database.close()

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(main_window={self.main_window!r})"


# region[Main_Exec]
if __name__ == '__main__':
    pass

# endregion[Main_Exec]
