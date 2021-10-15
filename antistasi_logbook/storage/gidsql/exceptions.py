class GidSqliteError(Exception):
    pass


class GidSqliteColumnAlreadySetError(GidSqliteError):

    def __init__(self, table_name, column_name, msg=None):
        self.table_name = table_name
        self.column_name = column_name
        self.msg = '' if msg is None else msg
        self.message = f"The SQL phrase for table '{self.table_name}', has the column '{self.column_name}' already set. {self.msg}"
        super().__init__(self.message)


class GidSqliteSemiColonError(GidSqliteError):
    def __init__(self, msg=None):
        self.extra_message = '' if msg is None else msg
        self.message = f"forbidden Semi-colon was detected in input. {self.extra_message}"
        super().__init__(self.message)


class GidSqliteNoTableNameError(GidSqliteError):
    def __init__(self, extra_msg=None):
        self.message = "No table name set!"
        if extra_msg is not None:
            self.message += f' {str(extra_msg)}'
        super().__init__(self.message)