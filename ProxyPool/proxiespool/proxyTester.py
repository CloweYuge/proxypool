import aiohttp
import asyncio
import time
import random
from .proxyAdd import RedisClient
from aiohttp import ClientProxyConnectionError as ClientError, ClientConnectorError, ClientOSError, ServerDisconnectedError, ClientHttpProxyError, ClientResponseError
from asyncio import TimeoutError
from .proxySetting import VALID_STATUS_CODES, BATCH_TEST_SIZE, URL_TEST, GetTestUrl, UserAgent

# VALID_STATUS_CODES = [200]
# TEST_URL = 'http://www.baidu.com'
# BATCH_TEST_SIZE = 100


class Tester(object):
    def __init__(self):
        self.redis = RedisClient()


    async def test_single_proxy(self, proxy,rediskey):
        """
        测试单个代理
        :param proxy: 单个代理
        :return: None
        """
        conn = aiohttp.TCPConnector(verify_ssl=False)
        async with aiohttp.ClientSession(connector=conn) as session:
            try:
                if isinstance(proxy, bytes):
                    proxy = proxy.decode('utf-8')
                real_url = GetTestUrl().random_get_url()
                real_proxy = 'http://' + proxy
                header = {
                    'User-Agent': UserAgent().random(),
                    'Accept-Encoding': 'gzip, deflate, br',
                    'Accept-Language': 'zh-CN, zh;q=0.9',
                    'Cache-Control': 'max-age=0',
                    'Connection': 'close'
                }
                async with session.get(real_url, proxy=real_proxy, headers=header, timeout=10) as response:
                    if response.status in VALID_STATUS_CODES:
                        print('[测试模块] 代理可用', rediskey, proxy, real_url)
                        self.redis.max(proxy, rediskey)
                        self.redis.move(proxy=proxy, now_key=GetTestUrl().get_url_key(real_url))
                        # print(await response.json())
                    else:
                        self.redis.decrease(proxy, rediskey)
                        print('[测试模块] 请求响应码不合法：', proxy, response.status)
            except (ClientError, ClientConnectorError, ClientHttpProxyError, ClientOSError, TimeoutError, AttributeError, ServerDisconnectedError, ClientResponseError):
                self.redis.decrease(proxy, rediskey)
                print('[测试模块] 代理请求失败：', proxy)

    def run(self):
        """
        测试主函数
        :return: None
        """
        print('[测试模块] 开始运行')
        try:
            testscore = random.randint(1, 10)
            if testscore <= URL_TEST:
                redis_key = self.redis.randomurlkeys()
            else:
                redis_key = self.redis.randomhttpkeys()
            print('[测试模块] 当前测试代理数据键名：', redis_key)

            proxies = self.redis.all(redis_key=redis_key)
            loop = asyncio.get_event_loop()
            # 批量测试
            for i in range(0, len(proxies), BATCH_TEST_SIZE):
                test_proxies = proxies[i:i + BATCH_TEST_SIZE]
                tasks = [self.test_single_proxy(proxy, rediskey=redis_key) for proxy in test_proxies]
                loop.run_until_complete(asyncio.wait(tasks))
                time.sleep(5)
        except Exception as e:
            print('[测试模块] 发生错误', e.args)
