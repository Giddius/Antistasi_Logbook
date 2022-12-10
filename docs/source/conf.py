
# region [Imports]

import os
import sys
import time
from pathlib import Path
from types import ModuleType
import importlib.util
import json

sys.path.insert(0, os.path.abspath('.'))
sys.path.insert(0, os.path.abspath('../antistasi_logbook'))

THIS_FILE_DIR = Path(__file__).parent.absolute()
# endregion[Imports]

# region [Project_Info]

project = 'Antistasi Logbook'
copyright = '2022, Antistasi-Tools'
author = 'Antistasi-Tools'
release = '0.4.6'
html_logo = "_images/app_logo.png"
html_favicon = "_images/app_favicon.png"
# endregion [Project_Info]

# region [Sphinx_Settings]

extensions = ['sphinxcontrib.mermaid',
              "sphinx_inline_tabs",
              "sphinx.ext.githubpages",
              'sphinx_copybutton',
              "sphinx_design",
              'sphinx.ext.autosectionlabel',
              #   "sphinxcontrib.fulltoc",
              'sphinx_issues']

templates_path = ['_templates']

html_static_path = ['_static']
html_css_files = [
    'css/extra_styling.css',
]

exclude_patterns = []


# get available styles via `pygmentize -L styles`
# pygments_style = "tomorrow-night-eighties"
pygments_style = "monokai"


# endregion [Sphinx_Settings]


html_theme = 'furo'


html_context = {"base_css_name": html_theme}


class ExternalLink:

    def __init__(self, name: str, url: str, description: str = None) -> None:
        self.name = name
        self.url = url
        self.description = description

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name={self.name!r}, url={self.url!r}, description={self.description!r})"


def get_link_data() -> tuple[ExternalLink]:
    link_file = THIS_FILE_DIR.joinpath("_data").joinpath("links.json")
    if not link_file.exists():
        return tuple()

    with link_file.open("r", encoding='utf-8', errors='ignore') as f:
        return tuple(ExternalLink(**i) for i in json.load(f))


print(get_link_data())
