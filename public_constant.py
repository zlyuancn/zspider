# -*- coding: utf-8 -*-
"""
-------------------------------------------------
   File Name：    public_constant.py
   Author :       Zhang Fan
   date：         2019/3/26
   Description :
-------------------------------------------------
"""
__author__ = 'Zhang Fan'

from zconst.const_decorator import const

from zspider.get_config import get_config


class _except_retry_flag:
    pass


@const
class Public_Constant():
    '''公共常量'''
    seed_queue_suffix = eval(get_config().get_value('seed_queue', 'suffix',
                                                    "['vip', 'd1', 'd2', 'd3', 'seed', 'error']"))
    req_timeout = get_config().get_value('public_constant', 'req_timeout', 20)
    spider_err_wait_time = get_config().get_value('public_constant', 'spider_err_wait_time', 3)
    empty_seed_wait_time = get_config().get_value('public_constant', 'empty_seed_wait_time', 120)
    default_html_encoding = get_config().get_value('public_constant', 'default_html_encoding',
                                                   'utf8')
    retry_wait_fixed = get_config().get_value('public_constant', 'retry_wait_fixed', 0.5)
    max_attempt_count = get_config().get_value('public_constant', 'max_attempt_count', 5)

    seed_collname_suffix = 'seed'
    dup_collname_suffix = 'dup'
    error_seed_suffix = 'error'
    error_seed_parser_suffix = 'error_parser'

    except_retry_flag = _except_retry_flag
