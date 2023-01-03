"""
WiP.

Soon.
"""

# region [Imports]

# * Standard Library Imports ---------------------------------------------------------------------------->
import os
import base64
from io import BytesIO
from typing import Any, Union, Literal, Optional, TypeAlias
from pathlib import Path
from datetime import datetime, timezone, timedelta

# * Third Party Imports --------------------------------------------------------------------------------->
import yarl
import httpx
from PIL import Image
from peewee import BigIntegerField
from dateutil.tz import UTC, tzoffset
from playhouse.fields import CompressedField
from playhouse.apsw_ext import Field, BlobField, CharField, TextField, BooleanField, BigIntegerField
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

# * Gid Imports ----------------------------------------------------------------------------------------->
from gidapptools import get_logger
from gidapptools.general_helper.timing import get_dummy_profile_decorator_in_globals

# * Local Imports --------------------------------------------------------------------------------------->
from antistasi_logbook.utilities.misc import VersionItem
from antistasi_logbook.utilities.local_image import LocalImage
from antistasi_logbook.utilities.path_utilities import RemotePath

try:
    import bz2
except ImportError:
    bz2 = None
try:
    import zlib
except ImportError:
    zlib = None
try:
    import lzma
except ImportError:
    lzma = None

# endregion[Imports]

# region [TODO]


# endregion [TODO]

# region [Logging]


# endregion[Logging]

# region [Constants]
get_dummy_profile_decorator_in_globals()
THIS_FILE_DIR = Path(__file__).parent.absolute()
log = get_logger(__name__)
PATH_TYPE: TypeAlias = Union[os.PathLike, str]
# endregion[Constants]


class AntistasiLogbookBaseField:

    def __init__(self, **kwargs) -> None:
        self.show_as_column = kwargs.pop("show_as_column", True)
        super().__init__(**kwargs)


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


class RemotePathField(TextField):

    def db_value(self, value: RemotePath) -> Optional[str]:
        if value is not None:
            return RemotePath(value)._path.as_posix()

    def python_value(self, value) -> Optional[RemotePath]:
        if value is not None:
            return RemotePath(value)


class PathField(TextField):

    def db_value(self, value: PATH_TYPE) -> Optional[str]:
        if value is None:
            return

        return Path(value).as_posix().casefold()

    def python_value(self, value: Optional[str]) -> Optional[Path]:
        if value is None:
            return
        return Path(value)


class LocalImageField(PathField):

    def db_value(self, value: Union[PATH_TYPE, LocalImage]) -> Optional[str]:
        if value is None:
            return
        if isinstance(value, LocalImage):
            value = value.image_path

        return super().db_value(value)

    def python_value(self, value: Optional[str]) -> Optional[LocalImage]:
        if value is None:
            return
        image_path = super().python_value(value)
        return LocalImage(image_path)


class VersionField(TextField):
    """
    Field to store a version.

    Version has to be in the format `MAJOR.MINOR.PATCH.EXTRA` where `EXTRA` is optional.

    """
    field_type = "TEXT"

    def db_value(self, value: VersionItem):
        if value is not None:
            return str(value)

    def python_value(self, value) -> Optional[VersionItem]:
        if value is not None:
            return VersionItem.from_string(str(value))


class URLField(CharField):

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
    field_type = 'BIGINT'
    mult_factor = 1000000
    allowed_tz = (UTC, timezone.utc)

    def __init__(self, *args, **kwargs):

        self.utc = kwargs.pop('utc', True) or True
        if kwargs.get("null", False) is False:

            kwargs.setdefault('default', self._get_default)
        super().__init__(*args, **kwargs)

    def _get_default(self):
        if self.utc is True:
            return datetime.now(tz=timezone.utc)
        return datetime.now()

    def check_is_utc(self, in_value: Optional[datetime]):
        if in_value is None:
            return
        try:
            if in_value.utcoffset().total_seconds() == 0:
                return
        except AttributeError:
            if in_value.tzinfo is None:
                raise ValueError(f"tzinfo of {in_value} can not be none!")

            if in_value.tzinfo not in self.allowed_tz:
                raise TypeError(f"tzinfo needs to be utc not {in_value.tzinfo!r}")

    def db_value(self, value: datetime):
        if value is None:
            return None
        # if self.utc is True:
        #     self.check_is_utc(value)
        return int(value.timestamp() * self.mult_factor)

    def python_value(self, value):
        if value is None:
            return

        tz = timezone.utc if self.utc is True else None
        if isinstance(value, datetime):
            log.debug("value %r is already a datetime", value)
        return datetime.fromtimestamp((value / self.mult_factor), tz=tz)


class TzOffsetField(Field):
    field_type = "FLOAT"

    def db_value(self, value: Optional[tzoffset]) -> Optional[str]:
        if value is not None:
            return value.utcoffset(None).total_seconds()

    def python_value(self, value: Optional[str]):
        if value is not None:
            seconds = value
            delta = timedelta(seconds=seconds)
            return tzoffset(f"+{str(timedelta)}", delta)


class LZMACompressedTextField(CompressedField):
    LZMA = "lzma"
    algorithm_to_import = {
        LZMA: lzma,

    }

    def __init__(self, *args, **kwargs):
        self.algorithm = self.LZMA
        self.compress = lzma.compress
        self.decompress = lzma.decompress
        super(CompressedField, self).__init__(*args, **kwargs)

    def db_value(self, value: str):
        if value is not None:
            if isinstance(value, str):
                value = value.encode(encoding='utf-8', errors='ignore')

            return self._constructor(self.compress(value))

    def python_value(self, value):
        if value is not None:
            value: bytes = super().python_value(value)
            return value.decode(encoding='utf-8', errors='ignore')


class TextBlobField(BlobField):

    def python_value(self, value):
        if value is not None:
            if isinstance(value, bytes):
                return value.decode(encoding='utf-8', errors='ignore')
            if isinstance(value, str):
                return value


class MarkedField(BooleanField):
    _default_kwarg_dict: dict[str, Any] = {"index": True,
                                           "default": False,
                                           "help_text": "Mark items to find them easier",
                                           "verbose_name": "Marked",
                                           "constraints": []}

    def __init__(self, **kwargs):
        extra_constraints = kwargs.pop("constraints", [])
        actual_kwargs = self._default_kwarg_dict | kwargs
        actual_kwargs["constraints"] += extra_constraints
        super().__init__(**actual_kwargs)


class CommentsField(TextField):
    ...


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
