"""
WiP.

Soon.
"""

# region [Imports]

# * Standard Library Imports ---------------------------------------------------------------------------->
from pathlib import Path

# * Third Party Imports --------------------------------------------------------------------------------->
from antistasi_logbook.gui.resources.antistasi_logbook_resources_accessor import AllResourceItems

# * PyQt5 Imports --------------------------------------------------------------------------------------->
import PySide6
from PySide6 import QtCore
from PySide6.QtGui import QIcon
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QTreeView, QHeaderView, QAbstractScrollArea

# * Gid Imports ----------------------------------------------------------------------------------------->
from gidapptools import get_logger

# endregion[Imports]

# region [TODO]


# endregion [TODO]

# region [Logging]


# endregion[Logging]

# region [Constants]

THIS_FILE_DIR = Path(__file__).parent.absolute()
log = get_logger(__name__)
# endregion[Constants]


class BaseQueryTreeView(QTreeView):

    def __init__(self, name: str, icon: QIcon = None) -> None:
        self.icon = icon

        self.name = "" if name is None else name
        if self.icon is None:
            self.icon = getattr(AllResourceItems, f"{self.name.casefold().replace('-','_').replace(' ','_').replace('.','_')}_tab_icon_image").get_as_icon()
        super().__init__()

    @property
    def header_view(self) -> QHeaderView:
        return self.header()

    def setup(self) -> "BaseQueryTreeView":
        self.header_view.setStretchLastSection(False)
        self.header_view.setSizeAdjustPolicy(QAbstractScrollArea.SizeAdjustPolicy.AdjustToContents)
        self.header_view.setSectionResizeMode(QHeaderView.ResizeToContents)
        # self.header_view.setCascadingSectionResizes(F)
        self.setSortingEnabled(True)
        self.setTextElideMode(Qt.ElideNone)
        self.setWordWrap(False)
        self.setAlternatingRowColors(True)
        self.setSizeAdjustPolicy(QAbstractScrollArea.SizeAdjustPolicy.AdjustToContents)

        return self

    def adjustSize(self) -> None:
        self.header_view.setStretchLastSection(False)
        self.header_view.setSizeAdjustPolicy(QAbstractScrollArea.SizeAdjustPolicy.AdjustToContents)
        self.header_view.setSectionResizeMode(QHeaderView.ResizeToContents)

        self.header_view.adjustSize()
        self.header_view.resizeSections()
        self.header_view.setSectionResizeMode(QHeaderView.Interactive)
        super().adjustSize()

    def setModel(self, model: PySide6.QtCore.QAbstractItemModel) -> None:
        super().setModel(model)

    def reset(self) -> None:
        log.debug("reseting %s", self)
        return super().reset()

    # def keyPressEvent(self, event: PySide6.QtGui.QKeyEvent) -> None:
    #     if event.key() == Qt.Key_Alt:
    #         log.debug("alt_key was pressed in %r, event.key()=%r", self, event.key())
    #         self.verticalScrollBar().setSingleStep(30)
    #     return super().keyPressEvent(event)

    # def keyReleaseEvent(self, event: PySide6.QtGui.QKeyEvent) -> None:
    #     if event.key() == Qt.Key_Alt:
    #         log.debug("alt_key was rleased in %r, event.key()=%r", self, event.key())
    #         self.verticalScrollBar().setSingleStep(3)
    #     return super().keyReleaseEvent(event)

    def event(self, event: QtCore.QEvent) -> bool:
        # log.debug("%s received event %r", self, event.type().name)
        return super().event(event)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name={self.name!r}, icon={self.icon}, model={self.model()!r})"

    def __str__(self) -> str:
        return f"{self.__class__.__name__}(name={self.name!r})"


class ServerQueryTreeView(BaseQueryTreeView):

    def __init__(self) -> None:
        super().__init__(name="Server")


class LogFilesQueryTreeView(BaseQueryTreeView):
    def __init__(self) -> None:
        super().__init__(name="Log-Files")


# region[Main_Exec]

if __name__ == '__main__':
    pass

# endregion[Main_Exec]
