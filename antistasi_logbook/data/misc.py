# * Standard Library Imports ---------------------------------------------------------------------------->
import re

LOG_FILE_DATE_REGEX = re.compile(r"""(?P<year>\d{4})
                                     [^\d]
                                     (?P<month>[01]?\d)
                                     [^\d]
                                     (?P<day>[0-3]?\d)
                                     [^\d]
                                     (?P<hour>[0-2]?\d)
                                     [^\d]
                                     (?P<minute>[0-6]?\d)
                                     [^\d]
                                     (?P<second>[0-6]?\d)""", re.VERBOSE)


MOD_LINES_REGEX = re.compile(r"""^([0-2\s]?\d)
                                  [^\d]
                                  ([0-6]\d)
                                  [^\d]
                                  ([0-6]\d)
                                  \s?\=*\sList\sof\smods\s\=*
                                  \n
                                  (?P<mod_lines>(^([0-2\s]?\d)
                                                  [^\d]
                                                  ([0-6]\d)
                                                  [^\d]
                                                  ([0-6]\d)
                                                  \s(?!\=).*\n)
                                                  +
                                  )""", re.VERBOSE | re.MULTILINE)
