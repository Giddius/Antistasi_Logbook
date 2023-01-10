"""
WiP.

Soon.
"""

# region [Imports]

# * Standard Library Imports ---------------------------------------------------------------------------->
from typing import Any
from pathlib import Path

# * Third Party Imports --------------------------------------------------------------------------------->
import pyparsing as pp
from pyparsing import pyparsing_common as ppc

# * Gid Imports ----------------------------------------------------------------------------------------->
from gidapptools import get_logger
from gidapptools.general_helper.enums import MiscEnum
from gidapptools.general_helper.timing import get_dummy_profile_decorator_in_globals

# endregion [Imports]

# region [TODO]


# endregion [TODO]

# region [Logging]


# endregion [Logging]

# region [Constants]
get_dummy_profile_decorator_in_globals()
THIS_FILE_DIR = Path(__file__).parent.absolute()
log = get_logger(__name__)
# endregion [Constants]


def _maybe_join(parts):
    if parts is None:
        return ""
    try:
        ' '.join(parts)
    except TypeError as e:
        log.error(e, exc_info=True)
        return ""

# Array parsing Grammar


def _strip_quotes(in_string, in_location, in_token) -> str:

    return in_token[0].strip('"' + "'").replace(r"\ ".strip() + '"', '"').replace(r"\ ".strip() + "'", "'")


def _convert_bool_false(in_string, in_location, in_token) -> bool:
    return False


def _convert_bool_true(in_string, in_location, in_token) -> bool:
    return True


def get_array_grammar():
    colon = pp.Suppress(',')
    sqb_open = pp.Suppress('[')
    sqb_close = pp.Suppress(']')
    quote = pp.Suppress('"') | pp.Suppress("'")
    keywords = pp.Keyword("EAST") | pp.Keyword("WEST") | pp.Keyword("true", caseless=True).set_parse_action(_convert_bool_true) | pp.Keyword("false", caseless=True).set_parse_action(_convert_bool_false)
    items = pp.Forward()
    content = pp.Group(pp.ZeroOrMore(items + pp.Optional(colon)))
    array = sqb_open + content + sqb_close
    # string = quote + pp.OneOrMore(pp.Regex(r'[^\"\s]+')).set_parse_action(' '.join) + quote
    string = pp.quoted_string.set_parse_action(_strip_quotes)
    empty_string = quote + quote
    number = ppc.number
    items <<= string | empty_string | keywords | array | number
    return array


ARRAY_GRAMMAR = get_array_grammar()


def parse_text_array(in_text: str) -> list[list[Any]]:
    try:
        return ARRAY_GRAMMAR.parse_string(in_text, parse_all=True).as_list()[0]
    except pp.ParseException as e:
        log.error(e, exc_info=1, extra={"in_text": in_text}, stacklevel=3)
        log.critical("%r was caused by %r", e, in_text)
        return MiscEnum.ERROR


# region [Main_Exec]
if __name__ == '__main__':
    pass
# endregion [Main_Exec]
