from pathlib import Path
from typing import Optional
from enum import Enum

STYLE_SHEET_DIR = Path(__file__).parent.absolute()


ALL_STYLE_SHEETS: dict[str, Path] = {}
for file in STYLE_SHEET_DIR.iterdir():
    if file.is_file() and file.suffix.casefold() == '.qss' and file.stem != 'dynamic_style_additions':
        ALL_STYLE_SHEETS[file.name.casefold()] = file.resolve()


def get_style_sheet_data(name: str) -> Optional[str]:
    name = name.casefold()
    if not name.endswith('.qss'):
        name = name + '.qss'

    if name in ALL_STYLE_SHEETS:
        path = ALL_STYLE_SHEETS[name]
        return path.read_text(encoding='utf-8', errors='ignore')
