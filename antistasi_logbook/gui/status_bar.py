"""
WiP.

Soon.
"""

# region [Imports]

# * Standard Library Imports ---------------------------------------------------------------------------->
from typing import TYPE_CHECKING
from pathlib import Path
from datetime import datetime, timedelta
from threading import Thread

# * Third Party Imports --------------------------------------------------------------------------------->
from dateutil.tz import UTC

# * PyQt5 Imports --------------------------------------------------------------------------------------->
import PySide6
from PySide6.QtCore import Qt, Slot, Signal, QObject, QThread
from PySide6.QtWidgets import QLabel, QStatusBar, QProgressBar

# * Gid Imports ----------------------------------------------------------------------------------------->
from gidapptools import get_logger
from gidapptools.general_helper.conversion import seconds2human

if TYPE_CHECKING:
    # * Third Party Imports --------------------------------------------------------------------------------->
    from antistasi_logbook.gui.main_window import Backend, AntistasiLogbookMainWindow

# endregion[Imports]

# region [TODO]


# endregion [TODO]

# region [Logging]


# endregion[Logging]

# region [Constants]

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
        self.refresh_interval: int = 1000 * 10
        self.min_unit = "second"
        self.last_triggered: datetime = None
        self.label_text: str = None
        self.running_thread: QThread = None
        self.setup()

    def set_refresh_interval(self, new_interval: int) -> None:
        if new_interval == self.refresh_interval:
            return
        self.refresh_interval = new_interval
        self.start_timer()

    @property
    def last_update_finished_at(self) -> "datetime":
        return self.status_bar.backend.session_meta_data.get_absolute_last_update_finished_at()

    def setup(self) -> None:
        self.refresh_text()
        self.start_timer()

    def _thread_finished(self):
        self.running_thread = None
        self.setText(self.label_text)
        self.update()

    def _refresh_text_helper(self):
        log.debug("refreshing %s text", self)
        if self.last_update_finished_at is None:
            self.label_text = "Never Updated"
        else:
            delta = self._time_since_last_update_finished()
            delta_text = seconds2human(round(delta.total_seconds(), -1), min_unit=[v for k, v in self.min_unit_progression_table.items() if k <= delta][-1])
            self.label_text = f"Last update finished {delta_text} ago"

    def refresh_text(self) -> None:

        if self.running_thread is not None:
            return
        self.running_thread = FuncRunner(self, )
        self.running_thread.signaler.finished.connect(self._thread_finished)
        self.running_thread.start()

    def start_timer(self) -> None:
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

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(status_bar={self.status_bar!r})"

    def __str__(self) -> str:
        last_triggered = f"last_triggered={self.last_triggered.strftime('%Y-%m-%d %H:%M:%S UTC')!r}" if self.last_triggered is not None else f"last_triggered={self.last_triggered!r}"
        return f"{self.__class__.__name__}(interval={seconds2human(self.refresh_interval/1000)!r}, {last_triggered})"


class LogbookStatusBar(QStatusBar):

    def __init__(self, main_window: "AntistasiLogbookMainWindow") -> None:
        super().__init__(parent=main_window)
        self.main_window = main_window
        self.last_updated_label: LastUpdatedLabel = None
        self.update_running_label: QLabel = None
        self.update_progress: QProgressBar = None
        self.setup()

    @property
    def backend(self) -> "Backend":
        return self.main_window.backend

    def setup(self) -> None:
        self.setup_labels()
        self.update_progress = QProgressBar()
        self.insertWidget(2, self.update_progress, 2)
        self.update_progress.hide()

    def setup_labels(self) -> None:
        self.update_running_label = QLabel()
        self.update_running_label.setText("Updating...")
        self.update_running_label.hide()
        self.last_updated_label = LastUpdatedLabel(self)
        self.current_label = self.last_updated_label
        self.insertWidget(0, self.last_updated_label, 1)
        self.insertWidget(1, self.update_running_label, 1)

    def switch_labels(self, update_start: bool) -> None:
        if update_start is True:
            self.last_updated_label.hide()
            self.update_running_label.show()
            self.update_progress.show()
        else:
            self.update_running_label.hide()
            self.update_progress.hide()
            self.last_updated_label.show()

    @Slot(int, str)
    def start_progress_bar(self, max_amount: int, server_name: str):
        self.update_progress.reset()
        self.update_progress.setMaximum(max_amount)
        self.update_running_label.setText(f"Updating Server {server_name.title()}")

    def increment_progress_bar(self):
        self.update_progress.setValue(self.update_progress.value() + 1)


# region[Main_Exec]
if __name__ == '__main__':
    pass

# endregion[Main_Exec]
