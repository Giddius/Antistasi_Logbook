from pathlib import Path
import os
import sys
import shutil
import subprocess
import cairosvg
from PIL import Image, ImageChops, ImageFilter, ImageOps


def make_output_path(in_path: Path, overwrite: bool = True) -> Path:
    stem = in_path.stem
    name = f"{stem}.png"
    out_path = in_path.with_name(name)
    return out_path


def add_margin(pil_img, top, right, bottom, left):
    width, height = pil_img.size
    new_width = width + right + left
    new_height = height + top + bottom
    result = Image.new(pil_img.mode, (new_width, new_height))
    result.paste(pil_img, (left, top))
    return result


def convert(in_path: Path, out_path: Path, **kwargs) -> None:
    default_kwargs = {"dpi": 600, "scale": 1}
    kwargs = default_kwargs | kwargs
    cairosvg.svg2png(url=in_path.as_posix(), write_to=out_path.as_posix(), **kwargs)

    back_image = Image.new("RGBA", (128, 128))

    image = Image.open(out_path)
    image.thumbnail((100, 100), Image.ANTIALIAS)

    pad_image = Image.new("RGBA", back_image.size)
    b0 = (pad_image.width - image.width) // 2, (pad_image.height - image.height) // 2
    pad_image.paste(image, b0)

    image = pad_image

    white_image = Image.new("RGBA", back_image.size, "white")

    alpha = image.getchannel("A")
    alpha = alpha.convert("L")
    alpha = alpha.filter(ImageFilter.BLUR)
    white_image.putalpha(alpha)
    b1 = (image.width - white_image.width) // 2, (image.height - white_image.height) // 2
    white_image.paste(image, b1)
    b = (back_image.width - image.width) // 2, (back_image.height - image.height) // 2

    back_image.paste(white_image, b)

    back_image.save(out_path, format="PNG")
    print(f"saved to {out_path.as_posix()!r}")


def main():
    for possible_path in sys.argv[1:]:
        try:
            path = Path(possible_path).resolve(strict=True)
            if not path.is_file():
                continue
            convert(in_path=path, out_path=make_output_path(path))
        except FileNotFoundError as e:
            print(e)


if __name__ == '__main__':
    main()
