"""
WiP.

Soon.
"""

# region [Imports]

# * Standard Library Imports ---------------------------------------------------------------------------->
import os
import sys
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Union, Literal, Optional, TypeAlias
from pathlib import Path

# * Third Party Imports --------------------------------------------------------------------------------->
from PIL import Image
from PIL.ExifTags import TAGS

if sys.version_info >= (3, 11):
    from typing import Self
else:
    from typing_extensions import Self

# * Standard Library Imports ---------------------------------------------------------------------------->
from hashlib import blake2s

# * Qt Imports --------------------------------------------------------------------------------------->
from PySide6.QtGui import QIcon, QImage, QPixmap
from PySide6.QtCore import Qt, QSize

# * Third Party Imports --------------------------------------------------------------------------------->
import numpy as np
import numpy.typing as np_typing

# * Type-Checking Imports --------------------------------------------------------------------------------->
if TYPE_CHECKING:
    ...

# endregion [Imports]

# region [TODO]


# endregion [TODO]

# region [Logging]


# endregion [Logging]

# region [Constants]

THIS_FILE_DIR = Path(__file__).parent.absolute()
PATH_TYPE: TypeAlias = Union[os.PathLike, str]
# endregion [Constants]


class BaseImageInfo(ABC):

    def __init__(self) -> None:
        self._file_size: int = None
        self._size: tuple[int, int] = None
        self._format: str = None
        self._exif: Optional[dict] = None
        self._other_info: Optional[dict] = None
        self._content_hash: str = None

    @property
    def file_size(self) -> int:
        return self._file_size

    @property
    def size(self) -> tuple[int, int]:
        return self._size

    @property
    def width(self) -> int:
        return self._size[0]

    @property
    def height(self) -> int:
        return self._size[1]

    @property
    def format(self) -> str:
        return self._format

    @property
    def exif(self) -> Optional[dict]:
        return self._exif

    @property
    def other_info(self) -> Optional[dict]:
        return self._other_info

    @property
    def content_hash(self) -> str:
        if self._content_hash is None:
            self._content_hash = self.get_content_hash()
        return self._content_hash

    @abstractmethod
    def get_content_hash(self) -> str:
        ...

    @abstractmethod
    def load_image_info(self) -> Self:
        ...


class LocalImageInfo(BaseImageInfo):

    def __init__(self, image_path: Path) -> None:
        super().__init__()
        self._image_path = image_path

    def get_content_hash(self) -> str:
        content_hash = blake2s(usedforsecurity=False)
        chunk_size: int = 26214400  # 25mb
        with self._image_path.open("rb", buffering=chunk_size) as f:
            for chunk in f:
                content_hash.update(chunk)
        return content_hash.hexdigest()

    def load_image_info(self) -> Self:
        with Image.open(self._image_path) as image:
            self._size = image.size
            self._format = image.format
            self._exif = {TAGS[k]: v for k, v in image.getexif().items()}
            self._other_info = dict(image.info)
        return self


class LocalImage:
    standard_icon_size: tuple[int, int] = (32, 32)

    def __init__(self, image_path: PATH_TYPE) -> None:
        self.image_path: Path = Path(image_path)
        self._image_info = None

    @property
    def name(self) -> str:
        return self.image_path.stem

    @property
    def image_info(self) -> LocalImageInfo:
        if self._image_info is None:
            self._image_info = LocalImageInfo(self.image_path).load_image_info()
        return self._image_info

    def to_pil_image(self) -> Image.Image:
        return Image.open(self.image_path)

    def to_numpy_array(self, rotate: float = 0.0) -> np_typing.ArrayLike:
        image = Image.open(self.image_path).rotate(rotate)
        return np.asarray(image)

    def to_qimage(self) -> QImage:
        return QImage(self.image_path)

    def to_qicon(self, icon_size: Union[Literal["original", "standard"], tuple[int, int], QSize] = "standard") -> QIcon:
        if isinstance(icon_size, str) and icon_size == "standard":
            icon_size = QSize(self.standard_icon_size[0], self.standard_icon_size[1])
        elif isinstance(icon_size, str) and icon_size == "original":
            icon_size = None

        elif isinstance(icon_size, tuple):
            icon_size = QSize(icon_size[0], icon_size[1])

        if icon_size is not None:
            pixmap = QPixmap(self.image_path)
            pixmap = pixmap.scaled(icon_size, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
            icon = QIcon(pixmap)

        else:
            icon = QIcon(self.image_path)

        return icon

    def to_qpixmap(self) -> QPixmap:
        return QPixmap(self.image_path)

    def to_bytes(self) -> bytes:
        return self.image_path.read_bytes()

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(image_path={self.image_path})"


# region [Main_Exec]
if __name__ == '__main__':
    pass

# endregion [Main_Exec]
