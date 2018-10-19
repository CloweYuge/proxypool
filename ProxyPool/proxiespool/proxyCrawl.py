# import requests                               # 如果不想使用Getter中的方法，可以启用requests
import time                                     # 用来休眠
from pyquery import PyQuery as pq               # 用来使用css选择器解析网页
from .proxyAdd import RedisClient                # 用来链接储存模块
from .proxySetting import POOL_UPPER_THRESHOLD   # 用来获得代理池的上限
from .proxyGetter import get_page                # 用来使用Getter模块中的请求网页方法

# POOL_UPPER_THRESHOLD = 1500                  # 代理池上限，在这里只会判定基础库的代理数量，其他任何筛选出的站点库上限不会高于基础库


class ProxyMetaclass(type):                    # type是python内建元类，新建的元类需要继承type，元类用来创建类，类用来创建对象
    """
    至于这个动态获取方法名的原理我也不太清楚，反正是这么就是工作运行的0.0，可能需要补习一下元类中的__new__构造函数
    补习完成，这涉及到类的生成方式，这里总的来说就是新建一个元类，来重写__new__方法，然后指定用这个元类来生成一个类
    事实上需要新生成一个类可以直接使用type("People",(object,),{"eat":eat})，其中eat是这个类中的方法
    该方法一般很少用，一般先由type生成元类，再有元类生成类，由类衍生出对象实例，比如说声明class关键字
    而使用以这个元类来生成的类，都将拥有__CrawlFunc__和__CrawlFuncCount__属性，当然你也可以添加一些方法进去
    在__new__添加方法的方式有两种，一种是attrs["方法名"] = lambda 使用匿名函数
    或者提前定义好一个函数，然后以attrs["方法名"] = 函数名
    之后使用的方式跟调用类中的方法一样
    """
    def __new__(cls, name, bases, attrs):
        """
        也就是说这个元类继承了type，然后在new中添加了两个属性，当用来生成类的时候由于new会被优先执行
        这两个属性就会被同时添加到类中，所以也可以用来添加方法
        这里的cls参数其实是传入了由这个元类构造的类，当我们迭代这个attrs容器时，即可获得需要构造的类中所有属性和方法
        :param name:
        :param bases:
        :param attrs: 这是一个容器
        :return:
        """
        count = 0
        attrs['__CrawlFunc__'] = []                     # 设置一个名为__CrawlFunc__的属性，类型为列表
        for k, _ in attrs.items():                         # 获取当前类中的所有属性和方法名，其中k代表名称
            if 'crawl_' in k:                            # 判断以crawl_开头的方法名在不在k列表里边
                attrs['__CrawlFunc__'].append(k)        # 如果在，就加入到__CrawlFunc__属性里边
                count += 1                                # 声明一个记录数量的变量，用来记录有几个符合条件的方法
        attrs['__CrawlFuncCount__'] = count             # 声明一个记录数量的属性，并将上面的count给它赋值
        return type.__new__(cls, name, bases, attrs)        # 将需要构造的类和添加好的attrs返回给type中的new方法


class Crawler(object, metaclass=ProxyMetaclass):
    # 默认新式类由type()构造，可以通过指定metaclass关键字参数后，则由metaclass构造
    """
    如果需要新增代理网站的爬取，就在本来中写出新网站的爬取规则，方法名以crawl_开头
    这里的四个爬取规则都是用了pyquery中的css选择器，当然你同样也可以使用正则，或者xpath，bs4等
    """
    def get_proxies(self, callback):
        """
        这里就是执行本类中的所有crawl__方法，需要执行的方法名以参数的形式动态执行
        :param callback: 传入的方法名
        :return:
        """
        proxies = []
        for proxy in eval("self.{}()".format(callback)):   # eval表示将字符串当作一个可执行的表达式进行运算并获得返回值
            proxies.append(proxy)
        print('成功获取到代理', proxies)
        return proxies

    def crawl_kuaidaili(self):
        start_url = 'https://www.kuaidaili.com/free/inha/{}/'
        urls = [start_url.format(page) for page in range(1, 4)]         # 我这里只爬取前三页，毕竟网站一天也就新增一两页
        for url in urls:
            print('爬取快代理Http：', url)
            # html = requests.get(url=url).text                        # 如果想使用requests方法来请求，就将下一句注释掉
            html = get_page(url)                                      # 使用的是Getter模块中的请求方法，也可以不用
            if html:
                html_doc = pq(html)                                    # 使用pyquery的css选择器需要先初始化
                proxy_list = html_doc('.table.table-bordered.table-striped tbody').find('tr').items()
                for proxy_str in proxy_list:
                    ip = proxy_str.find('td:nth-child(1)').text()
                    port = proxy_str.find('td:nth-child(2)').text()
                    yield ':'.join([ip, port])
            time.sleep(5)                                               # 休眠五秒，免得被代理网站封掉ip

    def crawl_xicidaili(self):
        start_url = 'http://www.xicidaili.com/nn/{}'
        urls = [start_url.format(page) for page in range(1, 4)]
        for url in urls:
            print('爬取西刺代理Http：', url)
            # html = requests.get(url=url, headers=header).text
            html = get_page(url)
            if html:
                html_doc = pq(html)
                # 由于有一个tr节点不合规矩，所以在tr节点内部找到符合规矩的地方，再获取父节点到tr位置，另外一种方式在下面
                proxy_list = html_doc('#ip_list').find('.country img').parents('tr').items()
                for proxy_str in proxy_list:
                    if proxy_str.find('td:nth-child(6)').text() == 'HTTP':
                        ip = proxy_str.find('td:nth-child(2)').text()
                        port = proxy_str.find('td:nth-child(3)').text()
                        yield ':'.join([ip, port])
            time.sleep(5)

    def crawl_31f(self):
        start_url = 'http://31f.cn/http-proxy/'
        print('爬取31f代理Http：', start_url)
        # html = requests.get(url=start_url).text
        html = get_page(start_url)
        if html:
            html_doc = pq(html)
            proxy_list = html_doc('.table.table-striped').find('td small').parents('tr').items()
            for proxy_str in proxy_list:
                ip = proxy_str.find('td:nth-child(2)').text()
                port = proxy_str.find('td:nth-child(3)').text()
                yield ':'.join([ip, port])

    def crawl_yqie(self):
        start_url = 'http://ip.yqie.com/proxygaoni/'
        print('爬取yqie代理Http：', start_url)
        # html = requests.get(url=start_url).text
        html = get_page(start_url)
        if html:
            html_doc = pq(html)
            # 除了使用上面的方式来获取有效节点，也可以删掉那个碍事的第一个不符合规矩的tr节点
            html_doc('#GridViewOrder').find('tr:nth-child(1)').remove()
            proxy_list = html_doc('#GridViewOrder').find('tr').items()
            for proxy_str in proxy_list:
                if proxy_str.find('td:nth-child(5)').text() == 'HTTP':
                    ip = proxy_str.find('td:nth-child(2)').text()
                    port = proxy_str.find('td:nth-child(3)').text()
                    yield ':'.join([ip, port])


class Getter():
    def __init__(self):
        self.redis = RedisClient()
        self.crawler = Crawler()

    def is_over_threshold(self):
        """
        判断是否达到代理池限制，这里如果不为count()方法传入键名，默认将判断默认的键名代理池
        :return:
        """
        if self.redis.count() >= POOL_UPPER_THRESHOLD:
            return True
        else:
            return False

    def run(self):
        """
        首先判断了是否达到限制，再去获取crawl方法名的数量生成数列，以数列为索引获取方法名，之后就调用get_proxies方法执行
        :return:
        """
        print('获取器开始启动执行')
        if not self.is_over_threshold():
            for callback_label in range(self.crawler.__CrawlFuncCount__):       # 实例化之后就可以直接使用类中的属性
                callback = self.crawler.__CrawlFunc__[callback_label]
                proxies = self.crawler.get_proxies(callback)
                for proxy in proxies:
                    self.redis.add(proxy)

if __name__ == '__main__':              # 用来调试的代码，如果自行新增了新的代理网站爬取，可以在下面执行测试
    tested = Crawler()
    # kuai = '--'.join(tested.crawl_kuaidaili())
    # print(kuai)
    # xici = '--'.join(tested.crawl_xicidaili())
    # print(xici)
    # syif = '--'.join(tested.crawl_31f())
    # print(syif)
    yqie = '--'.join(tested.crawl_yqie())
    print(yqie)
