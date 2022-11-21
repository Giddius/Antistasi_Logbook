
# region [Imports]

import os
import sys
import time
from pathlib import Path
from types import ModuleType
import importlib.util

sys.path.insert(0, os.path.abspath('.'))
sys.path.insert(0, os.path.abspath('../antistasi_logbook'))


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
              "sphinxcontrib.fulltoc",
              "sphinx.ext.githubpages",
              'sphinx_copybutton',
              "sphinx_design",
              'sphinx.ext.autosectionlabel',
              'sphinx_issues']

templates_path = ['_templates']
exclude_patterns = []

# endregion [Sphinx_Settings]


def fix_multiline_text(in_text: str, indentation: int = 0) -> str:
    fixed_lines = in_text.strip().splitlines()
    return '\n'.join(('   ' * indentation) + line.strip() for line in fixed_lines)


def do_underline(in_title: str) -> str:
    ul = "=" * int(len(in_title) * 1.25)
    return f"\n{in_title}\n{ul}\n\n"


html_theme = 'alabaster'
html_static_path = ['_static']

html_context = {"do_underline": do_underline,
                "fix_multiline_text": fix_multiline_text}

source_suffix = {".rst": "restructuredtext",
                 ".rst_t": "restructuredtext"}


def rstjinja(app, docname, source):
    """
    Render our pages as a jinja template for fancy templating goodness.
    """
    print(f"{docname=}\n")
    src = source[0]
    rendered = app.builder.templates.render_string(
        src, app.config.html_context
    )
    source[0] = rendered


def setup(app):
    app.connect("source-read", rstjinja)
