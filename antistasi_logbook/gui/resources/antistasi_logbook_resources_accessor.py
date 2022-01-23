"""
This File was auto-generated
"""





# region[Imports]

import os
from enum import Enum, auto, Flag
from pathlib import Path
from PySide6.QtGui import QPixmap, QIcon, QImage
from typing import Union, Optional, Iterable, TYPE_CHECKING
from collections import defaultdict
import atexit
import pp
from pprint import pprint, pformat
from gidapptools.gidapptools_qt.resources.resources_helper import ressource_item_factory, ResourceItem, AllResourceItemsMeta
from gidapptools import get_meta_info, get_logger
from . import antistasi_logbook_resources

# endregion[Imports]

log = get_logger(__name__)


ANTISTASI_LOGBOOK_SPLASH_PREPARING_DATABASE_IMAGE = ressource_item_factory(file_path='D:/Dropbox/hobby/Modding/Programs/Github/My_Repos/Antistasi_Logbook/designer_files/resources/antistasi_logbook_splash_preparing_database.png', qt_path=':/images/antistasi_logbook_splash_preparing_database.png')

FILTER_PAGE_SYMBOL_IMAGE = ressource_item_factory(file_path='D:/Dropbox/hobby/Modding/Programs/Github/My_Repos/Antistasi_Logbook/designer_files/resources/filter_page_symbol.svg', qt_path=':/images/filter_page_symbol.svg')

OPEN_EYE_IMAGE = ressource_item_factory(file_path='D:/Dropbox/hobby/Modding/Programs/Github/My_Repos/Antistasi_Logbook/designer_files/resources/open_eye.svg', qt_path=':/images/open_eye.svg')

FOLDER_SETTINGS_IMAGE = ressource_item_factory(file_path='D:/Dropbox/hobby/Modding/Programs/Github/My_Repos/Antistasi_Logbook/designer_files/resources/folder_settings.svg', qt_path=':/images/folder_settings.svg')

LOG_FILES_TAB_ICON_IMAGE = ressource_item_factory(file_path='D:/Dropbox/hobby/Modding/Programs/Github/My_Repos/Antistasi_Logbook/designer_files/resources/log_files_tab_icon.svg', qt_path=':/images/log_files_tab_icon.svg')

TIME_SETTINGS_IMAGE = ressource_item_factory(file_path='D:/Dropbox/hobby/Modding/Programs/Github/My_Repos/Antistasi_Logbook/designer_files/resources/time_settings.svg', qt_path=':/images/time_settings.svg')

CLOSE_CANCEL_IMAGE = ressource_item_factory(file_path='D:/Dropbox/hobby/Modding/Programs/Github/My_Repos/Antistasi_Logbook/designer_files/resources/close-cancel.svg', qt_path=':/images/close-cancel.svg')

SERVER_TAB_ICON_IMAGE = ressource_item_factory(file_path='D:/Dropbox/hobby/Modding/Programs/Github/My_Repos/Antistasi_Logbook/designer_files/resources/server_tab_icon.svg', qt_path=':/images/server_tab_icon.svg')

DOWNLOADING_SETTINGS_IMAGE = ressource_item_factory(file_path='D:/Dropbox/hobby/Modding/Programs/Github/My_Repos/Antistasi_Logbook/designer_files/resources/downloading_settings.svg', qt_path=':/images/downloading_settings.svg')

CHECK_MARK_BLACK_IMAGE = ressource_item_factory(file_path='D:/Dropbox/hobby/Modding/Programs/Github/My_Repos/Antistasi_Logbook/designer_files/resources/check_mark_black.svg', qt_path=':/images/check_mark_black.svg')

APP_ICON_IMAGE = ressource_item_factory(file_path='D:/Dropbox/hobby/Modding/Programs/Github/My_Repos/Antistasi_Logbook/designer_files/resources/app_icon.png', qt_path=':/images/app_icon.png')

LOG_RECORDS_TAB_ICON_IMAGE = ressource_item_factory(file_path='D:/Dropbox/hobby/Modding/Programs/Github/My_Repos/Antistasi_Logbook/designer_files/resources/log_records_tab_icon.svg', qt_path=':/images/log_records_tab_icon.svg')

COLORING_ICON_1_IMAGE = ressource_item_factory(file_path='D:/Dropbox/hobby/Modding/Programs/Github/My_Repos/Antistasi_Logbook/designer_files/resources/coloring_icon_1.svg', qt_path=':/images/coloring_icon_1.svg')

WARNING_SIGN_TRIANGLE_RED_IMAGE = ressource_item_factory(file_path='D:/Dropbox/hobby/Modding/Programs/Github/My_Repos/Antistasi_Logbook/designer_files/resources/warning_sign_triangle_red.png', qt_path=':/images/warning_sign_triangle_red.png')

CHECK_MARK_GREEN_IMAGE = ressource_item_factory(file_path='D:/Dropbox/hobby/Modding/Programs/Github/My_Repos/Antistasi_Logbook/designer_files/resources/check_mark_green.svg', qt_path=':/images/check_mark_green.svg')

SETTINGS_WINDOW_SYMBOL_IMAGE = ressource_item_factory(file_path='D:/Dropbox/hobby/Modding/Programs/Github/My_Repos/Antistasi_Logbook/designer_files/resources/settings_window_symbol.svg', qt_path=':/images/settings_window_symbol.svg')

CLOSE_BLACK_IMAGE = ressource_item_factory(file_path='D:/Dropbox/hobby/Modding/Programs/Github/My_Repos/Antistasi_Logbook/designer_files/resources/close_black.svg', qt_path=':/images/close_black.svg')

PLACEHOLDER_IMAGE = ressource_item_factory(file_path='D:/Dropbox/hobby/Modding/Programs/Github/My_Repos/Antistasi_Logbook/designer_files/resources/placeholder.png', qt_path=':/images/placeholder.png')

ANTISTASI_LOGBOOK_SPLASH_BACKUP_IMAGE = ressource_item_factory(file_path='D:/Dropbox/hobby/Modding/Programs/Github/My_Repos/Antistasi_Logbook/designer_files/resources/antistasi_logbook_splash_backup.png', qt_path=':/images/antistasi_logbook_splash_backup.png')

ANTISTASI_LOGBOOK_SPLASH_STARTING_BACKEND_IMAGE = ressource_item_factory(file_path='D:/Dropbox/hobby/Modding/Programs/Github/My_Repos/Antistasi_Logbook/designer_files/resources/antistasi_logbook_splash_starting_backend.png', qt_path=':/images/antistasi_logbook_splash_starting_backend.png')

WARNING_SIGN_ROUND_YELLOW_IMAGE = ressource_item_factory(file_path='D:/Dropbox/hobby/Modding/Programs/Github/My_Repos/Antistasi_Logbook/designer_files/resources/warning_sign_round_yellow.svg', qt_path=':/images/warning_sign_round_yellow.svg')

CLOSED_EYE_IMAGE = ressource_item_factory(file_path='D:/Dropbox/hobby/Modding/Programs/Github/My_Repos/Antistasi_Logbook/designer_files/resources/closed_eye.svg', qt_path=':/images/closed_eye.svg')

ANTISTASI_LOGBOOK_SPLASH_SHUTDOWN_BACKEND_IMAGE = ressource_item_factory(file_path='D:/Dropbox/hobby/Modding/Programs/Github/My_Repos/Antistasi_Logbook/designer_files/resources/antistasi_logbook_splash_shutdown_backend.png', qt_path=':/images/antistasi_logbook_splash_shutdown_backend.png')

DATABASE_SETTINGS_IMAGE = ressource_item_factory(file_path='D:/Dropbox/hobby/Modding/Programs/Github/My_Repos/Antistasi_Logbook/designer_files/resources/database_settings.svg', qt_path=':/images/database_settings.svg')

SPINNER_GIF = ressource_item_factory(file_path='D:/Dropbox/hobby/Modding/Programs/Github/My_Repos/Antistasi_Logbook/designer_files/resources/spinner.gif', qt_path=':/gifs/spinner.gif')

STATS_ICON_2_IMAGE = ressource_item_factory(file_path='D:/Dropbox/hobby/Modding/Programs/Github/My_Repos/Antistasi_Logbook/designer_files/resources/stats_icon_2.svg', qt_path=':/images/stats_icon_2.svg')

HIDDEN_ICON_IMAGE = ressource_item_factory(file_path='D:/Dropbox/hobby/Modding/Programs/Github/My_Repos/Antistasi_Logbook/designer_files/resources/hidden_icon.svg', qt_path=':/images/hidden_icon.svg')

COLORING_ICON_3_IMAGE = ressource_item_factory(file_path='D:/Dropbox/hobby/Modding/Programs/Github/My_Repos/Antistasi_Logbook/designer_files/resources/coloring_icon_3.svg', qt_path=':/images/coloring_icon_3.svg')

SELECT_PATH_SYMBOL_IMAGE = ressource_item_factory(file_path='D:/Dropbox/hobby/Modding/Programs/Github/My_Repos/Antistasi_Logbook/designer_files/resources/select_path_symbol.svg', qt_path=':/images/select_path_symbol.svg')

UNMARK_IMAGE = ressource_item_factory(file_path='D:/Dropbox/hobby/Modding/Programs/Github/My_Repos/Antistasi_Logbook/designer_files/resources/unmark.svg', qt_path=':/images/unmark.svg')

VISIBLE_ICON_IMAGE = ressource_item_factory(file_path='D:/Dropbox/hobby/Modding/Programs/Github/My_Repos/Antistasi_Logbook/designer_files/resources/visible_icon.svg', qt_path=':/images/visible_icon.svg')

GENERAL_SETTINGS_IMAGE = ressource_item_factory(file_path='D:/Dropbox/hobby/Modding/Programs/Github/My_Repos/Antistasi_Logbook/designer_files/resources/general_settings.svg', qt_path=':/images/general_settings.svg')

WEBDAV_SETTINGS_IMAGE = ressource_item_factory(file_path='D:/Dropbox/hobby/Modding/Programs/Github/My_Repos/Antistasi_Logbook/designer_files/resources/webdav_settings.svg', qt_path=':/images/webdav_settings.svg')

DEBUG_SETTINGS_IMAGE = ressource_item_factory(file_path='D:/Dropbox/hobby/Modding/Programs/Github/My_Repos/Antistasi_Logbook/designer_files/resources/debug_settings.svg', qt_path=':/images/debug_settings.svg')

SEARCH_PAGE_SYMBOL_IMAGE = ressource_item_factory(file_path='D:/Dropbox/hobby/Modding/Programs/Github/My_Repos/Antistasi_Logbook/designer_files/resources/search_page_symbol.svg', qt_path=':/images/search_page_symbol.svg')

HIDDEN_IMAGE = ressource_item_factory(file_path='D:/Dropbox/hobby/Modding/Programs/Github/My_Repos/Antistasi_Logbook/designer_files/resources/hidden.svg', qt_path=':/images/hidden.svg')

COLORING_ICON_2_IMAGE = ressource_item_factory(file_path='D:/Dropbox/hobby/Modding/Programs/Github/My_Repos/Antistasi_Logbook/designer_files/resources/coloring_icon_2.svg', qt_path=':/images/coloring_icon_2.svg')

UPDATING_SETTINGS_IMAGE = ressource_item_factory(file_path='D:/Dropbox/hobby/Modding/Programs/Github/My_Repos/Antistasi_Logbook/designer_files/resources/updating_settings.svg', qt_path=':/images/updating_settings.svg')

MARK_IMAGE = ressource_item_factory(file_path='D:/Dropbox/hobby/Modding/Programs/Github/My_Repos/Antistasi_Logbook/designer_files/resources/mark.svg', qt_path=':/images/mark.svg')

ANTISTASI_LOGBOOK_SPLASH_PREPARING_BACKEND_IMAGE = ressource_item_factory(file_path='D:/Dropbox/hobby/Modding/Programs/Github/My_Repos/Antistasi_Logbook/designer_files/resources/antistasi_logbook_splash_preparing_backend.png', qt_path=':/images/antistasi_logbook_splash_preparing_backend.png')

GUI_SETTINGS_IMAGE = ressource_item_factory(file_path='D:/Dropbox/hobby/Modding/Programs/Github/My_Repos/Antistasi_Logbook/designer_files/resources/gui_settings.svg', qt_path=':/images/gui_settings.svg')

STATS_ICON_IMAGE = ressource_item_factory(file_path='D:/Dropbox/hobby/Modding/Programs/Github/My_Repos/Antistasi_Logbook/designer_files/resources/stats_icon.svg', qt_path=':/images/stats_icon.svg')

PARSING_SETTINGS_IMAGE = ressource_item_factory(file_path='D:/Dropbox/hobby/Modding/Programs/Github/My_Repos/Antistasi_Logbook/designer_files/resources/parsing_settings.svg', qt_path=':/images/parsing_settings.svg')


class AllResourceItems(metaclass=AllResourceItemsMeta):
    categories = {'image', 'gif'}
    missing_items = defaultdict(set)

    antistasi_logbook_splash_preparing_database_image = ANTISTASI_LOGBOOK_SPLASH_PREPARING_DATABASE_IMAGE
    filter_page_symbol_image = FILTER_PAGE_SYMBOL_IMAGE
    open_eye_image = OPEN_EYE_IMAGE
    folder_settings_image = FOLDER_SETTINGS_IMAGE
    log_files_tab_icon_image = LOG_FILES_TAB_ICON_IMAGE
    time_settings_image = TIME_SETTINGS_IMAGE
    close_cancel_image = CLOSE_CANCEL_IMAGE
    server_tab_icon_image = SERVER_TAB_ICON_IMAGE
    downloading_settings_image = DOWNLOADING_SETTINGS_IMAGE
    check_mark_black_image = CHECK_MARK_BLACK_IMAGE
    app_icon_image = APP_ICON_IMAGE
    log_records_tab_icon_image = LOG_RECORDS_TAB_ICON_IMAGE
    coloring_icon_1_image = COLORING_ICON_1_IMAGE
    warning_sign_triangle_red_image = WARNING_SIGN_TRIANGLE_RED_IMAGE
    check_mark_green_image = CHECK_MARK_GREEN_IMAGE
    settings_window_symbol_image = SETTINGS_WINDOW_SYMBOL_IMAGE
    close_black_image = CLOSE_BLACK_IMAGE
    placeholder_image = PLACEHOLDER_IMAGE
    antistasi_logbook_splash_backup_image = ANTISTASI_LOGBOOK_SPLASH_BACKUP_IMAGE
    antistasi_logbook_splash_starting_backend_image = ANTISTASI_LOGBOOK_SPLASH_STARTING_BACKEND_IMAGE
    warning_sign_round_yellow_image = WARNING_SIGN_ROUND_YELLOW_IMAGE
    closed_eye_image = CLOSED_EYE_IMAGE
    antistasi_logbook_splash_shutdown_backend_image = ANTISTASI_LOGBOOK_SPLASH_SHUTDOWN_BACKEND_IMAGE
    database_settings_image = DATABASE_SETTINGS_IMAGE
    stats_icon_2_image = STATS_ICON_2_IMAGE
    hidden_icon_image = HIDDEN_ICON_IMAGE
    coloring_icon_3_image = COLORING_ICON_3_IMAGE
    select_path_symbol_image = SELECT_PATH_SYMBOL_IMAGE
    unmark_image = UNMARK_IMAGE
    visible_icon_image = VISIBLE_ICON_IMAGE
    general_settings_image = GENERAL_SETTINGS_IMAGE
    webdav_settings_image = WEBDAV_SETTINGS_IMAGE
    debug_settings_image = DEBUG_SETTINGS_IMAGE
    search_page_symbol_image = SEARCH_PAGE_SYMBOL_IMAGE
    hidden_image = HIDDEN_IMAGE
    coloring_icon_2_image = COLORING_ICON_2_IMAGE
    updating_settings_image = UPDATING_SETTINGS_IMAGE
    mark_image = MARK_IMAGE
    antistasi_logbook_splash_preparing_backend_image = ANTISTASI_LOGBOOK_SPLASH_PREPARING_BACKEND_IMAGE
    gui_settings_image = GUI_SETTINGS_IMAGE
    stats_icon_image = STATS_ICON_IMAGE
    parsing_settings_image = PARSING_SETTINGS_IMAGE
    spinner_gif = SPINNER_GIF


    @classmethod
    def dump_missing(cls):
        missing_items = {k: [i.rsplit('_', 1)[0] for i in v] for k, v in cls.missing_items.items()}

        log.info("Missing Ressource Items:\n%s", pp.fmt(missing_items).replace("'", '"'))


if get_meta_info().is_dev is True:
    atexit.register(AllResourceItems.dump_missing)
