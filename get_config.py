# -*- coding: utf-8 -*-
"""
-------------------------------------------------
   File Name：    get_config.py
   Author :       Zhang Fan
   date：         2019/3/26
   Description :
-------------------------------------------------
"""
__author__ = 'Zhang Fan'

import os

from zsingleton.singleton_decorator import singleton
import zinifile

from zspider import get_config_file


@singleton
class get_config():
    def __init__(self):
        config_file = get_config_file()
        assert os.path.isfile(config_file), f'配置文件不存在:{config_file}'
        self._config = zinifile.load(config_file)

    @property
    def config(self):
        return self._config

    def get_table(self, table, default=None):
        return self.config.get(table, default)

    def get_value(self, table, key, default=None):
        section = self.config.get(table)
        if section is None:
            return default
        return section.get(key, default)


if __name__ == '__main__':
    config = get_config().config
    print(config.seed_db.host)
