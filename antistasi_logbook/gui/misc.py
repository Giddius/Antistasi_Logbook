"""
WiP.

Soon.
"""

# region [Imports]

# * Standard Library Imports ---------------------------------------------------------------------------->
from enum import Enum, auto, unique
from pathlib import Path

# * Qt Imports --------------------------------------------------------------------------------------->
from PySide6.QtCore import Qt, Signal, QObject

# endregion[Imports]

# region [TODO]


# endregion [TODO]

# region [Logging]


# endregion[Logging]

# region [Constants]

THIS_FILE_DIR = Path(__file__).parent.absolute()

# endregion[Constants]


class UserRole(Enum):
    def _generate_next_value_(name, start, count, last_values):
        return Enum._generate_next_value_(name, int(Qt.UserRole), count, last_values)


@unique
class CustomRole(int, UserRole):
    STD_COPY_DATA = auto()
    RAW_DATA = auto()


class UpdaterSignaler(QObject):
    update_started = Signal(bool)
    update_finished = Signal(bool)
    update_info = Signal(int, str)
    update_increment = Signal()
    change_update_text = Signal(str)

    def send_update_increment(self):
        self.update_increment.emit()

    def send_update_started(self):
        self.update_started.emit(True)

    def send_update_finished(self):
        self.update_finished.emit(False)

    def send_update_info(self, amount, name):
        self.update_info.emit(amount, name)


# region[Main_Exec]

if __name__ == '__main__':
    pass
# endregion[Main_Exec]
