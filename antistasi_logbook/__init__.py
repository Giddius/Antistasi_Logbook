"""Antistasi_Serverlog_Statistics"""
__version__ = '0.1.0'

from gidapptools.meta_data import setup_meta_data
import logging

logging.basicConfig(level=logging.INFO)


import os


setup_meta_data(__file__, use_output_numbering=True, use_rule_seperator=True, use_extra_newline_pre=True, use_extra_newline_post=True)
