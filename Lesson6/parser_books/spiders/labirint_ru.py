# Загружаем необходимые библиотеки
import scrapy
from scrapy.http import HtmlResponse
from items import ParserBooksItem
from scrapy.loader import ItemLoader


class LabirintRuSpider(scrapy.Spider):
    # Задаем имя паука и домен второго уровня сайта labirint.ru
    name = "labirint_ru"
    allowed_domains = ["labirint.ru"]

    # В методе init задаем стартовую страницу прасинга - все новинки
    def __init__(self, name=None, **kwargs):
        super().__init__(name, **kwargs)
        self.start_urls = ["https://www.labirint.ru/novelty/"]

    def parse(self, response: HtmlResponse):
        # Получаем адрес следующей страницы
        get_next_page = response.xpath("//div[@class='pagination-next']/a/@href").get()
        if get_next_page:
            # В случае наличия страницы выполняем ее запрос
            yield response.follow(get_next_page, callback=self.parse)

        # Получим список ссылок на новые книги
        books_links_list = response.xpath("//a[@class='cover']")
        # Если список пустой значит скорее всего нас заблокированли
        if not books_links_list:
            print("Скорее всего доступ заблокирован из-за большого количества запросов!")
            exit()

        # Запускаем обработку каждой ссылки на книгу методом parse_book
        for link in books_links_list:
            yield response.follow(link, callback=self.parse_book)

        print("\n############################\n%s\n##########################\n" % response.url)

    # Метод запрашивает страницу книги и получает информацию о книге
    def parse_book(self, response: HtmlResponse):

        # Инициализируем загрузчик классом элементов определенных в файле items.py
        loader = ItemLoader(item=ParserBooksItem(), response=response)

        # Отправляем на обработку наименование книги
        loader.add_xpath('name', "//h1/text()")
        # Отправляем на обработку ссылку на книгу
        loader.add_value('url', response.url)
        # Получаем закодированную ссылку на фото обложки
        photo_links = response.xpath("//div[@id='product-thumbnails']/div[@id='product-screenshot']/@data-source").get()
        # Если ссылки нет то это значит что обложки нет
        if photo_links is None:
            photo_links = ['-']
        # Отправляем на обработку ссылку или '-'
        loader.add_value('photo', photo_links)
        # Отправляем на обработку ФИО автора книги
        loader.add_xpath('authors', "//a[@data-event-label='author']/text()")
        # Отправляем на обработку переводчика книги
        loader.add_xpath('translators', "//a[@data-event-label='translator']/text()")
        # Если специальной цены со скидкой нет
        if response.xpath("//span[@class='buying-price-val-number']/text()"):
            # отправляем на обработку только стандартную цену
            loader.add_xpath('price', "//span[@class='buying-price-val-number']/text()")
            loader.add_value('discounted_price', '0')
        else:
            # Отправляем на обработку и специальную и стандартную цену
            loader.add_xpath('price', "//span[@class='buying-priceold-val-number']/text()")
            loader.add_xpath('discounted_price', "//span[@class='buying-pricenew-val-number']/text()")
        # Отправляем на обработку код ISBN книги
        loader.add_xpath('isbn', "//div[@class='isbn']/text()")
        # Отправляем на обработку количество страниц книги
        loader.add_xpath('pages', "//div[@class='pages2']/text()")
        # Отправляем на обработку рейтинг книги
        loader.add_xpath('rate', "//div[@id='rate']/text()")
        yield loader.load_item()


