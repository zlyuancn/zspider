# -*- coding: utf-8 -*-
"""
-------------------------------------------------
   File Name：    proxy_base.py
   Author :       Zhang Fan
   date：         2019/3/27
   Description :
-------------------------------------------------
"""
__author__ = 'Zhang Fan'

from zspider.get_config import get_config


class proxy_base():

    def __init__(self):
        config = get_config().get_table('proxy')
        self.use_proxy = config.get('use_proxy')
        self.proxy_server = config.get('proxy_server')
        self.proxy_path = config.get('proxy_path')
        self.except_wait = config.get('except_wait')
        self.proxy_init()

    def proxy_init(self):
        # 初始化后会调用这个函数
        pass

    def get_proxy(self):
        # 返回当前使用的代理, 字典{"http": "http://主机:端口", "https": "http://主机:端口"}
        pass

    def change_proxy(self):
        # 要求切换代理地址
        pass


if __name__ == '__main__':
    a = proxy_base()
    print(a.use_proxy)
    print(a.proxy_server)
    print(a.proxy_path)
    print(a.except_wait)
