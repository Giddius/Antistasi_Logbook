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

THIS_FILE_DIR = Path(__file__).parent.absolute()
log = get_logger(__name__)
# endregion[Constants]

# Array parsing Grammar

colon = pp.Suppress(',')
sqb_open = pp.Suppress('[')
sqb_close = pp.Suppress(']')
quote = pp.Suppress('"')
keywords = pp.Keyword("EAST") | pp.Keyword("WEST") | pp.Keyword("true", caseless=True) | pp.Keyword("false", caseless=True)
items = pp.Forward()
content = pp.Group(pp.ZeroOrMore(items + pp.Optional(colon)))
array = sqb_open + content + sqb_close
string = quote + pp.OneOrMore(pp.Word(pp.printables.replace('"', ''))).set_parse_action(' '.join) + quote
empty_string = quote + quote
number = ppc.number
items <<= string | empty_string | keywords | array | number


def parse_text_array(in_text: str) -> list[list[Any]]:
    try:
        return array.parse_string(in_text, parse_all=True).as_list()[0]
    except pp.ParseException as e:
        log.error(e, exc_info=True, extra={"in_text": in_text})
        log.critical("%r was caused by %r", e, in_text)
        return "ERROR"
# region[Main_Exec]


if __name__ == '__main__':
    x = '''[["CUP_arifle_ACRC_EGLM_blk_556","CUP_muzzle_snds_M16","CUP_acc_ANPEQ_15_Black","CUP_optic_1P87_RIS",["CUP_30Rnd_556x45_PMAG_QP",30],["CUP_1Rnd_HE_M203",1],""],[],[],[],[],[],"","",[],["","","","","",""]]'''
    pprint(parse_text_array(x))
# endregion[Main_Exec]
