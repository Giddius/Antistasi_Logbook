"""
WiP.

Soon.
"""

# region [Imports]

# * Standard Library Imports ---------------------------------------------------------------------------->
import os
import base64
from io import BytesIO
from typing import Union, Literal, Optional, Any
from pathlib import Path
from datetime import datetime, timezone, timedelta

# * Third Party Imports --------------------------------------------------------------------------------->
import yarl
import httpx
from PIL import Image
from dateutil.tz import UTC, tzoffset
from playhouse.fields import CompressedField
from playhouse.apsw_ext import Field, BlobField, TextField, BooleanField, BigIntegerField
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

# * Gid Imports ----------------------------------------------------------------------------------------->
from gidapptools import get_logger

# * Local Imports --------------------------------------------------------------------------------------->
from antistasi_logbook.utilities.misc import VersionItem
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


class FakeField:
    field_type = "FAKE"

    def __init__(self, name: str, verbose_name: str) -> None:
        self.name = name
        self.verbose_name = verbose_name
        self.help_text = None


class CaselessTextField(TextField):

    def db_value(self, value):
        if value is not None:
            value = str(value).casefold()
        return super().db_value(value)

    def python_value(self, value):
        if value is not None:
            value = value.casefold()
        return super().python_value(value)


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


class VersionField(TextField):
    """
    Field to store a version.

    Version has to be in the format `MAJOR.MINOR.PATCH.EXTRA` where `EXTRA` is optional.

    """
    field_type = "VERSION"

    def db_value(self, value: VersionItem):
        if value is not None:
            return str(value)

    def python_value(self, value) -> Optional[VersionItem]:
        if value is not None:
            return VersionItem.from_string(str(value))


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


class AwareTimeStampField(BigIntegerField):
    field_type = 'TIMESTAMP'
    mult_factor = 1000000

    def __init__(self, *args, **kwargs):

        self.utc = kwargs.pop('utc', False) or False
        if kwargs.get("null", False) is False:

            kwargs.setdefault('default', self._get_default)
        super().__init__(*args, **kwargs)

    def _get_default(self):
        if self.utc is True:
            return datetime.now(tz=UTC)
        return datetime.now()

    def db_value(self, value: datetime):
        if value is None:
            return
        if value.tzinfo is None:
            raise ValueError(f"tzinfo of {value} can not be non!")
        if value.tzinfo is not UTC and value.tzinfo is not timezone.utc:
            # value = value.astimezone(UTC)
            raise TypeError(f"tzinfo needs to be utc not {value.tzinfo!r}")
        raw_value = value.timestamp()
        return int(raw_value * self.mult_factor)

    def python_value(self, value):

        if value is None:
            return

        reduced_value = value / self.mult_factor
        dt = datetime.fromtimestamp(reduced_value)
        if self.utc and dt.tzinfo is None:
            dt = dt.astimezone(tz=UTC)

        return dt


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


class MarkedField(BooleanField):
    _default_kwarg_dict: dict[str, Any] = {"index": True,
                                           "default": False,
                                           "help_text": "Mark items to find them easier",
                                           "verbose_name": "Marked"}

    def __init__(self, **kwargs):
        actual_kwargs = self._default_kwarg_dict | kwargs
        super().__init__(**actual_kwargs)


class CommentsField(CompressedTextField):

    def __init__(self, compression_level=6, algorithm=CompressedField.ZLIB, **kwargs):
        kwargs.pop("verbose_name", None)
        kwargs.pop("help_text", None)
        kwargs.pop("null", None)
        super().__init__(compression_level=compression_level, algorithm=algorithm, verbose_name="Comments", help_text="Stored Comments", null=True, **kwargs)


class CompressedImageField(CompressedField):

    def __init__(self, return_as: Union[Literal["pil_image"], Literal['bytes'], Literal['qt_image']] = "bytes", **kwargs):
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
    field_type = 'BLOB'

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
    field_type = 'BLOB'

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
