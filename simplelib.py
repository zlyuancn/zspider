# -*- coding: utf-8 -*-
"""
-------------------------------------------------
   File Name：    simplelib.py
   Author :       Zhang Fan
   date：         2019/3/27
   Description :
-------------------------------------------------
"""
__author__ = 'Zhang Fan'

import copy

from requests.utils import cookiejar_from_dict  # dict转cookie
from requests.utils import get_encoding_from_headers
from requests.utils import get_encodings_from_content

from zspider.public_constant import Public_Constant


def dict_update_ignore_case(src_dict: dict, new_dict: dict):
    def lower_key(key):
        return key.lower() if isinstance(key, str) else key

    def set_value(item: dict, new_key, value):
        l_key = lower_key(new_key)

        for src_key in item:
            if lower_key(src_key) == l_key:
                del item[src_key]
                break

        item[new_key] = value

    for new_key, new_value in new_dict.items():
        set_value(src_dict, new_key, new_value)


def merge_cookies(cook1: dict, cook2: dict):
    result = copy.deepcopy(cook1 or {})
    if not cook2:
        return result

    result.update(copy.deepcopy(cook2))
    return result


def extract_headers_cookies(headers: dict):
    cookies = None
    for k, v in headers.items():
        if k.lower() == 'cookie':
            cookies = v
            break

    if cookies:
        result = dict()
        for line in cookies.split(';'):
            k = line.find('=')
            if k != -1:
                result[line[:k].strip()] = line[k + 1:].strip()
        return result


def get_cookies_from_request(req_inst):
    header_cookies = extract_headers_cookies(req_inst.headers)
    return merge_cookies(req_inst.cookies, header_cookies)  # header中的cookies优先级更高


def get_non_cookies():
    return cookiejar_from_dict({})


def html_encoding(response_inst):
    encoding = getattr(response_inst, 'encoding', None)
    if encoding is False:  # 不使用编码, 可能是非文本页面
        return

    if not encoding:
        html_text = response_inst.response.text[1:]  # 去除bom标记
        encodings = get_encodings_from_content(html_text)
        if encodings:
            encoding = encodings[0]

    if not encoding:
        encoding = get_encoding_from_headers(response_inst.response.headers)

    response_inst.response.encoding = encoding or Public_Constant.default_html_encoding
