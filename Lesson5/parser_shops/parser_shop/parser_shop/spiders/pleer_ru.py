# Загружаем необходимые библиотеки
import scrapy
from scrapy.http import HtmlResponse

# Загружаем клас атрибутов товара определенный в items.py
from parser_shop.parser_shop.items import ParserShopItem

# Обьявляем клас паука
class PleerRuSpider(scrapy.Spider):
    name = 'pleer_ru'
    allowed_domains = ['pleer.ru']
    start_urls = ['http://pleer.ru/']

    def parse(self, response: HtmlResponse):
        # Получим список ссылок на предлагаемые товары
        products_links_list = response.xpath("//div[@class='slider__item']/a/@href").getall()
        # Проверяем на отсутствие товаров
        if not products_links_list:
            print("Скорее всего доступ заблокирован из-за большого количества запросов!")
            exit()

        # Преобразуем относительные пути в полные
        for i in range(len(products_links_list)):
            products_links_list[i] = response.url + products_links_list[i]

        # Запускаем очередь на загрузку и обработку страницы по каждому товару
        for link in products_links_list:
            yield response.follow(link, callback=self.parse_product)

    # Обьявляем метод обработки страницы товара
    def parse_product(self, response: HtmlResponse):
        # Получим наименование товара
        product_name = response.css("span.product_title::text").get()
        # Получим стоимость товара
        # Первый вариант цены иногрда бывает пустым
        # Поэтому проверяем на наличие цены
        if response.css("div.price::text").get():
            product_price1 = response.css("div.price::text")[0].get()
        else: # если цены нет то сохраняем 0
            product_price1 = '0'
        product_price1_info = response.css("div.info::text")[0].get()
        product_price2 = response.css("div.price span.price_disk::text")[0].get()
        product_price2_info = response.css("div.info a::text")[0].get()
        product_price3 = response.css("div.price span.price_disk::text")[1].get()
        product_price3_info = response.css("div.info a::text")[1].get()
        # Получаем валюту для стоимости
        product_price_currency = product_price2.split()[-1]

        # Получим ссылку на страницу товара
        product_url = response.url
        # Получим ссылку на фото товара
        product_photo_link = "https:" + response.css("table.product_photo_price img").attrib['src']

        # передаем полученные результаты парсинга в обьекты класа ParserShopItem
        yield ParserShopItem(
            name=product_name,
            url=product_url,
            photo_url=product_photo_link,
            # Для цены формируем небор вложенных словарей так как у нас может быть три варианта цен
            price={'currency': product_price_currency,
                   'price1': {'price': PleerRuSpider.get_price_from_string(product_price1),
                              'info': product_price1_info},
                   'price2': {'price': PleerRuSpider.get_price_from_string(product_price2),
                              'info': product_price2_info},
                   'price3': {'price': PleerRuSpider.get_price_from_string(product_price3),
                              'info': product_price3_info},
                   }
        )

    # Обьявляеи статический метод преобразования строк в стоимость и тип float
    @staticmethod
    def get_price_from_string(price_string):
        # Если строка с ценой отсутствует
        if price_string == '0':
            price_number = 0.0
        # в противном случае
        else:
            price_list = price_string.split()
            price_number = float(price_list[0] + price_list[1])
        return price_number
