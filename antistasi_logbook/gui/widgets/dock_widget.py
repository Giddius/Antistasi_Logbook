"""
WiP.

Soon.
"""

# region [Imports]

# * Standard Library Imports ---------------------------------------------------------------------------->
from typing import TYPE_CHECKING, Union
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
from gidapptools import get_logger
# * Type-Checking Imports --------------------------------------------------------------------------------->
if TYPE_CHECKING:
    from gidapptools.gid_config.interface import GidIniConfig

    from antistasi_logbook.backend import Backend
    from antistasi_logbook.gui.application import AntistasiLogbookApplication
    from antistasi_logbook.gui.main_window import AntistasiLogbookMainWindow

# endregion[Imports]

# region [TODO]


# endregion [TODO]

# region [Logging]


# endregion[Logging]

# region [Constants]

THIS_FILE_DIR = Path(__file__).parent.absolute()
log = get_logger(__name__)
# endregion[Constants]


class BaseDockWidget(QDockWidget):

    def __init__(self,
                 parent: QMainWindow,
                 title: str,
                 start_floating: bool = False,
                 start_hidden: bool = False,
                 allowed_areas: Qt.DockWidgetArea = Qt.AllDockWidgetAreas,
                 features: QDockWidget.DockWidgetFeature = QDockWidget.DockWidgetMovable | QDockWidget.DockWidgetClosable | QDockWidget.DockWidgetFloatable,
                 add_to_menu: QMenu = None):
        super().__init__(parent)
        self.title = title
        self.setWindowTitle(title)
        self.first_shown: bool = False
        self.setHidden(start_hidden)
        self.setFloating(start_floating)
        self.setAllowedAreas(allowed_areas)
        self.setFeatures(features)
        if add_to_menu is not None:
            self._add_to_menu_bar(add_to_menu)

    def _add_to_menu_bar(self, add_to_menu: QMenu):
        view_action = self.toggleViewAction()
        view_action.setText(f"{self.title} Window")
        add_to_menu.addAction(view_action)

    @property
    def app(self) -> "AntistasiLogbookApplication":
        return QApplication.instance()

    @property
    def backend(self) -> "Backend":
        return self.app.backend

    @property
    def config(self) -> "GidIniConfig":
        return self.app.config

    @property
    def main_window(self) -> "AntistasiLogbookMainWindow":
        return self.parentWidget()

    def show_if_first(self):
        if self.first_shown is False:
            self.show()

    def show(self) -> None:
        super().show()
        if self.first_shown is False:
            self.first_shown = True


class QueryWidget(BaseDockWidget):

    def __init__(self, parent: QMainWindow, add_to_menu: QMenu = None, start_floating: bool = False):
        self.pages: dict[str, QWidget] = {}
        super().__init__(parent, title="Query", start_floating=start_floating, add_to_menu=add_to_menu)
        self.setWidget(QStackedWidget(self))
        self.widget.setHidden(True)

    def add_page(self, widget: QWidget, name: str = None):
        if name is None:
            for attr_name in ["name", "title"]:
                if hasattr(widget, attr_name):
                    name = getattr(widget, attr_name)
                    break
        if name is None:
            raise AttributeError(f"missing parameter 'name' for {widget!r}")
        page_index = self.widget.addWidget(widget)
        widget.page_index = page_index
        self.pages[name] = widget
        self.widget.setHidden(False)

    def set_current_index(self, target: Union[str, int, QWidget]):
        if isinstance(target, int):
            index = target
        elif isinstance(target, str):
            index = self.pages[target].page_index

        elif isinstance(target, QWidget):
            index = target.page_index
        self.widget.setCurrentIndex(index)

    @property
    def widget(self) -> QStackedWidget:
        return super().widget()

    def sizeHint(self) -> QSize:
        base_width = 500
        base_height = 400
        try:
            size = self.widget.currentWidget().sizeHint()
            max_width = max([base_width, size.width()])
            max_height = max([base_height, size.height()])
        except AttributeError:
            max_width = base_width
            max_height = base_height
        log.debug("Size for %r: max_width: %r, max_height:%r", self, max_width, max_width)
        return QSize(max_width, max_height)


# region[Main_Exec]
if __name__ == '__main__':
    pass

# endregion[Main_Exec]
