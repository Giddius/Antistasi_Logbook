"""
WiP.

Soon.
"""

# region [Imports]

# * Standard Library Imports ---------------------------------------------------------------------------->
import queue
from typing import TYPE_CHECKING, Any, Union, Callable, Optional
from pathlib import Path
from functools import partial
from threading import Event

# * Third Party Imports --------------------------------------------------------------------------------->
from peewee import Field, Query
from antistasi_logbook.storage.models.models import BaseModel
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
                            QWaitCondition, Qt, QAbstractItemModel, QAbstractListModel, QAbstractTableModel, Signal, QPersistentModelIndex, Slot)

from PySide6.QtGui import (QAction, QBrush, QColor, QConicalGradient, QCursor, QFont, QFontDatabase, QFontMetrics, QGradient, QIcon, QImage,
                           QKeySequence, QLinearGradient, QPainter, QPalette, QPixmap, QRadialGradient, QTransform)

from PySide6.QtWidgets import (QApplication, QBoxLayout, QCheckBox, QColorDialog, QColumnView, QComboBox, QDateTimeEdit, QDialogButtonBox,
                               QDockWidget, QDoubleSpinBox, QFontComboBox, QFormLayout, QFrame, QGridLayout, QGroupBox, QHBoxLayout, QHeaderView,
                               QLCDNumber, QLabel, QLayout, QLineEdit, QListView, QListWidget, QMainWindow, QMenu, QMenuBar, QMessageBox,
                               QProgressBar, QProgressDialog, QPushButton, QSizePolicy, QSpacerItem, QSpinBox, QStackedLayout, QStackedWidget,
                               QStatusBar, QStyledItemDelegate, QSystemTrayIcon, QTabWidget, QTableView, QTextEdit, QTimeEdit, QToolBox, QTreeView,
                               QVBoxLayout, QWidget, QAbstractItemDelegate, QAbstractItemView, QAbstractScrollArea, QRadioButton, QFileDialog, QButtonGroup)

from natsort import natsorted
from gidapptools import get_logger
if TYPE_CHECKING:
    # * Third Party Imports --------------------------------------------------------------------------------->
    from antistasi_logbook.backend import Backend
    from antistasi_logbook.records.abstract_record import AbstractRecord
    from antistasi_logbook.gui.widgets.data_tool_widget import BaseDataToolWidget, BaseDataToolPage

    from antistasi_logbook.storage.database import GidSqliteApswDatabase
    from antistasi_logbook.gui.application import AntistasiLogbookApplication
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
INDEX_TYPE = Union[QModelIndex, QPersistentModelIndex]

DATA_ROLE_MAP_TYPE = dict[Union[Qt.ItemDataRole, int], Callable[[INDEX_TYPE], Any]]

HEADER_DATA_ROLE_MAP_TYPE = dict[Union[Qt.ItemDataRole, int], Callable[[int, Qt.Orientation], Any]]


class BaseQueryDataModel(QAbstractTableModel):
    extra_columns = set()
    strict_exclude_columns = set()

    bool_images = {True: AllResourceItems.check_mark_green_image.get_as_icon(),
                   False: AllResourceItems.close_black_image.get_as_icon()}

    def __init__(self, db_model: "BaseModel", parent: Optional[QtCore.QObject] = None) -> None:
        self.data_role_table: DATA_ROLE_MAP_TYPE = {Qt.DisplayRole: self._get_display_data,
                                                    Qt.ToolTipRole: self._get_tool_tip_data,
                                                    Qt.TextAlignmentRole: self._get_text_alignment_data,
                                                    Qt.DecorationRole: self._get_decoration_data,
                                                    # Qt.ForegroundRole: self._get_foreground_data,
                                                    # Qt.BackgroundRole: self._get_background_data,
                                                    # Qt.FontRole: self._get_font_data,
                                                    # Qt.EditRole: self._get_edit_data,
                                                    # Qt.InitialSortOrderRole: self._get_initial_sort_order_data,
                                                    # Qt.SizeHintRole: self._get_size_hint_data,
                                                    # Qt.StatusTipRole: self._get_status_tip_data,
                                                    # Qt.WhatsThisRole: self._get_whats_this_data,
                                                    # Qt.CheckStateRole: self._get_check_state_data,
                                                    # Qt.AccessibleTextRole: self._get_accessible_text_data,
                                                    # Qt.DisplayPropertyRole: self._get_display_property_data,
                                                    # Qt.ToolTipPropertyRole: self._get_tool_tip_property_data,
                                                    # Qt.StatusTipPropertyRole: self._get_status_tip_property_data,
                                                    # Qt.WhatsThisPropertyRole: self._get_whats_this_property_data,
                                                    # Qt.DecorationPropertyRole: self._get_decoration_property_data,
                                                    # Qt.AccessibleDescriptionRole: self._get_accessible_description_data,

                                                    }

        self.header_data_role_table: HEADER_DATA_ROLE_MAP_TYPE = {Qt.DisplayRole: self._get_display_header_data,
                                                                  #   Qt.ToolTipRole: self._get_tool_tip_header_data,
                                                                  #   Qt.ForegroundRole: self._get_foreground_header_data,
                                                                  #   Qt.BackgroundRole: self._get_background_header_data,
                                                                  #   Qt.FontRole: self._get_font_header_data,
                                                                  #   Qt.EditRole: self._get_edit_header_data,
                                                                  #   Qt.InitialSortOrderRole: self._get_initial_sort_order_header_data,
                                                                  #   Qt.UserRole: self._get_user_header_data,
                                                                  #   Qt.SizeHintRole: self._get_size_hint_header_data,
                                                                  #   Qt.StatusTipRole: self._get_status_tip_header_data,
                                                                  #   Qt.WhatsThisRole: self._get_whats_this_header_data,
                                                                  #   Qt.DecorationRole: self._get_decoration_header_data,
                                                                  #   Qt.CheckStateRole: self._get_check_state_header_data,
                                                                  #   Qt.TextAlignmentRole: self._get_text_alignment_header_data,
                                                                  #   Qt.AccessibleTextRole: self._get_accessible_text_header_data,
                                                                  #   Qt.DisplayPropertyRole: self._get_display_property_header_data,
                                                                  #   Qt.ToolTipPropertyRole: self._get_tool_tip_property_header_data,
                                                                  #   Qt.StatusTipPropertyRole: self._get_status_tip_property_header_data,
                                                                  #   Qt.WhatsThisPropertyRole: self._get_whats_this_property_header_data,
                                                                  #   Qt.DecorationPropertyRole: self._get_decoration_property_header_data,
                                                                  #   Qt.AccessibleDescriptionRole: self._get_accessible_description_header_data
                                                                  }

        self.db_model = db_model
        self.ordered_by = (self.db_model.id,)
        self.content_items: list[Union["BaseModel", "AbstractRecord"]] = None
        self.columns: tuple[Field] = tuple(c for c in list(self.db_model.get_meta().sorted_fields) + list(self.extra_columns) if c.name not in self.strict_exclude_columns)
        self.data_tool: "BaseDataToolWidget" = None
        self.original_sort_order: tuple[int] = tuple()

        super().__init__(parent=parent)

    @property
    def app(self) -> "AntistasiLogbookApplication":
        return QApplication.instance()

    @property
    def backend(self) -> "Backend":
        return self.app.backend

    @property
    def database(self) -> "GidSqliteApswDatabase":
        return self.backend.database

    def modify_index(self, index: INDEX_TYPE) -> INDEX_TYPE:
        index.row_item = self.content_items[index.row()]
        index.column_item = self.columns[index.column()]
        return index

    def get_query(self) -> "Query":
        return self.db_model.select().order_by(self.ordered_by)

    def get_content(self) -> "BaseQueryDataModel":
        """
        [summary]

        Overwrite in subclasses!

        Returns:
            [type]: [description]
        """
        return self

    def get_columns(self) -> "BaseQueryDataModel":
        """
        [summary]

        Overwrite in subclasses!

        Returns:
            [type]: [description]
        """
        self.columns = tuple(c for c in list(self.db_model.get_meta().sorted_fields) + list(self.extra_columns) if c.name not in self.strict_exclude_columns)
        return self

    def get_column_index(self, column: Union[str, Field]) -> Optional[int]:

        if isinstance(column, str):
            try:
                return [idx for idx, c in enumerate(self.columns) if c.name == column][0]
            except IndexError:
                return None
        return list(self.columns).index(column)

    @profile
    def on_display_data_bool(self, role: int, item: "BaseModel", column: "Field", value: bool) -> str:
        if role == Qt.DisplayRole:
            if column.name == "marked":
                return ""
            return "Yes" if value is True else "No"
        if role == Qt.DecorationRole:
            if column.name == "marked":
                return self.bool_images[True] if value is True else None

            return self.bool_images[value]

    @profile
    def on_display_data_none(self, role: int, item: "BaseModel", column: "Field") -> str:
        if role == Qt.DisplayRole:
            return '-'

    def _modify_display_data(self, data: Any) -> str:
        return str(data)

    @profile
    def columnCount(self, parent: Union[PySide6.QtCore.QModelIndex, PySide6.QtCore.QPersistentModelIndex] = None) -> int:
        if self.columns is None:
            return 0
        return len(self.columns)

    @profile
    def rowCount(self, parent: Union[PySide6.QtCore.QModelIndex, PySide6.QtCore.QPersistentModelIndex] = None) -> int:
        if self.content_items is None:
            return 0
        return len(self.content_items)

    @profile
    def data(self, index: INDEX_TYPE, role: int = None) -> Any:
        if not index.isValid():
            return
        if not 0 <= index.row() < len(self.content_items):
            return None
        if role not in self.data_role_table:
            return
        if role is not None:
            handler = self.data_role_table.get(role, None)
            if handler is not None:
                return handler(index=self.modify_index(index))

    @profile
    def _get_display_data(self, index: INDEX_TYPE) -> Any:
        data = index.row_item.get_data(index.column_item.name)
        return self._modify_display_data(data)

    def _get_foreground_data(self, index: INDEX_TYPE) -> Any:
        pass

    def _get_background_data(self, index: INDEX_TYPE) -> Any:
        pass

    def _get_font_data(self, index: INDEX_TYPE) -> Any:
        pass

    @profile
    def _get_tool_tip_data(self, index: INDEX_TYPE) -> Any:
        return index.column_item.help_text

    def _get_edit_data(self, index: INDEX_TYPE) -> Any:
        pass

    def _get_user_data(self, index: INDEX_TYPE) -> Any:
        pass

    def _get_size_hint_data(self, index: INDEX_TYPE) -> Any:
        pass

    @profile
    def _get_decoration_data(self, index: INDEX_TYPE) -> Any:

        data = getattr(index.row_item, index.column_item.name)
        if data is None:
            return self.on_display_data_none(role=Qt.DecorationRole, item=index.row_item, column=index.column_item)
        if isinstance(data, bool):
            return self.on_display_data_bool(role=Qt.DecorationRole, item=index.row_item, column=index.column_item, value=data)

    def _get_status_tip_data(self, index: INDEX_TYPE) -> Any:
        pass

    def _get_whats_this_data(self, index: INDEX_TYPE) -> Any:
        pass

    def _get_check_state_data(self, index: INDEX_TYPE) -> Any:
        pass

    @profile
    def _get_text_alignment_data(self, index: INDEX_TYPE) -> Any:
        return Qt.AlignVCenter | Qt.AlignLeft

    def _get_accessible_text_data(self, index: INDEX_TYPE) -> Any:
        pass

    def _get_display_property_data(self, index: INDEX_TYPE) -> Any:
        pass

    def _get_tool_tip_property_data(self, index: INDEX_TYPE) -> Any:
        pass

    def _get_decoration_property_data(self, index: INDEX_TYPE) -> Any:
        pass

    def _get_status_tip_property_data(self, index: INDEX_TYPE) -> Any:
        pass

    def _get_whats_this_property_data(self, index: INDEX_TYPE) -> Any:
        pass

    def _get_accessible_description_data(self, index: INDEX_TYPE) -> Any:
        pass

    @profile
    def headerData(self, section: int, orientation: Qt.Orientation, role: int = None) -> Any:
        if role not in self.header_data_role_table:
            return
        if role is not None:
            handler = self.header_data_role_table.get(role, None)
            if handler is not None:
                return handler(section, orientation)

    @profile
    def _get_display_header_data(self, section: int, orientation: Qt.Orientation) -> Any:
        if orientation == Qt.Horizontal:
            _out = self.columns[section].verbose_name
            if _out is None:
                _out = self.columns[section].name
            return _out

    def _get_foreground_header_data(self, section: int, orientation: Qt.Orientation) -> Any:
        pass

    def _get_background_header_data(self, section: int, orientation: Qt.Orientation) -> Any:
        pass

    def _get_font_header_data(self, section: int, orientation: Qt.Orientation) -> Any:
        pass

    @profile
    def _get_tool_tip_header_data(self, section: int, orientation: Qt.Orientation) -> Any:
        if orientation == Qt.Horizontal:
            return self.columns[section].help_text

    def _get_edit_header_data(self, section: int, orientation: Qt.Orientation) -> Any:
        pass

    def _get_initial_sort_order_header_data(self, section: int, orientation: Qt.Orientation) -> Any:
        pass

    def _get_user_header_data(self, section: int, orientation: Qt.Orientation) -> Any:
        pass

    def _get_size_hint_header_data(self, section: int, orientation: Qt.Orientation) -> Any:
        pass

    def _get_decoration_header_data(self, section: int, orientation: Qt.Orientation) -> Any:
        pass

    def _get_status_tip_header_data(self, section: int, orientation: Qt.Orientation) -> Any:
        pass

    def _get_whats_this_header_data(self, section: int, orientation: Qt.Orientation) -> Any:
        pass

    def _get_check_state_header_data(self, section: int, orientation: Qt.Orientation) -> Any:
        pass

    def _get_text_alignment_header_data(self, section: int, orientation: Qt.Orientation) -> Any:
        pass

    def _get_accessible_text_header_data(self, section: int, orientation: Qt.Orientation) -> Any:
        pass

    def _get_display_property_header_data(self, section: int, orientation: Qt.Orientation) -> Any:
        pass

    def _get_tool_tip_property_header_data(self, section: int, orientation: Qt.Orientation) -> Any:
        pass

    def _get_decoration_property_header_data(self, section: int, orientation: Qt.Orientation) -> Any:
        pass

    def _get_status_tip_property_header_data(self, section: int, orientation: Qt.Orientation) -> Any:
        pass

    def _get_whats_this_property_header_data(self, section: int, orientation: Qt.Orientation) -> Any:
        pass

    def _get_accessible_description_header_data(self, section: int, orientation: Qt.Orientation) -> Any:
        pass

    @profile
    def sort(self, column: int, order: PySide6.QtCore.Qt.SortOrder = None) -> None:

        self.layoutAboutToBeChanged.emit()

        if self.columns is None or self.content_items is None:
            return
        new_content = list(self.content_items)
        if column < 0:
            if self.original_sort_order:
                _helper_dict = {i.id: i for i in self.content_items}
                new_content = [_helper_dict.get(i) for i in self.original_sort_order]
        else:
            _column = self.columns[column]

            if order == Qt.AscendingOrder:
                reverse = False
            elif order == Qt.DescendingOrder:
                reverse = True
            try:
                new_content = natsorted(list(self.content_items), key=lambda x: x.get_data(_column.name), reverse=reverse)
            except TypeError:
                new_content = sorted(list(self.content_items), key=lambda x: x.get_data(_column.name), reverse=reverse)

        self.content_items = tuple(new_content)

        self.layoutChanged.emit()

    def refresh(self) -> "BaseQueryDataModel":
        self.beginResetModel()
        self.get_columns().get_content()
        self.endResetModel()

        return self

    def refresh_items(self):
        new_items = []
        with self.database:
            for item in self.content_items:
                new_item = self.db_model.get_by_id(item.id)
                new_items.append(new_item)
        self.content_items = tuple(new_items)
        self.dataChanged.emit(self.index(0, 0, QModelIndex()), self.index(self.rowCount(), self.columnCount(), QModelIndex()))

    def refresh_item(self, index: "INDEX_TYPE"):
        item = self.content_items[index.row()]
        with self.database:
            new_item = self.db_model.get_by_id(item.id)
        self.content_items = tuple([new_item if i is item else i for i in self.content_items])
        self.dataChanged.emit(self.index(index.row(), 0, QModelIndex()), self.index(index.row(), self.columnCount(), QModelIndex()))

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(backend={self.backend!r}, db_model={self.db_model!r}, parent={self.parent()!r})"
# region[Main_Exec]


if __name__ == '__main__':
    pass

# endregion[Main_Exec]
