"""
WiP.

Soon.
"""

# region [Imports]

# * Standard Library Imports ---------------------------------------------------------------------------->
from typing import TYPE_CHECKING, Any, Optional
from pathlib import Path

# * Qt Imports --------------------------------------------------------------------------------------->
import PySide6
from PySide6.QtGui import QFont
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QLabel, QWidget, QFormLayout, QApplication

# * Gid Imports ----------------------------------------------------------------------------------------->
from gidapptools import get_logger
from gidapptools.general_helper.enums import MiscEnum
from gidapptools.general_helper.string_helper import StringCase, StringCaseConverter

# * Local Imports --------------------------------------------------------------------------------------->
from antistasi_logbook.gui.widgets.data_view_widget.type_fields import TypeFieldProtocol, get_type_widget

# * Type-Checking Imports --------------------------------------------------------------------------------->
if TYPE_CHECKING:
    from antistasi_logbook.backend import Backend
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


class DataRow:
    def __init__(self, name: str, value: Any, type_widget: type["TypeFieldProtocol"] = MiscEnum.NOTHING, position: int = None) -> None:
        self.name = name
        self.value = value
        self.type_widget = type_widget
        self.position = position
        self._value_widget: QWidget = MiscEnum.NOTHING
        self._label: QLabel = None

    @property
    def label(self) -> str:
        if self._label is None:

            self._label = QLabel('<b>' + StringCaseConverter.convert_to(self.name, StringCase.TITLE) + ':' + '</b>')
        return self._label

    @property
    def value_widget(self) -> Optional[QWidget]:
        if self.type_widget is None or self.type_widget is MiscEnum.NOTHING:
            return
        if self._value_widget is MiscEnum.NOTHING:
            self._value_widget = self.type_widget()
            self._value_widget.set_value(self.value)
        return self._value_widget

    def get_sort_key(self) -> int:
        if self.position in {None, MiscEnum.NOTHING}:
            return 9999999
        return self.position


def wrap_in_tag(text: str, tag: str) -> str:
    return f"<{tag}>{text}</{tag}>"


class TitleLabel(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setAlignment(Qt.AlignCenter)
        self.setProperty("is_title_label", True)
        self.setup()

    def setup(self):
        self._modify_font()

    def _modify_font_point_size(self, old_size: int) -> int:
        return int(old_size * 1.5)

    def _modify_font(self):
        font: QFont = self.font()
        font.setPointSize(self._modify_font_point_size(font.pointSize()))
        self.setFont(font)

    def _modify_text(self, text: str) -> str:
        new_text = text
        new_text = wrap_in_tag(new_text, "b")
        new_text = wrap_in_tag(new_text, "u")
        return new_text

    def setText(self, text: str) -> None:
        text = self._modify_text(text)

        return super().setText(text)


class DataView(QFrame):

    def __init__(self,
                 parent: Optional[QWidget] = None,
                 show_none: bool = False,
                 title: str = None,
                 border: bool = False) -> None:
        super().__init__(parent=parent)
        self._is_built: bool = False
        self.border = border
        self.show_none = show_none
        self.setLayout(QFormLayout())
        self.setup_layout()
        self.setup_border()
        self.title = title
        self.title_label = TitleLabel()
        self.layout.addRow(self.title_label)
        self.title_label.setVisible(False)
        self.rows: dict[str, DataRow] = {}

    def setup_layout(self):
        self.layout.setHorizontalSpacing(50)
        self.layout.setVerticalSpacing(25)

    def setup_border(self):
        if self.border is False:
            self.setFrameShape(QFrame.NoFrame)
        else:
            self.setFrameShape(QFrame.StyledPanel)
            self.setFrameShadow(QFrame.Sunken)
            self.setLineWidth(4)
            self.setMidLineWidth(2)

    def set_title(self, title: str):
        if title in {None, ""}:
            title = None
        self.title = title
        self.rebuild()

    def set_show_none(self, value: bool) -> None:
        old_show_none = self.show_none
        if old_show_none is not value:
            self.show_none = value
            self.rebuild()

    @property
    def layout(self) -> QFormLayout:
        return super().layout()

    @property
    def app(self) -> "AntistasiLogbookApplication":
        return QApplication.instance()

    @property
    def backend(self) -> "Backend":
        return self.app.backend

    def add_row(self, name: str, value: Any, type_widget=MiscEnum.NOTHING, position: int = MiscEnum.NOTHING):
        data_row = DataRow(name=name, value=value, position=position, type_widget=type_widget)
        self.rows[name] = data_row

    def clear(self):
        pass

    def build(self) -> "DataView":
        if self._is_built is False:
            self.rebuild()
        return self

    def rebuild(self):
        self.clear()
        if self.title is not None:
            self.title_label.setText(self.title)
            self.title_label.setVisible(True)
        else:
            self.title_label.setVisible(False)
        for row in sorted(self.rows.values(), key=lambda x: x.get_sort_key()):
            if row.type_widget is MiscEnum.NOTHING:
                row.type_widget = get_type_widget(row.value)
            if row.value_widget is None:
                continue
            self.layout.addRow(row.label, row.value_widget)
            row.value_widget.set_size(self.fontMetrics().height(), self.fontMetrics().height())
            row.position = int(self.layout.getWidgetPosition(row.value_widget)[0])

        self._is_built = True

    def show(self):
        self.app.extra_windows.add_window(self)
        self.rebuild()

        return super().show()

    def closeEvent(self, event: PySide6.QtGui.QCloseEvent) -> None:
        self.app.extra_windows.remove_window(self)
        return super().closeEvent(event)

    def repaint(self):
        self.rebuild()
        self.setup_border()
        super().repaint()
# region[Main_Exec]


if __name__ == '__main__':
    pass

# endregion[Main_Exec]
