'''
    本模块用于编写一些用于Scrapy中的一些可用函数
'''
import hashlib
import re
from zheye import zheye

__author__ = 'Yan'
__date__ = '2019/3/25 20:56'


def get_md5(url):
    '''
        将url进行md5哈希，返回固定长度的字符串
    '''
    if isinstance(url, str):
        url = url.encode('utf-8')
    return hashlib.md5(url).hexdigest()


def get_position(captcha):
    '''
        识别知乎倒立文字验证码，返回倒立文字所在坐标
    '''
    z = zheye()
    positions = z.Recognize(captcha)
    result = []
    if len(positions) == 2:
        # two inverted characters
        if positions[0][1] > positions[1][1]:
            result.append([positions[1][1], positions[1][0]])
            result.append([positions[0][1], positions[0][0]])
        else:
            result.append([positions[0][1], positions[0][0]])
            result.append([positions[1][1], positions[1][0]])
    else:
        # one inverted characters
        result.append([positions[0][1], positions[0][0]])
    return result


def extract_nums(text):
    '''
        从text中提取出数字
    '''
    text = text.replace(',', '')
    re_match = re.match('.*?(\d+).*', text)
    nums = 0
    if re_match:
        nums = re_match.group(1)
    return int(nums)


if __name__ == "__main__":
    result = get_position('../zhihu_image/a.gif')
    print(result)
