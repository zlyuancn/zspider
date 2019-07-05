# -*- coding: utf-8 -*-
"""
-------------------------------------------------
   File Name：    dup_filter.py
   Author :       Zhang Fan
   date：         2019/3/27
   Description :
-------------------------------------------------
"""
__author__ = 'Zhang Fan'

import hashlib

from zsingleton.singleton_decorator import singleton

from zspider.logger import logger
from zspider.public_constant import Public_Constant
from zspider.db_handler import get_ssdb_inst


@singleton
class dup_filter():
    def __init__(self, spider_name):
        self.spider_name = spider_name
        self.log = logger(spider_name)
        self.log.info('初始化 dup_filter')
        self.collname = f'{spider_name}:{Public_Constant.dup_collname_suffix}'
        self._db_inst = get_ssdb_inst()

    def check(self, item, collname=None):
        # 返回是否允许访问
        self._db_inst.change_coll(collname or self.collname)
        text = str(item)
        if self._db_inst.set_add(self._make_md5(text)):
            return True
        self.log.info(f'已过滤:{text}')

    def remove(self, item, collname=None):
        self._db_inst.change_coll(collname or self.collname)
        text = str(item)
        if self._db_inst.set_remove(self._make_md5(text)):
            self.log.info(f'已移除:{text}')
            return True

    def _make_md5(self, text):
        way = hashlib.md5()
        way.update(text.encode('utf8'))
        return way.hexdigest()

    def clear_queue(self, collname=None):
        # 清空dup队列
        coll = collname or self.collname
        self.log.info(f'正在清除: {coll}')
        self._db_inst.set_clear(coll)


if __name__ == '__main__':
    a = dup_filter('aaa')
    a.check('123')
    a.check('123')
    a.remove('123')
