# -*- coding: utf-8 -*-
"""
-------------------------------------------------
   File Name：    __init__.py.py
   Author :       Zhang Fan
   date：         2019/3/26
   Description :
-------------------------------------------------
"""
__author__ = 'Zhang Fan'

import os
import sys


def get_config_file():
    file = os.getenv('ZSPIDER_CONFIG')
    if file:
        return file
    if 'win' in sys.platform.lower():
        return 'c:/zspider/config.ini'
    return '/etc/zspider/config.ini'
