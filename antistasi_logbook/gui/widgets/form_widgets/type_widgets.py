"""
WiP.

Soon.
"""

# region [Imports]

# * Standard Library Imports ---------------------------------------------------------------------------->
import re
from typing import Any, Union, Iterable, Optional, Protocol, runtime_checkable
from pathlib import Path
from datetime import timedelta

# * Third Party Imports --------------------------------------------------------------------------------->
from antistasi_logbook.gui.resources.antistasi_logbook_resources_accessor import AllResourceItems

# * PyQt5 Imports --------------------------------------------------------------------------------------->
import PySide6
from PySide6.QtGui import QFont
from PySide6.QtCore import Qt, Slot, Signal
from PySide6.QtWidgets import (QWidget, QSpinBox, QComboBox, QLineEdit, QTextEdit, QFileDialog, QGridLayout, QHBoxLayout,
                               QListWidget, QPushButton, QSizePolicy, QSpacerItem, QButtonGroup, QRadioButton, QDoubleSpinBox)

# * Gid Imports ----------------------------------------------------------------------------------------->
from gidapptools import get_logger
from gidapptools.general_helper.conversion import FILE_SIZE_REFERENCE, TimeUnit, TimeUnits, bytes2human, human2bytes, seconds2human
from gidapptools.general_helper.typing_helper import implements_protocol
from gidapptools.gid_config.conversion.extra_base_typus import NonTypeBaseTypus

# region [TODO]


# endregion [TODO]

# region [Logging]


# endregion[Logging]

# region [Constants]

THIS_FILE_DIR = Path(__file__).parent.absolute()
log = get_logger(__name__)
# endregion[Constants]


@runtime_checkable
class TypeWidgetProtocol(Protocol):

    def value_is_changed(self) -> bool:
        ...

    def set_value(self, value: Any, is_start: bool = False) -> None:
        ...

    def get_value(self) -> Any:
        ...

    def set_alignment(self, alignment: Qt.Alignment):
        ...


ALL_VALUE_FIELDS: dict[type, type[TypeWidgetProtocol]] = {}


def _add_value_field(value_field: type[TypeWidgetProtocol]):
    ALL_VALUE_FIELDS[value_field.___for_type___] = value_field


@implements_protocol(TypeWidgetProtocol)
class BoolValueField(QWidget):
    ___for_type___ = bool

    def __init__(self, true_text: str = "Yes", false_text: str = "No", parent: Optional[PySide6.QtWidgets.QWidget] = None) -> None:
        super().__init__(parent=parent)
        self.start_value: bool = None
        self.true_text = true_text
        self.false_text = false_text
        self.true_button: QRadioButton = None
        self.false_button: QRadioButton = None
        self.button_group: QButtonGroup = None
        self.setLayout(QHBoxLayout(self))
        self.setup_buttons()

    def setup_buttons(self):
        self.layout.addItem(QSpacerItem(100, 20, QSizePolicy.Expanding, QSizePolicy.Fixed))
        self.button_group = QButtonGroup(self)
        self.true_button = QRadioButton(self.true_text, self)
        self.false_button = QRadioButton(self.false_text, self)
        self.button_group.addButton(self.true_button)
        self.button_group.addButton(self.false_button)
        self.true_button.setChecked(True)
        self.false_button.setChecked(False)
        self.layout.addWidget(self.true_button)
        self.layout.addWidget(self.false_button)

    def value_is_changed(self) -> bool:
        return self.get_value() is not self.start_value

    def set_value(self, value: bool, is_start: bool = False):
        if value is True:
            self.true_button.setChecked(True)
        else:
            self.false_button.setChecked(True)
        if is_start:
            self.start_value = value

    def get_value(self) -> bool:
        return self.true_button.isChecked()

    @property
    def layout(self):
        return super().layout()

    def set_alignment(self, alignment: Qt.Alignment):
        self.layout.setAlignment(alignment)


_add_value_field(BoolValueField)


class TimeSpinBox(QSpinBox):
    increase_next = Signal()

    def __init__(self, unit: TimeUnit, parent: Optional[PySide6.QtWidgets.QWidget] = None) -> None:
        super().__init__(parent=parent)
        self.unit = unit
        self.setSuffix(f" {self.unit.plural.title()}")
        self.is_plural = True
        self.valueChanged.connect(self.on_changed)

    @Slot(int)
    def on_changed(self, new_value: int):
        if self.value() != 1 and self.is_plural is False:
            self.setSuffix(f" {self.unit.plural.title()}")
            self.is_plural = True
        elif self.value() == 1 and self.is_plural is True:
            self.setSuffix(f" {self.unit.name.title()} ")
            self.is_plural = False

        if new_value == self.maximum():
            self.setValue(0)
            self.increase_next.emit()

    @Slot()
    def on_increase_next_received(self):
        self.setValue(self.value() + 1)

    def setAlignment(self, value):
        self.layout.setAlignment(value)


@implements_protocol(TypeWidgetProtocol)
class TimeDeltaValueField(QWidget):
    ___for_type___ = timedelta
    all_units = tuple(unit for unit in TimeUnits(False) if unit.factor >= TimeUnits(False)["second"].factor)

    def __init__(self, parent: Optional[PySide6.QtWidgets.QWidget] = None) -> None:
        super().__init__(parent=parent)
        self.start_value: timedelta = None
        self.setLayout(QHBoxLayout(self))
        font = QFont()
        font.setFamily("Cascadia Mono")
        self.setFont(font)
        self.inputs: dict[TimeUnit, QSpinBox] = {}
        self.setup_inputs()

    def setAlignment(self, value):
        self.layout.setAlignment(value)

    def setup_inputs(self):
        self.layout.addItem(QSpacerItem(100, 20, QSizePolicy.Expanding, QSizePolicy.Fixed))
        for idx, unit in enumerate(self.all_units):
            item = TimeSpinBox(unit, self)
            if idx == 0:
                item.setMaximum(1000000)
            else:
                next_item = self.all_units[idx - 1]

                item.setMaximum(((next_item.factor - unit.factor) // unit.factor) + 1)
                item.increase_next.connect(self.inputs[next_item].on_increase_next_received)
            self.layout.addWidget(item)
            self.inputs[unit] = item

    def value_is_changed(self) -> bool:
        return self.get_value() != self.start_value

    def set_value(self, value: timedelta, is_start: bool = False):
        parts = seconds2human(value, as_list_result=True)
        for _unit, _value in parts.items():
            self.inputs[_unit].setValue(_value)
        if is_start:
            self.start_value = value

    def get_value(self) -> timedelta:
        seconds = 0
        for unit, spinbox in self.inputs.items():
            seconds += spinbox.value() * unit.factor
        return timedelta(seconds=seconds)

    @property
    def layout(self):
        return super().layout()

    def set_alignment(self, alignment: Qt.Alignment):
        self.layout.setAlignment(alignment)

    @property
    def layout(self):
        return super().layout()


_add_value_field(TimeDeltaValueField)


@implements_protocol(TypeWidgetProtocol)
class FileSizeValueField(QWidget):
    ___for_type___ = NonTypeBaseTypus.FILE_SIZE
    all_symbols = tuple(["b"] + list(FILE_SIZE_REFERENCE.symbols))
    extraction_regex = re.compile(r"(?P<number_value>[\d\.\,]+)\s*(?P<unit_value>" + r'|'.join(all_symbols) + r")", re.IGNORECASE)

    def __init__(self, parent: Optional[PySide6.QtWidgets.QWidget] = None) -> None:
        super().__init__(parent=parent)
        self.start_value: int = None
        self.setLayout(QHBoxLayout(self))
        self.number_part = QDoubleSpinBox(self)
        self.number_part.setKeyboardTracking(False)
        self.number_part.setMaximum(10000000)
        self.number_part.setMinimum(0)
        self.number_part.setDecimals(1)
        self.layout.addItem(QSpacerItem(100, 20, QSizePolicy.Expanding, QSizePolicy.Fixed))
        self.layout.addWidget(self.number_part)
        self.unit_part = QComboBox(self)
        self.unit_part.addItems(self.all_symbols)
        self.layout.addWidget(self.unit_part)
        self.number_part.valueChanged.connect(self.on_value_change)
        self.unit_part.currentIndexChanged.connect(self.on_unit_change)

    def set_bytes_value(self, bytes_value: int):
        text = bytes2human(bytes_value)
        self.set_text_value(text)

    def set_text_value(self, text_value: str):
        match = self.extraction_regex.match(text_value)
        self.number_part.setValue(float(match.group("number_value")))
        self.unit_part.setCurrentIndex({name.casefold(): idx for idx, name in enumerate(self.all_symbols)}[match.group('unit_value').casefold()])
        if self.unit_part.currentIndex() == 0:
            self.number_part.setSingleStep(1)
            self.number_part.setDecimals(0)
        else:
            self.number_part.setSingleStep(0.1)
            self.number_part.setDecimals(1)

    def get_value(self):
        text = f"{self.number_part.value()} {self.unit_part.currentText()}"
        return human2bytes(text)

    @Slot(int)
    def on_unit_change(self, new_index: int):
        if new_index == 0:
            self.number_part.setSingleStep(1)
            self.number_part.setValue(int(self.number_part.value()))
            self.number_part.setDecimals(0)
        else:
            self.number_part.setSingleStep(0.1)
            self.number_part.setDecimals(1)

    @Slot(float)
    def on_value_change(self, new_value: float):

        if new_value < 1 and self.unit_part.currentIndex() != 0:
            self.set_bytes_value(self.get_value())
        elif new_value > 1024 and self.unit_part.currentIndex() != len(FILE_SIZE_REFERENCE.symbols) - 1:
            self.set_bytes_value(self.get_value())

    @property
    def layout(self):
        return super().layout()

    def set_alignment(self, alignment: Qt.Alignment):
        self.layout.setAlignment(alignment)

    def value_is_changed(self) -> bool:
        return self.get_value() != self.start_value

    def set_value(self, value: Union[str, int], is_start: bool = False):
        if isinstance(value, int):
            self.set_bytes_value(value)
        else:
            self.set_text_value(value)
        if is_start:
            self.start_value = value


_add_value_field(FileSizeValueField)


@implements_protocol(TypeWidgetProtocol)
class IntegerValueField(QWidget):
    ___for_type___ = int

    def __init__(self, parent: Optional[PySide6.QtWidgets.QWidget] = None, maximum: int = 100000) -> None:
        super().__init__(parent=parent)
        self.start_value: int = None
        self.setLayout(QGridLayout(self))
        self.number_part = QSpinBox(self)
        self.number_part.setMaximum(maximum)
        self.layout.addWidget(self.number_part)

    @property
    def layout(self):
        return super().layout()

    def value_is_changed(self) -> bool:
        return self.get_value() != self.start_value

    def set_value(self, value: int, is_start: bool = False):
        self.number_part.setValue(value)
        if is_start:
            self.start_value = value

    def get_value(self) -> int:
        return self.number_part.value()

    def set_alignment(self, alignment: Qt.Alignment):
        self.layout.setAlignment(alignment)


_add_value_field(IntegerValueField)


@implements_protocol(TypeWidgetProtocol)
class FloatValueField(QWidget):
    ___for_type___ = float

    def __init__(self, parent: Optional[PySide6.QtWidgets.QWidget] = None, maximum: int = 100000, decimals: int = 2) -> None:
        super().__init__(parent=parent)
        self.start_value: int = None
        self.setLayout(QGridLayout(self))
        self.number_part = QDoubleSpinBox(self)
        self.number_part.setMaximum(maximum)
        self.number_part.setDecimals(decimals)
        self.layout.addWidget(self.number_part)

    @property
    def layout(self):
        return super().layout()

    def value_is_changed(self) -> bool:
        return self.get_value() != self.start_value

    def set_value(self, value: float, is_start: bool = False):
        self.number_part.setValue(value)
        if is_start:
            self.start_value = value

    def get_value(self) -> float:
        return self.number_part.value()

    def set_alignment(self, alignment: Qt.Alignment):
        self.layout.setAlignment(alignment)


_add_value_field(FloatValueField)


@implements_protocol(TypeWidgetProtocol)
class StringValueField(QWidget):
    ___for_type___ = str

    def __init__(self, parent: Optional[PySide6.QtWidgets.QWidget] = None, multiline: bool = False) -> None:
        super().__init__(parent=parent)
        self.start_value: int = None
        self.setLayout(QGridLayout(self))
        self.multiline = multiline
        self.text_part = QLineEdit(parent=self) if self.multiline is False else QTextEdit(parent=self)
        self.layout.addWidget(self.text_part)

    def set_alignment(self, alignment: Qt.Alignment):
        self.layout.setAlignment(alignment)

    @property
    def layout(self):
        return super().layout()

    def value_is_changed(self) -> bool:
        return self.get_value() != self.start_value

    def set_value(self, value: str, is_start: bool = False):
        self.text_part.setText(value)
        if is_start:
            self.start_value = value

    def get_value(self) -> str:
        return self.text_part.text()


_add_value_field(StringValueField)


@implements_protocol(TypeWidgetProtocol)
class PathValueField(QWidget):
    ___for_type___ = Path

    def __init__(self, base_dir: Path = Path.cwd(),
                 parent: Optional[PySide6.QtWidgets.QWidget] = None,
                 for_file: bool = False,
                 default_file_name: str = None,
                 file_extension: str = None) -> None:
        super().__init__(parent=parent)
        self.setLayout(QGridLayout(self))
        self.start_value: Path = None
        self.base_dir = base_dir
        self.for_file = for_file
        self.default_file_name = default_file_name
        self.file_extension = file_extension
        self.path_part: QLineEdit = None
        self.button: QPushButton = None
        self.setup_parts()

    def setup_parts(self):
        self.path_part = QLineEdit(self)
        self.path_part.setClearButtonEnabled(True)
        self.button = QPushButton(parent=self)
        self.button.setIcon(AllResourceItems.select_path_symbol.get_as_icon())
        self.layout.addWidget(self.button, 0, 3, 1, 1)
        self.layout.addWidget(self.path_part, 0, 0, 1, 4)

        self.button.clicked.connect(self.open_path_browser)

    def value_is_changed(self) -> bool:
        return self.get_value() != self.start_value

    def set_value(self, value: Path, is_start: bool = False):
        self.path_part.setText(value.as_posix())
        self.base_dir = value
        if is_start:
            self.start_value = value

    def get_value(self) -> Optional[Path]:

        _out = self.path_part.text()
        if _out:
            return Path(_out)

    @property
    def layout(self) -> QGridLayout:
        return super().layout()

    def set_alignment(self, alignment: Qt.Alignment):
        self.layout.setAlignment(alignment)

    def open_path_browser(self, checked: bool = False):
        if self.for_file is False:
            new_path = QFileDialog.getExistingDirectory(dir=str(self.base_dir), caption="Select Folder")
        else:
            new_path = QFileDialog.getSaveFileName(caption="Select File", dir=str(self.base_dir), filter=f"*{self.file_extension}")
        if new_path:
            new_path = Path(new_path)
            self.path_part.setText(new_path.as_posix())
            self.base_dir = new_path.parent if new_path.is_file() else new_path


_add_value_field(PathValueField)


@implements_protocol(TypeWidgetProtocol)
class ListValueField(QWidget):
    ___for_type___ = list

    def __init__(self, parent: Optional[PySide6.QtWidgets.QWidget] = None) -> None:
        super().__init__(parent=parent)
        self.start_value: list = None
        self.setLayout(QGridLayout(self))
        self.list_part = QListWidget(self)
        self.layout.addWidget(self.list_part)

    def set_value(self, value: list, is_start: bool = False):
        for item in value:
            self.list_part.addItem(str(item))
        if is_start:
            self.start_value = value

    def value_is_changed(self) -> bool:
        return self.get_value() != self.start_value

    def get_value(self) -> list:
        return list(self.list_part.items())

    @property
    def layout(self) -> QGridLayout:
        return super().layout()

    def set_alignment(self, alignment: Qt.Alignment):
        self.layout.setAlignment(alignment)


_add_value_field(ListValueField)


@implements_protocol(TypeWidgetProtocol)
class StringChoicesValueField(QWidget):
    ___for_type___ = NonTypeBaseTypus.STRING_CHOICE

    def __init__(self, parent: Optional[PySide6.QtWidgets.QWidget] = None, choices: Iterable[str] = tuple()) -> None:
        super().__init__(parent=parent)
        self.setLayout(QGridLayout(self))
        self.start_value: str = None
        self.choices = [""] + list(choices)
        self.text_part = QComboBox(self)

        self.text_part.addItems(self.choices)
        self.layout.addWidget(self.text_part)

    def set_value(self, value: str, is_start: bool = False):
        self.text_part.setCurrentIndex(self.choices.index(value))
        if is_start is True:
            self.start_value = value

    def get_value(self) -> str:
        text = self.text_part.currentText()
        if text == "":
            return None
        return text

    def value_is_changed(self) -> bool:
        return self.get_value() != self.start_value

    def set_alignment(self, alignment: Qt.Alignment):
        self.layout.setAlignment(alignment)

    @property
    def layout(self):
        return super().layout()


_add_value_field(ListValueField)
# region[Main_Exec]
if __name__ == '__main__':
    pass

# endregion[Main_Exec]
