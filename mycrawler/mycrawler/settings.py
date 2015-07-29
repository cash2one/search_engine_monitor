# Scrapy settings for mycrawler project
#
# For simplicity, this file contains only the most important settings by
# default. All the other settings are documented here:
#
#     http://doc.scrapy.org/topics/settings.html
#

BOT_NAME = 'mycrawler'

SPIDER_MODULES = ['mycrawler.spiders']
NEWSPIDER_MODULE = 'mycrawler.spiders'

# Crawl responsibly by identifying yourself (and your website) on the user-agent
USER_AGENT = 'mycrawler (+http://www.yourdomain.com)'

DB_CONF = {
    "host"  : "192.168.254.10",
    "user"  : "homestead",
    "passwd": "secret",
    "database"  : "search_engine_monitor",
    "port"      : 3306,
    "charset"   : "utf8"
}
