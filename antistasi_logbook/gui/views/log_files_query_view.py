"""
WiP.

Soon.
"""

# region [Imports]

# * Standard Library Imports ---------------------------------------------------------------------------->
from typing import TYPE_CHECKING, TextIO
from pathlib import Path
from datetime import datetime, timezone, timedelta

# * Qt Imports --------------------------------------------------------------------------------------->
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QToolBar, QFileDialog, QErrorMessage, QMessageBox
import peewee
# * Gid Imports ----------------------------------------------------------------------------------------->
from gidapptools import get_logger

# * Local Imports --------------------------------------------------------------------------------------->
from antistasi_logbook.gui.widgets.tool_bars import LogFileToolBar
from antistasi_logbook.gui.views.base_query_tree_view import BaseQueryTreeView
from antistasi_logbook.storage.models.models import Server, LogFile
from antistasi_logbook.parsing.meta_log_finder import MetaFinder
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


class LogFilesQueryTreeView(BaseQueryTreeView):
    initially_hidden_columns: set[str] = {"id", "comments"}

    def __init__(self) -> None:
        super().__init__(name="Log-Files")
        self.item_size_by_column_name = self._item_size_by_column_name.copy() | {"name": 300,
                                                                                 "modified_at": 175,
                                                                                 "created_at": 175,
                                                                                 "size": 75,
                                                                                 "version": 125,
                                                                                 "game_map": 125,
                                                                                 "is_new_campaign": 100,
                                                                                 "campaign_id": 100,
                                                                                 "server": 100,
                                                                                 "amount_warnings": 75,
                                                                                 "amount_errors": 75,
                                                                                 "amount_log_records": 75,
                                                                                 "utc_offset": 100,
                                                                                 "time_frame": 250,
                                                                                 "unparsable": 100}

    def create_tool_bar_item(self) -> QToolBar:
        tool_bar = LogFileToolBar()
        self.current_items_changed.connect(tool_bar.export_action_widget.set_items)
        tool_bar.add_local_log_file_action.triggered.connect(self.add_local_log_file)
        return tool_bar

    def add_local_log_file(self) -> None:

        def _is_valid_file(in_file_path: Path):
            with in_file_path.open(encoding='utf-8', errors='ignore') as f:
                meta_parser = MetaFinder().parse_file(f)

            return meta_parser.utc_offset is not None

        file_path, _ = QFileDialog.getOpenFileName(caption="Select the Log-File you want to add", filter="Text (*.txt *.log *.rpt)")
        if not file_path:
            return
        file_path = Path(file_path).resolve()
        if not _is_valid_file(file_path):
            QMessageBox.critical(self,
                                 "UNPARSABLE",
                                 "Log-File is unparsable, because it has no full UTC timestamp.\nUnable to calculate UTC-offset!",
                                 QMessageBox.StandardButton.Ok,
                                 QMessageBox.StandardButton.NoButton)
            return
        server = list(Server.select().where(Server.name == "NO_SERVER").limit(1).execute())[0]
        try:
            log_file = LogFile.get(server=server,
                                   name=file_path.stem,
                                   remote_path=file_path)

            log_file.modified_at = datetime.fromtimestamp(file_path.stat().st_mtime)
            log_file.size = file_path.stat().st_size
            log_file.created_at = datetime.fromtimestamp(file_path.stat().st_ctime)
            log_file.manually_added = True
            log_file.save()
        except peewee.DoesNotExist:
            log_file = LogFile.create(server=server,
                                      name=file_path.stem,
                                      remote_path=file_path,
                                      modified_at=datetime.fromtimestamp(file_path.stat().st_mtime),
                                      size=file_path.stat().st_size,
                                      created_at=datetime.fromtimestamp(file_path.stat().st_ctime),
                                      manually_added=True)
        self.app.backend.updater.process_log_file(log_file=log_file, force=True)
        self.model.refresh()

    def post_set_model(self):
        super().post_set_model()
        self.sortByColumn(self.model.get_column_index("modified_at"), Qt.DescendingOrder)


# region[Main_Exec]

if __name__ == '__main__':
    pass

# endregion[Main_Exec]
