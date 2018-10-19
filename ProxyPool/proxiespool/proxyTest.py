import requests
from proxyAdd import RedisClient
from proxySetting import UserAgent

redis = RedisClient()
proxy = redis.random()
print(proxy)
proxies = {
    'http': 'http://' + proxy,
    'https': 'https://' + proxy
}
header = {'User-Agent': UserAgent().random()}
html = requests.get("https://httpbin.org/get", proxies=proxies, headers=header)
print(html.text, html.status_code)
