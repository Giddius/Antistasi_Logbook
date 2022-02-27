"""
WiP.

Soon.
"""

# region [Imports]

# * Standard Library Imports ---------------------------------------------------------------------------->
from typing import TYPE_CHECKING, Optional, Any
from pathlib import Path

# * Qt Imports --------------------------------------------------------------------------------------->
import PySide6
from PySide6 import (QtCore, QtGui, QtWidgets, Qt3DAnimation, Qt3DCore, Qt3DExtras, Qt3DInput, Qt3DLogic, Qt3DRender, QtAxContainer, QtBluetooth,
                     QtCharts, QtConcurrent, QtDataVisualization, QtDesigner, QtHelp, QtMultimedia, QtMultimediaWidgets, QtNetwork, QtNetworkAuth,
                     QtOpenGL, QtOpenGLWidgets, QtPositioning, QtPrintSupport, QtQml, QtQuick, QtQuickControls2, QtQuickWidgets, QtRemoteObjects,
                     QtScxml, QtSensors, QtSerialPort, QtSql, QtStateMachine, QtSvg, QtSvgWidgets, QtTest, QtUiTools, QtWebChannel, QtWebEngineCore,
                     QtWebEngineQuick, QtWebEngineWidgets, QtWebSockets, QtXml)

from PySide6.QtCore import (QByteArray, QCoreApplication, QDate, QDateTime, QEvent, QLocale, QMetaObject, QModelIndex, QModelRoleData, QMutex,
                            QMutexLocker, QObject, QPoint, QRect, QRecursiveMutex, QRunnable, QSettings, QSize, QThread, QThreadPool, QTime, QUrl,
                            QWaitCondition, Qt, QAbstractItemModel, QAbstractListModel, QAbstractTableModel, Signal, Slot)

from PySide6.QtGui import (QAction, QBrush, QColor, QConicalGradient, QCursor, QFont, QFontDatabase, QFontMetrics, QGradient, QIcon, QImage,
                           QKeySequence, QLinearGradient, QPainter, QPalette, QPixmap, QRadialGradient, QTransform)

from PySide6.QtWidgets import (QApplication, QBoxLayout, QCheckBox, QColorDialog, QColumnView, QComboBox, QDateTimeEdit, QDialogButtonBox,
                               QDockWidget, QDoubleSpinBox, QFontComboBox, QFormLayout, QFrame, QGridLayout, QGroupBox, QHBoxLayout, QHeaderView,
                               QLCDNumber, QLabel, QLayout, QLineEdit, QListView, QListWidget, QMainWindow, QMenu, QMenuBar, QMessageBox,
                               QProgressBar, QProgressDialog, QPushButton, QSizePolicy, QSpacerItem, QSpinBox, QStackedLayout, QStackedWidget,
                               QStatusBar, QStyledItemDelegate, QSystemTrayIcon, QTabWidget, QTableView, QTextEdit, QTimeEdit, QToolBox, QTreeView,
                               QVBoxLayout, QWidget, QAbstractItemDelegate, QAbstractItemView, QAbstractScrollArea, QRadioButton, QFileDialog, QButtonGroup)

from concurrent.futures import Future
# * Gid Imports ----------------------------------------------------------------------------------------->
from gidapptools import get_logger
from peewee import Field
# * Local Imports --------------------------------------------------------------------------------------->
from antistasi_logbook.storage.models.models import GameMap
from antistasi_logbook.gui.models.base_query_data_model import BaseQueryDataModel, ModelContextMenuAction

# * Type-Checking Imports --------------------------------------------------------------------------------->
if TYPE_CHECKING:
    from antistasi_logbook.gui.views.base_query_tree_view import CustomContextMenu

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


class GameMapModel(BaseQueryDataModel):
    strict_exclude_columns = {"map_image_low_resolution", "map_image_high_resolution", "coordinates"}
    avg_player_calculation_finished = Signal(float, object)

    def __init__(self, parent: Optional[QtCore.QObject] = None) -> None:

        super().__init__(GameMap, parent=parent)
        self.filter_item = None
        self.avg_player_calculation_finished.connect(self.show_avg_players)

    def _modify_display_data(self, data: Any, item: GameMap, column: "Field") -> str:
        if column.verbose_name == "Internal Name":
            return getattr(item, column.name)
        return super()._modify_display_data(data, item, column)

    def add_context_menu_actions(self, menu: "CustomContextMenu", index: QModelIndex):
        super().add_context_menu_actions(menu, index)
        item, column = self.get(index)

        if item is None or column is None:
            return
        tell_avg_players_action = ModelContextMenuAction(item, column, index, text="Show Mean Player per Hour", parent=menu)
        tell_avg_players_action.clicked.connect(self.tell_avg_players_per_hour)
        menu.add_action(tell_avg_players_action)

    @Slot(object, object, QModelIndex)
    def tell_avg_players_per_hour(self, item: GameMap, column: Field, index: QModelIndex):
        def show_result(f: Future):
            if f.exception() is not None:
                log.error(f.exception())
                return
            result = f.result()
            self.avg_player_calculation_finished.emit(result, item)

        future: Future = self.app.gui_thread_pool.submit(item.get_avg_players_per_hour)
        future.add_done_callback(show_result)

    def show_avg_players(self, result: float, item: GameMap):
        QMessageBox.information(self.parent(), f"avg players for {item.pretty_name}", str(round(result, 2)) + " players per hour", QMessageBox.Ok)


# region[Main_Exec]
if __name__ == '__main__':
    pass

# endregion[Main_Exec]
