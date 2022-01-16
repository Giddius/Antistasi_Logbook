"""
WiP.

Soon.
"""

# region [Imports]

# * Standard Library Imports ---------------------------------------------------------------------------->
from typing import TYPE_CHECKING
from pathlib import Path
from time import sleep
# * Qt Imports --------------------------------------------------------------------------------------->
import PySide6
from PySide6 import (QtCore, QtGui, QtWidgets, Qt3DAnimation, Qt3DCore, Qt3DExtras, Qt3DInput, Qt3DLogic, Qt3DRender, QtAxContainer, QtBluetooth,
                     QtCharts, QtConcurrent, QtDataVisualization, QtDesigner, QtHelp, QtMultimedia, QtMultimediaWidgets, QtNetwork, QtNetworkAuth,
                     QtOpenGL, QtOpenGLWidgets, QtPositioning, QtPrintSupport, QtQml, QtQuick, QtQuickControls2, QtQuickWidgets, QtRemoteObjects,
                     QtScxml, QtSensors, QtSerialPort, QtSql, QtStateMachine, QtSvg, QtSvgWidgets, QtTest, QtUiTools, QtWebChannel, QtWebEngineCore,
                     QtWebEngineQuick, QtWebEngineWidgets, QtWebSockets, QtXml)

from PySide6.QtCore import (QByteArray, QMargins, QStandardPaths, QItemSelectionModel, QCoreApplication, QDate, QDateTime, QEvent, QLocale, QMetaObject, QModelIndex, QModelRoleData, QMutex,
                            QMutexLocker, QObject, QPoint, QRect, QRecursiveMutex, QRunnable, QSettings, QSize, QThread, QThreadPool, QTime, QUrl,
                            QWaitCondition, Qt, QAbstractItemModel, QAbstractListModel, QAbstractTableModel, Signal, Slot)

from PySide6.QtGui import (QAction, QBrush, QColor, QConicalGradient, QCursor, QScreen, QFont, QFontDatabase, QFontMetrics, QGradient, QIcon, QImage,
                           QKeySequence, QLinearGradient, QPainter, QPalette, QPixmap, QRadialGradient, QTransform)

from PySide6.QtWidgets import (QApplication, QBoxLayout, QCheckBox, QColorDialog, QColumnView, QComboBox, QDateTimeEdit, QDialogButtonBox,
                               QDockWidget, QDoubleSpinBox, QFontComboBox, QFormLayout, QFrame, QGridLayout, QGroupBox, QHBoxLayout, QHeaderView,
                               QLCDNumber, QLabel, QLayout, QLineEdit, QListView, QListWidget, QMainWindow, QMenu, QMenuBar, QMessageBox,
                               QProgressBar, QProgressDialog, QPushButton, QSizePolicy, QSpacerItem, QSpinBox, QStackedLayout, QStackedWidget,
                               QStatusBar, QStyledItemDelegate, QSystemTrayIcon, QTabWidget, QTableView, QTextEdit, QTimeEdit, QToolBox, QTreeView,
                               QVBoxLayout, QWidget, QAbstractItemDelegate, QAbstractItemView, QAbstractScrollArea, QRadioButton, QFileDialog, QButtonGroup)


# * Gid Imports ----------------------------------------------------------------------------------------->
from gidapptools import get_logger

# * Local Imports --------------------------------------------------------------------------------------->
from antistasi_logbook.gui.views.base_query_tree_view import BaseQueryTreeView, CustomContextMenu
from antistasi_logbook.gui.misc import CustomRole
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


class LogRecordsQueryView(BaseQueryTreeView):
    initially_hidden_columns: set[str] = {"id", "comments"}
    about_to_screenshot = Signal()
    screenshot_finished = Signal()

    def __init__(self, parent=None) -> None:
        super().__init__(name="Log-Records", parent=parent)

    def extra_setup(self):
        super().extra_setup()
        self.setSortingEnabled(False)

    def add_free_context_menu_options(self, menu: "CustomContextMenu"):
        super().add_free_context_menu_options(menu)
        copy_as_menu = menu.add_menu("Copy as", menu)
        std_copy_action = QAction("Copy")
        std_copy_action.triggered.connect(self.on_std_copy)
        menu.add_action(std_copy_action)

        screenshot_action = QAction("Screenshot Selection")
        screenshot_action.triggered.connect(self.on_screenshot_selection)
        menu.add_action(screenshot_action)

    def on_std_copy(self):
        rows = self.selectionModel().selectedRows()
        text = '\n'.join([t for t in (self.model.data(i, CustomRole.STD_COPY_DATA) for i in rows) if t is not None])
        clipboard = self.app.clipboard()
        clipboard.setText(text)

    def on_screenshot_selection(self):
        self.about_to_screenshot.emit()

        def check_continous(_rows: list[int]):
            amount = len(rows)
            min_row = min([i.row() for i in _rows])
            max_row = max([i.row() for i in _rows])
            log.debug("amount: %r, min_row: %r, max_row: %r, diff: %r", amount, min_row, max_row, max_row - min_row)
            return (max_row - min_row) == (amount - 1)

        selection: QItemSelectionModel = self.selectionModel()
        rows = selection.selectedRows()
        if check_continous(rows) is False:
            self.screenshot_finished.emit()
            return

        self.temp_screenshot_shower = None
        region = self.visualRegionForSelection(selection.selection())
        bounding_rect = region.boundingRect().normalized()
        selection.clearSelection()
        selection.clear()

        margins = QMargins()
        margins.setTop(bounding_rect.height() * (1 / len(rows)))
        margins.setBottom(bounding_rect.height() * (1 / len(rows)))
        bounding_rect = bounding_rect.marginsAdded(margins)
        pixmap = self.grab(bounding_rect)
        desktop_path = Path(QStandardPaths.standardLocations(QStandardPaths.DesktopLocation)[0])
        log.debug(f"{desktop_path.as_posix()=}")

        pixmap.save(str(desktop_path.joinpath("screenshot.png")), "PNG", 75)

        self.screenshot_finished.emit()

    @ property
    def header_view(self) -> QHeaderView:
        return self.header()

    def pre_set_model(self):
        super().pre_set_model()

    def post_set_model(self):
        super().post_set_model()

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}"


# region[Main_Exec]

if __name__ == '__main__':
    pass

# endregion[Main_Exec]
