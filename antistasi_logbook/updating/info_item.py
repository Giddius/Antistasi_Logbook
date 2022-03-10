"""
WiP.

Soon.
"""

# region [Imports]

# * Standard Library Imports ---------------------------------------------------------------------------->
from typing import Any
from pathlib import Path
from datetime import datetime

# * Third Party Imports --------------------------------------------------------------------------------->
import attr

# * Gid Imports ----------------------------------------------------------------------------------------->
from gidapptools import get_logger
from gidapptools.general_helper.timing import get_dummy_profile_decorator_in_globals
from gidapptools.general_helper.dict_helper import replace_dict_keys

# * Local Imports --------------------------------------------------------------------------------------->
from antistasi_logbook.utilities.enums import RemoteItemType
from antistasi_logbook.data.content_types import ContentType
from antistasi_logbook.utilities.path_utilities import RemotePath

# endregion[Imports]

# region [TODO]


# endregion [TODO]

# region [Logging]


# endregion[Logging]

# region [Constants]

THIS_FILE_DIR = Path(__file__).parent.absolute()


log = get_logger(__name__)
# endregion[Constants]

# {'content_language': None,
#  'content_length': None,
#  'content_type': '',
#  'created': None,
#  'display_name': None,
#  'etag': '"60112172c62eb"',
#  'href': '/dev_drive/remote.php/dav/files/Giddi/E-Books/',
#  'modified': datetime.datetime(2021, 1, 27, 8, 16, 50, tzinfo=datetime.timezone.utc),
#  'name': 'E-Books',
# 'type': 'directory'}


@attr.s(slots=True, weakref_slot=True, auto_attribs=True, auto_detect=True, kw_only=True, frozen=True)
class InfoItem:
    """
    Class to convert the received Json to and item and also change some names to abstract the remote-storage implementation.


    """
    type: RemoteItemType = attr.ib(converter=RemoteItemType)
    remote_path: RemotePath = attr.ib(converter=RemotePath)
    name: str = attr.ib()
    etag: str = attr.ib(converter=lambda x: x.strip('"' + "'"))
    raw_created_at: datetime = attr.ib(default=None)
    modified_at: datetime = attr.ib()
    content_type: ContentType = attr.ib(default=None, converter=ContentType)
    display_name: str = attr.ib(default=None)
    size: int = attr.ib(default=None)
    content_language: str = attr.ib(default=None)
    raw_info: dict[str, Any] = attr.ib()

    @name.default
    def _name_from_remote_path(self) -> str:
        return self.remote_path.stem

    @classmethod
    def from_webdav_info(cls, webdav_info: dict[str, Any]) -> "InfoItem":
        webdav_info = webdav_info.copy()
        raw_info = webdav_info.copy()
        webdav_info = replace_dict_keys(webdav_info, ('name', 'remote_path'), ('created', 'raw_created_at'), ('modified', 'modified_at'), ("content_length", "size"))
        webdav_info.pop('href')
        webdav_info['raw_info'] = raw_info
        return cls(**webdav_info)

    @classmethod
    def from_schema_item(cls, item) -> "InfoItem":
        """
        Used for Testing.
        """
        return cls(**item)

    def as_dict(self) -> dict[str, Any]:
        """
        Converts the instance to a dict.

        """
        return attr.asdict(self)


# region[Main_Exec]
if __name__ == '__main__':
    pass

# endregion[Main_Exec]
