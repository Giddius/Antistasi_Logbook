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

HIDDEN_ICON_IMAGE = ressource_item_factory(file_path='D:/Dropbox/hobby/Modding/Programs/Github/My_Repos/Antistasi_Logbook/designer_files/resources/hidden_icon.svg', qt_path=':/images/hidden_icon.svg')

OPEN_EYE_IMAGE = ressource_item_factory(file_path='D:/Dropbox/hobby/Modding/Programs/Github/My_Repos/Antistasi_Logbook/designer_files/resources/open_eye.svg', qt_path=':/images/open_eye.svg')

UNMARK_IMAGE = ressource_item_factory(file_path='D:/Dropbox/hobby/Modding/Programs/Github/My_Repos/Antistasi_Logbook/designer_files/resources/unmark.svg', qt_path=':/images/unmark.svg')

LOG_FILES_TAB_ICON_IMAGE = ressource_item_factory(file_path='D:/Dropbox/hobby/Modding/Programs/Github/My_Repos/Antistasi_Logbook/designer_files/resources/log_files_tab_icon.svg', qt_path=':/images/log_files_tab_icon.svg')

CLOSE_CANCEL_IMAGE = ressource_item_factory(file_path='D:/Dropbox/hobby/Modding/Programs/Github/My_Repos/Antistasi_Logbook/designer_files/resources/close-cancel.svg', qt_path=':/images/close-cancel.svg')

SERVER_TAB_ICON_IMAGE = ressource_item_factory(file_path='D:/Dropbox/hobby/Modding/Programs/Github/My_Repos/Antistasi_Logbook/designer_files/resources/server_tab_icon.svg', qt_path=':/images/server_tab_icon.svg')

VISIBLE_ICON_IMAGE = ressource_item_factory(file_path='D:/Dropbox/hobby/Modding/Programs/Github/My_Repos/Antistasi_Logbook/designer_files/resources/visible_icon.svg', qt_path=':/images/visible_icon.svg')

CHECK_MARK_BLACK_IMAGE = ressource_item_factory(file_path='D:/Dropbox/hobby/Modding/Programs/Github/My_Repos/Antistasi_Logbook/designer_files/resources/check_mark_black.svg', qt_path=':/images/check_mark_black.svg')

APP_ICON_IMAGE = ressource_item_factory(file_path='D:/Dropbox/hobby/Modding/Programs/Github/My_Repos/Antistasi_Logbook/designer_files/resources/app_icon.png', qt_path=':/images/app_icon.png')

LOG_RECORDS_TAB_ICON_IMAGE = ressource_item_factory(file_path='D:/Dropbox/hobby/Modding/Programs/Github/My_Repos/Antistasi_Logbook/designer_files/resources/log_records_tab_icon.svg', qt_path=':/images/log_records_tab_icon.svg')

WARNING_SIGN_TRIANGLE_RED_IMAGE = ressource_item_factory(file_path='D:/Dropbox/hobby/Modding/Programs/Github/My_Repos/Antistasi_Logbook/designer_files/resources/warning_sign_triangle_red.png', qt_path=':/images/warning_sign_triangle_red.png')

CHECK_MARK_GREEN_IMAGE = ressource_item_factory(file_path='D:/Dropbox/hobby/Modding/Programs/Github/My_Repos/Antistasi_Logbook/designer_files/resources/check_mark_green.svg', qt_path=':/images/check_mark_green.svg')

CLOSE_BLACK_IMAGE = ressource_item_factory(file_path='D:/Dropbox/hobby/Modding/Programs/Github/My_Repos/Antistasi_Logbook/designer_files/resources/close_black.svg', qt_path=':/images/close_black.svg')

MARK_IMAGE = ressource_item_factory(file_path='D:/Dropbox/hobby/Modding/Programs/Github/My_Repos/Antistasi_Logbook/designer_files/resources/mark.svg', qt_path=':/images/mark.svg')

LOG_FILE_FILTER_PAGE_SYMBOL_IMAGE = ressource_item_factory(file_path='D:/Dropbox/hobby/Modding/Programs/Github/My_Repos/Antistasi_Logbook/designer_files/resources/log_file_filter_page_symbol.svg', qt_path=':/images/log_file_filter_page_symbol.svg')

ANTISTASI_LOGBOOK_SPLASH_BACKUP_IMAGE = ressource_item_factory(file_path='D:/Dropbox/hobby/Modding/Programs/Github/My_Repos/Antistasi_Logbook/designer_files/resources/antistasi_logbook_splash_backup.png', qt_path=':/images/antistasi_logbook_splash_backup.png')

ANTISTASI_LOGBOOK_SPLASH_PREPARING_BACKEND_IMAGE = ressource_item_factory(file_path='D:/Dropbox/hobby/Modding/Programs/Github/My_Repos/Antistasi_Logbook/designer_files/resources/antistasi_logbook_splash_preparing_backend.png', qt_path=':/images/antistasi_logbook_splash_preparing_backend.png')

WARNING_SIGN_ROUND_YELLOW_IMAGE = ressource_item_factory(file_path='D:/Dropbox/hobby/Modding/Programs/Github/My_Repos/Antistasi_Logbook/designer_files/resources/warning_sign_round_yellow.svg', qt_path=':/images/warning_sign_round_yellow.svg')

ANTISTASI_LOGBOOK_SPLASH_STARTING_BACKEND_IMAGE = ressource_item_factory(file_path='D:/Dropbox/hobby/Modding/Programs/Github/My_Repos/Antistasi_Logbook/designer_files/resources/antistasi_logbook_splash_starting_backend.png', qt_path=':/images/antistasi_logbook_splash_starting_backend.png')

PLACEHOLDER_IMAGE = ressource_item_factory(file_path='D:/Dropbox/hobby/Modding/Programs/Github/My_Repos/Antistasi_Logbook/designer_files/resources/placeholder.png', qt_path=':/images/placeholder.png')

CLOSED_EYE_IMAGE = ressource_item_factory(file_path='D:/Dropbox/hobby/Modding/Programs/Github/My_Repos/Antistasi_Logbook/designer_files/resources/closed_eye.svg', qt_path=':/images/closed_eye.svg')

SPINNER_GIF = ressource_item_factory(file_path='D:/Dropbox/hobby/Modding/Programs/Github/My_Repos/Antistasi_Logbook/designer_files/resources/spinner.gif', qt_path=':/gifs/spinner.gif')


class AllResourceItems(metaclass=AllResourceItemsMeta):
    categories = {'image', 'gif'}
    missing_items = defaultdict(set)

    antistasi_logbook_splash_preparing_database_image = ANTISTASI_LOGBOOK_SPLASH_PREPARING_DATABASE_IMAGE
    hidden_icon_image = HIDDEN_ICON_IMAGE
    open_eye_image = OPEN_EYE_IMAGE
    unmark_image = UNMARK_IMAGE
    log_files_tab_icon_image = LOG_FILES_TAB_ICON_IMAGE
    close_cancel_image = CLOSE_CANCEL_IMAGE
    server_tab_icon_image = SERVER_TAB_ICON_IMAGE
    visible_icon_image = VISIBLE_ICON_IMAGE
    check_mark_black_image = CHECK_MARK_BLACK_IMAGE
    app_icon_image = APP_ICON_IMAGE
    log_records_tab_icon_image = LOG_RECORDS_TAB_ICON_IMAGE
    warning_sign_triangle_red_image = WARNING_SIGN_TRIANGLE_RED_IMAGE
    check_mark_green_image = CHECK_MARK_GREEN_IMAGE
    close_black_image = CLOSE_BLACK_IMAGE
    mark_image = MARK_IMAGE
    log_file_filter_page_symbol_image = LOG_FILE_FILTER_PAGE_SYMBOL_IMAGE
    antistasi_logbook_splash_backup_image = ANTISTASI_LOGBOOK_SPLASH_BACKUP_IMAGE
    antistasi_logbook_splash_preparing_backend_image = ANTISTASI_LOGBOOK_SPLASH_PREPARING_BACKEND_IMAGE
    warning_sign_round_yellow_image = WARNING_SIGN_ROUND_YELLOW_IMAGE
    antistasi_logbook_splash_starting_backend_image = ANTISTASI_LOGBOOK_SPLASH_STARTING_BACKEND_IMAGE
    placeholder_image = PLACEHOLDER_IMAGE
    closed_eye_image = CLOSED_EYE_IMAGE
    spinner_gif = SPINNER_GIF


    @classmethod
    def dump_missing(cls):
        missing_items = {k: [i.rsplit('_', 1)[0] for i in v] for k, v in cls.missing_items.items()}

        log.info("Missing Ressource Items:\n%s", pp.fmt(missing_items).replace("'", '"'))


if get_meta_info().is_dev is True:
    atexit.register(AllResourceItems.dump_missing)
