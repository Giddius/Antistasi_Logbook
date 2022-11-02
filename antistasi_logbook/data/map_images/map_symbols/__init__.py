from pathlib import Path
import numpy as np
from numpy.typing import ArrayLike
from PIL import Image, ImageEnhance


MAP_SYMBOLS_DIR = Path(__file__).parent.resolve()


def ReduceOpacity(im, opacity):
    """
    Returns an image with reduced opacity.
    Taken from http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/362879
    """
    assert opacity >= 0 and opacity <= 1
    if im.mode != 'RGBA':
        im = im.convert('RGBA')
    else:
        im = im.copy()
    alpha = im.split()[3]
    alpha = ImageEnhance.Brightness(alpha).enhance(opacity)
    im.putalpha(alpha)
    return im


def get_map_symbol_as_np_array(name: str, as_size: tuple[int, int] = None, new_alpha: float = None) -> ArrayLike:
    file = MAP_SYMBOLS_DIR.joinpath(name.upper() + '.png')
    img: Image.Image = Image.open(file).rotate(-90)
    if as_size is not None:
        img = img.thumbnail(as_size, Image.ANTIALIAS)
    if new_alpha is not None:
        img = ReduceOpacity(img, new_alpha)
    return np.asarray(img)
