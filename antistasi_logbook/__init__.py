"""Antistasi_Serverlog_Statistics"""
__version__ = '0.1.0'

from gidapptools.meta_data import setup_meta_data
import logging
from pathlib import Path
logging.basicConfig(level=logging.INFO)


THIS_FILE_DIR = Path(__file__).parent.absolute()

import os


def setup():
    setup_meta_data(__file__, configs_to_create=[THIS_FILE_DIR.joinpath("data", "general_config.ini")], spec_to_create=[THIS_FILE_DIR.joinpath("data", "general_configspec.json")])
