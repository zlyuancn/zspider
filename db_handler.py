# -*- coding: utf-8 -*-
"""
-------------------------------------------------
   File Name：    db_handler.py
   Author :       Zhang Fan
   date：         2019/3/27
   Description :
-------------------------------------------------
"""
__author__ = 'Zhang Fan'

from zssdb import ssdb_inst

from zspider.get_config import get_config


def get_ssdb_inst(**kwargs) -> ssdb_inst:
    section = get_config().get_table('ssdb')
    kw = {key: value for key, value in section.items()}
    kw.update(kwargs)
    return ssdb_inst(**kw)


if __name__ == '__main__':
    a = get_ssdb_inst()
    print(a)
