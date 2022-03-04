"""
WiP.

Soon.
"""

# region [Imports]

# * Standard Library Imports ---------------------------------------------------------------------------->
from pprint import pprint
from typing import Any
from pathlib import Path

# * Third Party Imports --------------------------------------------------------------------------------->
import pyparsing as pp
from pyparsing import pyparsing_common as ppc

# * Gid Imports ----------------------------------------------------------------------------------------->
from gidapptools import get_logger

# endregion[Imports]

# region [TODO]


# endregion [TODO]

# region [Logging]


# endregion[Logging]

# region [Constants]
from gidapptools.general_helper.timing import get_dummy_profile_decorator_in_globals

THIS_FILE_DIR = Path(__file__).parent.absolute()
log = get_logger(__name__)
# endregion[Constants]


def _maybe_join(parts):
    if parts is None:
        return ""
    try:
        ' '.join(parts)
    except TypeError as e:
        log.error(e, exc_info=True)
        return ""

# Array parsing Grammar


def get_array_grammar():
    colon = pp.Suppress(',')
    sqb_open = pp.Suppress('[')
    sqb_close = pp.Suppress(']')
    quote = pp.Suppress('"')
    keywords = pp.Keyword("EAST") | pp.Keyword("WEST") | pp.Keyword("true", caseless=True).set_parse_action(lambda x: True) | pp.Keyword("false", caseless=True).set_parse_action(lambda x: False)
    items = pp.Forward()
    content = pp.Group(pp.ZeroOrMore(items + pp.Optional(colon)))
    array = sqb_open + content + sqb_close
    string = quote + pp.OneOrMore(pp.Regex(r'[^\"\s]+')).set_parse_action(' '.join) + quote
    empty_string = quote + quote
    number = ppc.number
    items <<= string | empty_string | keywords | array | number
    return array


def parse_text_array(in_text: str) -> list[list[Any]]:
    try:
        return get_array_grammar().parse_string(in_text, parse_all=True).as_list()[0]
    except pp.ParseException as e:
        log.error(e, exc_info=1, extra={"in_text": in_text}, stacklevel=3)
        log.critical("%r was caused by %r", e, in_text)
        return "ERROR"
# region[Main_Exec]


if __name__ == '__main__':
    x = '''[["CUP_arifle_ACRC_EGLM_blk_556","CUP_muzzle_snds_M16","CUP_acc_ANPEQ_15_Black","CUP_optic_1P87_RIS",["CUP_30Rnd_556x45_PMAG_QP",30],["CUP_1Rnd_HE_M203",1],""],[],[],[],[],[],"","",[],["","","","","",""]]'''
    pprint(parse_text_array(x))
# endregion[Main_Exec]
