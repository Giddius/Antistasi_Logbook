from json import JSONDecoder, JSONEncoder
from typing import Any
from datetime import datetime, timezone, timedelta


class DatetimeJsonEncoder(JSONEncoder):
    def default(self, o: Any) -> Any:
        if isinstance(o, datetime):
            return datetime.isoformat()
        return super().default(o)
