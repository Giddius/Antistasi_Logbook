"""
WiP.

Soon.
"""

# region [Imports]

# * Standard Library Imports ---------------------------------------------------------------------------->
from typing import TYPE_CHECKING, Any, Union, Mapping, Callable, Optional
from pathlib import Path

# * Qt Imports --------------------------------------------------------------------------------------->
import PySide6
from PySide6 import QtGui
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtCore import Qt, Slot, QSize, QTimer, Signal
from PySide6.QtWidgets import (QFrame, QLabel, QWidget, QSpinBox, QCheckBox, QComboBox, QGroupBox, QLineEdit, QTextEdit, QTimeEdit, QFormLayout, QGridLayout, QHBoxLayout, QListWidget,
                               QPushButton, QSizePolicy, QVBoxLayout, QDateTimeEdit, QFontComboBox, QDoubleSpinBox, QStackedWidget, QListWidgetItem, QDialogButtonBox, QAbstractItemView)

# * Gid Imports ----------------------------------------------------------------------------------------->
from gidapptools import get_logger
from gidapptools.errors import EntryMissingError
from gidapptools.general_helper.string_helper import StringCase, StringCaseConverter
from gidapptools.gid_config.interface import GidIniConfig, ResolvedEntry, ResolvedSection
# * Local Imports --------------------------------------------------------------------------------------->
from antistasi_logbook.gui.application import AntistasiLogbookApplication
from antistasi_logbook.storage.models.models import RemoteStorage
from antistasi_logbook.gui.widgets.form_widgets.type_widgets import ALL_VALUE_FIELDS, StyleValueField, StringValueField, UpdateTimeFrameValueField
from antistasi_logbook.gui.resources.antistasi_logbook_resources_accessor import AllResourceItems
from gidapptools.general_helper.enums import MiscEnum
# * Type-Checking Imports --------------------------------------------------------------------------------->
if TYPE_CHECKING:
    from gidapptools.gid_config.interface import GidIniConfig

    from antistasi_logbook.gui.main_window import AntistasiLogbookMainWindow

# endregion[Imports]

# region [TODO]


# endregion [TODO]

# region [Logging]


# endregion[Logging]

# region [Constants]

THIS_FILE_DIR = Path(__file__).parent.absolute()
log = get_logger(__name__)
# endregion[Constants]


def name_to_title(name: str) -> str:
    cleaned_name = StringCaseConverter.convert_to(name, StringCase.SPLIT)
    return cleaned_name[0].upper() + cleaned_name[1:]


class CategorySelectionWidget(QListWidget):
    clicked = Signal(int)

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent=parent)
        self.setup()

    def setup(self):
        self.setViewMode(QListWidget.ViewMode.IconMode)
        self.setFlow(QListWidget.Flow.LeftToRight)
        self.setSortingEnabled(False)
        self.setFixedWidth(100)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setItemAlignment(Qt.AlignCenter)
        self.setGridSize(QSize(75, 75))
        self.setIconSize(QSize(50, 50))
        self.setUniformItemSizes(True)
        self.setWordWrap(False)
        self.setMovement(QListWidget.Movement.Static)
        self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectItems)

    def add_category(self, name: str, icon: QIcon, category_page_number: int):
        item = QListWidgetItem(icon, name)
        item.page_number = category_page_number
        self.addItem(item)

    def __repr__(self) -> str:
        """
        Basic Repr
        !REPLACE!
        """
        return f'{self.__class__.__name__}'


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
        self.setLayout(QVBoxLayout(self))
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
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

    def mousePressEvent(self, event: QtGui.QMouseEvent) -> None:
        self.setFrameStyle(QFrame.Sunken | QFrame.Panel)
        self.clicked.emit(self.category_page_number)

    def mouseReleaseEvent(self, event: QtGui.QMouseEvent) -> None:
        self.setFrameStyle(self.base_style)

    @property
    def layout(self) -> QVBoxLayout:
        return super().layout()

    def __repr__(self) -> str:
        """
        Basic Repr
        !REPLACE!
        """
        return f'{self.__class__.__name__}'


class PictureCategorySelector(QGroupBox):

    def __init__(self, content_widget: QStackedWidget, parent: QStackedWidget = None, ):
        super().__init__(parent=parent)
        self.content_widget = content_widget
        self.setLayout(QHBoxLayout(self))
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setAlignment(Qt.AlignCenter)
        self.setFlat(True)
        self.setTitle("Categories")
        self.categories: dict[str, CategoryPicture] = {}

    @property
    def layout(self) -> QHBoxLayout:
        return super().layout()

    def add_category(self, name: str, picture: QPixmap, category_page_number: int, verbose_name: str = None):
        verbose_name = verbose_name or name_to_title(name)
        category = CategoryPicture(verbose_name, picture.scaled(60, 60, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation), category_page_number, self)

        self.layout.addWidget(category)
        self.categories[name] = category

        category.clicked.connect(self.content_widget.setCurrentIndex)

    def resize_categories(self):
        widths = []
        heights = []
        for category in self.categories.values():
            widths.append(category.sizeHint().width())
            heights.append(category.height())

        max_width = max(widths)
        max_heights = max(heights)
        for category in self.categories.values():
            category.resize(max_width, max_heights)

    def __repr__(self) -> str:
        """
        Basic Repr
        !REPLACE!
        """
        return f'{self.__class__.__name__}'


SETTINGS_VALUE_FIELD_TYPE = Union[QTextEdit, QComboBox, QFontComboBox, QSpinBox, QCheckBox, QDoubleSpinBox, QDateTimeEdit, QTimeEdit]


class SettingsField:

    def __init__(self, name: str, value: Union[Callable, Any], value_typus, verbose_name: str = None) -> None:

        self.key_field: QLabel = None
        self.value_field: SETTINGS_VALUE_FIELD_TYPE = None
        self.name = name
        self.verbose_name = verbose_name or name_to_title(self.name)
        self.start_value = value() if callable(value) else value
        self.value_typus = value_typus
        self.setup()

    def setup(self):
        self.key_field = QLabel(self.verbose_name)

        self.value_field = self.determine_value_field()

    def determine_value_field(self) -> SETTINGS_VALUE_FIELD_TYPE:
        if self.name == "style":

            field = StyleValueField()

        elif self.name == "max_update_time_frame":
            field = UpdateTimeFrameValueField()

        else:
            field_class = ALL_VALUE_FIELDS.get(self.value_typus, StringValueField)
            field = field_class()

        if self.start_value is not None:
            field.set_value(value=self.start_value, is_start=True)
        field.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        return field

    def get_value(self) -> Any:
        pass

    def setEnabled(self, value: bool):
        self.key_field.setEnabled(value)
        self.value_field.setEnabled(value)

    def setToolTip(self, tool_tip: str):
        self.key_field.setToolTip(tool_tip)
        self.value_field.setToolTip(tool_tip)

    def __repr__(self) -> str:
        """
        Basic Repr
        !REPLACE!
        """
        return f'{self.__class__.__name__}'


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
    def from_resolve_section_item(cls, resolve_section: ResolvedSection, parent: QStackedWidget = None) -> "SettingsForm":
        instance: "SettingsForm" = cls(resolve_section.name, parent)
        instance.setWindowTitle(resolve_section.verbose_name)
        for resolve_entry in resolve_section.entries:
            if resolve_entry.gui_visible is False:
                continue

            field = SettingsField(resolve_entry.entry_name, resolve_entry.value, value_typus=resolve_entry.value_typus, verbose_name=resolve_entry.verbose_name)
            if resolve_entry.description:
                field.setToolTip(resolve_entry.description)
            if resolve_entry.implemented is False:
                field.setEnabled(False)
                field.setToolTip("NOT IMPLEMENTED")

            instance.add_field(field)

        return instance

    @classmethod
    def from_dict(cls, section_name: str, data_dict: Mapping[str, tuple[Any, Any]], parent: QStackedWidget = None) -> "SettingsForm":
        instance: "SettingsForm" = cls(section_name, parent)

        instance.setWindowTitle(section_name.title())

        for key, attributes in data_dict.items():
            if attributes.get("gui_visible", True) is False:
                continue
            try:

                field = SettingsField(key, attributes["value"], value_typus=attributes["converter"], verbose_name=attributes.get("verbose_name", None))
                if attributes.get("short_description", "") is not MiscEnum.NOTHING:
                    field.setToolTip(attributes.get("short_description", ""))
                if attributes.get("implemented", True) is False:
                    field.setEnabled(False)
                    field.setToolTip("NOT IMPLEMENTED")

                instance.add_field(field)
            except KeyError as e:
                log.warning("KeyError for %r and attributes %r", key, attributes)

        return instance

    def __repr__(self) -> str:
        """
        Basic Repr
        !REPLACE!
        """
        return f'{self.__class__.__name__}'


class ContentStackedwidget(QStackedWidget):

    def __init__(self, parent: Optional[PySide6.QtWidgets.QWidget] = None) -> None:
        super().__init__(parent=parent)
        self.pages: dict[str, QWidget] = {}
        self.setFrameShape(QFrame.WinPanel)
        self.setFrameShadow(QFrame.Sunken)
        self.setLineWidth(2)
        self.setMidLineWidth(2)

    def addWidget(self, w: "SettingsForm") -> int:
        self.pages[w.section_name] = w
        return super().addWidget(w)

    def __repr__(self) -> str:
        """
        Basic Repr
        !REPLACE!
        """
        return f'{self.__class__.__name__}'


class SettingsWindow(QWidget):
    window_title: str = "Settings"
    exclude_categories: set[str] = {"logging", "mod_handling"}

    def __init__(self, general_config: "GidIniConfig", main_window: "AntistasiLogbookMainWindow", parent=None) -> None:
        super().__init__(parent=parent, f=Qt.Dialog)
        self.general_config = general_config
        self.main_window = main_window
        self.main_layout: QGridLayout = None
        self.buttons: QDialogButtonBox = None
        self.selection_box: PictureCategorySelector = None
        self.content_widget: ContentStackedwidget = None

    def setup(self) -> "SettingsWindow":
        self.setWindowTitle(self.window_title)
        self.setWindowIcon(AllResourceItems.settings_window_symbol_image.get_as_icon())

        self.main_layout = QGridLayout()
        self.setLayout(self.main_layout)

        self.setup_buttons()
        self.setup_content_widget()
        self.setup_selection_box()

        for section in self.general_config.sections:
            if section.name in self.exclude_categories:
                continue

            self.add_category(section, getattr(AllResourceItems, f"{section.name}_settings_image").get_as_pixmap())

        self.selection_box.resize_categories()
        return self

    @property
    def app(self) -> "AntistasiLogbookApplication":
        return AntistasiLogbookApplication.instance()

    def setup_buttons(self) -> None:
        self.buttons = QDialogButtonBox(self)
        self.buttons.setOrientation(Qt.Horizontal)
        self.buttons.setStandardButtons(QDialogButtonBox.Cancel | QDialogButtonBox.Ok)
        self.main_layout.addWidget(self.buttons, 2, 0, 1, 1, Qt.AlignBottom)
        self.buttons.rejected.connect(self.on_cancelled)
        self.buttons.accepted.connect(self.on_accepted)

    def setup_content_widget(self) -> None:
        self.content_widget = ContentStackedwidget(self)
        self.main_layout.addWidget(self.content_widget, 1, 0, 1, 1)

    def setup_selection_box(self) -> None:
        self.selection_box = PictureCategorySelector(self.content_widget)

        self.main_layout.addWidget(self.selection_box, 0, 0, 1, 1, Qt.AlignTop)

    def add_category(self, section_item: ResolvedSection, picture: QPixmap):
        form = SettingsForm.from_resolve_section_item(resolve_section=section_item, parent=self.content_widget)
        if section_item.description:
            form.setToolTip(section_item.description)
        page_number = self.content_widget.addWidget(form)
        self.selection_box.add_category(section_item.verbose_name, picture, page_number)

    def change_page(self, current_item, previous_item):
        self.content_widget.setCurrentIndex(current_item.page_number)

    def on_accepted(self):
        self.save_config()
        self.close()

    def on_cancelled(self):
        page = self.content_widget.pages.get("gui")
        if page is not None:
            field = page.fields.get("style")
            if field.value_field.value_is_changed():
                log.debug("style value has changed from %r to %r", field.start_value, field.get_value())
                self.main_window.set_app_style_sheet(self.main_window.current_app_style_sheet)
        self.close()

    def save_config(self) -> None:
        old_auto_write = self.general_config.config.auto_write
        self.general_config.config.auto_write = True
        for i in range(self.content_widget.count()):
            page: SettingsForm = self.content_widget.widget(i)
            sect_name = page.section_name
            for field in page.fields.values():
                if field.value_field.value_is_changed():
                    self.general_config.set(sect_name, field.name, field.value_field.get_value())
                    if sect_name == "updating" and field.name == "update_interval":
                        if self.main_window.cyclic_update_running is True:
                            self.main_window.start_update_timer()
        # self.general_config.config.save()
        self.general_config.config.auto_write = old_auto_write

    def show(self) -> None:

        return super().show()

    def __repr__(self) -> str:
        """
        Basic Repr
        !REPLACE!
        """
        return f'{self.__class__.__name__}'


class CredentialsBox(QGroupBox):
    def __init__(self, remote_storage: RemoteStorage, parent=None):
        super().__init__(parent=parent)
        self.remote_storage = remote_storage
        self.setLayout(QFormLayout())
        self.setTitle(self.remote_storage.name)
        self.login_input_widget = QLineEdit(self)
        self.login_input_widget.setClearButtonEnabled(True)

        self.password_input_widget = QLineEdit(self)
        self.password_input_widget.setEchoMode(QLineEdit.Password)
        self.password_input_widget.setClearButtonEnabled(True)

        self.show_password_checkbox = QCheckBox(self)

        self.submit_button = QPushButton("Submit")

        self.layout.addRow("Login", self.login_input_widget)
        self.layout.addRow("Password", self.password_input_widget)
        self.layout.addRow("Show Password", self.show_password_checkbox)
        self.layout.addWidget(self.submit_button)

        self.submit_button.pressed.connect(self.submit_credentials)
        self.show_password_checkbox.clicked.connect(self.show_password)
        self._single_shot_timer: QTimer = None

    def setup(self):
        if self.remote_storage.get_login() is not None:
            self.login_input_widget.setText(self.remote_storage.get_login())
        if self.remote_storage.get_password() is not None:
            self.password_input_widget.setText(self.remote_storage.get_password())

    @property
    def app(self) -> "AntistasiLogbookApplication":
        return AntistasiLogbookApplication.instance()

    @property
    def layout(self) -> QFormLayout:
        return super().layout()

    @Slot(bool)
    def show_password(self, show: bool):
        if show:
            self.password_input_widget.setEchoMode(QLineEdit.Normal)
        else:
            self.password_input_widget.setEchoMode(QLineEdit.Password)

    def color_box(self, clean: bool = True):
        if clean is False:
            self.login_input_widget.setStyleSheet("background-color: rgba(75,181,67, 200)")
            self.password_input_widget.setStyleSheet("background-color: rgba(75,181,67, 200)")
            self.submit_button.setStyleSheet("background-color: rgba(75,181,67, 200)")
        else:
            self.login_input_widget.setStyleSheet("")
            self.password_input_widget.setStyleSheet("")
            self.submit_button.setStyleSheet("")

    def indicate_success(self):
        self.color_box(False)
        self._single_shot_timer = QTimer.singleShot(1 * 1000, self.color_box)

    def submit_credentials(self):
        login = self.login_input_widget.text()
        password = self.password_input_widget.text()

        if not login:
            self.login_input_widget.setStyleSheet("background-color: red")

        if not password:
            self.password_input_widget.setStyleSheet("background-color: red")

        if not login or not password:
            return

        self.login_input_widget.setStyleSheet("")
        self.password_input_widget.setStyleSheet("")
        self.remote_storage.set_login_and_password(login=login, password=password)
        self.indicate_success()

    def __repr__(self) -> str:
        """
        Basic Repr
        !REPLACE!
        """
        return f'{self.__class__.__name__}'


class CredentialsManagmentWindow(QWidget):

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent=parent)
        self.setLayout(QVBoxLayout())
        with self.app.backend.database:
            for remote_storage in RemoteStorage.select():
                if remote_storage.credentials_required:
                    widget = CredentialsBox(remote_storage, self)
                    self.layout.addWidget(widget)
                    widget.setup()

    @property
    def app(self) -> "AntistasiLogbookApplication":
        return AntistasiLogbookApplication.instance()

    @property
    def layout(self) -> QVBoxLayout:
        return super().layout()

    def __repr__(self) -> str:
        """
        Basic Repr
        !REPLACE!
        """
        return f'{self.__class__.__name__}'

# region[Main_Exec]


if __name__ == '__main__':
    pass

# endregion[Main_Exec]
