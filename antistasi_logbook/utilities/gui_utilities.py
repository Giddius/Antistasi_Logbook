"""
WiP.

Soon.
"""

# region [Imports]

# * Standard Library Imports ---------------------------------------------------------------------------->
from typing import Literal
from pathlib import Path

# * PyQt5 Imports --------------------------------------------------------------------------------------->
from PySide6.QtWidgets import QFrame

# endregion[Imports]

# region [TODO]


# endregion [TODO]

# region [Logging]


# endregion[Logging]

# region [Constants]

THIS_FILE_DIR = Path(__file__).parent.absolute()

# endregion[Constants]


def make_line(direction: Literal["horizontal", "vertical"]):
    line = QFrame()
    direction = QFrame.HLine if direction == "horizontal" else QFrame.VLine
    line.setFrameShape(direction)
    line.setFrameShadow(QFrame.Sunken)
    return line


# region[Main_Exec]
if __name__ == '__main__':
    pass

# endregion[Main_Exec]
