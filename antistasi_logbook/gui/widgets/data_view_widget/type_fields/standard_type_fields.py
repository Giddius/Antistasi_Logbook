"""
WiP.

Soon.
"""

# region [Imports]

# * Standard Library Imports ---------------------------------------------------------------------------->
from typing import Mapping, Iterable
from pathlib import Path
from functools import cached_property

# * Qt Imports --------------------------------------------------------------------------------------->
from PySide6.QtGui import QFont, QColor
from PySide6.QtCore import Qt, QSize
from PySide6.QtWidgets import QLabel, QListWidget, QTreeWidget, QTreeWidgetItem

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
        self.setup()

    def setup(self):
        self.setItemAlignment(Qt.AlignCenter)

    def set_size(self, h, w):
        pass

    def set_value(self, value: list):
        self.values = value
        self.addItems(str(i) for i in value)

    @classmethod
    def add_to_type_field_table(cls, table: dict):
        table[cls.___typus___] = cls
        return table


@implements_protocol(TypeFieldProtocol)
class DictTypeField(QTreeWidget):
    ___typus___: type = dict
    bool_images = {True: AllResourceItems.check_mark_green_image.get_as_icon(),
                   False: AllResourceItems.close_black_image.get_as_icon()}

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.values = None
        self.setup()

    @cached_property
    def bool_font(self) -> QFont:
        font: QFont = self.font()
        font.setBold(True)
        return font

    @cached_property
    def key_font(self) -> QFont:
        font: QFont = self.font()
        font.setBold(True)
        return font

    def setup(self):
        self.setRootIsDecorated(True)
        self.header().setHidden(True)

    def set_size(self, h, w):
        pass

    def _fill_item(self, item: QTreeWidgetItem, value):
        item.setExpanded(True)
        if isinstance(value, Mapping):
            for key, val in value.items():
                child = QTreeWidgetItem()
                child.setText(0, str(key))
                child.setFont(0, self.key_font)
                item.addChild(child)
                self._fill_item(child, val)
        elif isinstance(value, Iterable) and not isinstance(value, str):
            for val in value:
                child = QTreeWidgetItem()
                item.addChild(child)
                if isinstance(val, Mapping):
                    child.setText(0, '[dict]')
                    self._fill_item(child, val)
                elif isinstance(value, Iterable) and not isinstance(value, str):
                    child.setText(0, '[list]')
                    self._fill_item(child, val)
                elif isinstance(val, bool):
                    child.setFont(0, self.bool_font)
                    if val is True:
                        child.setForeground(0, QColor(0, 225, 0, 200))
                        child.setIcon(0, self.bool_images[True])
                    elif val is False:
                        child.setForeground(0, QColor(225, 0, 0, 200))
                        child.setIcon(0, self.bool_images[False])
                    child.setText(0, str(val))
                else:
                    child.setText(0, str(val))
                child.setExpanded(True)
        else:
            child = QTreeWidgetItem()
            child.setText(0, str(value))
            item.addChild(child)

    def fill_widget(self, value: dict):
        self.clear()
        self._fill_item(self.invisibleRootItem(), value)

    def set_value(self, value: dict):
        self.values = value
        self.fill_widget(value)

    @classmethod
    def add_to_type_field_table(cls, table: dict):
        table[cls.___typus___] = cls
        return table


# region[Main_Exec]
if __name__ == '__main__':
    pass

# endregion[Main_Exec]
