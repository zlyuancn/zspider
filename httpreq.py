# -*- coding: utf-8 -*-
"""
-------------------------------------------------
   File Name：    httpreq.py
   Author :       Zhang Fan
   date：         2019/3/27
   Description :
-------------------------------------------------
"""
__author__ = 'Zhang Fan'

import time
import traceback

# import requests.packages.urllib3
# requests.packages.urllib3.disable_warnings()  # 关闭SSL认证警告
import urllib3

urllib3.disable_warnings()  # 关闭SSL认证警告

import copy
import importlib

from requests import Session
from requests import Request
from requests.utils import dict_from_cookiejar

from zspider.simplelib import dict_update_ignore_case
from zspider.simplelib import get_cookies_from_request
from zspider.simplelib import merge_cookies
from zspider.simplelib import get_non_cookies
from zspider.public_constant import Public_Constant
from zspider.logger import logger
from zspider.except_retry import except_retry
from zspider.random_headers import random_headers
from zspider.get_config import get_config


class downloader_exception(Exception):
    pass


class httpreq():
    def __init__(self, use_cookie=False):
        self.log = logger('httpreq')
        self.log.info('初始化 downloader')
        self.session = Session()
        self.previous_cookies = None  # type:dict
        self.proxy_inst = self.get_proxy_inst()

        self.use_cookie = use_cookie

        self.make_request_params = dict(
            method='get',
            url=None,
            files=None,
            data=None,
            json=None,
            params=None,
            auth=None,
            cookies=None,
            hooks=None,
        )

    @except_retry
    def req(self, seed_inst):
        seed_dict = seed_inst.to_req_dict()
        try:
            self.log.info(f'请求: {seed_dict.get("url")}')
            self._clear_session_cookie()  # 无论如何都清除之前的cookie, 由seed传入cookie

            req_inst = self._make_req_from_seed(seed_dict)  # 根据seed构建一个Request实例
            prep = self.session.prepare_request(req_inst)  # 让session准备好

            proxies = seed_dict.get('proxies') or self.proxy_inst.get_proxy()
            if proxies:
                self.log.info(f'使用代理 : {proxies.get("http", "non_proxy")}')

            settings = self.session.merge_environment_settings(
                prep.url, proxies or dict(),
                stream=seed_dict.get('stream') or False,
                verify=seed_dict.get('verify') or False,
                cert=seed_dict.get('cert')
            )

            send_kwargs = {
                'timeout': seed_dict.get('timeout') or Public_Constant.req_timeout,
                'allow_redirects': seed_dict.get('allow_redirects', True),
            }
            send_kwargs.update(settings)

            req_time = time.time()
            resp = self.session.send(prep, **send_kwargs)

            if self.use_cookie:
                req_cookies = get_cookies_from_request(req_inst)
                session_cookies = dict_from_cookiejar(self.session.cookies)
                self.previous_cookies = merge_cookies(req_cookies, session_cookies)  # session_cookies是请求后服务器的设置,优先级更高

            self.log.info('请求成功, 本次请求耗时<%.2fs>' % (time.time() - req_time))
            return resp
        except:
            self.log.warning(f'{traceback.format_exc()}\n请求失败,切换代理后进行重试')
            self.proxy_inst.change_proxy()
            if seed_dict.get('proxies'):
                seed_inst.proxies = self.proxy_inst.get_proxy()
            raise downloader_exception
        finally:
            # requests底层漏洞, 不关闭session在偶然情况下会导致内存泄漏
            self.session.close()

    def _make_req_from_seed(self, seed_dict: dict):
        # 优先取seed_dict的值
        req_params = {key: (seed_dict[key] if key in seed_dict else value)
                      for key, value in self.make_request_params.items()}
        req_params['headers'] = self.get_headers_of_seed(seed_dict)
        return Request(**req_params)

    def get_headers_of_seed(self, seed_dict):
        headers = random_headers(seed_dict.get('ua_type'))
        seed_headers = seed_dict.get('headers')
        if isinstance(seed_headers, dict):
            dict_update_ignore_case(headers, copy.deepcopy(seed_headers))  # 允许修改headers的值, 允许修改为None
        return headers

    def _clear_session_cookie(self):
        self.previous_cookies = None
        self.session.cookies = get_non_cookies()

    def get_proxy_inst(self):
        proxy_pack_name = get_config().get_value('proxy', 'proxy_pack_name', 'zspider.proxy_base')
        proxy_class_name = get_config().get_value('proxy', 'proxy_class_name', 'proxy_base')
        module_file = importlib.import_module(proxy_pack_name)
        cls = getattr(module_file, proxy_class_name)
        return cls()

    def change_proxy(self):
        self.proxy_inst.change_proxy()


if __name__ == '__main__':
    a = httpreq()
    from zspider.seed import Seed

    url = 'https://www.baidu.com/'
    seed = Seed(url, None)
    res = a.req(seed)
    print(res.text)
