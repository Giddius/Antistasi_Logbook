"""
WiP.

Soon.
"""

# region [Imports]
from typing import TYPE_CHECKING, Union, Optional, Any, Iterable, Callable, Mapping
# * Standard Library Imports ---------------------------------------------------------------------------->
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

from PySide6.QtWidgets import (QApplication, QBoxLayout, QCheckBox, QColorDialog, QColumnView, QComboBox, QDateTimeEdit, QScrollBar, QDialogButtonBox,
                               QDockWidget, QDoubleSpinBox, QFontComboBox, QFormLayout, QFrame, QGridLayout, QGroupBox, QHBoxLayout, QHeaderView,
                               QLCDNumber, QLabel, QLayout, QLineEdit, QListView, QListWidget, QMainWindow, QMenu, QMenuBar, QMessageBox,
                               QProgressBar, QProgressDialog, QPushButton, QSizePolicy, QSpacerItem, QSpinBox, QStackedLayout, QStackedWidget,
                               QStatusBar, QStyledItemDelegate, QSystemTrayIcon, QTabWidget, QTableView, QTextEdit, QTimeEdit, QToolBox, QTreeView,
                               QVBoxLayout, QWidget, QAbstractItemDelegate, QAbstractItemView, QAbstractScrollArea, QRadioButton, QFileDialog, QButtonGroup)

# * Gid Imports ----------------------------------------------------------------------------------------->
from gidapptools import get_logger
if TYPE_CHECKING:
    from antistasi_logbook.gui.models.base_query_data_model import BaseQueryDataModel
    from antistasi_logbook.backend import Backend
    from antistasi_logbook.storage.database import GidSqliteApswDatabase
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


class HeaderContextMenuAction(QAction):
    clicked = Signal(int)

    def __init__(self, section: int, icon: QIcon = None, text: str = None, parent=None):
        super().__init__(**{k: v for k, v in dict(icon=icon, text=text, parent=parent).items() if v is not None})
        self.section = section
        self.triggered.connect(self.on_triggered)

    @Slot()
    def on_triggered(self):
        self.clicked.emit(self.section)


class BaseQueryTreeView(QTreeView):
    initially_hidden_columns: set[str] = set()

    def __init__(self, name: str, icon: QIcon = None) -> None:
        self.icon = icon

        self.name = "" if name is None else name
        if self.icon is None:
            self.icon = getattr(AllResourceItems, f"{self.name.casefold().replace('-','_').replace(' ','_').replace('.','_')}_tab_icon_image").get_as_icon()
        super().__init__()

    @property
    def app(self) -> "AntistasiLogbookApplication":
        return QApplication.instance()

    @property
    def backend(self) -> "Backend":
        return self.app.backend

    @property
    def database(self) -> "GidSqliteApswDatabase":
        return self.backend.database

    @property
    def header_view(self) -> QHeaderView:
        return self.header()

    @property
    def vertical_scrollbar(self) -> Optional[QScrollBar]:
        return self.verticalScrollBar()

    @property
    def model(self) -> "BaseQueryDataModel":
        return super().model()

    def setup(self) -> "BaseQueryTreeView":
        # self.setRootIsDecorated(False)
        self.setSortingEnabled(True)
        self.header_view.setSortIndicatorClearable(True)
        self.setUniformRowHeights(True)
        self.setup_scrollbars()
        self.extra_setup()
        return self

    def setup_headers(self):
        for column_name in self.initially_hidden_columns:
            index = self.model.get_column_index(column_name)
            if index is not None:
                self.header_view.hideSection(index)

        self.header_view.setContextMenuPolicy(Qt.CustomContextMenu)
        self.header_view.customContextMenuRequested.connect(self.handle_header_custom_context_menu)

    def handle_header_custom_context_menu(self, pos: QPoint):
        def get_amount_not_hidden():
            not_hidden = []
            for _column in self.model.columns:
                _idx = self.model.get_column_index(_column.name)
                _hidden = self.header_view.isSectionHidden(_idx)
                if not _hidden:
                    not_hidden.append(_idx)
            return len(not_hidden)

        column_section = self.header_view.logicalIndexAt(pos)
        col = self.model.columns[column_section]

        log.debug("logical index: %r, column from logical index: %r", column_section, col)

        menu = QMenu(self.header_view)

        for column in self.model.columns:
            idx = self.model.get_column_index(column.name)
            hidden = self.header_view.isSectionHidden(idx)
            name = column.verbose_name or column.name

            if hidden is False:
                change_visibility_action = HeaderContextMenuAction(section=idx, icon=AllResourceItems.check_mark_black_image.get_as_icon(), text=name, parent=self.header_view)
                if get_amount_not_hidden() == 1:
                    change_visibility_action.setEnabled(False)
            else:
                change_visibility_action = HeaderContextMenuAction(section=idx, text=name, parent=self.header_view)
            change_visibility_action.clicked.connect(self.toggle_header_section_hidden)
            menu.addAction(change_visibility_action)
        menu.exec(self.header_view.mapToGlobal(pos))

    def toggle_header_section_hidden(self, section: int):
        is_hidden = self.header_view.isSectionHidden(section)
        if is_hidden:
            log.debug("setting section %r with idx %r to visible", self.model.columns[section], section)
            self.header_view.setSectionHidden(section, False)
        else:
            log.debug("setting section %r with idx %r to hidden", self.model.columns[section], section)
            self.header_view.setSectionHidden(section, True)

    def extra_setup(self):
        pass

    def setup_scrollbars(self):
        self.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.setHorizontalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.vertical_scrollbar.setSingleStep(3)

    def pre_set_model(self):
        self.setEnabled(False)
        self._temp_original_sorting_enabled = self.isSortingEnabled()
        if self._temp_original_sorting_enabled is True:
            self.setSortingEnabled(False)

    def post_set_model(self):
        self.setEnabled(True)

        self.setSortingEnabled(self._temp_original_sorting_enabled)

    def setModel(self, model: PySide6.QtCore.QAbstractItemModel) -> None:
        try:
            self.pre_set_model()
            self.reset()
            super().setModel(model)
            self.setup_headers()
        finally:
            self.post_set_model()

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name={self.name!r}, icon={self.icon}, model={self.model!r})"

    def __str__(self) -> str:
        return f"{self.__class__.__name__}(name={self.name!r})"


class LogFilesQueryTreeView(BaseQueryTreeView):
    initially_hidden_columns: set[str] = {"id", "comments"}

    def __init__(self) -> None:
        super().__init__(name="Log-Files")


# region[Main_Exec]

if __name__ == '__main__':
    pass

# endregion[Main_Exec]
