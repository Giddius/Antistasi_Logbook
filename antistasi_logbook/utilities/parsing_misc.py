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

number = ppc.number
items <<= string | keywords | array | number


def parse_text_array(in_text: str) -> list[list[Any]]:
    try:
        return array.parse_string(in_text, parse_all=True).as_list()[0]
    except pp.ParseException as e:
        log.error(e, exc_info=True, extra={"in_text": in_text})
        log.critical("%r was caused by %r", e, in_text)
        return "ERROR"
# region[Main_Exec]


if __name__ == '__main__':
    x = """[
        ["LAND_LIGHT",-1,"GROUP"]
["LAND_LIGHT",-1,"GROUP"]
["LAND_DEFAULT",0,"EMPTY"]
["HELI_TRANSPORT",-1,"SQUAD"]
["HELI_TRANSPORT",0,"EMPTY"]
["LAND_LIGHT",-1,"SQUAD"]
]"""
    pprint(parse_text_array(x))
# endregion[Main_Exec]
