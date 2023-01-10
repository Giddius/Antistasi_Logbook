"""
WiP.

Soon.
"""

# region [Imports]

# * Standard Library Imports ---------------------------------------------------------------------------->
from typing import TYPE_CHECKING
from pathlib import Path

# * Qt Imports --------------------------------------------------------------------------------------->
from PySide6.QtGui import QFont, QAction
from PySide6.QtCore import Qt, Signal, QMargins, QStandardPaths, QItemSelectionModel
from PySide6.QtWidgets import QToolBar, QFontDialog, QGridLayout, QHeaderView, QPushButton

# * Gid Imports ----------------------------------------------------------------------------------------->
from gidapptools import get_logger

# * Local Imports --------------------------------------------------------------------------------------->
from antistasi_logbook.gui.views.base_query_tree_view import BaseQueryTreeView, CustomContextMenu
from antistasi_logbook.records.special_message_formats import DiscordText
from antistasi_logbook.gui.widgets.log_records_tool_bar import LogRecordToolBar
from antistasi_logbook.gui.resources.antistasi_logbook_resources_accessor import AllResourceItems

# * Type-Checking Imports --------------------------------------------------------------------------------->
if TYPE_CHECKING:
    from antistasi_logbook.records.base_record import BaseRecord
    from antistasi_logbook.gui.models.log_records_model import LogRecordsModel
    from antistasi_logbook.gui.models.proxy_models.base_proxy_model import BaseProxyModel

# endregion [Imports]

# region [TODO]


# endregion [TODO]

# region [Logging]


# endregion [Logging]

# region [Constants]

THIS_FILE_DIR = Path(__file__).parent.absolute()
log = get_logger(__name__)
# endregion [Constants]


class FontSettingsWindow(QFontDialog):

    def __init__(self, default_font: QFont, initial_font: QFont = None, parent=None):
        super().__init__(parent)
        self.setOptions(QFontDialog.FontDialogOptions() | QFontDialog.MonospacedFonts)
        self.default_font = default_font
        self.initial_font = initial_font
        if self.initial_font is not None:
            self.setCurrentFont(self.initial_font)
        self.reset_button = QPushButton(AllResourceItems.reset_font_image.get_as_icon(), "Reset Font", self)
        self.reset_button.pressed.connect(self.reset_font)
        layout: QGridLayout = self.layout()
        layout.addWidget(self.reset_button, layout.rowCount() - 1, 0, Qt.AlignLeft | Qt.AlignVCenter)

    def reset_font(self):
        self.setCurrentFont(self.default_font)


class LogRecordsQueryView(BaseQueryTreeView):
    initially_hidden_columns: set[str] = {"id", "comments"}
    about_to_screenshot = Signal()
    screenshot_finished = Signal()

    def __init__(self, parent=None) -> None:
        super().__init__(name="Log-Records", parent=parent)
        self.item_size_by_column_name = self._item_size_by_column_name.copy() | {"message": 1000,
                                                                                 "start": 75,
                                                                                 "end": 75,
                                                                                 "recorded_at": 175,
                                                                                 "log_file": 250,
                                                                                 "Origin": 75,
                                                                                 "log_level": 100,
                                                                                 "called_by": 225,
                                                                                 "logged_from": 225}

    def extra_setup(self):
        super().extra_setup()
        self.setSortingEnabled(False)

    def create_tool_bar_item(self) -> QToolBar:
        tool_bar = LogRecordToolBar()
        tool_bar.font_settings_action.triggered.connect(self.show_font_settings_window)
        if self.original_model is None:
            tool_bar.font_settings_action.setEnabled(False)
        return tool_bar

    def show_font_settings_window(self):
        font_dialog = FontSettingsWindow(self.original_model._create_message_font(reset=True), self.original_model.message_font, self)
        _ok = font_dialog.exec()
        if _ok:
            font = font_dialog.currentFont()
            self.original_model.set_message_font(font)
            self.repaint()

    def add_free_context_menu_options(self, menu: "CustomContextMenu"):
        super().add_free_context_menu_options(menu)
        copy_as_menu = menu.add_menu("Copy as", menu)
        discord_copy_action = QAction("Discord")
        discord_copy_action.triggered.connect(self.on_discord_copy)
        copy_as_menu.add_action(discord_copy_action)

        std_copy_action = QAction("Copy")
        std_copy_action.triggered.connect(self.on_std_copy)
        menu.add_action(std_copy_action)

        screenshot_action = QAction("Screenshot Selection")
        screenshot_action.triggered.connect(self.on_screenshot_selection)
        menu.add_action(screenshot_action)

    def on_discord_copy(self):
        items: list["BaseRecord"] = [self.model.content_items[idx.row()] for idx in self.current_selection]
        if len(items) <= 0:
            return

        text = DiscordText(items).make_text()
        clipboard = self.app.clipboard()
        clipboard.setText(text.strip())

    def on_std_copy(self):
        items = [self.model.content_items[idx.row()] for idx in self.current_selection]
        text = ""

        for item in items:
            text += '\n'.join(item.get_formated_message(msg_format="ORIGINAL")) + '\n'

        clipboard = self.app.clipboard()
        clipboard.setText(text.strip())

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

    @property
    def model(self) -> "BaseProxyModel":
        _out = super().model
        if callable(_out):
            _out = _out()
        return _out

    @ property
    def header_view(self) -> QHeaderView:
        return self.header()

    def pre_set_model(self):
        super().pre_set_model()

    def post_set_model(self):
        super().post_set_model()
        self.tool_bar_item.font_settings_action.setEnabled(True)

    def setModel(self, model: "LogRecordsModel") -> None:
        self.original_model = model
        model = model.proxy_model
        return super().setModel(model)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}"


# region [Main_Exec]

if __name__ == '__main__':
    pass

# endregion [Main_Exec]
