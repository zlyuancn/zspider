# -*- coding: utf-8 -*-
"""
-------------------------------------------------
   File Name：    spider_base.py
   Author :       Zhang Fan
   date：         2019/3/27
   Description :
-------------------------------------------------
"""
__author__ = 'Zhang Fan'

import os
import signal
import time
import traceback
import copy
from collections import Iterable

from zspider.get_config import get_config
from zspider.logger import logger
from zspider.except_retry import except_retry
from zspider.dup_filter import dup_filter
from zspider.public_constant import Public_Constant

from zspider.simplelib import merge_cookies
from zspider.simplelib import html_encoding
from zspider.httpreq import httpreq

from zspider.seed import Seed
from zspider.seed_handler import seed_handler


class spider_base():
    spider_name = ''
    method = 'get'
    encoding = None
    base_headers = None

    time_out = 20
    auto_cookie_enable = False

    check_html_func = None
    retry_http_code = []

    def __init__(self):
        assert self.spider_name, 'spider_name不能为空(不需要前缀spider_)'
        self.config = get_config()
        self.pid = os.getpid()

        self.log = logger(self.spider_name)
        self.log.info(f'spider=<{self.spider_name}>, 开始启动. ')

        self.seed_handler = seed_handler(self.spider_name)
        self._dup_filter = dup_filter(self.spider_name)

        self.downloader = httpreq(self.auto_cookie_enable)

        self._raw_seed_dict = None
        self._signal_init()

        self.log.info('spider_base初始化完成, 即将调用用户定义函数')
        self.spider_init()

        self.log.info(f'爬虫{self.spider_name}初始化完成')

    def _signal_init(self):
        for sig in [signal.SIGINT, signal.SIGTERM]:
            signal.signal(sig, self._signal_handle)

    def _signal_handle(self, *kw, **rs):
        if self._raw_seed_dict:
            self.seed_handler.put_error_seed(self._raw_seed_dict)
        os._exit(0)

    def run_of_error_parser(self):
        self.seed_handler.queue_collname_list = [f'{self.spider_name}:{Public_Constant.error_seed_parser_suffix}']
        self.run()

    def run(self):
        while True:  # 不考虑停止
            try:
                self._run_once_task()
            except:
                self.log.error(
                    f'{traceback.format_exc()}\n运行spider_{self.spider_name}出错,休眠 {Public_Constant.spider_err_wait_time}秒 后继续')
                time.sleep(Public_Constant.spider_err_wait_time)

    def _run_once_task(self):
        raw_seed_dict = self.seed_handler.get_seed()
        if not raw_seed_dict:
            self.log.info(f'所有队列为空,休眠 {Public_Constant.empty_seed_wait_time}秒')
            time.sleep(Public_Constant.empty_seed_wait_time)
            return

        # 通过中间件处理类型为dict的种子
        try:
            seed_dict = self._request_handle(raw_seed_dict)
        except:
            self.seed_handler.put_error_seed(raw_seed_dict)
            self.log.error(f'{traceback.format_exc()}\n该seed在经过中间件时出现了一个未处理的错误')
            return

        if not isinstance(seed_dict, dict):  # 只要中间件返回的数据不是dict, 都认为是放弃该种子
            self.log.info('该seed已被中间件处理,本次任务结束')
            return

        seed_inst = self._make_seed_from_dict(copy.deepcopy(seed_dict))

        # 执行http请求
        try:
            resp = self._get_response(seed_inst)  # 如果重试多次仍然无法获取正常的response会报错
        except:
            resp = None

        if resp is None or resp is Public_Constant.except_retry_flag:
            self.log.warning('请求失败,将seed写入error队列.')
            self.seed_handler.put_error_seed(copy.deepcopy(raw_seed_dict))
            return

        if resp is True:  # 由中间件接收, 要求放弃该response
            self.log.info('该请求结果已被中间件处理,本次任务结束')
            return

        self._parser_process(resp.parser_func, resp)

    @except_retry
    def _get_response(self, seed_inst: Seed):
        try:
            req_result = self.downloader.req(seed_inst)
        except:
            return None

        seed_inst._set_response(req_result)

        try:
            seed_inst = self._response_handle(seed_inst)
            if seed_inst is False:  # 要求重试
                self.downloader.change_proxy()
                return Public_Constant.except_retry_flag
        except:
            self.log.error(f'{traceback.format_exc()}\n在执行response_middleware_handler时出现了一个未处理的错误')
            return None  # 让爬虫将种子放到error队列

        return seed_inst

    def _request_handle(self, seed_dict):
        if not isinstance(seed_dict, dict):
            self.seed_handler.put_error_seed(seed_dict)
            self.log.error(f'该种子不是dict, 而是{type(seed_dict)}, 不合法')
            return False

        if not seed_dict.get('parser_func'):  # 无parser_func或parser_func为空数据
            self.seed_handler.put_error_seed(seed_dict)
            self.log.error('该种子缺少parser_func, 不合法的seed')
            return False

        if seed_dict.get('url'):  # 存在url
            return seed_dict

        self._parser_process(seed_dict.get('parser_func'), seed_dict)
        return True

    def _response_handle(self, response_inst):
        if self.retry_http_code:
            if response_inst.response.status_code in self.retry_http_code:
                self.log.warning(f'拦截response的状态码: {response_inst.response.status_code}, 需重新请求')
                return False

        html_encoding(response_inst)

        check_html_func = response_inst.check_html_func
        if check_html_func:
            if not hasattr(self, check_html_func):
                raise AttributeError(f'spider缺少配置的check_html_func方法=<{check_html_func}>，请检查')

            result = getattr(self, check_html_func)(response_inst)
            if result is False:
                self.log.warning(f'该response因<{check_html_func}>中间件不通过, 即将重试请求')
                return False

        return response_inst

    def _parser_process(self, parser_func_name, resp):
        try:
            parser_result = getattr(self, parser_func_name)(resp)
            if isinstance(parser_result, Iterable):
                for result_item in parser_result:
                    self._parser_result_handler(result_item)

        except:
            self.log.error(f'{traceback.format_exc()}\n解析出错')
            if isinstance(resp, dict):  # 空url的种子请求结果
                self.seed_handler.put_error_seed(resp, is_parser_error=True)
            else:
                save_dict = resp.to_save_dict()
                save_dict.update({'html': resp.response_text})  # 存入抓下来的html
                self.seed_handler.put_error_seed(save_dict, is_parser_error=True)

    def _parser_result_handler(self, result):
        # 对解析函数的每一个结果进行处理
        if not result:
            return

        if isinstance(result, dict):
            self.seed_handler.put_seed(result)
            return

        if isinstance(result, Seed):
            suffix = getattr(result, 'suffix', None)
            front = getattr(result, 'front', None)

            kw = dict()
            if suffix is not None:
                kw['suffix'] = suffix
            if front is not None:
                kw['front'] = suffix

            self.seed_handler.put_seed(result.to_save_dict(), **kw)

    def _make_seed_from_dict(self, seed_dict: dict):
        url = seed_dict.pop('url', None)
        parser_func = seed_dict.pop('parser_func', None)
        return Seed(url, parser_func, **seed_dict)

    def dup_check(self, item, collname=None):
        return self._dup_filter.check(item, collname=collname)

    def clear_all_queue(self, clear_parser_error=True, clear_dup=True):
        queue_suffix_list = eval(self.config.get_frame_value('seed_queue', 'suffix'))  # type:list
        if clear_parser_error:
            queue_suffix_list.append(Public_Constant.error_seed_parser_suffix)
        self.seed_handler.clear_queue(*queue_suffix_list)

        if clear_dup:
            self._dup_filter.clear_queue()

    def make_seed(self, url, parser_func,
                  check_html_func=None, meta=None,
                  ua_type=None,
                  method=None, params=None,
                  cookies=None, headers=None,
                  data=None, timeout=None, encoding=None,
                  files=None, auth=None, allow_redirects=True, proxies=None,
                  hooks=None, stream=False, verify=False, cert=None, json=None,
                  **kwargs):

        cookies = merge_cookies(self.downloader.previous_cookies, cookies) if self.auto_cookie_enable else cookies

        if hasattr(parser_func, '__call__'):
            parser_func = parser_func.__name__

        if hasattr(check_html_func, '__call__'):
            check_html_func = check_html_func.__name__

        if encoding is None:
            encoding = self.encoding

        kwargs.update({"method": method or self.method,
                       "params": params,
                       "cookies": cookies,
                       "headers": headers or self.base_headers,
                       "check_html_func": check_html_func or self.check_html_func,
                       "meta": meta,
                       "data": data,
                       "timeout": timeout or self.time_out,
                       "encoding": encoding,
                       'ua_type': ua_type,

                       'files': files,
                       'auth': auth,
                       'allow_redirects': allow_redirects,
                       'proxies': proxies,
                       'hooks': hooks,
                       'stream': stream,
                       'verify': verify,
                       'cert': cert,
                       'json': json
                       })
        return Seed(url, parser_func, **kwargs)

    def yield_for_start_seed(self, force_yield=False):
        if not force_yield and not self.seed_handler.check_seeds_is_empty():
            self.log.info('队列不为空已忽略本次提交初始种子任务')
            return

        self.log.info('开始提交初始种子')
        if isinstance(self.start_seed, tuple):  # 使用了aps调度器, 此时不需要管参数
            result = self.start_seed[0](self)
        else:
            result = self.start_seed()

        if isinstance(result, Iterable):
            for result_item in result:
                self._parser_result_handler(result_item)
        self.log.info('初始提交完毕种子')

    def _parser_yield_start_seed_signal(self, *args, **kw):
        self.log.info('收到提交初始种子信号')
        self.yield_for_start_seed(force_yield=kw.pop('force_yield', False))

    def _check_save_result(self, result_dict):
        if isinstance(result_dict, dict):
            return True

        if result_dict:
            self.log.warning(f'已抛弃未定义处理类型的save_result, {type(result_dict)}')
        else:
            self.log.info('已抛弃空数据的save_result')

    def spider_init(self):
        pass

    def start_seed(self):
        pass

    def check_has_need_data(self, res: Seed):
        # 检查页面是否存在需要的数据, 返回False时爬虫框架会重抓当前页面
        pass

    def parser_response(self, res: Seed):
        pass
