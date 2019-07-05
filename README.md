# 分布式爬虫精简框架


###  安装
```
pip install zspider
```

###  框架依赖
+ 由于使用了队列系统, 此爬虫框架依赖于ssdb

### 配置爬虫框架
+ 创建一个目录, 这个目录作为你的爬虫组织主路径

```
mkdir /home/myspider
mkdir /home/myspider/log
mkdir /home/myspider/spiders
```

+ 创建日志目录, 所有的爬虫的日志都将存放到这个目录

```
cd /home/myspider
mkdir log
```

+ 创建配置文件
```
touch /etc/zspider/config.ini
# win系统: "c:/zspider/config.ini"
# 其他系统: "/etc/zspider/config.ini"
# 可以使用环境变量 ZSPIDER_CONFIG 指定配置文件路径, 优先级最高
```

+ 修改配置文件为你的设置

```
[log]
;是否输出到流
;write_stream = true
;是否输出到文件
;write_file = true
;日志文件输出路径
;write_path = /home/myspider/log
;日志等级
;log_level = debug
;每隔几天就新增一个日志文件
;log_interval = 1
;保留几个旧的日志文件
;log_backupCount = 2

[seed_queue]
;种子队列查询后缀, 请不要更改这个配置, 除非你完全了解此爬虫框架的队列系统是如何运行的
;suffix = ['vip', 'd1', 'd2', 'd3', 'seed', 'error']

[public_constant]
;请求等待时间
;req_timeout = 20
;一次完整的任务逻辑中出错时, 等待一定时间后才能开始下一个任务
;spider_err_wait_time = 3
;种子队列为空后爬虫休眠时间
;empty_seed_wait_time = 120
;默认html编码方式
;default_html_encoding = 'utf-8'
;重试等待时间
;retry_wait_fixed = 0.5
;最大尝试次数
;max_attempt_count = 5

[ssdb]
;是否为集群
cluster = false
;主机地址
host = 你的ssdb服务主机
;主机端口
port = 你的ssdb服务端口

[proxy]
;use_proxy = false
;代理获取服务器ip和端口,如(xxx.xxx.xxx:1234)
;proxy_server =
;代理获取服务器路径,如(getproxy?format=json)
;proxy_path =
;无法获取代理地址时重试等待时间
;except_wait = 1
;代理模块包名
;proxy_pack_name = zspider.proxy_base
;代理模块名
;proxy_class_name = proxy_base
```

# 大功告成, 终于可以开始制作爬虫了

### 一个简单的爬虫

+ 在爬虫目录下创建一个文件 my\_spider.py, 写入如下内容

```python
from zspider.spider_base import spider_base

class my_spider(spider_base):
    spider_name = 'my_spider'

    def start_seed(self):
        yield self.make_seed('https://pypi.org/project/zspider', self.parser_html, encoding='utf8')

    def parser_html(self, res):
        self.log.info(res.response_text)

if __name__ == '__main__':
    a = my_spider()
    a.yield_for_start_seed()
    a.run()
```

+ 运行它, 随后你可以在控制台看到打印出来的网页数据

### 这个爬虫做了什么
```python
# 从爬虫框架zspider的spider_base模块中导入spider_base类
from zspider.spider_base import spider_base

# 创建自己的爬虫类并继承spider_base
class my_spider(spider_base):
    #设置爬虫的名称为my_spider, 注意: 如果没有设置名称会报错
    spider_name = 'my_spider'

    #爬虫开始爬取网页时总有一个最开始的网址给它抓取, 这里提交最开始的网址给种子队列
    def start_seed(self):
        #构建并提交一个url种子给种子队列, 这个种子包含了三种基本信息: 抓取的网址是'https://pypi.org/project/zspider', 用parser_html函数来解析网页, 这个网页的编码是utf8
        yield self.make_seed('https://pypi.org/project/zspider', self.parser_html, encoding='utf8')

    #创建一个解析函数, 此函数接收一个参数, 此参数是_seed.Seed类的实例
    def parser_html(self, res):
        #将网页数据打印出来
        self.log.info(res.response_text)

if __name__ == '__main__':
    #爬虫实例化
    a = my_spider()
    #开始提交初始种子
    a.yield_for_start_seed()
    #开启爬虫
    a.run()
```

### 让爬虫不停的爬下去
```
    #在解析函数中
    def parser_html(self, res):
        urls = []
        #在此处写入自己的解析代码, 获取这个网页的一些url存入到urls中
        #遍历创建并提交url种子
        for url in urls:
            #去重检查, 只有第一次检查的数据才会返回True, 可以防止已经抓取的页面再次抓取导致死循环
            if self.dup_check(url):
                #这里没有写encoding, 爬虫框架会对每一个网页自动分析出合适的编码来解析网页, 就像浏览器一样
                yield self.make_seed(url, self.parser_html)

        self.save_result('你想要保存的数据, 它应该是一个dict')
```

### spider\_base内建参数说明
+ 所有的重复参数遵循就近优先原则

参数名|数据类型|默认值|描述|在make\_seed中<br>为种子单独设置
--|:--:|:--:|---|:--:
spider\_name | str | | 必须设置 |
method | str | get | 默认请求方式 | 是
encoding | str | | 默认页面编码解码模式, 设为None由爬虫框架自动判断 | 是
base\_headers | dict | {} | 默认请求头, 允许用户添加或修改请求头, 忽略大小写, 爬虫框架会自动补全必须的请求头字段 | 是
time\_out | float | 20 | 请求超时 | 是
auto\_cookie_enable | bool | False | 是否自动管理cookie
check\_html_func | function<br>str | | 页面解析预处理函数, 可能因为某些原因导致页面内容不是你预想的内容, 你可以在这里检查页面内容, 如果不是你想要的内容请返回False, 爬虫框架会更换代理后重新抓取此页面 | 是
retry\_http\_code | list | [] | 如果页面状态码在这个列表中, 爬虫框架会重新抓取页面, 如404 |


### spider\_base方法说明
+ run\_of\_error\_parser
> 仅使用解析错误error\_parser队列进行抓取, 对调试爬虫很有帮助

+ run
> 运行爬虫

+ dup\_check
> 去重检查, 可以有效避免重复抓取页面

参数名|数据类型|默认值|描述
--|:--:|:--:|---
item | | | 必须参数, 这个参数在运算之前会调用str格式为字符串, 然后加密为md5\_32位字符串, 只有第一次调用去重检查的数据才会返回True
collname | str | None | 可选参数, 去重过滤器使用哪个文档保存被去重的数据, 如果设为None, 文档名默认为<爬虫名:dup>

+ clear\_all\_queue
> 清除队列, 慎用, 此函数会将爬虫的种子完全清除

参数名|数据类型|默认值|描述
--|:--:|:--:|---
clear\_parser\_error | bool | True | 是否清除解析错误的队列
clear\_dup | bool | True | 是否清除去重过滤器文档


+ make\_seed
> 此函数用户构建一个url种子, 它将和页面相关的一切信息保存到一个种子里面

参数名|数据类型|必须参数|描述
--|:--:|:--:|---
url | str | | 要抓取的网址, 尽量把http或https写入, 这样抓取更准确, 允许为空
parser\_func | function<br>str | 是 | 表示页面抓取成功后调用哪个解析函数来解析它, 此函数接收一个参数, 请参考[可继承函数说明.parser\_response]
check\_html\_func | function<br>str | | 页面抓取成功后调用哪个页面解析预处理函数, 此函数接收一个参数, 请参考[可继承函数说明.check\_has\_need\_data]
meta | python基本类型 | | 此参数用于保存用户想要传递到下一个解析函数的数据, 没错就和scrapy的meta一样
ua\_type | str | | 随机浏览器头类型('pc', 'ua\_type', 'ios')
method | str | | 使用什么方式请求url, get还是post, 如果为空则使用内建的爬虫内建参数method, 还是空则默认为get
params | | | 参考requests的params
cookies | dict | | cookies, 要求爬虫内建参数cookie\_enable为True
headers | dict | | 请求头, 参考爬虫内建参数base\_headers
data | | | 参考requests的data
timeout | float | | 页面请求等待时间, 超时则认为请求失败, 设为空或0, 爬虫框架会自动更改为20, 爬虫不应该一直等待一个网页
encoding | str | | 页面编码解码方式, gbk还是utf8? 设为空则使用爬虫内建参数encoding, 还是空则由爬虫框架智能判断. 当页面是图片或是其他非文本页面时, 设为False关闭此种子的解码功能
proxies | dict | | 主动为此种子设置代理



+ yield\_for\_start\_seed
> 根据start\_url函数提交初始种子

参数名|数据类型|默认值|描述
--|:--:|:--:|---
force\_yield | bool | False | 是否强行提交初始种子, 如果为False, 在所有正常的种子抓取完毕之前忽略本次操作, 如果为True, 不管是否存在未抓取完毕的种子都立即提交初始种子

### 可继承函数说明
+ spider\_init
> 爬虫初始化完成后会调用这个函数

+ start\_seed
> 提交初始种子函数, yield\_for\_start\_seed方法会调用此函数, 此函数允许提交多个初始种子

+ check\_has\_need\_data
> 页面解析预处理函数, 要使用此函数必须在构建种子的时候用参数check\_html\_func指明, 或者在spider\_base内建参数中设置默认值, 如果你返回了False, 那么爬虫框架会重新抓取这个页面. 如果你的代码出错了, 爬虫框架会将这个种子放入error队列

参数名|数据类型|描述
--|:--:|---
res | seed.Seed | 此值包含了抓取成功的页面数据以及原始种子的信息, 参考seed.Seed参数说明. 如果url是空的, 那么这个参数是一个dict, 请参考原始代码seed.Seed.\_\_attrs\_dict\_\_

+ parser\_response
> 页面解析函数, 要使用此函数必须在构建种子的时候用参数parser\_func指明, 你可以在此函数内正式解析页面, 然后使用yield提交种子, 如果你的代码出错了, 爬虫框架会将这个种子放入error\_parser队列

参数名|数据类型|描述
--|:--:|---
res | seed.Seed | 此值包含了抓取成功的页面数据以及原始种子的信息, 参考seed.Seed参数说明. 如果url是空的, 那么这个参数是一个dict, 请参考原始代码seed.Seed.\_\_attrs\_dict\_\_

### seed.Seed参数说明
+ 你构建种子时传入的所有参数都将会成为种子实例的属性, 当爬虫框架使用这个种子成功抓取页面后, 以下属性将可用

参数名|数据类型|描述
--|:--:|---
response | | 请参考requests.Request
response\_text | str | 网页源代码
response\_etree | | 请参考lxml.etree.\_Element
response\_json | dict | 将网页源代码视为json格式并获取转换为dict的值
raw\_data | bytes | 获取网页原始数据, 如果是图片或其他非文本网页时非常有用

### seed.Seed方法说明

+ url\_join
> 补全连接地址为完整的网页地址

参数名|数据类型|描述
--|:--:|---
link | str | 一个连接地址, 它可能是不完整的, 使用此函数后会根据当前页面地址补全为完整的地址

### 代理接口说明

+ 创建一个类, 继承zspider.proxy\_base模块中的proxy\_base类

```python
# my_proxy.py
from zspider.proxy_base import proxy_base

class my_proxy_interface(proxy_base):
    def proxy_init(self):
        # 初始化后会调用这个函数
        pass

    def get_proxy(self):
        # 返回当前使用的代理, 字典{"http": "http://主机:端口", "https": "http://主机:端口"}
        pass

    def change_proxy(self):
        # 要求切换代理地址
        pass

# 然后修改配置文件中[proxy]表的proxy_pack_name为你的代理接口包名, 修改proxy_class_name为你的代理接口类名
```

### 更新日志
发布时间|发布版本|发布说明
--|:--:|---
19-03-28 | 1.0.2 | 修复一个bug, 在未设置encoding的情况下页面分析会报错
19-03-28 | 1.0.1 | 现在终结进程时,当前种子会放入error队列,种子不会丢失了
19-03-27 | 1.0.0 | 发布正式版, 相对于旧版本(0.1.0)更改了大多数使用方法, 取消了mongo依赖:因为用户不一定要用mongo存数据, 缓存服务由redis改为了ssdb, 配置文件简化为最少需要[ssdb]表, 其他修改请自行阅读说明本文档

- - -
##### 本项目仅供所有人学习交流使用, 禁止用于商业用途
