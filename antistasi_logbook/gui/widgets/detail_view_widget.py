"""
WiP.

Soon.
"""

# region [Imports]

# * Standard Library Imports ---------------------------------------------------------------------------->
from typing import TYPE_CHECKING, Union, Optional, Iterable, Any
from pathlib import Path

# * Third Party Imports --------------------------------------------------------------------------------->


# * Gid Imports ----------------------------------------------------------------------------------------->
from gidapptools import get_logger
import PySide6
from PySide6 import (QtCore, QtGui, QtWidgets, Qt3DAnimation, Qt3DCore, Qt3DExtras, Qt3DInput, Qt3DLogic, Qt3DRender, QtAxContainer, QtBluetooth,
                     QtCharts, QtConcurrent, QtDataVisualization, QtDesigner, QtHelp, QtMultimedia, QtMultimediaWidgets, QtNetwork, QtNetworkAuth,
                     QtOpenGL, QtOpenGLWidgets, QtPositioning, QtPrintSupport, QtQml, QtQuick, QtQuickControls2, QtQuickWidgets, QtRemoteObjects,
                     QtScxml, QtSensors, QtSerialPort, QtSql, QtStateMachine, QtSvg, QtSvgWidgets, QtTest, QtUiTools, QtWebChannel, QtWebEngineCore,
                     QtWebEngineQuick, QtWebEngineWidgets, QtWebSockets, QtXml)

from PySide6.QtCore import (QByteArray, QCoreApplication, QDate, QDateTime, QEvent, QLocale, QMetaObject, QModelIndex, QModelRoleData, QMutex,
                            QMutexLocker, QObject, QPoint, QRect, QRecursiveMutex, QRunnable, QSettings, QSize, QThread, QThreadPool, QTime, QUrl,
                            QWaitCondition, Qt, QUrl, QAbstractItemModel, QAbstractListModel, QAbstractTableModel, Signal, Slot)

from PySide6.QtGui import (QAction, QBrush, QColor, QConicalGradient, QCursor, QFont, QFontDatabase, QFontMetrics, QGradient, QIcon, QImage,
                           QKeySequence, QDesktopServices, QLinearGradient, QPainter, QPalette, QPixmap, QRadialGradient, QTransform, Qt)

from PySide6.QtWidgets import (QApplication, QBoxLayout, QCheckBox, QColorDialog, QColumnView, QComboBox, QDateTimeEdit, QDialogButtonBox,
                               QDockWidget, QDoubleSpinBox, QFontComboBox, QFormLayout, QFrame, QGridLayout, QGroupBox, QHBoxLayout, QHeaderView,
                               QLCDNumber, QLabel, QLayout, QLineEdit, QListView, QListWidget, QMainWindow, QMenu, QMenuBar, QMessageBox,
                               QProgressBar, QProgressDialog, QPushButton, QSizePolicy, QSpacerItem, QSpinBox, QStackedLayout, QStackedWidget,
                               QStatusBar, QStyledItemDelegate, QSystemTrayIcon, QTabWidget, QTableView, QTextEdit, QTimeEdit, QToolBox, QTreeView,
                               QVBoxLayout, QWidget, QAbstractItemDelegate, QInputDialog, QAbstractItemView, QAbstractScrollArea, QRadioButton, QFileDialog, QListView, QButtonGroup)

from antistasi_logbook.storage.models.models import RecordClass, LogFile, ModLink, Server, LogRecord, LogLevel, GameMap, RemoteStorage, Mod, LogFileAndModJoin
from peewee import Field, IntegrityError
import pyqtgraph as pg
import re
from gidapptools.general_helper.color.color_item import Color
if TYPE_CHECKING:

    # * Third Party Imports --------------------------------------------------------------------------------->
    from antistasi_logbook.records.abstract_record import AbstractRecord

# endregion[Imports]

# region [TODO]


# endregion [TODO]

# region [Logging]


# endregion[Logging]

# region [Constants]

THIS_FILE_DIR = Path(__file__).parent.absolute()
log = get_logger(__name__)
# endregion[Constants]

VIEW_ABLE_ITEMS_TYPE = Union["AbstractRecord", "LogRecord", "LogFile", "Server"]


class ModModel(QAbstractTableModel):
    ace_compat_regex = re.compile(r"ace.*compat", re.IGNORECASE)
    column_names_to_exclude = {"id", "full_path", "mod_hash_short", "mod_hash", "marked", "comments", "link", "mod_dir"}

    def __init__(self, mods: Mod, parent: Optional[PySide6.QtCore.QObject] = None) -> None:
        super().__init__(parent=parent)
        self.mods = sorted(mods, key=lambda x: (x.official is True, x.default is True, self.ace_compat_regex.search(x.name) is not None, "rhs" in x.name.casefold(), "3cb" in x.name.casefold(), "cup" in x.name.casefold()))
        self.columns: tuple[Field] = self.get_columns()

    def get_columns(self) -> tuple[Field]:
        columns = sorted([field for field_name, field in Mod._meta.fields.items() if field_name not in self.column_names_to_exclude], key=lambda x: x.name != "name")

        return tuple(columns)

    def rowCount(self, parent: Union[PySide6.QtCore.QModelIndex, PySide6.QtCore.QPersistentModelIndex] = ...) -> int:
        return len(self.mods)

    def columnCount(self, parent: Union[PySide6.QtCore.QModelIndex, PySide6.QtCore.QPersistentModelIndex] = ...) -> int:
        return len(self.columns)

    def data(self, index: Union[PySide6.QtCore.QModelIndex, PySide6.QtCore.QPersistentModelIndex], role: int = ...) -> Any:
        if not index.isValid():
            return
        if not 0 <= index.row() < len(self.mods):
            return None
        item = self.mods[index.row()]
        column = self.columns[index.column()]
        if role == Qt.DisplayRole:
            return str(item.get_data(column.name))

        if role == Qt.BackgroundRole:
            if item.official is True:
                return Color.get_color_by_name("gray").with_alpha(0.25).qcolor

            if self.ace_compat_regex.search(item.name):
                return Color.get_color_by_name("brown").with_alpha(0.25).qcolor
            if "rhs" in item.name.casefold():
                return Color.get_color_by_name("red").with_alpha(0.25).qcolor
            if "3cb" in item.name.casefold():
                return Color.get_color_by_name("green").with_alpha(0.25).qcolor

            if "zeus" in item.name.casefold():
                return Color.get_color_by_name("blue").with_alpha(0.25).qcolor

            if "cup" in item.name.casefold():
                return Color.get_color_by_name("purple").with_alpha(0.25).qcolor

        if role == Qt.ToolTipRole:
            if item.link:
                return str(item.link)

    def headerData(self, section: int, orientation: PySide6.QtCore.Qt.Orientation, role: int = ...) -> Any:
        if orientation == Qt.Horizontal:
            column = self.columns[section]
            if role == Qt.DisplayRole:
                return column.name

    def add_link(self, index, link):
        item = self.mods[index.row()]
        link_item = ModLink(cleaned_mod_name=item.cleaned_name, link=link)
        try:
            link_item.save()
        except IntegrityError:
            link_item.update()


class ValueLineEdit(QLineEdit):
    style_sheet_data = """
    """

    def __init__(self, text: str = None, parent=None):
        super().__init__(text, parent=parent)
        self.setReadOnly(True)
        self.setAlignment(Qt.AlignCenter)
        self.setProperty("display_only", True)
        self.setStyleSheet(self.style_sheet_data)


class BaseDetailWidget(QWidget):

    def __init__(self, parent: Optional[PySide6.QtWidgets.QWidget] = None) -> None:
        super().__init__(parent=parent)
        self.setLayout(QFormLayout(self))

    @ property
    def layout(self) -> QFormLayout:
        return super().layout()


class ServerDetailWidget(BaseDetailWidget):

    def __init__(self, server: Server, parent: Optional[PySide6.QtWidgets.QWidget] = None) -> None:
        super().__init__(parent=parent)
        self.server = server
        self.name_label: QLabel = None
        self.name_value: ValueLineEdit = None

        self.amount_log_files_label: QLabel = None
        self.amount_log_files_value: QLCDNumber = None

        self.remote_path_label: QLabel = None
        self.remote_path_value: ValueLineEdit = None

        self.player_stats_label: QLabel = None
        self.player_stats_value: pg.PlotWidget = None

    def setup(self):
        self.name_label = QLabel(text="Name")
        self.name_value = ValueLineEdit(self.server.name, parent=self)

        self.layout.addRow(self.name_label, self.name_value)

        self.amount_log_files_label = QLabel(text="Amount Log-Files")
        self.amount_log_files_value = QLCDNumber(3, self)
        self.amount_log_files_value.display(LogFile.select().where(LogFile.server == self.server).count())
        self.layout.addRow(self.amount_log_files_label, self.amount_log_files_value)

        self.remote_path_label = QLabel(text="Remote Path")
        self.remote_path_value = ValueLineEdit(self.server.remote_path.as_posix(), parent=self)

        self.layout.addRow(self.remote_path_label, self.remote_path_value)

        # TODO: Find Faster solution, or only on button press

        # self.player_stats_label = QLabel(text="Players")
        # axis = pg.DateAxisItem()
        # self.player_stats_value = pg.PlotWidget()
        # self.player_stats_value.getPlotItem().setAxisItems({'bottom': axis})
        # self.player_stats_value.getPlotItem().plot(*self.get_player_stats())

        # self.layout.addRow(self.player_stats_label, self.player_stats_value)

    def get_player_stats(self):
        log_files = LogFile.select().where(LogFile.server == self.server)
        all_log_files = {log_file.id: log_file for log_file in LogFile.select()}
        record_class = RecordClass.get(name="PerformanceRecord")
        conc_record_class = record_class.record_class
        x = []
        y = []
        for record in list(LogRecord.select().where((LogRecord.log_file << log_files) & (LogRecord.record_class == record_class)).order_by(LogRecord.recorded_at).dicts()):
            log_file = all_log_files.get(record.get("log_file"))
            item = conc_record_class.from_model_dict(record, log_file=log_file)
            x.append(item.recorded_at.timestamp())
            y.append(item.stats.get("Players"))

        return x, y


class LogFileDetailWidget(BaseDetailWidget):

    def __init__(self, log_file: LogFile, parent: Optional[PySide6.QtWidgets.QWidget] = None) -> None:
        super().__init__(parent=parent)
        self.log_file = log_file

        self.name_label: QLabel = None
        self.name_value: ValueLineEdit = None

        self.server_label: QLabel = None
        self.server_value: ValueLineEdit = None

        self.game_map_label: QLabel = None
        self.game_map_value: ValueLineEdit = None

        self.version_label: QLabel = None
        self.version_value: ValueLineEdit = None

        self.campaign_id_label: QLabel = None
        self.campaign_id_value: ValueLineEdit = None

        self.amount_log_records_label: QLabel = None
        self.amount_log_records_value: ValueLineEdit = None

        self.mods_label: QLabel = None
        self.mods_value: QListView = None

    def setup(self):
        self.name_label = QLabel(text="Name")
        self.name_value = ValueLineEdit(self.log_file.name, parent=self)

        self.layout.addRow(self.name_label, self.name_value)

        self.server_label = QLabel(text="Server")
        self.server_value = ValueLineEdit(text=self.log_file.server.name, parent=self)
        self.layout.addRow(self.server_label, self.server_value)

        self.game_map_label = QLabel("Game Map", parent=self)
        self.game_map_value = ValueLineEdit(text=self.log_file.game_map.full_name, parent=self)
        if self.log_file.game_map.map_image_low_resolution is not None:
            self.game_map_value.setToolTip(f'<b>{self.log_file.game_map.map_image_low_resolution.stem.removesuffix("_thumbnail").replace("_"," ").title()}</b><br><img src="{self.log_file.game_map.map_image_low_resolution.as_posix()}">')

        self.layout.addRow(self.game_map_label, self.game_map_value)

        self.version_label = QLabel("Version", parent=self)
        self.version_value = ValueLineEdit(text=str(self.log_file.version), parent=self)
        self.layout.addRow(self.version_label, self.version_value)

        self.campaign_id_label = QLabel("Campaign ID", parent=self)
        self.campaign_id_value = ValueLineEdit(text=str(self.log_file.campaign_id), parent=self)
        self.layout.addRow(self.campaign_id_label, self.campaign_id_value)

        # self.amount_log_records_label = QLabel("Amount Log-Records", parent=self)
        self.amount_log_records_value = ValueLineEdit(text=str(self.log_file.amount_log_records), parent=self)
        self.layout.addRow("Amount Log-Records", self.amount_log_records_value)

        self.mods_label = QLabel("Mods", parent=self)
        self.mods_value = QListView(self)
        model = ModModel(self.log_file.get_mods())
        self.mods_value.setModel(model)

        self.layout.addRow(self.mods_label, self.mods_value)
        self.mods_value.doubleClicked.connect(self.open_mod_link)
        # self.mods_value.doubleClicked.connect(self.add_mod_link)

    def open_mod_link(self, index):

        item = self.mods_value.model().mods[index.row()]
        if item.default is True or item.official is True:
            return
        if item.link:
            QDesktopServices.openUrl(QUrl(str(item.link)))
        else:
            QDesktopServices.openUrl(QUrl(f'https://www.google.com/search?q={item.cleaned_name}'))

    def add_mod_link(self, index):
        item = self.mods_value.model().mods[index.row()]
        link, valid = QInputDialog.getText(self, f"link for {item!s}", f"link for {item!s}")
        if valid and link:
            self.mods_value.model().add_link(index, link)


# region[Main_Exec]
if __name__ == '__main__':
    pass

# endregion[Main_Exec]
