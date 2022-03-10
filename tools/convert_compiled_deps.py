from pathlib import Path
import re

THIS_FILE_DIR = Path(__file__).parent.absolute()

in_file = THIS_FILE_DIR.parent.joinpath("compiled_dependencies.txt")

text = in_file.read_text(encoding='utf-8', errors='ignore')

lines = []
for line in text.splitlines():
    if not line:
        continue
    if line.startswith("#"):
        continue
    lines.append(f'"{line.strip()}",')


in_file.write_text('\n'.join(lines))
