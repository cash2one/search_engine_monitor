# coding: utf8

import os
import sys
import re
import logging
import urllib
import pdb

sys.path.append("/home/yangrq/projects/pycore")

from utils.common_handler import CommonHandler
from utils.http_client import HttpClient

from scrapy.http import Request
from scrapy.selector import HtmlXPathSelector
from scrapy.contrib.linkextractors.sgml import SgmlLinkExtractor
from scrapy.spider import BaseSpider

class BaseParser(CommonHandler):
    def __init__(self):
        pass

    def parse(self, div_selector):
        pass

    def _parse_id(self, a_selector):
        idx = a_selector.select("@id").extract()
        if len(idx) > 0:
            idx = idx[0]
        else:
            idx = "-1"
        return idx

    def _parse_title(self, a_selector):
        title = a_selector.select('.//h3/a').extract()
        if len(title) > 0:
            title = title[0].strip()
        else:
            title = ""
        title = self.strip_html_tag(title)
        title = title.replace("\n", "")
        return title

    def _get_lst_str(self, str_lst):
        if len(str_lst) > 0:
            return str_lst[0].strip()
        else:
            return ''

    def strip_html_tag(self, content):
#        content = re.sub(r"<script[^>]*?>.*?</script>", "", content)
        content = self.ToString(content)
        content = re.sub(r"<[^>]*?>", "", content)
        pos = content.find(">")
        if pos >= 0:
            content = content[pos+1:]
        pos = content.find("<")
        if pos > 0:
            content = content[:pos]
        return content

class ParserAlading(BaseParser):
    TYPE = 'op_alading'
    def __init__(self):
        pass

    def parse(self, div_selector):
        div_class = div_selector.select("@class").extract()[0]
        if not div_class.startswith('result-op'):
            return {}

        idx = self._parse_id(div_selector)
        title = self._parse_title(div_selector)

        domain = div_selector.select('.//div/span/text()').extract()
        domain = self._get_lst_str(domain)
        if domain:
            domain = domain.split()[0]
            domain = domain.strip('.')

        return {'id': idx, 'title': title, 'domain': domain, 'type': self.TYPE}

class ParserOpJingyan(BaseParser):
    TYPE = 'op_jingyan'
    def __init__(self):
        pass

    def parse(self, div_selector):
        div_class = div_selector.select("@class").extract()[0]
        if not div_class.startswith('result-op'):
            return {}

        idx = self._parse_id(div_selector)
        title = self._parse_title(div_selector)

        domain = div_selector.select(".//div/span[@class='c-showurl']/text()").extract()
        domain = self._get_lst_str(domain)
        if domain:
            domain = domain.split()[0]
            domain = domain.strip('.')

        return {'id': idx, 'title': title, 'domain': domain, 'type': self.TYPE}

class ParserCommon(BaseParser):
    TYPE = 'common'
    def __init__(self):
        pass

    def parse(self, div_selector):
        div_class = div_selector.select("@class").extract()[0]
        if not div_class.startswith('result c-container'):
            return {}

        idx = self._parse_id(div_selector)
        title = self._parse_title(div_selector)

        description = div_selector.select(".//div[@class='c-abstract']").extract()
        description = self._get_lst_str(description)
        if description:
            description = self.strip_html_tag(description)
            description = description.replace("\n", "")

        domain = div_selector.select(".//div[@class=\"f13\"]/span").extract()
        domain = self._get_lst_str(domain)
        if domain:
            domain = self.strip_html_tag(domain)
            domain = domain.replace("\n", "")
            domain = domain.split()[0]
            domain = domain.strip('.')

        return {'id': idx, 'title': title, 'description': description, 'domain': domain, 'type': self.TYPE}

class ParserBaiduBaike(BaseParser):
    TYPE = 'baidubaike'
    def __init__(self):
        pass

    def parse(self, div_selector):
        div_class = div_selector.select("@class").extract()[0]
        if not div_class.startswith('result c-container'):
            return {}

        idx = div_selector.select("@id").extract()
        idx = self._parse_id(div_selector)
        title = self._parse_title(div_selector)

        description = div_selector.select(".//div/div/p[0]").extract()
        description = self._get_lst_str(description)
        if not description:
            return {}
        description = self.strip_html_tag(description)
        description = description.replace("\n", "")

        domain = div_selector.select(".//div/div/p/span/text()").extract()
        domain = self._get_lst_str(domain)
        if domain:
            domain = domain.split()[0]
            domain = domain.strip('.')

        return {'id': idx, 'title': title, 'description': description, 'domain': domain, 'type': self.TYPE}

class ParserImage(BaseParser):
    TYPE = 'image'
    def __init__(self):
        pass

    def parse(self, div_selector):
        div_class = div_selector.select("@class").extract()[0]
        if not div_class.startswith('result c-container'):
            return {}

        idx = self._parse_id(div_selector)
        title = self._parse_title(div_selector)

        description = div_selector.select(".//div/div[@class='c-abstract']").extract()
        description = self._get_lst_str(description)
        if not description:
            return {} # is not 
        description = self.strip_html_tag(description)
        description = description.replace("\n", "")

        domain = div_selector.select(".//div/div[@class=\"f13\"]/span/text()").extract()
        domain = self._get_lst_str(domain)
        if domain:
            domain = domain.split()[0]
            domain = domain.strip('.')

        return {'id': idx, 'title': title, 'description': description, 'domain': domain, 'type': self.TYPE}

class ParserTable(BaseParser):
    TYPE = 'table'
    def __init__(self):
        pass

    def parse(self, table_selector):
        table_class = table_selector.select("@class").extract()[0]
        if not table_class.startswith('result'):
            return {}
        idx = self._parse_id(table_selector)
        description = table_selector.extract()
        description = self.strip_html_tag(description)
        return {'id': idx, 'description': description, 'type': self.TYPE}

class ParserBroker(CommonHandler, HttpClient):
    TEST_FILE   = ".parser_baidu_core_keyword.html"
# 这个顺序很重要，越在前面的优先级越高
    div_parsers = [ParserImage(), ParserBaiduBaike(), ParserCommon(), ParserAlading()]
    table_parsers = [ParserTable(),]

    def parse(self, html):
        div_list = self.parse_div(html)
        table_list = self.parse_table(html)
        div_list.extend(table_list)

        new_lst = sorted(div_list, key=lambda x: int(x['id']))
        return new_lst

    def parse_table(self, html):
        hxs = HtmlXPathSelector(text=html)
        content_left_table_selectors = hxs.select(".//*[@id='content_left']/table[starts-with(@class,'result')]")

        table_result_list = []
        for table_selector in content_left_table_selectors:
            for parser in self.table_parsers:
                item_dict = parser.parse(table_selector)
                if item_dict and len(item_dict) > 0:
                    table_result_list.append(item_dict)
                    break
        return table_result_list

    def parse_div(self, html):
        hxs = HtmlXPathSelector(text=html)
        content_left_div_selectors = hxs.select(".//*[@id='content_left']/div[starts-with(@class,'result')]")

        div_result_list = []
        for div_selector in content_left_div_selectors:
            for parser in self.div_parsers:
                item_dict = parser.parse(div_selector)
                if item_dict and len(item_dict)  > 0:
                    div_result_list.append(item_dict)
                    break
        return div_result_list

    def test_parse(self, p=False):
        keyword = '代理服务器'
        url = "http://www.baidu.com/s?ie=utf-8&mod=0&isid=F3B6D39EEF328045&pstg=0&wd=%s&ie=utf-8&tn=baiduhome_pg&f=8&rn=20" % urllib.quote_plus(keyword)
        print url
        urllib.urlretrieve(url, self.TEST_FILE)
        html_data = self.LoadFile(self.TEST_FILE)
        lst   = self.parse(html_data)
        for d in lst:
            for x,y in d.iteritems():
                print x,y
            print ''


if __name__ == '__main__':
    b   = ParserBroker()
    b.test_parse(True)
