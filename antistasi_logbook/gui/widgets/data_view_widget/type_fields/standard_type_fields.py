"""
WiP.

Soon.
"""

# region [Imports]

# * Standard Library Imports ---------------------------------------------------------------------------->
from pathlib import Path

# * Qt Imports --------------------------------------------------------------------------------------->
from PySide6.QtCore import Qt, QSize
from PySide6.QtWidgets import QLabel, QListWidget

# * Gid Imports ----------------------------------------------------------------------------------------->
from gidapptools import get_logger
from gidapptools.general_helper.typing_helper import implements_protocol

# * Local Imports --------------------------------------------------------------------------------------->
from antistasi_logbook.gui.resources.antistasi_logbook_resources_accessor import AllResourceItems
from antistasi_logbook.gui.widgets.data_view_widget.type_fields.base_type_field import TypeFieldProtocol

# endregion[Imports]

# region [TODO]


# endregion [TODO]

# region [Logging]


# endregion[Logging]

# region [Constants]

THIS_FILE_DIR = Path(__file__).parent.absolute()
log = get_logger(__name__)
# endregion[Constants]


@implements_protocol(TypeFieldProtocol)
class BoolTypeField(QLabel):
    ___typus___: type = bool

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        # self.setLayoutDirection(Qt.RightToLeft)
        self.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self._image_size: QSize = QSize(50, 50)
        self.image_table = {True: AllResourceItems.check_mark_green_image.get_as_pixmap(),
                            False: AllResourceItems.close_cancel_image.get_as_pixmap()}

    def set_size(self, w: int, h: int) -> None:
        self._image_size = QSize(w, h)
        if self.pixmap() is not None:
            self.setPixmap(self.pixmap().scaled(self._image_size, Qt.KeepAspectRatioByExpanding))

    def set_value(self, value: bool) -> None:
        self.clear()
        pixmap = self.image_table.get(value, None)
        if pixmap is None:

            self.setText('-')
        else:
            if self._image_size is not None:
                pixmap = pixmap.scaled(self._image_size, Qt.KeepAspectRatioByExpanding)
            self.setPixmap(pixmap)

    @classmethod
    def add_to_type_field_table(cls, table: dict):
        table[cls.___typus___] = cls
        return table


@implements_protocol(TypeFieldProtocol)
class StringTypeField(QLabel):
    ___typus___: type = str

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setLayoutDirection(Qt.RightToLeft)
        self.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.setTextFormat(Qt.MarkdownText)

    def set_size(self, h, w):
        pass

    def set_value(self, value: str):
        self.setText(f"`{value}`")

    @classmethod
    def add_to_type_field_table(cls, table: dict):
        table[cls.___typus___] = cls
        return table


@implements_protocol(TypeFieldProtocol)
class IntTypeField(StringTypeField):
    ___typus___: type = int

    def set_value(self, value: int):
        return super().set_value(str(value))


@implements_protocol(TypeFieldProtocol)
class FloatTypeField(StringTypeField):
    ___typus___: type = float

    def set_value(self, value: float):
        return super().set_value(str(value))


@implements_protocol(TypeFieldProtocol)
class ListTypeField(QListWidget):
    ___typus___: type = list

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.values = None

    def set_size(self, h, w):
        pass

    def set_value(self, value: list):
        self.values = value
        self.addItems(str(i) for i in value)

    @classmethod
    def add_to_type_field_table(cls, table: dict):
        table[cls.___typus___] = cls
        return table


# region[Main_Exec]
if __name__ == '__main__':
    pass

# endregion[Main_Exec]
