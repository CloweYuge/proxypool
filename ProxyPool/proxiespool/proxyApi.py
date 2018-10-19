from .proxyAdd import RedisClient
from flask import Flask, g, request
from .proxySetting import API_PORT

__all__ = ['app']
app = Flask(__name__)


def get_conn():
    if not hasattr(g, 'redis'):
        g.redis = RedisClient()
    return g.redis


@app.route('/')
def index():
    return '<h2>Welcome to Proxy Pool System</h2>'


@app.route('/random')
def get_proxy():
    """
    返回随机代理，默认选择未经筛选的代理池，加上urls参数则选择指定的代理池
    :return:
    """
    conn = get_conn()
    p = request.args.get('urls')
    keys = conn.urlkeys()
    if p in keys:
        return conn.random(redis_key=p)
    else:
        return conn.random()


@app.route('/count')
def get_counts():
    """
    获取未经筛选的代理池中代理总数量,如果加上urls参数访问则返回指定代理池的数量
    :return:
    """
    conn = get_conn()
    p = request.args.get('urls')
    keys = conn.urlkeys()
    if p in keys:
        return str(conn.count(redis_key=p))
    else:
        return str(conn.count())


@app.route('/urls')
def get_urlkeys():
    """
    获取数据库中所有站点代理集合的键名，通过这个我们可以知道数据库目前有哪些站点的有效代理
    :return:
    """
    conn = get_conn()
    return str(conn.urlkeys('*'))


if __name__ == '__main__':
    app.run(port=API_PORT)
