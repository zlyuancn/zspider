# -*- coding: utf-8 -*-
"""
-------------------------------------------------
   File Name：    logger.py
   Author :       Zhang Fan
   date：         2019/3/27
   Description :
-------------------------------------------------
"""
__author__ = 'Zhang Fan'

import zlogger

from zspider.get_config import get_config


def logger(name):
    if '_log_instance' not in globals():
        section = get_config().get_table('log')

        write_stream = section.get("write_stream", True)
        write_file = section.get("write_file", True)
        write_path = section.get("write_path") or './'
        log_level = zlogger.logger_level(section.get("log_level", 'DEBUG').upper())
        log_interval = section.get("log_interval", 1)
        log_backupCount = section.get("log_backupCount", 2)

        globals()['_log_instance'] = zlogger.logger(name, write_stream=write_stream, write_file=write_file,
                                                    file_dir=write_path,
                                                    level=log_level, interval=log_interval, backupCount=log_backupCount)

    return globals()['_log_instance']


if __name__ == '__main__':
    a = logger('cs')
    a.info('aaa')
    a.info('123')
    b = logger('cs')
    b.info('aaa')
    b.info('123')
    print(a is b)
