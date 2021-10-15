# region [Imports]

# * Standard Library Imports ---------------------------------------------------------------------------->
import enum
import logging
import sqlite3 as sqlite
import textwrap
import asyncio
from typing import Union, Callable, Any
from threading import Lock
# * Gid Imports ----------------------------------------------------------------------------------------->


# * Local Imports --------------------------------------------------------------------------------------->
from antistasi_serverlog_statistic.storage.gidsql.db_action_base import GidSqliteActionBase
from contextlib import asynccontextmanager, nullcontext
# endregion[Imports]

__updated__ = '2020-11-28 02:04:13'

# region [AppUserData]

# endregion [AppUserData]

# region [Logging]

log = logging.getLogger('gidsql')


# endregion[Logging]

# region [Constants]

# endregion[Constants]


class Fetch(enum.Enum):
    All = enum.auto()
    One = enum.auto()

    @classmethod
    def _missing_(cls, value: object) -> Any:
        if isinstance(value, str):
            mod_value = value.casefold()
            for member_name, member_value in cls.__members__.items():
                if member_name.casefold() == mod_value:
                    return cls(member_value)
        return super()._missing_(value)


class GidSqliteReader(GidSqliteActionBase):

    FETCH_ALL = Fetch.All
    FETCH_ONE = Fetch.One

    def __init__(self, in_db_loc, in_pragmas=None, log_execution: bool = True):
        super().__init__(in_db_loc, in_pragmas)

        self.log_execution = log_execution

    def query(self, sql_phrase, variables: tuple = None, fetch: Fetch = Fetch.All, row_factory=None):

        conn = sqlite.connect(self.db_loc, isolation_level=None, detect_types=sqlite.PARSE_DECLTYPES)
        if row_factory is not None:
            conn.row_factory = row_factory
        cursor = conn.cursor()
        try:
            self._execute_pragmas(cursor)
            if variables is not None:
                cursor.execute(sql_phrase, variables)
                if self.log_execution is True:
                    _log_sql_phrase = ' '.join(sql_phrase.replace('\n', ' ').split())
                    _log_args = textwrap.shorten(str(variables), width=200, placeholder='...')
                    log.debug("Queried sql phrase '%s' with args %s successfully", _log_sql_phrase, _log_args)
            else:
                cursor.execute(sql_phrase)
                if self.log_execution is True:
                    _log_sql_phrase = ' '.join(sql_phrase.replace('\n', ' ').split())
                    log.debug("Queried Script sql phrase '%s' successfully", _log_sql_phrase)
            _out = cursor.fetchone() if fetch is Fetch.One else cursor.fetchall()
        except sqlite.Error as error:
            _log_sql_phrase = ' '.join(sql_phrase.replace('\n', ' ').split())
            _log_args = textwrap.shorten(str(variables), width=200, placeholder='...')
            self._handle_error(error, _log_sql_phrase, _log_args)
        finally:
            conn.close()
        return _out


if __name__ == '__main__':
    pass
