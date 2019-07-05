# -*- coding: utf-8 -*-
"""
-------------------------------------------------
   File Name：    except_retry.py
   Author :       Zhang Fan
   date：         2019/3/27
   Description :
-------------------------------------------------
"""
__author__ = 'Zhang Fan'

import traceback

from zretry import retry

from zspider.logger import logger
from zspider.public_constant import Public_Constant


def except_retry(func):
    def error_callback(func):
        log = logger('except_retry')
        log.error(f'{traceback.format_exc()}\n执行函数<{func.__name__}>出错')

    return retry(interval=Public_Constant.retry_wait_fixed, max_attempt_count=Public_Constant.max_attempt_count,
                 result_retry_flag=Public_Constant.except_retry_flag, error_callback=error_callback)(func)


if __name__ == '__main__':
    @except_retry
    def fun():
        return 1 / 0


    fun()
