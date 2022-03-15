"""
WiP.

Soon.
"""

# region [Imports]

# * Standard Library Imports ---------------------------------------------------------------------------->
from typing import TYPE_CHECKING
from pathlib import Path

# * Qt Imports --------------------------------------------------------------------------------------->
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QColorDialog

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


THIS_FILE_DIR = Path(__file__).parent.absolute()
log = get_logger(__name__)

# endregion[Constants]


class BetterColorDialog(QColorDialog):
    default_color = QColor(255, 255, 255, 0)
    current_custom_color_index: int = 0
    max_custom_color_index: int = QColorDialog.customCount()
    _custom_colors: dict[int, QColor] = None

    def __init__(self, initial_color=None, show_alpha: bool = True, parent=None):
        self.initial_color = self._modify_initial_color(initial_color)
        super().__init__(self.initial_color, parent)
        self.show_alpha = show_alpha

    def _modify_initial_color(self, initial_color: QColor) -> QColor:
        if initial_color is None:
            initial_color = QColor(self.default_color)
        if initial_color.alpha() <= 0:
            initial_color.setAlpha(255)

        return initial_color

    @classmethod
    def set_custom_color(cls, color: QColor):
        if color.isValid():
            cls.setCustomColor(cls.current_custom_color_index, color)
            if cls.current_custom_color_index == cls.max_custom_color_index:
                cls.current_custom_color_index = 0
            else:
                cls.current_custom_color_index += 1
            cls._custom_colors = None

    @classmethod
    @property
    def custom_colors(cls) -> dict[int, QColor]:
        if cls._custom_colors is None:
            cls._custom_colors = {i: QColorDialog.customColor(i) for i in range(QColorDialog.customCount())}
        return cls._custom_colors

    @property
    def show_alpha(self) -> bool:
        return QColorDialog.ShowAlphaChannel in self.options()

    @show_alpha.setter
    def show_alpha(self, value: bool):
        self.setOption(QColorDialog.ShowAlphaChannel, value)

    @staticmethod
    def show_dialog(initial_color=None, show_alpha: bool = True):
        dialog = BetterColorDialog(initial_color, show_alpha)
        outcome = dialog.exec()
        current_color = dialog.currentColor()
        if outcome and current_color and current_color.isValid() and current_color is not initial_color:
            BetterColorDialog.set_custom_color(current_color)
            return True, current_color
        return False, current_color
# region[Main_Exec]


if __name__ == '__main__':
    pass

# endregion[Main_Exec]
