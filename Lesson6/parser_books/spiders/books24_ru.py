import scrapy
from scrapy.http import HtmlResponse


class Books24RuSpider(scrapy.Spider):
    name = "books24_ru"
    allowed_domains = ["books24.ru"]
    start_urls = ["https://book24.ru/novie-knigi/"]

    def parse(self, response: HtmlResponse):
        pass