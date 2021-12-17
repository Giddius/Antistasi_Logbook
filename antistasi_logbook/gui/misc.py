"""
WiP.

Soon.
"""

# region [Imports]

# * Standard Library Imports ---------------------------------------------------------------------------->
from pathlib import Path

# * PyQt5 Imports --------------------------------------------------------------------------------------->
from PySide6.QtCore import Signal, QObject

# endregion[Imports]

# region [TODO]


# endregion [TODO]

# region [Logging]


# endregion[Logging]

# region [Constants]

THIS_FILE_DIR = Path(__file__).parent.absolute()

# endregion[Constants]


class UpdaterSignaler(QObject):
    update_started = Signal(bool)
    update_finished = Signal(bool)
    update_info = Signal(int, str)
    update_increment = Signal()

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
