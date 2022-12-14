"""
WiP.

Soon.
"""

# region [Imports]

# * Standard Library Imports ---------------------------------------------------------------------------->
import os
import sys
import subprocess
from typing import TYPE_CHECKING, Any, Union, Callable, Iterable, Optional
from pathlib import Path
from functools import cached_property
from collections import defaultdict
from collections.abc import Mapping

# * Qt Imports --------------------------------------------------------------------------------------->
import PySide6
from PySide6.QtGui import QFont, QColor, QPixmap, QPalette, QFontInfo, QCloseEvent
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QMenu, QFrame, QLabel, QStyle, QLayout, QWidget, QGroupBox, QTextEdit, QFormLayout, QHBoxLayout, QListWidget, QMainWindow,
                               QPushButton, QScrollArea, QSizePolicy, QTreeWidget, QVBoxLayout, QApplication, QTreeWidgetItem, QAbstractScrollArea)

# * Gid Imports ----------------------------------------------------------------------------------------->
from gidapptools import get_logger
from gidapptools.general_helper.conversion import number_to_pretty
from gidapptools.general_helper.string_helper import shorten_string
from gidapptools.gidapptools_qt.helper.window_geometry_helper import move_to_center_of_screen

# * Local Imports --------------------------------------------------------------------------------------->
from antistasi_logbook.gui.widgets.dock_widget import BaseDockWidget
from antistasi_logbook.gui.resources.antistasi_logbook_resources_accessor import AllResourceItems

# * Type-Checking Imports --------------------------------------------------------------------------------->
if TYPE_CHECKING:
    from antistasi_logbook.gui.application import AntistasiLogbookApplication

# endregion[Imports]

# region [TODO]


# endregion [TODO]

# region [Logging]


# endregion[Logging]

# region [Constants]

THIS_FILE_DIR = Path(__file__).parent.absolute()
log = get_logger(__name__)

# endregion[Constants]


class ListOfDictsResultWidget(QTreeWidget):
    ___typus___: type = dict
    bool_images = {True: AllResourceItems.check_mark_green_image.get_as_icon(),
                   False: AllResourceItems.close_black_image.get_as_icon()}

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.values = None
        self.setup()

    @cached_property
    def top_font(self) -> QFont:
        font: QFont = self.font()
        font.setBold(True)
        font.setPointSize(int(font.pointSize() * 1.25))
        font.setUnderline(True)
        return font

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
            if len(value) <= 0:
                child = QTreeWidgetItem()
                child.setText(0, "{}")
                item.addChild(child)
            else:
                for key, val in value.items():
                    child = QTreeWidgetItem()
                    child.setText(0, str(key))
                    child.setFont(0, self.key_font)
                    item.addChild(child)
                    self._fill_item(child, val)
        elif isinstance(value, Iterable) and not isinstance(value, str):
            if len(value) <= 0:
                child = QTreeWidgetItem()
                child.setText(0, "[]")
                item.addChild(child)
            else:
                for val in value:
                    self._fill_item(item, val)
        elif isinstance(value, bool):
            child = QTreeWidgetItem()
            child.setFont(0, self.bool_font)
            if value is True:
                child.setForeground(0, QColor(0, 225, 0, 200))
                child.setIcon(0, self.bool_images[True])
            elif value is False:
                child.setForeground(0, QColor(225, 0, 0, 200))
                child.setIcon(0, self.bool_images[False])
            child.setText(0, str(value))
            item.addChild(child)
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


class ListOfDictsResult:

    def __init__(self, items: list[dict]):
        self.items = items

    def to_sub_widget(self, content_widget: QWidget):
        widget = ListOfDictsResultWidget()
        widget.setup()
        for item in self.items:
            name = item.pop("name", None)
            if name is None:
                widget._fill_item(widget.invisibleRootItem(), item)
            else:
                top_item = QTreeWidgetItem()
                top_item.setText(0, name)
                top_item.setFont(0, widget.top_font)

                top_item.setIcon(0, widget.style().standardIcon(QStyle.SP_FileDialogInfoView))
                widget.invisibleRootItem().addChild(top_item)
                widget._fill_item(top_item, item)

        widget.collapseAll()
        widget.setSizeAdjustPolicy(QAbstractScrollArea.SizeAdjustPolicy.AdjustToContents)
        return widget


class IconTextLabel(QWidget):
    def __init__(self, parent=None, text: str = None, icon: QPixmap = None):
        super().__init__(parent=parent)
        self.setLayout(QHBoxLayout())
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.icon_label = QLabel(self)
        self.text_label = QLabel(self)
        if icon is not None:
            self.icon_label.setPixmap(icon)

        if text is not None:
            self.text_label.setText(text)

        self.layout.addWidget(self.icon_label)
        self.layout.addWidget(self.text_label)
        self.layout.setAlignment(Qt.AlignCenter)

    @property
    def layout(self) -> QVBoxLayout:
        return super().layout()


class PathButton(QPushButton):

    def __init__(self, path: Union[str, os.PathLike, Path], parent=None):
        super().__init__(parent=parent)
        self.path = Path(path).resolve()
        self.is_file = self.path.is_file()
        self.is_dir = self.path.is_dir()
        self.setText(self.path.as_posix())

        link_color = QApplication.instance().palette().color(QPalette.Button.Link)
        r = link_color.red()
        g = link_color.green()
        b = link_color.blue()
        self.setStyleSheet(f"color: rgb({', '.join(str(i) for i in [r,g,b])})")
        self.setCursor(Qt.PointingHandCursor)

        self.pressed.connect(self.open_folder)

    def open_folder(self):
        safe_path = str(self.path)
        if self.is_dir is False and self.is_file is True:
            safe_path = str(self.path.parent)

        if sys.platform == 'darwin':
            subprocess.run(['open', '--', safe_path], check=False)
        elif sys.platform == 'linux2':
            subprocess.run(['gnome-open', '--', safe_path], check=False)
        elif sys.platform == 'win32':
            subprocess.run(['explorer', safe_path], check=False)

    @staticmethod
    def check_if_path(path: Union[str, os.PathLike, Path]) -> bool:
        if isinstance(path, str) and path.strip() == "":
            return False
        if isinstance(path, os.PathLike):
            return True
        try:
            maybe_path = Path(path)
            if maybe_path.exists() is True:
                return True

            if maybe_path.absolute().exists() is True:
                return True
        except (TypeError, ValueError):
            return False
        return False


class PathListWidget(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setLayout(QFormLayout())

    @property
    def layout(self) -> QFormLayout:
        return super().layout()

    def addItems(self, items: Iterable[Union[str, os.PathLike, Path]]):
        for item in items:
            widget = PathButton(item, self)
            self.layout.addRow('▶', widget)


class FontInfoWidget(QWidget):
    attr_names = ("family",
                  "style",
                  "pointSize",
                  "weight",
                  "bold",
                  "italic",
                  "overline",
                  "pixelSize",
                  "strikeOut",
                  "styleHint",
                  "styleName",
                  "underline",
                  "exactMatch",
                  "fixedPitch",
                  "pointSizeF")

    def __init__(self, font: QFont, parent=None):
        super().__init__(parent=parent)
        self.setLayout(QFormLayout())
        self.target_font = font
        self.target_font_info = QFontInfo(self.target_font)
        for attr_name in self.attr_names:
            value = getattr(self.target_font_info, attr_name)()
            widget = QLabel()
            widget.setText(str(value))
            self.layout.addRow(attr_name, widget)

    @property
    def layout(self) -> QFormLayout:
        return super().layout()


class DebugDialog(QScrollArea):
    def __init__(self, title: str, key_text: str, value_data: Any, category: "DebugCategoryBox") -> None:
        super().__init__(parent=None)
        self.content_widget = QWidget()
        self.content_widget.setLayout(QVBoxLayout())
        self.setWindowTitle(title)
        self.setStyleSheet("""QTextEdit {
            background: transparent
            }
            """)
        self.category = category
        self.key_text = key_text
        self.value_data = value_data
        self.value_widget = None

        self.key_text_widget = QTextEdit(self)
        self.key_text_widget.setAlignment(Qt.AlignCenter)
        self.key_text_widget.setReadOnly(True)
        self.key_text_widget.setFrameStyle(QFrame.NoFrame)
        self.key_text_widget.setHtml(self.key_text)
        self.key_text_widget.setSizeAdjustPolicy(QTextEdit.AdjustToContents)
        self.key_text_widget.adjustSize()

        self.key_text_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        self.content_layout.addWidget(self.key_text_widget, 0)

        self.make_line()

        self.value_widget = self.make_value_widget(self.value_data)

        self.content_layout.addWidget(self.value_widget, 1)

        self.content_layout.addStretch()
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.setWidgetResizable(True)
        self.setWidget(self.content_widget)
        self.resize(1000, 400)

    def make_line(self):
        self.line = QFrame(self)
        self.line.setFrameShape(QFrame.HLine)
        self.line.setFrameShadow(QFrame.Sunken)

        self.content_layout.addWidget(self.line, 0)

    def make_value_widget(self, data: Any):

        if isinstance(data, defaultdict):
            data = dict(data)
        if isinstance(data, ListOfDictsResult):
            return data.to_sub_widget(self.content_widget)
        if PathButton.check_if_path(data) is True:
            return PathButton(data, self.content_widget)
        if isinstance(data, QWidget):
            return data

        if isinstance(data, QFont):
            return FontInfoWidget(data, self.content_widget)

        elif isinstance(data, (list, tuple, set, frozenset)):
            if all(PathButton.check_if_path(i) for i in data):
                widget = PathListWidget(self.content_widget)
                widget.addItems(sorted(data))
            else:
                widget = QListWidget(self.content_widget)
                try:
                    widget.addItems(repr(i) for i in sorted(data))
                except TypeError:
                    widget.addItems(repr(i) for i in data)
            return widget

        elif isinstance(data, bool):
            text = str(data).title()
            if data is True:
                icon = AllResourceItems.check_mark_green_image.get_as_pixmap(50, 50)
            elif data is False:
                icon = AllResourceItems.close_cancel_image.get_as_pixmap(50, 50)
            return IconTextLabel(self.content_widget, text, icon)

        elif isinstance(data, dict):
            widget = QWidget(self.content_widget)
            widget.setLayout(QFormLayout())
            for key, value in data.items():
                widget.layout().addRow(repr(key), self.make_value_widget(value))
            return widget

        elif isinstance(data, int):
            widget = QTextEdit(self.content_widget)
            widget.setText(number_to_pretty(data))
            widget.setReadOnly(True)
            widget.setFrameStyle(QFrame.NoFrame)
            return widget

        else:

            if not isinstance(data, (str, int, float)):
                log.debug("value_data has an unset type. (type: %r)", type(data))
            widget = QTextEdit(self.content_widget)
            widget.setAcceptRichText(True)
            widget.setText(str(data))

            widget.setReadOnly(True)
            widget.setFrameStyle(QFrame.NoFrame)
            return widget

    def closeEvent(self, event: QCloseEvent) -> None:
        log.debug("closing %r", self)
        self.category.current_display_dialog = None
        event.accept()
        self.deleteLater()
        return super().closeEvent(event)

    @property
    def content_layout(self) -> QVBoxLayout:
        return self.content_widget.layout()

    def show(self) -> None:
        if self.category.current_display_dialog is not None and self.category.current_display_dialog is not self:
            self.category.current_display_dialog.close()
        self.category.current_display_dialog = self

        move_to_center_of_screen(self, QApplication.instance().primaryScreen())

        return super().show()

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(title={self.windowTitle()!r})"


class ShowAttrButton(QPushButton):

    def __init__(self, attr_name: str, obj: object, parent=None):
        super().__init__(parent=parent)
        self.attr_name = attr_name
        self.obj = obj
        self.category_name = f"Show '{obj.__class__.__name__}'-attribute"
        self.setText(f"Show `{self.attr_name}`")

        self.pressed.connect(self.show_info_box)

    def show_info_box(self):
        title = self.attr_name

        attr_value = getattr(self.obj, self.attr_name)
        if callable(attr_value):
            attr_value = attr_value()

        key_text = f"Attribute <i><b>{self.attr_name!r}</b></i> of object <i><b>{self.obj!r}</b></i> is:"

        dialog = DebugDialog(title=title, key_text=key_text, value_data=attr_value, category=self.parent())
        dialog.show()


class ShowFunctionResultButton(QPushButton):
    def __init__(self, category_name: str, function: Callable, parent=None, **kwargs):
        super().__init__(parent=parent)
        self.category_name = category_name
        self.function = function
        self.kwargs = kwargs
        self._text = self.function.__name__
        if kwargs:
            self._text += " with " + ', '.join(f"{k}=>{shorten_string(repr(v),50,split_on=r'any')}" for k, v in self.kwargs.items())

        self.setText(f"show result for {self._text}")
        self.pressed.connect(self.show_info_box)
        if getattr(self.function, "is_disabled", False) is True:
            self.setEnabled(False)

    @property
    def app(self) -> "AntistasiLogbookApplication":
        return QApplication.instance()

    def show_info_box(self):
        title = f"Result for {self.function.__name__}"
        value = self.function(**self.kwargs)
        key_text = f"Result for <i><b>{self._text}</b></i> is:"

        dialog = DebugDialog(title=title, key_text=key_text, value_data=value, category=self.parent())

        dialog.show()


class DebugCategoryBox(QGroupBox):

    def __init__(self, name: str, layout_class: QVBoxLayout, parent=None):
        super().__init__(parent=parent)
        self.name = name
        self.setTitle(self.name)
        self.setLayout(layout_class())
        self.widgets: dict[str, QWidget] = {}
        self.current_display_dialog: DebugDialog = None

    @ property
    def layout(self) -> QLayout:
        return super().layout()

    def add_widget(self, name: str, widget: QWidget):
        self.layout.addWidget(widget)
        widget.setParent(self)
        self.widgets[name] = widget


class DebugContentWidget(QWidget):

    def __init__(self, parent: Optional[PySide6.QtWidgets.QWidget] = None,) -> None:
        super().__init__(parent=parent)
        self.setLayout(QVBoxLayout())
        self.categories: dict[str, DebugCategoryBox] = {}

    @ property
    def layout(self) -> QVBoxLayout:
        return super().layout()

    def add_category(self, name: str, layout_class: QLayout = QVBoxLayout):
        category = DebugCategoryBox(name=name, layout_class=layout_class)
        self.layout.addWidget(category)
        self.categories[name] = category


class DebugDockWidget(BaseDockWidget):

    def __init__(self, parent: QMainWindow, add_to_menu: QMenu = None):
        super().__init__(parent=parent,
                         title="DEBUG",
                         start_floating=True,
                         start_hidden=True,
                         add_to_menu=add_to_menu,
                         allowed_areas=Qt.BottomDockWidgetArea)
        self.scroll_area = QScrollArea()
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.scroll_area.setWidgetResizable(True)

        self.scroll_area.verticalScrollBar().setSingleStep(self.scroll_area.verticalScrollBar().singleStep() // 4)
        self.content_widget = DebugContentWidget(self)
        self.scroll_area.setWidget(self.content_widget)
        self.setWidget(self.scroll_area)
        self.setMinimumSize(50, 300)
        self.resize(600, 600)
        self.setScreen(QApplication.instance().screens()[0])
        move_to_center_of_screen(self, QApplication.instance().screens()[0])
        if self.app.is_dev is True:
            self.setVisible(True)

    def get_all_buttons(self) -> list[Union[ShowFunctionResultButton, ShowAttrButton]]:
        _out = []
        for cat in self.content_widget.categories.values():
            for button in cat.widgets.values():
                _out.append(button)

        return _out

    def fit_minimum_size_to_buttons(self):
        minimum_width = max(b.sizeHint().width() for b in self.get_all_buttons())
        self.setMinimumWidth(minimum_width)

    def add_widget(self, name: str, category: str, widget: QWidget):
        if category not in self.content_widget.categories:
            self.content_widget.add_category(name=category)

        category_box: DebugCategoryBox = self.content_widget.categories[category]
        category_box.add_widget(name=name, widget=widget)

    def add_show_attr_button(self, attr_name: str, obj: object):

        button = ShowAttrButton(attr_name=attr_name, obj=obj, parent=self)
        self.add_widget(button.text(), button.category_name, button)
        if button.sizeHint().width() > self.minimumWidth():
            self.fit_minimum_size_to_buttons()

    def add_show_func_result_button(self, function: Callable, category_name: str, **kwargs):
        button = ShowFunctionResultButton(category_name=category_name, function=function, **kwargs)
        self.add_widget(button.text(), button.category_name, button)
        self.fit_minimum_size_to_buttons()
        if button.sizeHint().width() > self.minimumWidth():
            self.fit_minimum_size_to_buttons()
# region[Main_Exec]


if __name__ == '__main__':
    pass

# endregion[Main_Exec]
