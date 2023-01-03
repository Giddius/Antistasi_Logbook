
# region [Imports]

import os
import sys
import time
from pathlib import Path
from types import ModuleType
import textwrap
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
    'css/extra_cards_styling.css',

]

exclude_patterns = []


# get available styles via `pygmentize -L styles`
# pygments_style = "tomorrow-night-eighties"
pygments_style = "monokai"


# endregion [Sphinx_Settings]

html_copy_source = False
html_theme = 'furo'


html_context = {"base_css_name": html_theme}
rst_epilog = ""
html_theme_options = {"sidebarwidth": "10em",
                      "light_css_variables": {
                          "logbook-card-background-color": "#ffffef40",
                          "sd-color-shadow": "#00000080"

                      },
                      "dark_css_variables": {
                          "logbook-card-background-color": "#54544440",
                          "sd-color-shadow": "#ffffff40"
                      }}


class ExternalLink:

    def __init__(self, name: str, url: str, description: str = None) -> None:
        self.name = name
        self.url = url
        self.description = description

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name={self.name!r}, url={self.url!r}, description={self.description!r})"


def get_link_data() -> tuple[ExternalLink]:
    link_data_file = THIS_FILE_DIR.joinpath("_data").joinpath("links.json")
    if not link_data_file.exists():
        return tuple()
    try:
        with link_data_file.open("r", encoding='utf-8', errors='ignore') as f:
            return tuple(sorted([ExternalLink(**i) for i in json.load(f)], key=lambda x: x.name.casefold()))
    except Exception as e:
        print(e)

        return tuple()


def write_link_file(link_data: tuple[ExternalLink]) -> None:
    link_rst_file = THIS_FILE_DIR.joinpath("links.rst")
    with link_rst_file.open("w", encoding='utf-8', errors='ignore') as f:
        f.write("Links\n=====\n\n\n")
        for external_link in link_data:
            f.write(f"`{external_link.name} <{external_link.url}>`_\n")
            if external_link.description is not None:
                f.write(textwrap.indent(external_link.description, "   "))
            f.write("\n\n")


def add_to_epilog(_epilog: str, link_data: tuple[ExternalLink]) -> str:
    for external_link in link_data:
        _epilog += f"\n\n.. _{external_link.name}: {external_link.url}\n\n"
    return _epilog


def ensure_links():
    global rst_epilog
    link_data = get_link_data()
    write_link_file(link_data=link_data)
    rst_epilog = add_to_epilog(_epilog=rst_epilog, link_data=link_data)


ensure_links()

import create_db_diagram

create_db_diagram.from_sphinx_config()
