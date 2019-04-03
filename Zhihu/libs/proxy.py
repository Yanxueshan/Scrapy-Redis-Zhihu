import requests
from scrapy.selector import Selector
import redis
import time

__author__ = 'Yan'
__date__ = '2019/4/1 7:50'


class Fetch_Proxy(object):
    '''
        从西刺网站获取免费ip代理
    '''
    def __init__(self):
        self.redis = redis.Redis(host='127.0.0.1', port=6379, db=0)
        self.redis_key = "proxy"

    def get_ip_list(self, pages):
        '''
            获取ip_list列表
        '''
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/66.0.3359.139 Safari/537.36'
        }
        for page in range(1, pages):
            url = 'https://www.xicidaili.com/wt/' + str(page)
            res = requests.get(url, headers=headers)
            selector = Selector(text=res.text)
            results = selector.css('#ip_list tr')
            for result in results[1:]:
                ip = result.css('td::text')[0].extract()
                port = result.css('td::text')[1].extract()
                proxy = ip + ':' + port
                self.redis.sadd(self.redis_key, proxy)

    def judge(self, proxy):
        '''
            判断ip是否可以用
        '''
        proxy_dict = {'http': "http://" + proxy}
        try:
            res = requests.get('https://www.baidu.com', proxies=proxy_dict)
        except Exception:
            print('该proxy：' + proxy + '无效')
            return False
        else:
            if res.status_code == 200:
                return True
            else:
                print('该proxy：' + proxy + '无效')
                self.redis.srem(self.redis_key, proxy)
                return False

    def insert_ip(self, proxy):
        '''
            往redis中添加数据
        '''
        self.redis.sadd(self.redis_key, proxy)

    def delete_ip(self, proxy):
        '''
            从redis中删除无效ip
        '''
        self.redis.srem(self.redis_key, proxy)

    def get_random_ip(self):
        '''
            从redis中随机获取一个proxy
        '''
        if self.redis.scard(self.redis_key) < 50:
            self.get_ip_list(5)
        proxy = self.redis.srandmember(self.redis_key, 1)[0].decode('utf8')
        result = self.judge(proxy)
        if result:
            return "http://" + proxy
        else:
            self.get_random_ip()


if __name__ == "__main__":
    start_time = time.time()
    fetch = Fetch_Proxy()
    print(fetch.get_random_ip())
    print("time cost: ", time.time()-start_time)
