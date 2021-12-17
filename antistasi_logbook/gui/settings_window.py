"""
WiP.

Soon.
"""

# region [Imports]

# * Standard Library Imports ---------------------------------------------------------------------------->
from typing import TYPE_CHECKING, Any, Union, Mapping, Callable
from pathlib import Path

# * Third Party Imports --------------------------------------------------------------------------------->
from antistasi_logbook.gui.resources.style_sheets import ALL_STYLE_SHEETS
from antistasi_logbook.gui.widgets.form_widgets.type_widgets import ALL_VALUE_FIELDS, StringValueField, StringChoicesValueField
from antistasi_logbook.gui.resources.antistasi_logbook_resources_accessor import AllResourceItems

# * PyQt5 Imports --------------------------------------------------------------------------------------->
import PySide6
from PySide6.QtGui import QPixmap
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (QFrame, QLabel, QWidget, QSpinBox, QCheckBox, QComboBox, QGroupBox, QTextEdit, QTimeEdit, QFormLayout, QGridLayout,
                               QSizePolicy, QVBoxLayout, QDateTimeEdit, QFontComboBox, QDoubleSpinBox, QStackedWidget, QDialogButtonBox)

# * Gid Imports ----------------------------------------------------------------------------------------->
from gidapptools import get_logger
from gidapptools.general_helper.string_helper import StringCase, StringCaseConverter

if TYPE_CHECKING:
    # * Third Party Imports --------------------------------------------------------------------------------->
    from antistasi_logbook.gui.main_window import AntistasiLogbookMainWindow

    # * Gid Imports ----------------------------------------------------------------------------------------->
    from gidapptools.gid_config.interface import GidIniConfig

# endregion[Imports]

# region [TODO]


# endregion [TODO]

# region [Logging]


# endregion[Logging]

# region [Constants]

THIS_FILE_DIR = Path(__file__).parent.absolute()
log = get_logger(__name__)
# endregion[Constants]


class CategoryPicture(QFrame):
    clicked = Signal(int)

    def __init__(self, text: str, picture: QPixmap, category_page_number: int, parent=None) -> None:
        super().__init__(parent=parent)
        self.text: QLabel = None
        self.picture: QLabel = None
        self.category_page_number = category_page_number
        self.base_style = QFrame.Raised | QFrame.Panel
        self.setup(text, picture)

    def setup(self, text: str, picture: QPixmap):
        self.setLayout(QGridLayout(self))
        self.setContentsMargins(0, 0, 0, 1)
        self.setFrameStyle(self.base_style)
        self.setMidLineWidth(3)
        self.setLineWidth(3)
        self.setToolTip(text)

        self.setup_text(text)
        self.setup_picture(picture)

    def setup_text(self, text: str):
        self.text = QLabel(text=text, parent=self)
        self.text.setAlignment(Qt.AlignHCenter | Qt.AlignBottom)
        self.text.setTextFormat(Qt.AutoText)

        self.layout.addWidget(self.text)

    def setup_picture(self, picture: QPixmap):
        self.picture = QLabel(self)
        self.picture.setPixmap(picture)
        self.picture.setAlignment(Qt.AlignCenter)

        self.layout.addWidget(self.picture)

    def mousePressEvent(self, event: PySide6.QtGui.QMouseEvent) -> None:
        self.setFrameStyle(QFrame.StyledPanel | QFrame.Plain)
        self.clicked.emit(self.category_page_number)

    def mouseReleaseEvent(self, event: PySide6.QtGui.QMouseEvent) -> None:
        self.setFrameStyle(self.base_style)

    @property
    def layout(self) -> QGridLayout:
        return super().layout()


class PictureCategorySelector(QGroupBox):

    def __init__(self, content_widget: QStackedWidget, parent: QStackedWidget = None, ):
        super().__init__(parent=parent)
        self.content_widget = content_widget
        self.setLayout(QVBoxLayout(self))
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.setTitle("Categories")
        self.categories: dict[str, CategoryPicture] = {}

    @property
    def layout(self):
        return super().layout()

    def add_category(self, name: str, picture: QPixmap, category_page_number: int):
        category = CategoryPicture(name, picture.scaled(50, 50, Qt.KeepAspectRatioByExpanding), category_page_number, self)

        self.layout.addWidget(category)
        self.categories[name] = category

        category.clicked.connect(self.content_widget.setCurrentIndex)


SETTINGS_VALUE_FIELD_TYPE = Union[QTextEdit, QComboBox, QFontComboBox, QSpinBox, QCheckBox, QDoubleSpinBox, QDateTimeEdit, QTimeEdit]


class SettingsField:

    def __init__(self, name: str, value: Union[Callable, Any], value_typus) -> None:

        self.key_field: QLabel = None
        self.value_field: SETTINGS_VALUE_FIELD_TYPE = None
        self.name = name
        self.start_value = value() if callable(value) else value
        self.value_typus = value_typus
        self.setup()

    def setup(self):
        title = StringCaseConverter.convert_to(self.name, StringCase.SPLIT)
        self.key_field = QLabel(title[0].upper() + title[1:])

        self.value_field = self.determine_value_field()

    def determine_value_field(self) -> SETTINGS_VALUE_FIELD_TYPE:
        if self.name == "style":
            field = StringChoicesValueField(choices=[i.removesuffix(".qss") for i in ALL_STYLE_SHEETS])
            if self.start_value is not None:
                if self.start_value.endswith('.qss'):
                    self.start_value = self.start_value.removesuffix(".qss")
                field.set_value(value=self.start_value, is_start=True)
        else:
            field_class = ALL_VALUE_FIELDS.get(self.value_typus.base_typus, StringValueField)
            field = field_class()

            if self.start_value is not None:
                field.set_value(value=self.start_value, is_start=True)
        field.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        return field

    def get_value(self) -> Any:
        pass


class SettingsForm(QFrame):

    def __init__(self, section_name: str, parent: QStackedWidget = None) -> None:
        super().__init__(parent=parent)
        self.section_name = section_name
        self.setLayout(QFormLayout(self))
        self.fields: dict[str, "SettingsField"] = {}

        self.layout.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)

    @property
    def layout(self) -> QFormLayout:
        return super().layout()

    def add_field(self, field: "SettingsField"):
        self.layout.addRow(field.key_field, field.value_field)
        self.fields[field.name] = field

    @classmethod
    def from_dict(cls, section_name: str, data_dict: Mapping[str, tuple[Any, Any]], parent: QStackedWidget = None) -> "SettingsForm":
        instance: "SettingsForm" = cls(section_name, parent)

        instance.setWindowTitle(section_name.title())

        for key, value in data_dict.items():
            field = SettingsField(key, value[0], value_typus=value[1])
            instance.add_field(field)

        return instance


class SettingsWindow(QWidget):
    window_title: str = "Settings"

    def __init__(self, general_config: "GidIniConfig", main_window: "AntistasiLogbookMainWindow") -> None:
        super().__init__()
        self.general_config = general_config
        self.main_window = main_window
        self.main_layout: QGridLayout = None
        self.buttons: QDialogButtonBox = None
        self.selection_box: PictureCategorySelector = None
        self.content_widget: QStackedWidget = None

    def setup(self) -> "SettingsWindow":
        self.setWindowTitle(self.window_title)
        self.setWindowIcon(AllResourceItems.settings_window_symbol.get_as_icon())

        self.main_layout = QGridLayout()
        self.setLayout(self.main_layout)

        self.setup_buttons()
        self.setup_content_widget()
        self.setup_selection_box()
        for cat, sub_data in self.general_config.as_dict(with_typus=True).items():
            self.add_category(cat, sub_data, getattr(AllResourceItems, f"{cat}_icon").get_as_pixmap())
        return self

    def setup_buttons(self) -> None:
        self.buttons = QDialogButtonBox(self)
        self.buttons.setOrientation(Qt.Horizontal)
        self.buttons.setStandardButtons(QDialogButtonBox.Cancel | QDialogButtonBox.Ok)
        self.main_layout.addWidget(self.buttons, 1, 0, 1, 2, Qt.AlignBottom)
        self.buttons.rejected.connect(self.close)
        self.buttons.accepted.connect(self.on_accepted)

    def setup_content_widget(self) -> None:
        self.content_widget = QStackedWidget(self)
        self.main_layout.addWidget(self.content_widget, 0, 1, 1, 1)

    def setup_selection_box(self) -> None:
        self.selection_box = PictureCategorySelector(content_widget=self.content_widget)
        self.main_layout.addWidget(self.selection_box, 0, 0, 1, 1, Qt.AlignTop)

    def add_category(self, text: str, data_dict: Mapping[str, Any], picture: QPixmap):
        page_number = self.content_widget.addWidget(SettingsForm.from_dict(section_name=text, data_dict=data_dict, parent=self.content_widget))
        self.selection_box.add_category(text, picture, page_number)

    def on_accepted(self):
        self.save_config()
        self.close()

    def save_config(self) -> None:
        old_auto_write = self.general_config.config.auto_write
        self.general_config.config.auto_write = False
        for i in range(self.content_widget.count()):
            page: SettingsForm = self.content_widget.widget(i)
            sect_name = page.section_name
            for field in page.fields.values():
                if field.value_field.value_is_changed():
                    log.debug("sect_name=%r, field.name=%r, field.value_field.get_value()=%r", sect_name, field.name, field.value_field.get_value())
                    self.general_config.set(sect_name, field.name, field.value_field.get_value())
                    if sect_name == "gui" and field.name == "style":
                        self.main_window.set_app_style_sheet(self.main_window.current_app_style)
        self.general_config.config.save()
        self.general_config.config.auto_write = old_auto_write

# region[Main_Exec]


if __name__ == '__main__':
    pass

# endregion[Main_Exec]
