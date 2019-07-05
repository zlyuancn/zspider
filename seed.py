# -*- coding: utf-8 -*-
"""
-------------------------------------------------
   File Name：    seed.py
   Author :       Zhang Fan
   date：         2019/3/27
   Description :
-------------------------------------------------
"""
__author__ = 'Zhang Fan'

from urllib.parse import urljoin
import json
import copy

from lxml import etree


class Seed():
    __attrs_dict__ = {
        'parser_func': None,
        'check_html_func': None,
        'meta': None,
        'encoding': 'utf8',
        'ua_type': None,

        'method': 'get',
        'url': None,
        'params': None,
        'data': None,
        'headers': None,
        'cookies': None,
        'files': None,
        'auth': None,
        'timeout': None,
        'allow_redirects': True,
        'proxies': None,
        'hooks': None,
        'stream': False,
        'verify': False,
        'cert': None,
        'json': None,
    }

    _response = None
    _response_etree = None
    _response_json = None

    def __init__(self, url, parser_func, **kwargs):
        self.url = url
        self.parser_func = parser_func

        kwargs = dict(url=url, parser_func=parser_func, **kwargs)  # 原始参数
        self._raw_kwargs = copy.deepcopy(kwargs)

        # 如果参数存在键优先放入参数的值, 否则放入原生__attrs_dict__的值
        for key, value in self.__attrs_dict__.items():
            setattr(self, key, (kwargs[key] if key in kwargs else value))

    def _set_response(self, response):
        self._response = response
        self._response_etree = None
        self._response_json = None

    @property
    def response(self):
        return self._response

    @property
    def response_text(self):
        return self._response.text

    @property
    def response_etree(self):
        if self._response_etree is None:
            try:
                self._response_etree = etree.HTML(self._response.text)
            except:
                pass
        return self._response_etree

    @property
    def response_json(self):
        if self._response_json is None:
            try:
                text = self._response.text
                if text[0] == chr(65279):
                    text = text[1:]
                self._response_json = json.loads(text)
            except:
                pass
        return self._response_json

    @property
    def raw_data(self):
        return self._response.content

    def to_save_dict(self):
        # 将实例的参数转化为dict, 获取到的是实例的数据而不是传入的原始数据, 此数据用于存入到种子队列
        must_keys = ['url', 'parser_func']
        result = {}
        for key in self.__attrs_dict__:
            value = getattr(self, key, None)
            if key in must_keys or value != self.__attrs_dict__[key]:
                result[key] = value
        return copy.deepcopy(result)

    def to_req_dict(self):
        # 将实例的参数转化为dict, 获取到的是实例的数据而不是传入的原始数据, 此数据用于请求
        must_keys = ['url', 'parser_func']
        result = {}
        for key in self.__attrs_dict__:
            value = getattr(self, key, None)
            if key in must_keys or value is not None:
                result[key] = value
        return copy.deepcopy(result)

    def url_join(self, link):
        assert self._response
        return urljoin(self._response.url, link)  # 必须用跳转后的页面地址进行链接才能获取真实的地址


if __name__ == '__main__':
    a = Seed('h://w.aa.c', None)
    print(a.to_save_dict())
    print(a.to_req_dict())
