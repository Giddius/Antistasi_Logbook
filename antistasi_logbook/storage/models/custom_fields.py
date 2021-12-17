"""
WiP.

Soon.
"""

# region [Imports]

# * Standard Library Imports ---------------------------------------------------------------------------->
import os
import base64
from io import BytesIO
from typing import Union, Literal, Optional
from pathlib import Path
from datetime import datetime, timezone, timedelta

# * Third Party Imports --------------------------------------------------------------------------------->
import yarl
import httpx
from PIL import Image
from peewee import Field, BlobField
from dateutil.tz import UTC, tzoffset
from playhouse.fields import CompressedField
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from antistasi_logbook.utilities.misc import Version
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from antistasi_logbook.utilities.path_utilities import RemotePath

# endregion[Imports]

# region [TODO]


# endregion [TODO]

# region [Logging]


# endregion[Logging]

# region [Constants]

THIS_FILE_DIR = Path(__file__).parent.absolute()

# endregion[Constants]


class RemotePathField(Field):
    field_type = "REMOTEPATH"

    def db_value(self, value: RemotePath) -> Optional[str]:
        if value is not None:
            if isinstance(value, str):
                value = RemotePath(value)
            return value._path.as_posix()

    def python_value(self, value) -> Optional[RemotePath]:
        if value is not None:
            return RemotePath(value)


class PathField(Field):
    field_type = "PATH"

    def db_value(self, value: Path) -> Optional[str]:
        if value is not None:
            if isinstance(value, str):
                value = Path(value)
            return value.as_posix()

    def python_value(self, value) -> Optional[Path]:
        if value is not None:
            return Path(value)


class VersionField(Field):
    field_type = "VERSION"

    def db_value(self, value: Version):
        if value is not None:
            return str(value)

    def python_value(self, value) -> Optional[Version]:
        if value is None:
            return None
        return Version.from_string(value)


class URLField(Field):
    field_type = "URL"

    def db_value(self, value: Union[str, yarl.URL, httpx.URL, Path]):
        if value is None:
            return value
        if isinstance(value, Path):
            value = value.as_uri()
        if not isinstance(value, yarl.URL):
            value = yarl.URL(str(value))
        return str(value)

    def python_value(self, value):
        if value is not None:
            return yarl.URL(value)


class BetterDateTimeField(Field):
    field_type = 'DATETIME'

    def db_value(self, value: Optional[datetime]):
        if value is not None:
            if value.tzinfo not in [UTC, timezone.utc]:
                raise RuntimeError(f"{value!r} is a different timezone than {UTC!r} or {timezone.utc!r} -> {value.tzinfo!r}")
            return value.isoformat()

    def python_value(self, value):
        if value is not None:
            return datetime.fromisoformat(value)


class TzOffsetField(Field):
    field_type = "TZOFFSET"

    def db_value(self, value: Optional[tzoffset]) -> Optional[str]:
        if value is not None:
            return value.utcoffset(None).total_seconds()

    def python_value(self, value: Optional[str]):
        if value is not None:
            seconds = value
            delta = timedelta(seconds=seconds)
            return tzoffset(f"+{str(timedelta)}", delta)


class CompressedTextField(CompressedField):

    def db_value(self, value: str):
        if value is not None:
            value = value.encode(encoding='utf-8', errors='ignore')
            return super().db_value(value)

    def python_value(self, value):
        if value is not None:
            value: bytes = super().python_value(value)
            return value.decode(encoding='utf-8', errors='ignore')


class CompressedImageField(CompressedField):

    def __init__(self, return_as: Union[Literal["pil_image"], Literal['bytes'], Literal['qt_image']] = "pil_image", **kwargs):
        super().__init__(**kwargs)
        return_func_table = {"pil_image": self.return_as_pil_image,
                             "bytes": self.return_as_bytes,
                             "qt_image": self.return_as_not_implemented}
        self.return_as = return_func_table.get(return_as, self.return_as_not_implemented)

    @staticmethod
    def image_to_byte_array(image: Image.Image):
        with BytesIO() as bf:
            image.save(bf, format=image.format)
            imgByteArr = bf.getvalue()
            return imgByteArr

    @staticmethod
    def return_as_pil_image(data: bytes) -> Image.Image:
        with BytesIO() as bf:
            bf.write(data)
            bf.seek(0)
            image = Image.open(bf)
            image.load()
            return image

    @staticmethod
    def return_as_bytes(data: bytes) -> bytes:
        return data

    @staticmethod
    def return_as_not_implemented(data: bytes) -> NotImplemented:
        return NotImplemented

    def db_value(self, value: Union[bytes, Path, Image.Image]):
        if value is not None:
            if isinstance(value, Path):
                bytes_value = self.image_to_byte_array(Image.open(value))
            elif isinstance(value, Image.Image):
                bytes_value = self.image_to_byte_array(value)
            elif isinstance(value, bytes):
                bytes_value = value
            return super().db_value(bytes_value)

    def python_value(self, value):
        if value is not None:
            bytes_value = super().python_value(value)
            return self.return_as(bytes_value)


class LoginField(BlobField):

    @property
    def key(self) -> bytes:
        raw_key = os.environ["USERDOMAIN"].encode(encoding='utf-8', errors='ignore')
        kdf = PBKDF2HMAC(algorithm=hashes.SHA256(),
                         length=32,
                         salt=os.getlogin().encode(encoding='utf-8', errors='ignore'),
                         iterations=100000)
        return base64.urlsafe_b64encode(kdf.derive(raw_key))

    def db_value(self, value: str):
        if value is not None:
            fernet = Fernet(self.key)
            return fernet.encrypt(value.encode(encoding='utf-8', errors='ignore'))

    def python_value(self, value):
        if value is not None:
            fernet = Fernet(self.key)
            return fernet.decrypt(value).decode(encoding='utf-8', errors='ignore')


class PasswordField(BlobField):

    @property
    def key(self) -> bytes:
        raw_key = os.environ["USERDOMAIN"].encode(encoding='utf-8', errors='ignore')
        kdf = PBKDF2HMAC(algorithm=hashes.SHA256(),
                         length=32,
                         salt=b"1",
                         iterations=100000)
        return base64.urlsafe_b64encode(kdf.derive(raw_key))

    def db_value(self, value: str):
        if value is not None:
            fernet = Fernet(self.key)
            return fernet.encrypt(value.encode(encoding='utf-8', errors='ignore'))

    def python_value(self, value):
        if value is not None:
            fernet = Fernet(self.key)
            return fernet.decrypt(value).decode(encoding='utf-8', errors='ignore')


# region[Main_Exec]
if __name__ == '__main__':

    pass
# endregion[Main_Exec]
