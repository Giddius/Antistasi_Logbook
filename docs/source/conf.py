
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

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'alabaster'
html_static_path = ['_static']
