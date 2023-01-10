"""
WiP.

Soon.
"""

# region [Imports]

# * Standard Library Imports ---------------------------------------------------------------------------->
from pathlib import Path

# * Third Party Imports --------------------------------------------------------------------------------->
from rich.style import Style

# * Gid Imports ----------------------------------------------------------------------------------------->
from gidapptools import get_logger

# endregion [Imports]

# region [TODO]


# endregion [TODO]

# region [Logging]


# endregion [Logging]

# region [Constants]

THIS_FILE_DIR = Path(__file__).parent.absolute()


log = get_logger(__name__)
# endregion [Constants]


PANEL_STYLE = Style(bgcolor="black", )
PANEL_BORDER_STYLE = Style(bold=True, color="white")

# region [Main_Exec]

if __name__ == '__main__':
    pass

# endregion [Main_Exec]
