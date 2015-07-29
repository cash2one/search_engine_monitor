# coding: utf8
import string,os,sys,re,time,math,random,hashlib
from datetime import datetime, timedelta
import pdb
import logging
import subprocess
from optparse import OptionParser

sys.path.append('/home/yangrq/projects/pycore')
from db.mysqlv6 import MySQLOperator
from utils.common_handler import CommonHandler
from utils.daemon_util import DaemonUtil
from utils.btlog import btlog_init

sys.path.append('mycrawler') # for config.py
import settings

class SeoCoreKeywordManager(CommonHandler, DaemonUtil):
    def __init__(self):
        DaemonUtil.__init__(self, 'baidu_keyword_scrapy_manager')

        self.task_db_conn = MySQLOperator()
        if not self.task_db_conn.Connect(**settings.DB_CONF):
            raise Exception, "db error"

    # start scrapy
    def do_run(self):
        # get min(task_date)
        sql = "select task_date from baidu_keyword_manager where flag = 'init' order by task_date asc limit 1"
        result_set = self.task_db_conn.Query(sql)
        if not result_set or len(result_set) == 0:
            logging.info("no task")
            return
        task_date = result_set[0][0]
        cmd = "/usr/local/bin/scrapy crawl baidu_keyword -a task_date=%s --logfile=log_scrapy.baidu_keyword.%s.log" % (task_date, task_date)
        logging.info("cmd: %s" % cmd)
        subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE).communicate()[0].strip()

    def run(self):
        if self.IsRunning():
            logging.info('== is running ==')
            return

        self.WritePidFile()
        self.do_run()

if __name__ == '__main__':
    btlog_init("log_baidu_keyword_scrapy_manager.log", logfile=True, console=False)
    t = SeoCoreKeywordManager()
    t.run()
