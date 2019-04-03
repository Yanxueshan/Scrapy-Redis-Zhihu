from scrapy import signals
from fake_useragent import UserAgent
from settings import USER_AGENT_LIST, BASE_DIR
import random
from scrapy.http import HtmlResponse
import os
import pickle
from libs.proxy import Fetch_Proxy


class ZhihuSpiderMiddleware(object):
    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the spider middleware does not modify the
    # passed objects.

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_spider_input(self, response, spider):
        # Called for each response that goes through the spider
        # middleware and into the spider.

        # Should return None or raise an exception.
        return None

    def process_spider_output(self, response, result, spider):
        # Called with the results returned from the Spider, after
        # it has processed the response.

        # Must return an iterable of Request, dict or Item objects.
        for i in result:
            yield i

    def process_spider_exception(self, response, exception, spider):
        # Called when a spider or process_spider_input() method
        # (from other spider middleware) raises an exception.

        # Should return either None or an iterable of Response, dict
        # or Item objects.
        pass

    def process_start_requests(self, start_requests, spider):
        # Called with the start requests of the spider, and works
        # similarly to the process_spider_output() method, except
        # that it doesn’t have a response associated.

        # Must return only requests (not items).
        for r in start_requests:
            yield r

    def spider_opened(self, spider):
        spider.logger.info('Spider opened: %s' % spider.name)


class ZhihuDownloaderMiddleware(object):
    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the downloader middleware does not modify the
    # passed objects.

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_request(self, request, spider):
        # Called for each request that goes through the downloader
        # middleware.

        # Must either:
        # - return None: continue processing this request
        # - or return a Response object
        # - or return a Request object
        # - or raise IgnoreRequest: process_exception() methods of
        #   installed downloader middleware will be called
        return None

    def process_response(self, request, response, spider):
        # Called with the response returned from the downloader.

        # Must either;
        # - return a Response object
        # - return a Request object
        # - or raise IgnoreRequest
        return response

    def process_exception(self, request, exception, spider):
        # Called when a download handler or a process_request()
        # (from other downloader middleware) raises an exception.

        # Must either:
        # - return None: continue processing this exception
        # - return a Response object: stops process_exception() chain
        # - return a Request object: stops process_exception() chain
        pass

    def spider_opened(self, spider):
        spider.logger.info('Spider opened: %s' % spider.name)


class RandomUserAgentDownloaderMiddleware(object):
    '''
        randomly generated user-agent
    '''
    def __init__(self, crawler):
        # self.user_agent = UserAgent()
        self.user_agent_list = crawler.settings.get('USER_AGENT_LIST', [])
        super().__init__()

    @classmethod
    def from_crawler(cls, crawler):
        '''
            get crawler
        '''
        return cls(crawler)

    def process_request(self, request, spider):
        '''
            process request --> add random user-agent to request's headers
        '''
        user_agent = random.choice(self.user_agent_list)
        print("Using User-Agent: ", user_agent)
        request.headers.setdefault("User-Agent", user_agent)


class ProxyDownloaderMiddleware(object):
    '''
        设置IP代理
    '''
    def __init__(self, crawler):
        self.fetch = Fetch_Proxy()
        super().__init__()

    @classmethod
    def from_crawler(cls, crawler):
        '''
            自己写Middleware必须实现的函数，manager会自主调用
        '''
        return cls(crawler)

    def process_request(self, request, spider):
        '''
            process request --> add random user-agent to request's headers
        '''
        proxy = self.fetch.get_random_ip()
        print("Using proxy: ", proxy)
        request.meta["proxy"] = "http://" + proxy


class RedirectDealDownloaderMiddleware(object):
    '''
        处理知乎302重定向问题以及最初cookies传递问题
    '''
    def process_response(self, request, response, spider):
        '''
            deal with 302
        '''
        if response.status == 302 and 'signup' in response.url:
            cookies = spider.get_cookies()
            cookies_dict = {}
            for cookie in cookies:
                cookies_dict[cookie["name"]] = cookie["value"]

            headers = {
                'set-cookie': cookies_dict
            }
            return HtmlResponse(url=spider.browser.current_url, body=spider.browser.page_source,
                                encoding='utf8', request=request, headers=headers)
        if 'signin' in response.url:
            cookies = []
            if os.path.exists(BASE_DIR+'/Zhihu/cookies/zhihu.cookies'):
                cookies = pickle.load(open(BASE_DIR+'/Zhihu/cookies/zhihu.cookies', 'rb'))

            if not cookies:
                cookies = spider.get_cookies()

            cookies_dict = {}
            for cookie in cookies:
                cookies_dict[cookie["name"]] = cookie["value"]

            headers = {
                'set-cookie': cookies_dict
            }
            return HtmlResponse(url=spider.browser.current_url, body=spider.browser.page_source,
                                encoding='utf8', request=request, headers=headers)
        return response
