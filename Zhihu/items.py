# -*- coding: utf-8 -*-
import scrapy
from datetime import datetime
from settings import SQL_DATETIME_FORMAT


class ZhihuQuestionItem(scrapy.Item):
    '''
        zhihu's question item design
    '''
    question_id = scrapy.Field()
    topics = scrapy.Field()
    question_url = scrapy.Field()
    title = scrapy.Field()
    content = scrapy.Field()
    create_time = scrapy.Field()
    update_time = scrapy.Field()
    answer_nums = scrapy.Field()
    comment_nums = scrapy.Field()
    watch_user_nums = scrapy.Field()
    click_nums = scrapy.Field()
    crawl_time = scrapy.Field()
    crawl_update_time = scrapy.Field()

    def get_insert_sql(self):
        '''
            get insert_sql and parameters of question
        '''
        insert_sql = "insert into question(question_id, topics, question_url, title, content, answer_nums, " \
                     "comment_nums, watch_user_nums, click_nums, crawl_time)VALUES (%s, %s, %s, %s, %s, %s, %s, %s, " \
                     "%s, %s)ON DUPLICATE KEY UPDATE content=VALUES(content), answer_nums=VALUES(" \
                     "answer_nums),comment_nums=VALUES(comment_nums), watch_user_nums=VALUES" \
                     "(watch_user_nums),click_nums=VALUES(click_nums)"

        parameters = (
            self['question_id'], self['topics'], self['question_url'],
            self['title'], self['content'], self['answer_nums'],
            self['comment_nums'], self['watch_user_nums'],
            self['click_nums'], self['crawl_time']
        )
        return insert_sql, parameters


class ZhihuAnswerItem(scrapy.Item):
    '''
        zhihu's answer item design
    '''
    answer_id = scrapy.Field()
    question_id = scrapy.Field()
    answer_url = scrapy.Field()
    author_id = scrapy.Field()
    content = scrapy.Field()
    praise_nums = scrapy.Field()
    comment_nums = scrapy.Field()
    create_time = scrapy.Field()
    update_time = scrapy.Field()
    crawl_time = scrapy.Field()
    crawl_update_time = scrapy.Field()

    def get_insert_sql(self):
        '''
            get insert_sql and parameters of answer
        '''
        insert_sql = "insert into answer(answer_id, question_id, answer_url, author_id, content, praise_nums, " \
                     "comment_nums, create_time, update_time, crawl_time) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, " \
                     "%s, %s)ON DUPLICATE KEY UPDATE content=VALUES(content), praise_nums=VALUES(" \
                     "praise_nums), comment_nums=VALUES(comment_nums), update_time=VALUES(update_time)"

        create_time = datetime.fromtimestamp(self['create_time']).strftime(SQL_DATETIME_FORMAT)
        update_time = datetime.fromtimestamp(self['update_time']).strftime(SQL_DATETIME_FORMAT)

        parameters = (
            self['answer_id'], self['question_id'], self['answer_url'],
            self['author_id'], self['content'], self['praise_nums'],
            self['comment_nums'], create_time, update_time, self['crawl_time']
        )
        return insert_sql, parameters
