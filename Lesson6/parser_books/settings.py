# Scrapy settings for parser_books project
#
# For simplicity, this file contains only settings considered important or
# commonly used. You can find more settings consulting the documentation:
#
#     https://docs.scrapy.org/en/latest/topics/settings.html
#     https://docs.scrapy.org/en/latest/topics/downloader-middleware.html
#     https://docs.scrapy.org/en/latest/topics/spider-middleware.html

BOT_NAME = "parser_books"

SPIDER_MODULES = ["parser_books.spiders"]
NEWSPIDER_MODULE = "parser_books.spiders"
LOG_FILE = 'parser_books.log'
LOG_ENABLED = True
LOG_LEVEL = 'DEBUG'

IMAGES_STORE = 'photos'

# Crawl responsibly by identifying yourself (and your website) on the user-agent
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) " \
             "Chrome/110.0.0.0 Safari/537.36"

# Obey robots.txt rules
ROBOTSTXT_OBEY = False

# Configure maximum concurrent requests performed by Scrapy (default: 16)
CONCURRENT_REQUESTS = 1

# Configure a delay for requests for the same website (default: 0)
# See https://docs.scrapy.org/en/latest/topics/settings.html#download-delay
# See also autothrottle settings and docs
DOWNLOAD_DELAY = 5
# The download delay setting will honor only one of:
#CONCURRENT_REQUESTS_PER_DOMAIN = 16
#CONCURRENT_REQUESTS_PER_IP = 16

# Disable cookies (enabled by default)
COOKIES_ENABLED = True

# Disable Telnet Console (enabled by default)
#TELNETCONSOLE_ENABLED = False

# Override the default request headers:
DEFAULT_REQUEST_HEADERS = {
    'cookie': 'yuidss=7865139951667342343; yandexuid=7865139951667342343; ymex=1982702343.yrts.1667342343#1982702343.'
              'yrtsi.1667342343; _ym_uid=1667342344511078386; _ym_d=1667342345; is_gdpr=0; is_gdpr_b=CIyaHxDKlAEoAg==;'
              ' i=Azs+jMVW3/Q0HyYpieqLUWZgk2IWEss9u0hSuyoKi7r457z9If5sxpCU6nnFu3f7ZEjhWefmJ9M0TRcaSQ1OzQgvMnc=; '
              'yashr=1599161541674120162; gdpr=0; yandex_login=v.feldchun; Session_id=3:1676658234.5.0.1674637679357:'
              'agdaUQ:82.1.2:1|1747734627.0.2|3:10265727.109202.14kFa4fsyyaCH-CfiC_v2lnTaw0; sessionid2=3:1676658234.'
              '5.0.1674637679357:agdaUQ:82.1.2:1|1747734627.0.2|3:10265727.109202.fakesign0000000000000000000; '
              'skid=2802129131676659840; yabs-sid=1371937491676996042; yp=1989997679.udn.cDp2LmZlbGRjaHVu#1680019163.'
              'ygu.1; yandex_gid=117678',
#    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
#    "Accept-Language": "en",
}

# Enable or disable spider middlewares
# See https://docs.scrapy.org/en/latest/topics/spider-middleware.html
#SPIDER_MIDDLEWARES = {
#    "parser_books.middlewares.ParserBooksSpiderMiddleware": 543,
#}

# Enable or disable downloader middlewares
# See https://docs.scrapy.org/en/latest/topics/downloader-middleware.html
#DOWNLOADER_MIDDLEWARES = {
#    "parser_books.middlewares.ParserBooksDownloaderMiddleware": 543,
#}

# Enable or disable extensions
# See https://docs.scrapy.org/en/latest/topics/extensions.html
#EXTENSIONS = {
#    "scrapy.extensions.telnet.TelnetConsole": None,
#}

# Configure item pipelines
# See https://docs.scrapy.org/en/latest/topics/item-pipeline.html
ITEM_PIPELINES = {
    "parser_books.pipelines.ParserBooksPipeline": 300,
    "parser_books.pipelines.BooksPhotosPipeline": 200,
}

# Enable and configure the AutoThrottle extension (disabled by default)
# See https://docs.scrapy.org/en/latest/topics/autothrottle.html
#AUTOTHROTTLE_ENABLED = True
# The initial download delay
#AUTOTHROTTLE_START_DELAY = 5
# The maximum download delay to be set in case of high latencies
#AUTOTHROTTLE_MAX_DELAY = 60
# The average number of requests Scrapy should be sending in parallel to
# each remote server
#AUTOTHROTTLE_TARGET_CONCURRENCY = 1.0
# Enable showing throttling stats for every response received:
#AUTOTHROTTLE_DEBUG = False

# Enable and configure HTTP caching (disabled by default)
# See https://docs.scrapy.org/en/latest/topics/downloader-middleware.html#httpcache-middleware-settings
#HTTPCACHE_ENABLED = True
#HTTPCACHE_EXPIRATION_SECS = 0
#HTTPCACHE_DIR = "httpcache"
#HTTPCACHE_IGNORE_HTTP_CODES = []
#HTTPCACHE_STORAGE = "scrapy.extensions.httpcache.FilesystemCacheStorage"

# Set settings whose default value is deprecated to a future-proof value
REQUEST_FINGERPRINTER_IMPLEMENTATION = "2.7"
TWISTED_REACTOR = "twisted.internet.selectreactor.SelectReactor"
FEED_EXPORT_ENCODING = "utf-8"
