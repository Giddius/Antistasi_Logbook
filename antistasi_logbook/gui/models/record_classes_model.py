"""
WiP.

Soon.
"""

# region [Imports]

# * Standard Library Imports ---------------------------------------------------------------------------->
from typing import TYPE_CHECKING, Optional
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


# * Gid Imports ----------------------------------------------------------------------------------------->
from gidapptools import get_logger
from antistasi_logbook.gui.widgets.better_color_dialog import BetterColorDialog
from peewee import Field, Query, IntegerField
# * Local Imports --------------------------------------------------------------------------------------->
from antistasi_logbook.storage.models.models import RecordClass, BaseModel
from antistasi_logbook.storage.models.custom_fields import FakeField
from antistasi_logbook.gui.models.base_query_data_model import BaseQueryDataModel

# * Type-Checking Imports --------------------------------------------------------------------------------->
if TYPE_CHECKING:
    pass

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


class RecordClassesModel(BaseQueryDataModel):
    extra_columns = {FakeField(name="record_family", verbose_name="Record Family"), FakeField(name="specificity", verbose_name="Specificity")}
    color_config_name = "record"
    _item_size_by_column_name: dict[str, int] = {"id": 30, "marked": 60, "record_family": 200, "specificity": 100, "name": 250}

    def __init__(self, parent: Optional[QtCore.QObject] = None) -> None:

        super().__init__(RecordClass, parent=parent)
        self.filter_item = None

    @Slot(object, object, QModelIndex)
    def change_color(self, item: BaseModel, column: Field, index: QModelIndex):

        accepted, color = BetterColorDialog.show_dialog(self.color_config.get(self.color_config_name, item.name, default=QColor(255, 255, 255, 0)), True)
        if accepted:
            log.debug("custom color count: %r", QColorDialog.customCount())
            log.debug("custom colors: %r", [(QColorDialog.customColor(i), QColorDialog.customColor(i).name()) for i in range(QColorDialog.customCount())])

            item.record_class.set_background_color(color)
            try:
                del item.background_color
            except AttributeError:
                pass


# region[Main_Exec]
if __name__ == '__main__':
    pass

# endregion[Main_Exec]
