"""
WiP.

Soon.
"""

# region [Imports]

# * Standard Library Imports ---------------------------------------------------------------------------->
from typing import Mapping
from pathlib import Path

# endregion[Imports]

# region [TODO]


# endregion [TODO]

# region [Logging]


# endregion[Logging]

# region [Constants]

THIS_FILE_DIR = Path(__file__).parent.absolute()

# endregion[Constants]


def dict_to_html(in_dict: Mapping, title: str = None) -> str:
    text_lines = []
    if title is not None:
        text_lines.append(f"<title>{title!s}</title>")
    text_lines.append("<dl>")
    for name, value in in_dict.items():
        text_lines.append(f"    <dt>{name!s}</dt>")
        text_lines.append(f"    <dd>{value!s}</dd>")

    text_lines.append('</dl>')
    return '\n'.join(text_lines)

# region[Main_Exec]


if __name__ == '__main__':
    pass

# endregion[Main_Exec]
