# -*- coding: utf-8 -*-
from pymysql.cursors import DictCursor
from twisted.enterprise import adbapi


class MySQLTwistedPipeline(object):
    '''
        将MySQL插入操作变成异步化
    '''
    def __init__(self, db_pool):
        self.db_pool = db_pool

    @classmethod
    def from_settings(cls, settings):
        '''
            create db_pool
        '''
        db_parameters = dict(
            host=settings["MYSQL_HOST"],
            db=settings["MYSQL_DBNAME"],
            user=settings["MYSQL_USER"],
            passwd=settings["MYSQL_PASSWORD"],
            charset="utf8",
            cursorclass=DictCursor,
            use_unicode=True
        )
        db_pool = adbapi.ConnectionPool("pymysql", **db_parameters)
        return cls(db_pool)

    def process_item(self, item, spider):
        '''
            process item
        '''
        query = self.db_pool.runInteraction(self.do_insert, item)
        query.addErrback(self.handle_error, item, spider)

    def handle_error(self, failure, item, spider):
        '''
            handle error of insert to mysql
        '''
        print(failure)

    def do_insert(self, cursor, item):
        '''
            insert data into the database
        '''
        insert_sql, parameters = item.get_insert_sql()
        cursor.execute(insert_sql, parameters)
