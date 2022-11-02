"""
WiP.

Soon.
"""

# region [Imports]


from time import time, sleep

from pathlib import Path

from typing import TYPE_CHECKING, Union, Callable, Iterable, Optional, Mapping, Any, IO, TextIO, BinaryIO, Hashable, Generator, Literal, TypeVar, TypedDict, AnyStr


from PySide6.QtCore import (QSize, Qt)


from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QToolBar)

if TYPE_CHECKING:
    from antistasi_logbook.storage.models.models import LogFile
    from antistasi_logbook.gui.views.log_files_query_view import LogFilesQueryTreeView
    from antistasi_logbook.gui.models.base_query_data_model import BaseQueryDataModel
    from antistasi_logbook.gui.application import AntistasiLogbookApplication

# endregion[Imports]

# region [TODO]


# endregion [TODO]

# region [Logging]


# endregion[Logging]

# region [Constants]

THIS_FILE_DIR = Path(__file__).parent.absolute()

# endregion[Constants]


class BaseToolBar(QToolBar):

    def __init__(self, parent: Union[QMainWindow, QWidget] = None, title: str = None) -> None:
        super().__init__(*[i for i in (parent, title) if i])
        self.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        self.setOrientation(Qt.Horizontal)
        self.setMovable(False)
        self.setFloatable(False)
        self.setAllowedAreas(Qt.TopToolBarArea)
        self.setIconSize(QSize(35, 35))
        self.setMinimumHeight(85)
        self.setup_actions()

    def setup_actions(self):
        self.addSeparator()

    @property
    def app(self) -> "AntistasiLogbookApplication":
        return QApplication.instance()

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
