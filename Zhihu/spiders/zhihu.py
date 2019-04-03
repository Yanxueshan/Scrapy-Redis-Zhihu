# -*- coding: utf-8 -*-
import scrapy
import re
import os
import json
import datetime
import time
import pickle
import base64
import mouse
from settings import BASE_DIR, ZHIHU_ACCOUNT, ZHIHU_PASSWORD, CHAOJIYING_ACCOUNT, CHAOJIYING_PASSWORD, CAPTCHA_TYPE
from scrapy.xlib.pydispatch import dispatcher
from scrapy import signals
from scrapy.loader import ItemLoader
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from items import ZhihuAnswerItem, ZhihuQuestionItem
from urllib import parse
from libs.common import get_md5, get_position, extract_nums
from libs.chaojiying import Chaojiying_Client
from scrapy_redis.spiders import RedisSpider
from scrapy_redis.utils import bytes_to_str


class ZhihuSpider(RedisSpider):
    '''
        ZhihuSpier --> get question and answer from www.zhihu.com
    '''
    name = 'zhihu'
    allowed_domains = ['www.zhihu.com']
    redis_key = 'zhihu:start_urls'
    # start_urls = ['https://www.zhihu.com/']
    start_answer_url = 'https://www.zhihu.com/api/v4/questions/{0}/answers?include=data%5B%2A%5D.is_normal%2Cadmin_closed_comment%2Creward_info%2Cis_collapsed%2Cannotation_action%2Cannotation_detail%2Ccollapse_reason%2Cis_sticky%2Ccollapsed_by%2Csuggest_edit%2Ccomment_count%2Ccan_comment%2Ccontent%2Ceditable_content%2Cvoteup_count%2Creshipment_settings%2Ccomment_permission%2Ccreated_time%2Cupdated_time%2Creview_info%2Crelevant_info%2Cquestion%2Cexcerpt%2Crelationship.is_authorized%2Cis_author%2Cvoting%2Cis_thanked%2Cis_nothelp%2Cis_labeled%2Cis_recognized%2Cpaid_info%3Bdata%5B%2A%5D.mark_infos%5B%2A%5D.url%3Bdata%5B%2A%5D.author.follower_count%2Cbadge%5B%2A%5D.topics&limit={1}&offset={2}&platform=desktop&sort_by=default'
    # scrapy默认处理 >=200 并且 <300 的URL，其他的会过滤掉，handle_httpstatus_list表示对返回这些状态码的URL不过滤，自己处理
    handle_httpstatus_list = [302, 400, 403, 404, 500]

    def __init__(self):
        # scrapy集成selenium
        # chromedriver中有一些js变量会暴露，被服务器识别出来，所以保险起见，可以手动启动chromedriver
        # 1. 找到chrome.exe文件所在路径，cmd中进入该路径，执行chrome.exe --remote-debugging-port=9222
        # 2. 执行下列语句（执行第一步后要保证127.0.0.1:9222/json能够正常访问，在这之前需要退出所有的chrome）
        chrome_opt = Options()
        chrome_opt.add_argument("--disable-extensions")
        chrome_opt.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
        self.browser = webdriver.Chrome(executable_path="C:/Users/晏乐/Desktop/Lagou/chromedriver",
                                        chrome_options=chrome_opt)

        # crawl_url_count: 用来统计爬取URL的总数
        self.crawl_url_count = 0

        # 数据收集，收集Scrapy运行过程中302/403/404页面URL及URL数量
        # failed_url: 用来存放302/403/404页面URL
        self.failed_urls = []

        # 信号处理，当爬虫退出时执行spider_closed方法
        dispatcher.connect(self.spider_closed, signals.spider_closed)

        # 信号处理，当引擎从downloader中获取到一个新的Response对象时调用get_crawl_url_count方法
        dispatcher.connect(self.get_crawl_url_count, signals.response_received)

        super().__init__()

    # def start_requests(self):
    #     cookies = []
    #     if os.path.exists(BASE_DIR+'/Zhihu/cookies/zhihu.cookies'):
    #         cookies = pickle.load(open(BASE_DIR+'/Zhihu/cookies/zhihu.cookies', 'rb'))

    #     if not cookies:
    #         cookies = self.get_cookies()

    #     cookies_dict = {}
    #     for cookie in cookies:
    #         cookies_dict[cookie["name"]] = cookie["value"]

        # use_set = self.settings.getbool('REDIS_START_URLS_AS_SET', defaults.START_URLS_AS_SET)
        # fetch_one = self.server.lpop
        # data = fetch_one(self.redis_key)
        # url = bytes_to_str(data, self.redis_encoding)
        # for url in self.start_urls:
        #     yield scrapy.Request(url, dont_filter=True, cookies=cookies_dict)

    def parse(self, response):
        '''
            parse response --> get question's url
        '''
        # get all urls and filter
        all_urls = response.css("a::attr(href)").extract()
        all_urls = [parse.urljoin(response.url, url) for url in all_urls]
        all_urls = list(filter(lambda url: True if url.startswith("http") else False, all_urls))

        for url in all_urls:
            re_match = re.match('(.*?zhihu.com/question/(\d+)).*', url)
            if re_match:
                request_url = re_match.group(1)
                question_id = re_match.group(2)
                yield scrapy.Request(url=request_url, meta={"question_id": question_id}, callback=self.parse_question)
                break
            else:
                yield scrapy.Request(url=url, callback=self.parse)

    def parse_question(self, response):
        '''
            parse question
        '''
        if response.status in self.handle_httpstatus_list:
            self.failed_urls.append(response.url)
            # 数据收集，当Response状态码为403/404/500时，failed_url数加1
            self.crawler.stats.inc_value("failed_url")

        question_item = ZhihuQuestionItem()
        question_id = int(response.meta.get("question_id"))
        title = response.css('.QuestionHeader-title::text').extract_first('')
        question_url = response.url
        topics = response.css('meta[itemprop="keywords"]::attr(content)').extract()
        topics = '/'.join(topics)
        content = response.css('.QuestionRichText--collapsed div span::text').extract_first('')
        answer_nums = response.css('.List-headerText span::text').extract_first('')
        answer_nums = extract_nums(answer_nums)
        comment_nums = response.css('.QuestionHeader-Comment button::text').extract_first('')
        comment_nums = extract_nums(comment_nums)
        watch_user_nums = response.css('.NumberBoard-itemValue::text').extract_first('')
        watch_user_nums = extract_nums(watch_user_nums)
        click_nums = response.css('.NumberBoard-itemValue::text').extract()[1]
        click_nums = extract_nums(click_nums)
        crawl_time = datetime.datetime.now()

        question_item["question_id"] = question_id
        question_item["topics"] = topics
        question_item["question_url"] = question_url
        question_item["title"] = title
        question_item["content"] = content
        question_item["answer_nums"] = answer_nums
        question_item["comment_nums"] = comment_nums
        question_item["watch_user_nums"] = watch_user_nums
        question_item["click_nums"] = click_nums
        question_item["crawl_time"] = crawl_time

        yield question_item
        yield scrapy.Request(self.start_answer_url.format(question_id, 5, 0), callback=self.parse_answer)

    def parse_answer(self, response):
        '''
            parse answer
        '''
        if response.status in self.handle_httpstatus_list:
            self.failed_urls.append(response.url)
            # 数据收集，当Response状态码为403/404/500时，failed_url数加1
            self.crawler.stats.inc_value("failed_url")

        answer_dcit = json.loads(response.text)
        is_end = answer_dcit['paging']['is_end']
        next_url = answer_dcit['paging']['next']

        for answer in answer_dcit['data']:
            answer_item = ZhihuAnswerItem()
            answer_item["answer_id"] = answer['id']
            answer_item["question_id"] = answer['question']['id']
            answer_item["answer_url"] = answer['url']
            answer_item["author_id"] = answer['author']['id'] if 'id' in answer['author'] else ''
            answer_item["content"] = answer['content']
            answer_item["praise_nums"] = answer['voteup_count']
            answer_item["comment_nums"] = answer['comment_count']
            answer_item["create_time"] = answer['created_time']
            answer_item["update_time"] = answer['updated_time']
            answer_item["crawl_time"] = datetime.datetime.now()
            question_create_time = answer['question']['created']
            question_update_time = answer['question']['updated_time']
            yield answer_item

        if not is_end:
            yield scrapy.Request(next_url, callback=self.parse_answer)

    def spider_closed(self, spider):
        '''
            当爬虫退出时关闭chrome，收集爬取失败（302/403/404）的URL，并写入json文件中
        '''
        self.browser.quit()
        self.crawler.stats.set_value("failed_urls", ','.join(self.failed_urls))
        failed_url_dict = {'failed_urls': self.failed_urls}
        json_str = json.dumps(failed_url_dict)
        with open(BASE_DIR+"/Zhihu/failed_urls/failed_urls.json", 'w') as f:
            f.write(json_str)

    def get_crawl_url_count(self, spider):
        '''
            当引擎engine从downloader中获取到一个新的Response对象时调用，crawl_url_count+=1
        '''
        self.crawl_url_count += 1
        print("截至目前已爬取URL总数为: ", self.crawl_url_count)
        return self.crawl_url_count
    
    def get_cookies(self):
        '''
            get cookies from www.zhihu.com
        '''
        # 1. maximize the browser window
        try:
            self.browser.maximize_window()
        except Exception:
            pass

        # 2. login simulation
        self.browser.get("https://www.zhihu.com/signin")
        self.browser.find_element_by_css_selector(".SignFlow-accountInput.Input-wrapper input").send_keys(Keys.CONTROL + "a")
        self.browser.find_element_by_css_selector(".SignFlow-accountInput.Input-wrapper input").send_keys(ZHIHU_ACCOUNT)
        self.browser.find_element_by_css_selector(".SignFlow-password input").send_keys(Keys.CONTROL + "a")
        self.browser.find_element_by_css_selector(".SignFlow-password input").send_keys(ZHIHU_PASSWORD)
        self.browser.find_element_by_css_selector(".Button.SignFlow-submitButton").click()
        time.sleep(5)

        login_success = False
        while not login_success:
            # if login failed, login again --> captcha identification --> english captcha and chinese captcha
            
            # if login success, can find element with the class_name GlobalWrite-navTitle
            try:
                notify_ele = self.browser.find_element_by_class_name("GlobalWrite-navTitle")
                login_success = True
                break
            except Exception:
                pass

            # find english captcha or chinese captcha
            try:
                english_captcha_element = self.browser.find_element_by_class_name("Captcha-englishImg")
            except Exception:
                english_captcha_element = None
            try:
                chinese_captcha_element = self.browser.find_element_by_class_name("Captcha-chineseImg")
            except Exception:
                chinese_captcha_element = None

            # deal with chinese captcha
            if chinese_captcha_element:
                self.deal_with_chinese_captcha(chinese_captcha_element)

            # deal with english captcha
            if english_captcha_element:
                self.deal_with_english_captcha(english_captcha_element)

        if login_success:
            # if login success, get cookies and write cookies to a file
            cookies = self.browser.get_cookies()
            pickle.dump(cookies, open(BASE_DIR+"/Zhihu/cookies/zhihu.cookies", 'wb'))

        return cookies

    def deal_with_chinese_captcha(self, chinese_captcha_element):
        '''
            deal with chinese captcha
        '''
        # get chinese captcha image coordinate
        ele_position = chinese_captcha_element.location
        x_coordinate = ele_position['x']
        y_coordinate = ele_position['y']
        browser_navigation_panel_height = self.browser.execute_script(
            "return window.outerHeight - window.innerHeight;"
        )

        # find chinese captcha image and write to a file
        base64_text = chinese_captcha_element.get_attribute("src")
        code = base64_text.replace("data:image/jpg;base64,", "").replace("%0A", "")
        with open(BASE_DIR+'/Zhihu/captcha/chinese_captcha.jpeg', 'wb') as f:
            f.write(base64.b64decode(code))

        # deal with chinese captcha
        positions = get_position(BASE_DIR+'/Zhihu/captcha/chinese_captcha.jpeg')
        if len(positions) == 2:
            first_position = [positions[0][0] // 2, positions[0][1] // 2]
            second_position = [positions[1][0] // 2, positions[1][1] // 2]

            # click first inverted character
            mouse.move(
                x_coordinate+first_position[0],
                y_coordinate+browser_navigation_panel_height+first_position[1]
            )
            mouse.click()

            # click second inverted character
            time.sleep(2)
            mouse.move(
                x_coordinate+second_position[0],
                y_coordinate+browser_navigation_panel_height+second_position[1]
            )
            mouse.click()
        else:
            first_position = [positions[0][0] // 2, positions[0][1] // 2]
            mouse.move(
                x_coordinate+first_position[0],
                y_coordinate+browser_navigation_panel_height+first_position[1]
            )
            mouse.click()

        # input account and password again
        self.browser.find_element_by_css_selector(".SignFlow-accountInput.Input-wrapper input").send_keys(Keys.CONTROL + "a")
        self.browser.find_element_by_css_selector(".SignFlow-accountInput.Input-wrapper input").send_keys(ZHIHU_ACCOUNT)
        self.browser.find_element_by_css_selector(".SignFlow-password input").send_keys(Keys.CONTROL + "a")
        self.browser.find_element_by_css_selector(".SignFlow-password input").send_keys(ZHIHU_PASSWORD)
        self.browser.find_element_by_css_selector(".Button.SignFlow-submitButton").click()
        time.sleep(5)

    def deal_with_english_captcha(self, english_captcha_element):
        '''
            deal with english captcha
        '''
        # find english captcha image and write to a file
        base64_text = english_captcha_element.get_attribute("src")
        code = base64_text.replace("data:image/jpg;base64,", "").replace("%0A", "")
        with open(BASE_DIR+'/Zhihu/captcha/english_captcha.jpeg', 'wb') as f:
            f.write(base64.b64decode(code))

        # deal with english captcha
        chaojiying = Chaojiying_Client(CHAOJIYING_ACCOUNT, CHAOJIYING_PASSWORD, CAPTCHA_TYPE)
        with open(BASE_DIR+'/Zhihu/captcha/english_captcha.jpeg', 'rb') as f:
            im = f.read()
        result = chaojiying.PostPic(im, 1005)['pic_str']
        self.browser.find_element_by_css_selector('.Input-wrapper input[name="captcha"]').send_keys(Keys.CONTROL + 'a')
        self.browser.find_element_by_css_selector('.Input-wrapper input[name="captcha"]').send_keys(result)

        # input account and password again
        self.browser.find_element_by_css_selector(".SignFlow-accountInput.Input-wrapper input").send_keys(Keys.CONTROL + "a")
        self.browser.find_element_by_css_selector(".SignFlow-accountInput.Input-wrapper input").send_keys(ZHIHU_ACCOUNT)
        self.browser.find_element_by_css_selector(".SignFlow-password input").send_keys(Keys.CONTROL + "a")
        self.browser.find_element_by_css_selector(".SignFlow-password input").send_keys(ZHIHU_PASSWORD)
        self.browser.find_element_by_css_selector(".Button.SignFlow-submitButton").click()
        time.sleep(5)
