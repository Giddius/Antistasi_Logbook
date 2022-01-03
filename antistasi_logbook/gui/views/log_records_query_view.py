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
from PySide6 import (QtCore, QtGui, QtWidgets, Qt3DAnimation, Qt3DCore, Qt3DExtras, Qt3DInput, Qt3DLogic, Qt3DRender, QtAxContainer, QtBluetooth,
                     QtCharts, QtConcurrent, QtDataVisualization, QtDesigner, QtHelp, QtMultimedia, QtMultimediaWidgets, QtNetwork, QtNetworkAuth,
                     QtOpenGL, QtOpenGLWidgets, QtPositioning, QtPrintSupport, QtQml, QtQuick, QtQuickControls2, QtQuickWidgets, QtRemoteObjects,
                     QtScxml, QtSensors, QtSerialPort, QtSql, QtStateMachine, QtSvg, QtSvgWidgets, QtTest, QtUiTools, QtWebChannel, QtWebEngineCore,
                     QtWebEngineQuick, QtWebEngineWidgets, QtWebSockets, QtXml)

from PySide6.QtCore import (QByteArray, QCoreApplication, QDate, QDateTime, QEvent, QLocale, QMetaObject, QModelIndex, QModelRoleData, QMutex,
                            QMutexLocker, QObject, QPoint, QRect, QRecursiveMutex, QRunnable, QSettings, QSize, QThread, QThreadPool, QTime, QUrl,
                            QWaitCondition, QItemSelection, Qt, QAbstractItemModel, QAbstractListModel, QAbstractTableModel, Signal, Slot)

from PySide6.QtGui import (QAction, QBrush, QPainter, QColor, QConicalGradient, QCursor, QFont, QFontDatabase, QFontMetrics, QGradient, QIcon, QImage,
                           QKeySequence, QLinearGradient, QPalette, QPixmap, QRadialGradient, QTransform)

from PySide6.QtWidgets import (QApplication, QDataWidgetMapper, QBoxLayout, QCheckBox, QColorDialog, QColumnView, QComboBox, QDateTimeEdit, QDialogButtonBox,
                               QDockWidget, QDoubleSpinBox, QFontComboBox, QFormLayout, QFrame, QGridLayout, QGroupBox, QHBoxLayout, QHeaderView,
                               QLCDNumber, QLabel, QLayout, QLineEdit, QListView, QListWidget, QMainWindow, QMenu, QMenuBar, QMessageBox,
                               QProgressBar, QProgressDialog, QPushButton, QSizePolicy, QSpacerItem, QSpinBox, QStackedLayout, QStackedWidget,
                               QStatusBar, QStyledItemDelegate, QSystemTrayIcon, QTabWidget, QTableView, QTextEdit, QTimeEdit, QToolBox, QTreeView,
                               QVBoxLayout, QWidget, QAbstractItemDelegate, QItemDelegate, QStyleOptionViewItem, QStyleOptionGroupBox, QAbstractItemView, QAbstractScrollArea, QRadioButton, QFileDialog, QButtonGroup)
from datetime import datetime
import inspect
from antistasi_logbook.gui.resources.antistasi_logbook_resources_accessor import AllResourceItems
# * Gid Imports ----------------------------------------------------------------------------------------->
from gidapptools import get_logger
import pp
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
        self.name = "Log-Records"
        self.icon = AllResourceItems.log_records_tab_icon_image.get_as_icon()
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
        self.header_view.setSizeAdjustPolicy(self.header_view.AdjustToContents)
        self.setSortingEnabled(False)

        return self

    def selectionChanged(self, selected: QItemSelection, deselected: QItemSelection) -> None:
        self.model()._expand = {i.row() for i in selected.indexes()}
        for index in selected.indexes():

            self.dataChanged(index, index)
        for _index in deselected.indexes():

            self.dataChanged(_index, _index)

    def setModel(self, model: PySide6.QtCore.QAbstractItemModel) -> None:
        self.scheduleDelayedItemsLayout()
        super().setModel(model)

    def scheduleDelayedItemsLayout(self) -> None:
        log.debug("running 'scheduleDelayedItemsLayout'")
        self.setEnabled(False)
        return super().scheduleDelayedItemsLayout()

    def executeDelayedItemsLayout(self) -> None:
        log.debug("running 'executeDelayedItemsLayout'")

        super().executeDelayedItemsLayout()

        self.setEnabled(True)

    def doItemsLayout(self, forced: bool = False) -> None:
        if forced is False and self.current_model is not None and self.current_model.is_init is False:
            return
        log.debug("running 'doItemsLayout'")

        super().doItemsLayout()
        # self.header_view.setSectionResizeMode(QHeaderView.ResizeToContents)
        # self.header_view.resizeSections()
        # self.header_view.setSectionResizeMode(QHeaderView.Interactive)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}"


# region[Main_Exec]

if __name__ == '__main__':
    pass

# endregion[Main_Exec]
