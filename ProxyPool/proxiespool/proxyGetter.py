import requests
import asyncio
import aiohttp
from requests.exceptions import ConnectionError, ReadTimeout
from .proxySetting import UserAgent
from .proxyAdd import RedisClient

redis_proxy = RedisClient()

def get_page(url, options={}):
    """
    这个下载器大家应该都懂，我就不多说了
    :param url: 访问的地址
    :param options: 可带参数
    :return:
    """
    base_headers = {
        'User-Agent':  UserAgent().random(),                # 随机搞个User-Agent
        'Accept-Encoding': 'gzip, deflate, br',
        'Accept-Language': 'zh-CN,zh;q=0.9'
    }
    headers = dict(base_headers, **options)
    proxy = {
        'http': 'http://' + redis_proxy.random(),
    }
    try:
        r = requests.get(url, headers=headers, proxies=proxy, timeout=10)
        print('获取结果：', url, r.status_code, '--使用代理：', proxy)
        if r.status_code == 200:
            return r.text
        else:
            print('获取失败：', url, r.status_code, '--使用代理：', proxy)
            return None
    except (ConnectionError, ReadTimeout):
        print('获取出错：', url, '使用代理：', proxy)
        return None


class Downloader(object):
    """
    一个异步下载器，可以对代理源异步抓取，但是容易被BAN。
    """

    def __init__(self, urls):                   # 在实例化的时候就要指定urls，这可以是一个列表形式的多个url
        self.urls = urls
        self._htmls = []

    async def download_single_page(self, url):
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                self._htmls.append(await resp.text())

    def download(self):
        loop = asyncio.get_event_loop()           # 实例化一个池子，可以限定数量
        tasks = [self.download_single_page(url) for url in self.urls]           # 将任务放到池子里
        loop.run_until_complete(asyncio.wait(tasks))                            # 启动运行池子

    @property
    def htmls(self):                                # 要使用这个下载器实例化之后调用这个方法
        self.download()
        return self._htmls
