"""
WiP.

Soon.
"""

# region [Imports]

# * Standard Library Imports ---------------------------------------------------------------------------->
from enum import Enum, auto, unique
from pathlib import Path
from typing import Union, Iterable
# * Qt Imports --------------------------------------------------------------------------------------->
from PySide6.QtCore import Qt, Signal, QObject, QSettings

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
    update_record_classes_started = Signal(bool)
    update_record_classes_finished = Signal(bool)
    update_info = Signal(int, str)
    update_increment = Signal(int)
    change_update_text = Signal(str)
    update_log_file_finished = Signal()

    def send_update_increment(self, amount: int = 1):
        self.update_increment.emit(amount)

    def send_update_started(self):
        self.update_started.emit(True)

    def send_update_finished(self):
        self.update_finished.emit(False)

    def send_update_record_classes_started(self):
        self.update_record_classes_started.emit(True)

    def send_update_record_classes_finished(self):
        self.update_record_classes_finished.emit(False)

    def send_update_info(self, amount, name):
        self.update_info.emit(amount, name)

    def send_log_file_finished(self):
        self.update_log_file_finished.emit()

    def __repr__(self) -> str:
        """
        Basic Repr
        !REPLACE!
        """
        return f'{self.__class__.__name__}'


def write_settings(settings_obj: QSettings, key_path: Union[str, Iterable], value: object) -> None:
    if isinstance(key_path, str):
        settings_obj.setValue(key_path, value)

    elif len(key_path) == 1:
        settings_obj.setValue(key_path[0], value)

    else:
        groups_opened = 0
        for sub_key in key_path[:-1]:
            settings_obj.beginGroup(sub_key)
            groups_opened += 1

        settings_obj.setValue(key_path[-1], value)

        for _ in range(groups_opened):
            settings_obj.endGroup()


def read_settings(settings_obj: QSettings, key_path: Union[str, Iterable], default: object = ...) -> object:
    default_param = tuple() if default is ... else (default,)

    if isinstance(key_path, str):
        return settings_obj.value(key_path, *default_param)

    elif len(key_path) == 1:
        return settings_obj.value(key_path[0], *default_param)

    else:
        groups_opened = 0
        for sub_key in key_path[:-1]:
            settings_obj.beginGroup(sub_key)
            groups_opened += 1

        _out = settings_obj.value(key_path[-1], *default_param)

        for _ in range(groups_opened):
            settings_obj.endGroup()

        return _out

# region[Main_Exec]


if __name__ == '__main__':
    pass
# endregion[Main_Exec]
