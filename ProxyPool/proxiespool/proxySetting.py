from random import choice

# --------------------调度器相关----------------------#
TESTER_CYCLE = 60              # 检测代理有效性的间隔时间，秒为单位，这里设置为20分钟测试一批
GETTER_CYCLE = 60 * 60 * 12         # 获取器的间隔时间，以秒为单位，代理不要爬太快,这里设置了半天爬一次，一般代理网站也就只一天更新一次！！！
TESTER_ENABLED = False               # 测试器开关
GETTER_ENABLED = False              # 获取器开关             # 在测试环境中用来测试相应模块
API_ENABLED = True                 # api接口开关

# --------------------测试器相关----------------------#
VALID_STATUS_CODES = [200]          # 在判断代理有效性时可加入其他状态码来准确识别
BATCH_TEST_SIZE = 50                # 每一批次测试代理量，由于是异步io请求如果一个批次测试量过大，可能引起性能负担

# 以下是对不同站点进行筛选，如果测试能访问的话则会将代理加入TEST_URL相应的键名集合下，注意，这并不会移除原来代理池中的数据
URL_TEST = 5                        # 对于站点URL的测试权重，总数为10，如果设置为1，那么测试器90%会去测试未经筛选的基础代理池
TEST_URL = {                        # 测试url站点，用来筛选代理，每加入一个站点，测试器会以键名的生成这个站点的有效代理池
    'Httptest': 'http://httpbin.org/get',
    'Urlbaidu': 'https://www.baidu.com',
    'Urlweibo': 'https://www.weibo.com',
    'Urlff8': 'https://www.ff8.xyz'
}
# 键名以Http开头表示这个站点是用来测试代理有效性的，这个站点应该设置为不会封ip的站点
# 键名以Url开头表示站点是用来实际爬取数据的，测试器会把可以访问该站点的代理筛选出来，但它不会从基础池中移除，因为这个代理或许也能访问其它站点
# 一个代理可能存在于多个池中，表示这代理很好很牛批用起来贼爽，反之它可能会一次次的减分，直到从基础代理池中去除
# 在web接口中获取相应站点的有效代理，需要加上参数 url?urls= TEST_URL中的键名
# --------------------储存模块相关--------------------#
MAX_SCORE = 100                      # 代理的最高分，如果代理失效需要进行50次检测，直到分数被减至低于最低分
MIN_SCORE = 0                        # 代理的最低分，低于这个分数的代理会被移除
INITIAL_SCORE = 20                   # 代理的初始分数，在添加一个新代理时需要检测5次，直到分数被减至低于最低分来判定代理无效
EVERY_SCORE = -2                     # 原本每次是减1分，我觉得太低效了，所以我这增加一个属性，可以自由设置
REDIS_HOST = 'localhost'           # 数据库ip地址，如果是远程服务器请设置此ip,另外redis需要配置为可以接受远程连接
REDIS_PORT = 6379                    # 数据库的端口地址，redis数据库默认为6379，如果redis配置为其他端口请设置此处
REDIS_PASSWORD = 'myredis123'      # 数据库的连接密码，如果配置了redis密码请设置此处
REDIS_DB = 4                        # redis数据库中默认有15个db数据库，默认是0，如果需要指定请自行设置，我这里用的是第4个

REDIS_KEY_HTTP = 'Httpproxies'     # 代理池在redis数据库中有序集合的键名名称，这是一个代理未经筛选的基础代理池
# ---------------------爬取器相关----------------------#
POOL_UPPER_THRESHOLD = 1500           # 设置代理池上限

# ---------------------web接口相关----------------------#
API_PORT = 8050                      # 设置web接口的访问端口


class GetTestUrl():
    """
    这个类用来获取测试的站点，并且在需要的时候获取键名来新建一个站点的代理池集合
    """
    def __init__(self, test_url=TEST_URL):
        self.test_urls = test_url                                   # 如果没有指定就使用上面配置的站点
        self.url_keys = list(test_url.keys())                       # 获取字典中的key是以迭代器返回的，需要用list()方法转换成列表
        self.url_values = list(test_url.values())                   # 键值的获取也是同样的道理

    def random_get_url(self):
        """
        随机选择一个站点出来
        :return:
        """
        test_url = choice(self.url_values)
        return test_url

    def get_url_key(self, url):
        """
        获取站点url对应的键名
        :param url: 网页站点
        :return:
        """
        return self.url_keys[self.url_values.index(url)]

    def get_url_values(self, key):
        """
        获取站点键名对应的键值
        :param key:
        :return:
        """
        return self.url_values[self.url_keys.index(key)]


class UserAgent():
    """
    随机使用一个User-Agent:
    """
    def __init__(self):
        self.useragent = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:62.0) Gecko/20100101 Firefox/62.0',
            'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/69.0.3497.100 Safari/537.36'
        ]

    def random(self):
        return choice(self.useragent)
