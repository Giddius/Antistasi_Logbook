"""
This File was auto-generated
"""





# region[Imports]

from enum import Enum, auto, Flag
from pathlib import Path
from PySide6.QtGui import QPixmap, QIcon, QImage
from typing import Union, Optional, Iterable, TYPE_CHECKING
from collections import defaultdict
import atexit
import pp
from pprint import pprint, pformat
from gidapptools.gidapptools_qt.resources_helper import ressource_item_factory, ResourceItem, AllResourceItemsMeta
from gidapptools import get_meta_info, get_logger
from . import antistasi_logbook_resources

# endregion[Imports]

log = get_logger(__name__)


WARNING_SIGN_TRIANGLE_RED_IMAGE = ressource_item_factory(file_path='D:/Dropbox/hobby/Modding/Programs/Github/My_Repos/Antistasi_Logbook/designer_files/resources/warning_sign_triangle_red.png', qt_path=':/images/warning_sign_triangle_red.png')

CHECK_MARK_GREEN_IMAGE = ressource_item_factory(file_path='D:/Dropbox/hobby/Modding/Programs/Github/My_Repos/Antistasi_Logbook/designer_files/resources/check_mark_green.svg', qt_path=':/images/check_mark_green.svg')

CLOSE_BLACK_IMAGE = ressource_item_factory(file_path='D:/Dropbox/hobby/Modding/Programs/Github/My_Repos/Antistasi_Logbook/designer_files/resources/close_black.svg', qt_path=':/images/close_black.svg')

OPEN_EYE_IMAGE = ressource_item_factory(file_path='D:/Dropbox/hobby/Modding/Programs/Github/My_Repos/Antistasi_Logbook/designer_files/resources/open_eye.svg', qt_path=':/images/open_eye.svg')

PLACEHOLDER_IMAGE = ressource_item_factory(file_path='D:/Dropbox/hobby/Modding/Programs/Github/My_Repos/Antistasi_Logbook/designer_files/resources/placeholder.png', qt_path=':/images/placeholder.png')

WARNING_SIGN_ROUND_YELLOW_IMAGE = ressource_item_factory(file_path='D:/Dropbox/hobby/Modding/Programs/Github/My_Repos/Antistasi_Logbook/designer_files/resources/warning_sign_round_yellow.svg', qt_path=':/images/warning_sign_round_yellow.svg')

CLOSE_CANCEL_IMAGE = ressource_item_factory(file_path='D:/Dropbox/hobby/Modding/Programs/Github/My_Repos/Antistasi_Logbook/designer_files/resources/close-cancel.svg', qt_path=':/images/close-cancel.svg')

CLOSED_EYE_IMAGE = ressource_item_factory(file_path='D:/Dropbox/hobby/Modding/Programs/Github/My_Repos/Antistasi_Logbook/designer_files/resources/closed_eye.svg', qt_path=':/images/closed_eye.svg')

CHECK_MARK_BLACK_IMAGE = ressource_item_factory(file_path='D:/Dropbox/hobby/Modding/Programs/Github/My_Repos/Antistasi_Logbook/designer_files/resources/check_mark_black.svg', qt_path=':/images/check_mark_black.svg')

APP_ICON_IMAGE = ressource_item_factory(file_path='D:/Dropbox/hobby/Modding/Programs/Github/My_Repos/Antistasi_Logbook/designer_files/resources/app_icon.png', qt_path=':/images/app_icon.png')


class AllResourceItems(metaclass=AllResourceItemsMeta):
    categories = {'image'}
    missing_items = defaultdict(set)

    warning_sign_triangle_red_image = WARNING_SIGN_TRIANGLE_RED_IMAGE
    check_mark_green_image = CHECK_MARK_GREEN_IMAGE
    close_black_image = CLOSE_BLACK_IMAGE
    open_eye_image = OPEN_EYE_IMAGE
    placeholder_image = PLACEHOLDER_IMAGE
    warning_sign_round_yellow_image = WARNING_SIGN_ROUND_YELLOW_IMAGE
    close_cancel_image = CLOSE_CANCEL_IMAGE
    closed_eye_image = CLOSED_EYE_IMAGE
    check_mark_black_image = CHECK_MARK_BLACK_IMAGE
    app_icon_image = APP_ICON_IMAGE


    @classmethod
    def dump_missing(cls):
        missing_items = {k: [i.rsplit('_', 1)[0] for i in v] for k, v in cls.missing_items.items()}

        log.info("Missing Ressource Items:\n%s", pp.fmt(missing_items).replace("'", '"'))


if get_meta_info().is_dev is True:
    atexit.register(AllResourceItems.dump_missing)
