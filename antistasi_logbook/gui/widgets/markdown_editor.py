"""
WiP.

Soon.
"""

# region [Imports]

# * Standard Library Imports ---------------------------------------------------------------------------->
from typing import TYPE_CHECKING, Optional
from pathlib import Path

# * Qt Imports --------------------------------------------------------------------------------------->
import PySide6
from PySide6.QtGui import QFont, QTextDocument, QBrush, QColor
from PySide6.QtCore import Qt, QTimer, Signal, QItemSelectionModel
from PySide6.QtWidgets import QDialog, QWidget, QSpinBox, QGroupBox, QListWidgetItem, QLineEdit, QComboBox, QAbstractItemView, QListWidget, QTextEdit, QFormLayout, QGridLayout, QHBoxLayout, QPushButton, QVBoxLayout, QTextBrowser, QDialogButtonBox

# * Gid Imports ----------------------------------------------------------------------------------------->
from gidapptools import get_logger

# * Type-Checking Imports --------------------------------------------------------------------------------->
if TYPE_CHECKING:
    pass

# endregion[Imports]

# region [TODO]


# endregion [TODO]

# region [Logging]


# endregion[Logging]

# region [Constants]

from gidapptools.general_helper.timing import get_dummy_profile_decorator_in_globals
get_dummy_profile_decorator_in_globals()
THIS_FILE_DIR = Path(__file__).parent.absolute()
log = get_logger(__name__)

# endregion[Constants]


class AddListDialog(QDialog):
    list_accepted = Signal(str)

    def __init__(self, parent=None) -> None:
        super().__init__(parent=parent)

        self.setLayout(QFormLayout())
        self.select_list_type_input = QComboBox(self)
        self.select_list_type_input.addItems(["Unordered", "Ordered"])
        self.layout.addRow("List type", self.select_list_type_input)

        self.list_input = QListWidget(self)

        self.list_input.setEditTriggers(QAbstractItemView.AllEditTriggers)
        self.list_input.setSelectionMode(QListWidget.SingleSelection)

        self.layout.addRow("List", self.list_input)

        self.buttons = QDialogButtonBox(QDialogButtonBox.Cancel | QDialogButtonBox.Ok, Qt.Horizontal)
        self.buttons.setCenterButtons(True)
        self.buttons.rejected.connect(self.on_cancelled)
        self.buttons.accepted.connect(self.on_accepted)
        self.layout.addWidget(self.buttons)

        self.add_item_button = QPushButton("Add List-Item")
        self.add_item_button.pressed.connect(self.add_list_item)
        self.layout.addWidget(self.add_item_button)

    def add_list_item(self):
        item = QListWidgetItem()

        self.list_input.insertItem(self.list_input.count(), item)
        item.setFlags(item.flags() | Qt.ItemIsEditable)
        self.list_input.setCurrentItem(item, QItemSelectionModel.Select)

    def color_list_input(self, clear: bool = True):
        if clear is False:
            self.list_input.setStyleSheet("background-color: rgba(179, 58, 58,200)")
        else:
            self.list_input.setStyleSheet("")

    def get_text(self) -> str:

        list_strings = []
        for row in range(self.list_input.count()):
            item = self.list_input.item(row)
            if item.text():
                list_strings.append(item.text())
        list_type = self.select_list_type_input.currentText()
        if list_type == "Unordered":
            return '\n' + '\n'.join(f"* {i}" for i in list_strings) + '\n'

        _out = '\n'
        for idx, string in enumerate(list_strings):
            _out += f'{idx+1}. {string}\n'
        return _out

    def on_cancelled(self):
        self.close()

    def on_accepted(self):
        if self.list_input.count() == 0:
            self.color_list_input(False)
            self._single_shot_timer = QTimer.singleShot(1 * 1000, self.color_list_input)
            return
        text = self.get_text()
        self.list_accepted.emit(text)
        self.close()

    @property
    def layout(self) -> QFormLayout:
        return super().layout()


class AddTitleDialog(QDialog):
    title_accepted = Signal(str)

    def __init__(self, parent: Optional[PySide6.QtWidgets.QWidget] = None) -> None:
        super().__init__(parent=parent)

        self.setLayout(QFormLayout())
        self.level_selector = QSpinBox(self)
        self.level_selector.setMinimum(1)
        self.layout.addRow("Level", self.level_selector)

        self.text_input = QLineEdit(self)
        self.layout.addRow("Text", self.text_input)
        self.buttons = QDialogButtonBox(QDialogButtonBox.Cancel | QDialogButtonBox.Ok, Qt.Horizontal)
        self.buttons.setCenterButtons(True)
        self.buttons.rejected.connect(self.on_cancelled)
        self.buttons.accepted.connect(self.on_accepted)
        self.layout.addWidget(self.buttons)

    def color_text_input(self, clear: bool = True):
        if clear is False:
            self.text_input.setStyleSheet("background-color: rgba(179, 58, 58,200)")
        else:
            self.text_input.setStyleSheet("")

    def on_cancelled(self):
        self.close()

    def on_accepted(self):
        if not self.text_input.text():
            self.color_text_input(False)
            self._single_shot_timer = QTimer.singleShot(1 * 1000, self.color_text_input)
            return
        level_text = '#' * self.level_selector.value()
        title = f"\n{level_text} {self.text_input.text()}\n"
        self.title_accepted.emit(title)
        self.close()

    @property
    def layout(self) -> QFormLayout:
        return super().layout()


class AddLinkDialog(QDialog):
    link_accepted = Signal(str)

    def __init__(self, parent: Optional[PySide6.QtWidgets.QWidget] = None) -> None:
        super().__init__(parent=parent)

        self.setLayout(QFormLayout())
        self.link_text_input = QLineEdit(self)
        self.layout.addRow("text", self.link_text_input)

        self.link_url_input = QLineEdit(self)
        self.layout.addRow("URL", self.link_url_input)
        self.buttons = QDialogButtonBox(QDialogButtonBox.Cancel | QDialogButtonBox.Ok, Qt.Horizontal)
        self.buttons.setCenterButtons(True)
        self.buttons.rejected.connect(self.on_cancelled)
        self.buttons.accepted.connect(self.on_accepted)
        self.layout.addWidget(self.buttons)

    @property
    def layout(self) -> QFormLayout:
        return super().layout()

    def color_inputs(self, input_field: QLineEdit = None):
        if input_field is None:
            self.link_text_input.setStyleSheet("")
            self.link_url_input.setStyleSheet("")
            self.text_input.setStyleSheet("background-color: rgba(179, 58, 58,200)")
        else:
            input_field.setStyleSheet("background-color: rgba(179, 58, 58,200)")

    def on_cancelled(self):
        self.close()

    def on_accepted(self):
        if not self.link_text_input.text():
            self.color_inputs(self.link_text_input)
            self._single_shot_timer = QTimer.singleShot(1 * 1000, self.color_inputs)
            return

        if not self.link_url_input.text():
            self.color_inputs(self.link_url_input)
            self._single_shot_timer = QTimer.singleShot(1 * 1000, self.color_inputs)
            return

        link_text = f"[{self.link_text_input.text()}]({self.link_url_input.text()})"
        self.link_accepted.emit(link_text)
        self.close()


class MarkdownEditor(QWidget):
    accepted = Signal(str)
    cancelled = Signal()

    def __init__(self, text: str = None, parent: Optional[PySide6.QtWidgets.QWidget] = None) -> None:
        super().__init__(parent=parent)
        self.preset_text = text
        self.setLayout(QVBoxLayout())
        self.editor_layout = QHBoxLayout()
        self.layout.addLayout(self.editor_layout)

        self.input_widget: QTextEdit = None
        self.preview_widget: QTextBrowser = None
        self.buttons: QDialogButtonBox = None
        self.input_extras_box: QGroupBox = None
        self.input_extras: dict[str, QPushButton] = {}
        self.temp_dialog = None
        self.setup()

    def setup(self):
        self.setup_input_widget()
        self.setup_input_extras()
        self.setup_preview_widget()

        self.setup_buttons()
        if self.preset_text is not None:
            self.input_widget.setPlainText(self.preset_text)
            self.update_preview()

    def setup_input_widget(self):
        self.input_layout = QVBoxLayout(self)

        self.input_widget = QTextEdit(self)
        font: QFont = self.input_widget.font()
        font.setStyleHint(QFont.Monospace)
        self.input_widget.setFont(font)
        self.input_widget.setAcceptRichText(False)
        self.input_widget.setAutoFormatting(QTextEdit.AutoAll)
        self.input_widget.textChanged.connect(self.update_preview)
        self.input_layout.addWidget(self.input_widget)
        self.input_extras_box = QGroupBox()
        self.input_extras_box.setLayout(QHBoxLayout())

        self.input_layout.addWidget(self.input_extras_box)
        self.editor_layout.addLayout(self.input_layout)

    def setup_input_extras(self):
        add_title_button = QPushButton("add Title")
        add_title_button.pressed.connect(self.add_title)
        self.input_extras["add_title"] = add_title_button

        add_separator_button = QPushButton("add Separator")
        add_separator_button.pressed.connect(self.add_separator)
        self.input_extras["add_separator"] = add_separator_button

        add_link_button = QPushButton("add Link")
        add_link_button.pressed.connect(self.add_link)
        self.input_extras["add_link"] = add_link_button

        add_list_button = QPushButton("add List")
        add_list_button.pressed.connect(self.add_list)
        self.input_extras["add_list"] = add_list_button

        for widget in self.input_extras.values():
            self.input_extras_box.layout().addWidget(widget)

    def setup_preview_widget(self):
        self.preview_box = QGroupBox("Preview")
        self.preview_box.setCheckable(True)
        self.preview_box.setChecked(True)
        self.preview_box.setLayout(QGridLayout())

        self.preview_widget = QTextBrowser(self)

        self.preview_box.toggled.connect(self.preview_widget.setVisible)
        self.preview_widget.setReadOnly(True)

        self.preview_widget.setStyleSheet("background-color: rgba(255,255,255,0)")
        self.preview_widget.setOpenExternalLinks(True)
        self.preview_widget.setOpenLinks(True)
        self.preview_box.layout().addWidget(self.preview_widget)
        self.editor_layout.addWidget(self.preview_box)

    def setup_buttons(self):
        self.buttons = QDialogButtonBox(QDialogButtonBox.Cancel | QDialogButtonBox.Ok, Qt.Horizontal)
        self.buttons.rejected.connect(self.on_cancelled)
        self.buttons.accepted.connect(self.on_accepted)
        self.buttons.setCenterButtons(True)
        self.layout.addWidget(self.buttons)

    def update_preview(self):
        self.preview_widget.setMarkdown(self.input_widget.toMarkdown(QTextDocument.MarkdownDialectGitHub))

    def on_accepted(self):
        self.accepted.emit(self.input_widget.toMarkdown(QTextDocument.MarkdownDialectGitHub).strip())

    def on_cancelled(self):
        self.cancelled.emit()

    def add_separator(self):
        self.input_widget.insertPlainText("\n---\n")

    def add_title(self):
        self.temp_dialog = AddTitleDialog(self)
        self.temp_dialog.title_accepted.connect(self.input_widget.insertPlainText)
        self.temp_dialog.show()

    def add_link(self):
        self.temp_dialog = AddLinkDialog(self)
        self.temp_dialog.link_accepted.connect(self.input_widget.insertPlainText)
        self.temp_dialog.show()

    def add_list(self):
        self.temp_dialog = AddListDialog(self)
        self.temp_dialog.list_accepted.connect(self.input_widget.insertPlainText)
        self.temp_dialog.show()

    @property
    def layout(self) -> QHBoxLayout:
        return super().layout()


class MarkdownEditorDialog(QDialog):
    dialog_accepted = Signal(str)
    dialog_cancelled = Signal()

    def __init__(self, text: str = None, parent: Optional[PySide6.QtWidgets.QWidget] = ...) -> None:
        super().__init__(parent=parent)
        self.setLayout(QGridLayout())
        self.markdown_editor = MarkdownEditor(text=text)
        self.layout().addWidget(self.markdown_editor)
        self.markdown_editor.accepted.connect(self.on_accepted)
        self.markdown_editor.cancelled.connect(self.on_cancelled)
        self.setModal(True)
        self.resize(1000, 750)

    def on_accepted(self, text: str):
        log.debug("setting result of %r to %r", self, QDialog.Accepted)

        self.dialog_accepted.emit(text)
        self.done(QDialog.Accepted)

    def on_cancelled(self):
        log.debug("setting result of %r to %r", self, QDialog.Accepted)

        self.dialog_cancelled.emit()
        self.done(QDialog.Rejected)

    @classmethod
    def show_dialog(cls, text: str = None, parent=None) -> tuple[bool, Optional[str]]:
        dialog = cls(text=text, parent=parent)
        dialog.setModal(True)

        if dialog.exec() == QDialog.Accepted:
            return True, dialog.markdown_editor.input_widget.toMarkdown(QTextDocument.MarkdownDialectGitHub).strip()

        return False, None


# region[Main_Exec]
if __name__ == '__main__':
    pass

# endregion[Main_Exec]
