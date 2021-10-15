# region [Imports]

# * Standard Library Imports ---------------------------------------------------------------------------->
import os
import logging
import sqlite3 as sqlite
from pprint import pformat

# * Gid Imports ----------------------------------------------------------------------------------------->


# endregion[Imports]

__updated__ = '2020-11-26 17:04:37'

# region [AppUserData]

# endregion [AppUserData]

# region [Logging]

log = logging.getLogger('gidsql')


# endregion[Logging]

# region [Constants]

# endregion[Constants]


class GidSqliteActionBase:
    def __init__(self, in_db_loc, in_pragmas=None):
        self.db_loc = in_db_loc
        self.pragmas = in_pragmas

    @property
    def exists(self):
        """
            checks if the db exist and logs it

            Returns
            -------
            bool
                bool if the file exist or not
            """
        if os.path.isfile(self.db_loc):
            log.info("database at %s, does EXIST", self.db_loc)
            return True
        else:
            log.info("databse at %s does NOT EXIST", self.db_loc)
            return False

    @staticmethod
    def _handle_error(error, sql_phrase, variables):
        log.critical("%s - with SQL --> %s and args[%s]", str(error), sql_phrase, pformat(variables))
        if 'syntax error' in str(error):
            raise SyntaxError(error)

        raise sqlite.Error(error)

    def _execute_pragmas(self, in_cursor):
        if self.pragmas is not None and self.pragmas != '':
            in_cursor.executescript(self.pragmas)
            log.debug("Executed pragmas '%s' successfully", self.pragmas)

    def __repr__(self):
        return f"{self.__class__.__name__} ('{self.db_loc}')"

    def __str__(self):
        return self.__class__.__name__


# region[Main_Exec]


if __name__ == '__main__':
    pass

# endregion[Main_Exec]
