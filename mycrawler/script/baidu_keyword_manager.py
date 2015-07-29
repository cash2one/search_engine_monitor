#!/usr/bin/python
# coding: utf-8

import os
import sys
import time
import hashlib
import random
import logging
import pdb
from datetime import datetime, timedelta
from optparse import OptionParser

FILE_PATH = os.path.realpath(os.path.dirname(__file__))

CORE_PATH = '/home/yangrq/projects/pycore'
if CORE_PATH not in sys.path:
    sys.path.append(CORE_PATH)

from db.mysqlv6 import MySQLOperator
from utils.common_handler import CommonHandler
from utils.btlog import btlog_init

sys.path.append('../mycrawler')
import settings

class CoreKeywordGenerator(CommonHandler):
    def __init__(self):
        parser = OptionParser()
        parser.add_option("--gentask", action="store_true")
        (self.opt, other) = parser.parse_args()

        self.db_conn = MySQLOperator()
        if not self.db_conn.Connect(**settings.DB_CONF):
            raise Exception, 'db err'
        logging.info("end init")

        self.baidu_result_table_base = 'baidu_keyword_result'
        self.baidu_task_table     = 'baidu_keyword_task'
        self.baidu_seed_table     = 'baidu_keyword_seed'
        self.baidu_manager_table  = 'baidu_keyword_manager'

    def prepare_result_table(self, task_date):
        dest_table = self.baidu_result_table_base + '_' + task_date
        sql = "create table if not exists %s like %s" % (dest_table, self.baidu_result_table_base)
        logging.info(sql)
        self.db_conn.Execute(sql)

    def _get_stat_info(self, task_date):
        sql = "select flag, count(*) cnt from %s where task_date='%s' group by flag " % (self.baidu_task_table, task_date)
        result_set = self.db_conn.QueryDict(sql)
        info_str = ""
        for row in result_set:
            info_str += "%s: %s;" % (row['flag'], row['cnt'])
        return info_str[:-1]

    def _set_task(self, task_date, flag, info=''):
        sql = "update %s set flag='%s',info='%s' where task_date='%s'" % (self.baidu_manager_table, flag, info, task_date)
        logging.info(sql)
        self.db_conn.Execute(sql)

    # todo_date format: YYYYmmdd
    def task_maintain(self, todo_date=None):
        logging.info("task_maintain")

        # handle outdated task
        sql = "select * from %s where flag='init' order by task_date desc " % self.baidu_manager_table
        res = self.db_conn.QueryDict(sql)
        for row in res[1:]: # leave latest task
            self._set_task(row['task_date'], 'crawled', self._get_stat_info(row['task_date']))

        # handle the latest task
        if len(res) > 0:
            task_info = res[0]
            info = self._get_stat_info(task_info['task_date'])
            sql = "select count(*) cnt from %s where task_date=%s " % (self.baidu_task_table,task_info['task_date'])
            cnt = self.db_conn.Query(sql)
            if cnt > 0:
                self._set_task(task_info['task_date'], 'init', info)
            else:
                self._set_task(task_info['task_date'], 'done', info)

        # delete old kw task
        sql = "select * from %s where flag <> 'init' order by task_date desc " % self.baidu_manager_table
        res = self.db_conn.QueryDict(sql)
        for row in res[4:]:
            sql = "delete from %s where task_date='%s' " % (self.baidu_task_table, row['task_date'])
            self.db_conn.Execute(sql)

    def gentask(self, task_date):
        logging.info("gen task")
        # to task
        sql = "select keyword from %s" % self.baidu_seed_table
        result_set = self.db_conn.Query(sql)
        logging.info(sql)
        logging.info("result_set len: %d" % len(result_set))
        for row in result_set:
            sql = "insert ignore into %s(task_date,keyword,flag,create_time) values(%%s,%%s,'init',%%s)" % self.baidu_task_table
            self.db_conn.Execute(sql, [task_date,row[0],datetime.now()]) #unique key: task_date,keyword

        # put manager
        sql = "insert ignore into %s(task_date,flag,create_time) values(%%s,'init',%%s)" % self.baidu_manager_table
        self.db_conn.Execute(sql, [task_date,datetime.now()])

    def run(self):
        # gen task to seo_statistic_core_keyword_task
        task_date = datetime.now().strftime('%Y%m%d')

        self.prepare_result_table(task_date)

        self.task_maintain()

        if self.opt.gentask:
            self.gentask(task_date)

if __name__ == '__main__':
    btlog_init('log_baidu_keyword.log', logfile=False, console=True)
    d = CoreKeywordGenerator()
    d.run()
