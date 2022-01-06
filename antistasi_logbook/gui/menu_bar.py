"""
WiP.

Soon.
"""

# region [Imports]

# * Standard Library Imports ---------------------------------------------------------------------------->
from typing import Optional, TYPE_CHECKING, Any, Union
from pathlib import Path

# * Third Party Imports --------------------------------------------------------------------------------->
from antistasi_logbook.gui.resources.antistasi_logbook_resources_accessor import AllResourceItems

# * PyQt5 Imports --------------------------------------------------------------------------------------->
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


# * Gid Imports ----------------------------------------------------------------------------------------->
from gidapptools.gidapptools_qt.basics.menu_bar import BaseMenuBar
from gidapptools import get_logger

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


class LogbookMenuBar(BaseMenuBar):

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent=parent, auto_connect_standard_actions=True)

    @property
    def app(self) -> "AntistasiLogbookApplication":
        return QApplication.instance()

    def setup_menus(self) -> None:
        super().setup_menus()
        self.database_menu = self.add_new_menu("Database", add_before=self.help_menu.menuAction())
        self.single_update_action = self.add_new_action(self.database_menu, "Update Once")
        self.database_menu.addSeparator()

        self.open_settings_window_action = self.add_new_action(self.settings_menu, "Open Settings")

        self.exit_action.setIcon(AllResourceItems.close_cancel_image.get_as_icon())
        self.test_menu = self.add_new_menu("test")
        if self.app.meta_info.is_dev is False:
            self.test_menu.setVisible(False)

        self.folder_action = self.add_new_action(self.help_menu, "folder")
        self.open_credentials_managment_action = self.add_new_action(self.settings_menu, "Credentials Managment")
        self.data_menu = self.add_new_menu("Data", parent_menu=self.view_menu)
        self.show_game_maps_action = self.add_new_action(self.data_menu, "Game Maps")
        self.show_antistasi_function_action = self.add_new_action(self.data_menu, "Antistasi Functions/Files")
        self.show_mods_action = self.add_new_action(self.data_menu, "Mods")


# region[Main_Exec]


if __name__ == '__main__':
    pass

# endregion[Main_Exec]
