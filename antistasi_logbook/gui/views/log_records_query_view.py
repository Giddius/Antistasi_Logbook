"""
WiP.

Soon.
"""

# region [Imports]

# * Standard Library Imports ---------------------------------------------------------------------------->
from typing import TYPE_CHECKING, Optional, Union, Callable
from pathlib import Path
from threading import Lock

# * PyQt5 Imports --------------------------------------------------------------------------------------->
import PySide6
from PySide6.QtGui import QFont, QKeyEvent
from PySide6.QtCore import Qt, QThread, QThreadPool, QRunnable
from PySide6.QtWidgets import QTreeView, QHeaderView, QAbstractItemView, QApplication

# * Gid Imports ----------------------------------------------------------------------------------------->
from gidapptools import get_logger

if TYPE_CHECKING:
    # * Third Party Imports --------------------------------------------------------------------------------->
    from antistasi_logbook.gui.main_window import AntistasiLogbookMainWindow
    from antistasi_logbook.gui.models.log_records_model import LogRecordsModel

# endregion[Imports]

# region [TODO]


# endregion [TODO]

# region [Logging]


# endregion[Logging]

# region [Constants]

THIS_FILE_DIR = Path(__file__).parent.absolute()
log = get_logger(__name__)
# endregion[Constants]


class ResizeWorker(QThread):

    def __init__(self, view: "LogRecordsQueryView", parent: Optional[PySide6.QtCore.QObject] = None) -> None:
        super().__init__(parent=parent)
        self.view = view

    def run(self) -> None:
        self.view.setup_header()


class LogRecordsQueryView(QTreeView):

    def __init__(self, main_window: "AntistasiLogbookMainWindow", parent: Optional[PySide6.QtWidgets.QWidget] = None) -> None:
        super().__init__(parent=parent)
        self.resize_lock = Lock()
        self.main_window = main_window

    @property
    def header_view(self) -> QHeaderView:
        return self.header()

    @property
    def current_model(self) -> Optional["LogRecordsModel"]:
        return self.model()

    def setup(self) -> "LogRecordsQueryView":
        self.setUniformRowHeights(True)

        self.header_view.setSectionResizeMode(QHeaderView.Interactive)
        self.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.setHorizontalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.verticalScrollBar().setSingleStep(3)

        self.setSortingEnabled(False)

        return self

    def setModel(self, model: "LogRecordsModel") -> None:

        super().setModel(model)

        # self.resize_columns()

    def selectionChanged(self, selected: PySide6.QtCore.QItemSelection, deselected: PySide6.QtCore.QItemSelection) -> None:
        self.model()._expand = {i.row() for i in selected.indexes()}
        for index in selected.indexes():

            self.dataChanged(index, index)
        for _index in deselected.indexes():

            self.dataChanged(_index, _index)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}"


# region[Main_Exec]

if __name__ == '__main__':
    pass

# endregion[Main_Exec]
