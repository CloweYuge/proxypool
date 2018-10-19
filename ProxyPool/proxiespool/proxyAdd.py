import redis
from random import choice
from .proxyError import PoolEmptyError
from .proxySetting import MAX_SCORE,MIN_SCORE,INITIAL_SCORE,EVERY_SCORE,REDIS_DB,REDIS_HOST,REDIS_KEY_HTTP,REDIS_PASSWORD,REDIS_PORT

# MAX_SCORE = 100                     # 代理的最高分，如果代理失效需要进行100次检测，直到分数被减至低于最低分
# MIN_SCORE = 0                       # 代理的最低分，低于这个分数的代理会被移除
# INITIAL_SCORE = 10                  # 代理的初始分数，在添加一个新代理时需要检测10次，直到分数被减至低于最低分来判定代理无效
# EVERY_SCORE = -2                     # 原本每次是减1分，我觉得太低效了，所以我这增加一个属性，可以自由设置
# REDIS_HOST = 'localhost'          # 数据库ip地址，如果是远程服务器请设置此ip,另外redis需要配置为可以接受远程连接
# REDIS_PORT = 6379                   # 数据库的端口地址，redis数据库默认为6379，如果redis配置为其他端口请设置此处
# REDIS_PASSWORD = 'myredis123'     # 数据库的连接密码，如果配置了redis密码请设置此处
# REDIS_KEY_HTTP = 'Httpproxies'    # 代理池在redis数据库中有序集合的键名名称，自行设置
# REDIS_DB = 4                        # redis数据库中默认有15个db数据库，默认是0，如果需要指定请自行设置，我这里用的是第4个


class RedisClient(object):
    """
    参阅本类需要注意，redis数据库中有序集合是在集合数据的储存基础上多了一个score字段，这个字段是用来为键值排序的
    在这里我们使用这个属性来为代理打分，分数越高这个键值越靠前
    设置不同的键即代表一个新的有序集合数据库，因为有序集合实际上是向一个键添加zset元素，一个键可以包含多个zset元素
    对zset元素操作的方法一般是以z开头的，这些方法封装在redis，你同样也可以使用redis中的其他方法
    还有在本类中，设置了最高分来赋值给score，所以键值的score永远不会高于最高分，如果希望改变可以设置为其它数值
    当然也不会低于0，因为设置了最低分，低于这个最低分的键值则会被去除，如果希望改变也可以设置为其它的数值
    """
    # 当外部实例化这个类的时候__init__方法首先初始化本类
    def __init__(self, host=REDIS_HOST, port=REDIS_PORT, password=REDIS_PASSWORD, db=REDIS_DB):
        """
        初始化代理池连接对象，如果没有设置默认的数据库，或不想使用，则需要真正的redis数据库连接参数
        :param host: redis 地址
        :param port: redis 端口
        :param password: redis 密码
        """
        # 初始化一个redis数据库连接对象，名称为dbs
        # StrictRedis类在redis-py中是一个封装好的用来兼容旧版本redis数据库连接命令模块，也可以使用ConnectionPool方式
        # 或者使用ConnectionPool.from_URl的方式构造连接URL，传递给StrictRedis
        self.dbs = redis.StrictRedis(host=host, port=port, password=password, db=db, decode_responses=True)

    def add(self, proxy, redis_key=REDIS_KEY_HTTP, score=INITIAL_SCORE):
        """
        首次添加一个代理，设置分数为INITIAL_SCORE
        :param proxy: 代理ip地址
        :param score: 首次添加代理置分数
        :return: 添加结果
        """
        if not self.dbs.zscore(redis_key, proxy):               # zscore()方法取出键名为key，值为pr的元素的分数，返回None表示不存在
            return self.dbs.zadd(redis_key, score, proxy)       # zadd()方法添加一个或多个zet元素到键名为key中，并设置score分数

    def random(self, redis_key=REDIS_KEY_HTTP):
        """
        随机获取有效代理，优先获取高分代理，如果高分不存在，则按照排名获取，获取失败抛出异常
        :return: 获取的随机代理
        """
        result = self.dbs.zrangebyscore(redis_key, MAX_SCORE, MAX_SCORE, start=0, num=20)
        # zrangebysccore()方法获取键名为key，分数在min到max之间的zset元素。
        # start=指定起始索引，num=指定返回的个数-默认返回全部符合条件的元素，withscores=指定是否带分数一起返回-默认为False
        if len(result):                     # 判断result的元素长度不为零
            return choice(result)           # 随机选择一个元素
        else:
            result = self.dbs.zrevrange(redis_key, 0, 100)
            # zrevrange()返回键名为key中，按分数从大到小排序的所有元素，索引从0开始，返回前100个元素，withscores=默认为False
            if len(result):
                return choice(result)
            else:
                raise PoolEmptyError                    # 设置抛出一个PoolEmptyError异常，使外部调用时可以被try捕获

    def decrease(self, proxy, redis_key=REDIS_KEY_HTTP):
        """
        代理分数值减一分，分数小于最小值，则去除代理
        :param proxy: 代理
        :return: 修改后的代理分数
        """
        score = self.dbs.zscore(redis_key, proxy)       # 取出一个元素的分数，或许原作者并没有考虑到pr不存在的情况。
        # 但如果返回None的话也不会通过下面的if，真是高明
        if score and score > MIN_SCORE:                 # 如果score不为None或大于我们设置的最低分
            print('代理：', proxy, '当前分数', score, '减分')
            return self.dbs.zincrby(redis_key, proxy, EVERY_SCORE)          # 这里的score设置为负数，表示减去
            # zincrby()方法设置键名为key，值为pro元素的分数加上score数值，如果元素不存在，会添加一个该元素并设置分数为score
        else:
            print('代理：', proxy, '当前分数', score, '移除')
            return self.dbs.zrem(redis_key, proxy)      # 删除一个元素

    def exists(self, proxy, redis_key=REDIS_KEY_HTTP):
        """
        判断是否存在
        :param proxy: 代理
        :return: 是否存在
        """
        return not self.dbs.zscore(redis_key, proxy) == None            # 这句就有意思了，一定返回为None，则结果为not True，返回结果即为False

    def max(self, proxy, redis_key=REDIS_KEY_HTTP):
        """
        当检测代理时是有效的就将代理分数设置为MAX_SCORE
        :param proxy: 代理
        :return: 设置结果
        """
        print('代理：', proxy, '可用，设置为', MAX_SCORE)
        return self.dbs.zadd(redis_key, MAX_SCORE, proxy)               # zadd()向键名为key中添加zset元素，score用于排序，如果存在，则更新顺序

    def count(self, redis_key=REDIS_KEY_HTTP):
        """
        获取代理总数量
        :return: 数量
        """
        return self.dbs.zcard(redis_key)                                # zcard()方法返回key中的zset元素个数

    def all(self, redis_key=REDIS_KEY_HTTP):
        """
        获取全部代理
        :return: 代理列表
        """
        return self.dbs.zrangebyscore(redis_key, MIN_SCORE, MAX_SCORE)
        # zrangebyscore()方法返回所有符合分数区间的元素，由于我们设置的最高分为MAX，所以相当于返回所有zset元素

    def move(self, proxy, now_key, score=MAX_SCORE):
        if not self.dbs.zscore(now_key, proxy):  # zscore()方法取出键名为key，值为pr的元素的分数，返回None表示不存在
            return self.dbs.zadd(now_key, score, proxy)

    def randomhttpkeys(self):
        """
        随机返回一个Http开头的键名，一般是未经清洗的基础代理，只是用作测试代理有效性
        :return:
        """
        keys = self.dbs.keys('Http*')
        if len(keys):
            return choice(keys)
        else:
            return None

    def randomurlkeys(self):
        """
        随机返回一个Url开头的键名，一般是我们想用来实际爬取的站点的有效代理，如果还没有则会返回未经筛选的基础代理
        :return:
        """
        keys = self.dbs.keys('Url*')
        if len(keys):
            return choice(keys)
        else:
            print('未找到URL站点代理键，返回通用键！！')
            return self.randomhttpkeys()

    def urlkeys(self, urlre='Url*'):
        """
        返回redis数据库当前db中所有的键名
        :param urlre: 也可以指定获取规则，默认为“Url*”
        :return:
        """
        return self.dbs.keys(urlre)
