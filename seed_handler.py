# -*- coding: utf-8 -*-
"""
-------------------------------------------------
   File Name：    seed_handler.py
   Author :       Zhang Fan
   date：         2019/3/27
   Description :
-------------------------------------------------
"""
__author__ = 'Zhang Fan'

import time
import msgpack

from zsingleton.singleton_decorator import singleton

from zspider.logger import logger
from zspider.public_constant import Public_Constant
from zspider.db_handler import get_ssdb_inst


@singleton
class seed_handler():

    def __init__(self, spider_name):
        self.spider_name = spider_name
        self.log = logger(spider_name)
        self.log.info('初始化 seed_handler')

        self._seed_db_inst = get_ssdb_inst(decode_responses=False)
        queue_suffix = Public_Constant.seed_queue_suffix
        self.queue_collname_list = [f'{self.spider_name}:{suff}' for suff in queue_suffix]

    def get_seed(self, front=True):
        # 根据顺序遍历seed文档取出一条数据, 返回dict或None, 否则报错
        for collname in self.queue_collname_list:
            self._seed_db_inst.change_coll(collname)

            seed_raw = self._seed_db_inst.list_pop(front=front)
            if seed_raw is None:
                # self.log.debug(f'队列<{collname}>为空.')
                continue

            try:
                seed_dict = msgpack.loads(seed_raw, raw=False)
            except:
                self.log.error('seed不能转为dict,请检查种子格式,即将放入error队列')
                self.put_error_seed(seed_raw)
                raise Exception

            self.log.info(f'从<{collname}>队列取出一条种子')
            return seed_dict

    def put_seed(self, seed_dict: dict or bytes, suffix='seed', front=True):
        if not seed_dict:
            self.log.warning(f'空数据的种子已抛弃: {seed_dict}')

        collname = f'{self.spider_name}:{suffix}'
        self._seed_db_inst.change_coll(collname)

        if isinstance(seed_dict, dict):
            seed_bytes = msgpack.dumps(seed_dict, use_bin_type=True)
            result = self._seed_db_inst.list_push(seed_bytes, front=front)
            self.log.info(f'向<{suffix}>队列存入一条解析函数为<{seed_dict.get("parser_func")}>的种子,这个队列长度为 {result}')
        elif isinstance(seed_dict, bytes):
            result = self._seed_db_inst.list_push(seed_dict, front=front)
            self.log.info(f'向<{suffix}>队列存入一条bytes类型的种子数据,这个队列长度为 {result}')
        else:
            self.log.warning(f'类型为{type(seed_dict)}的种子已抛弃')

    def put_error_seed(self, seed_dict: dict or bytes, is_parser_error=False):
        '''放入错误种子, 错误种子总是放在队列末尾'''
        self.log.warning('将出错seed放入error队列')
        suffix = Public_Constant.error_seed_parser_suffix if is_parser_error else Public_Constant.error_seed_suffix
        self.put_seed(seed_dict, suffix=suffix, front=False)
        self.log.info(f'等待 {Public_Constant.spider_err_wait_time}秒')
        time.sleep(Public_Constant.spider_err_wait_time)

    def check_seeds_is_empty(self, check_error_queue=False):
        for collname in self.queue_collname_list:
            if not check_error_queue and 'error' in collname:
                continue

            if self._seed_db_inst.list_count(collname):
                return False
        return True

    def clear_queue(self, *queue_suffix):
        # 清空队列
        for suffix in queue_suffix:
            coll = f'{self.spider_name}:{suffix}'
            self.log.info(f'正在清除: {coll}')
            self._seed_db_inst.list_clear(coll)


if __name__ == '__main__':
    a = seed_handler('test')
    print(a.check_seeds_is_empty())
    a.put_seed({'a': '1'})
    print(a.check_seeds_is_empty())
