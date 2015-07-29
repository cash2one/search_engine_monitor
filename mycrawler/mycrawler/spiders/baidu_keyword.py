# coding: utf8

import sys
import logging
import urllib
import pdb

from scrapy.http import Request
from scrapy.selector import HtmlXPathSelector
from scrapy.spider import BaseSpider

sys.path.append("/home/yangrq/projects/pycore")
from db.mysqlv6 import MySQLOperator
from utils.common_handler import CommonHandler

from parser_baidu_keyword import ParserBroker

class KeywordSpider(BaseSpider, CommonHandler):
    name = "baidu_keyword"
    allowed_domains = ["baidu.com"]

    def __init__(self, task_date=None, kxdebug=None):
        self.task_date = task_date
        if not self.task_date:
            raise Exception, 'please provide task_date'

        self.kxdebug    = kxdebug
        self.url_format = "http://www.baidu.com/s?ie=utf-8&mod=0&isid=F3B6D39EEF328045&pstg=0&wd=%s&ie=utf-8&tn=baiduhome_pg&rn=50"

    def start_requests(self):
        self.db_conn = MySQLOperator()
        if not self.db_conn.Connect(**self.settings['DB_CONF']):
            raise Exception, 'connect db error'

        sql = "select id,keyword from baidu_keyword_task where task_date='%s' and flag = 'init' " % self.task_date
        if self.kxdebug:
            sql += " limit 1"
        result_set = self.db_conn.QueryDict(sql)
        self.log('sql: %s' % sql)
        self.log('==== task count: %d ' % len(result_set))

        request_list    = []
        for row in result_set:
            request = Request(
                url     = self.url_format % (urllib.quote_plus(self.ToString(row['keyword']))),
                meta    = {'kx_args': row})
            request_list.append(request)
        self.log("total request: %d" % len(request_list))
        return request_list

    def save_task(self, task_id, flag):
        self.log("ID: %s, flag: %s" % (str(task_id), flag))
        if flag:
            flag = 'finished'
        else:
            flag = 'failed'
        sql = "update baidu_keyword_task set flag='%s' where id=%s" % (flag, str(task_id))
        self.db_conn.Execute(sql)

    def parse(self, response):
        self.log("parse content len: %d" % len(response.body))

        html    = response.body
        kx_args = response.meta['kx_args']

        # parse
        parser = ParserBroker()
        parsed_lst = parser.parse(response.body)
        valid_flag = len(parsed_lst) >= 0
        
        self.save_task(kx_args['id'], valid_flag)
        if valid_flag:
            for row_dict in parsed_lst:
                db_dict                 = {}
                db_dict['keyword']      = kx_args['keyword']
                db_dict['idx']          = row_dict['id']
                db_dict['match_type']   = row_dict['type']
                db_dict['title']        = row_dict.get('title','')
                db_dict['domain']       = row_dict.get('domain', '')
                db_dict['description']  = row_dict.get('description', '')
                table_name = 'baidu_keyword_result_%s' % self.task_date
                self.db_conn.Upsert(table_name, db_dict, ['keyword', 'idx'])
