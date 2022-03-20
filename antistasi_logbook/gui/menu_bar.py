"""
WiP.

Soon.
"""

# region [Imports]

# * Standard Library Imports ---------------------------------------------------------------------------->
from typing import TYPE_CHECKING, Optional
from pathlib import Path
from weakref import WeakSet

# * Qt Imports --------------------------------------------------------------------------------------->
from PySide6.QtGui import QAction
from PySide6.QtCore import Qt, QTimer, Signal, QObject, QTimerEvent
from PySide6.QtWidgets import QStyle, QWidget, QApplication

# * Gid Imports ----------------------------------------------------------------------------------------->
from gidapptools import get_logger
from gidapptools.general_helper.conversion import seconds2human
from gidapptools.general_helper.string_helper import StringCase, StringCaseConverter
from gidapptools.gidapptools_qt.basics.menu_bar import BaseMenuBar

# * Local Imports --------------------------------------------------------------------------------------->
from antistasi_logbook.storage.models.models import Mod, GameMap, Version, LogLevel, BaseModel, RecordClass, ArmaFunction, RecordOrigin, RemoteStorage, ArmaFunctionAuthorPrefix
from antistasi_logbook.gui.resources.antistasi_logbook_resources_accessor import AllResourceItems

# * Type-Checking Imports --------------------------------------------------------------------------------->
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


class DataMenuAction(QAction):
    new_triggered = Signal(object)

    def __init__(self, db_model: BaseModel, parent=None):
        super().__init__(parent=parent)
        self.db_model = db_model

        self.setup()

    def setup(self):
        name = self.db_model.get_meta().table_name

        formated_name = StringCaseConverter.convert_to(name, StringCase.TITLE)
        if formated_name.endswith("s"):
            text = f"{formated_name}es"
        else:
            text = f"{formated_name}s"
        self.setText(text)
        self.triggered.connect(self.on_triggered)

    def on_triggered(self):
        self.new_triggered.emit(self.db_model)

    def __repr__(self) -> str:
        """
        Basic Repr
        !REPLACE!
        """
        return f'{self.__class__.__name__}'


class DataMenuActionGroup(QObject):
    triggered = Signal(object)

    def __init__(self, parent=None) -> None:
        super().__init__(parent=parent)
        self.actions: WeakSet[DataMenuAction] = WeakSet()

    def add_action(self, action: DataMenuAction):
        self.actions.add(action)
        action.new_triggered.connect(self.triggered.emit)

    def __repr__(self) -> str:
        """
        Basic Repr
        !REPLACE!
        """
        return f'{self.__class__.__name__}'


class TimeRemainingAction(QAction):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setEnabled(False)
        self.setText("")
        self.timer_id: int = None
        self.timer_to_watch: QTimer = None

    def start(self, timer: QTimer):
        self.timer_to_watch = timer
        if self.timer_id is None:
            self.timer_id = self.startTimer(1000 * 0.9, Qt.VeryCoarseTimer)

    def stop(self):
        if self.timer_id is not None:
            self.killTimer(self.timer_id)
            self.timer_id = None
        self.setText("")

    def timerEvent(self, event: QTimerEvent) -> None:
        if self.timer_id is not None and event.timerId() == self.timer_id:
            time_remaining = self.timer_to_watch.remainingTime() // 1000
            if time_remaining <= 0:
                text = "updating now!"
            else:
                text = f"updating in {seconds2human(time_remaining, with_year=False)}"

            self.setText(text)

    def __repr__(self) -> str:
        """
        Basic Repr
        !REPLACE!
        """
        return f'{self.__class__.__name__}'


class LogbookMenuBar(BaseMenuBar):
    general_disabled_action_names = frozenset(["show_app_log", "show_errors"])

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent=parent, auto_connect_standard_actions=True)

    @property
    def app(self) -> "AntistasiLogbookApplication":
        return QApplication.instance()

    def setup_extra_menus(self) -> None:
        super().setup_extra_menus()

        self.database_menu = self.add_new_menu("Database", add_before=self.help_menu.menuAction())
        self.single_update_action = self.add_new_action(self.database_menu, "Update Once")
        self.cyclic_update_action = self.add_new_action(self.database_menu, "Start Cyclic Update")
        self.cyclic_update_remaining = TimeRemainingAction()

        self.add_action(self.database_menu, self.cyclic_update_remaining)
        self.database_menu.addSeparator()
        self.reassign_record_classes_action = self.add_new_action(self.database_menu, "Reassign Record-Classes")

        self.open_settings_window_action = self.add_new_action(self.settings_menu, "Open Settings")

        self.exit_action.setIcon(AllResourceItems.close_cancel_image.get_as_icon())

        self.show_folder_action = self.add_new_action(self.help_menu, "Show Folder", add_before=self.help_separator, icon=self.style().standardIcon(QStyle.SP_DirIcon))

        self.show_app_log_action = self.add_new_action(self.help_menu, "Show App Log", add_before=self.help_separator)
        self.show_errors_action = self.add_new_action(self.help_menu, "Show Errors", add_before=self.help_separator, icon=AllResourceItems.error_symbol_image.get_as_icon())
        self.open_credentials_managment_action = self.add_new_action(self.settings_menu, "Credentials Managment")

        self.data_menu = self.add_new_menu("Data", parent_menu=self.view_menu)
        self.show_game_maps_action = self.add_action(self.data_menu, DataMenuAction(GameMap, self.data_menu))
        self.show_arma_function_action = self.add_action(self.data_menu, DataMenuAction(ArmaFunction, self.data_menu))
        self.show_arma_function_author_prefix_action = self.add_action(self.data_menu, DataMenuAction(ArmaFunctionAuthorPrefix, self.data_menu))
        self.show_mods_action = self.add_action(self.data_menu, DataMenuAction(Mod, self.data_menu))
        self.show_origins_action = self.add_action(self.data_menu, DataMenuAction(RecordOrigin, self.data_menu))
        self.show_versions_action = self.add_action(self.data_menu, DataMenuAction(Version, self.data_menu))
        self.show_log_level_action = self.add_action(self.data_menu, DataMenuAction(LogLevel, self.data_menu))
        self.show_remote_storage_action = self.add_action(self.data_menu, DataMenuAction(RemoteStorage, self.data_menu))
        self.show_record_classes_action = self.add_action(self.data_menu, DataMenuAction(RecordClass, self.data_menu))

        self.data_menu_actions_group = DataMenuActionGroup(self.data_menu)
        self.data_menu_actions_group.add_action(self.show_game_maps_action)
        self.data_menu_actions_group.add_action(self.show_arma_function_action)
        self.data_menu_actions_group.add_action(self.show_arma_function_author_prefix_action)
        self.data_menu_actions_group.add_action(self.show_mods_action)
        self.data_menu_actions_group.add_action(self.show_origins_action)
        self.data_menu_actions_group.add_action(self.show_versions_action)
        self.data_menu_actions_group.add_action(self.show_log_level_action)
        self.data_menu_actions_group.add_action(self.show_remote_storage_action)
        self.data_menu_actions_group.add_action(self.show_record_classes_action)
# region[Main_Exec]


if __name__ == '__main__':
    pass

# endregion[Main_Exec]
