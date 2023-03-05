# Загружаем необходимые библиотеки
import scrapy
from parser_goods.items import ParserGoodsItem
from scrapy.loader import ItemLoader
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from time import sleep


class CastoramaSpider(scrapy.Spider):
    name = "castorama"
    allowed_domains = ["castorama.ru"]
    start_urls = ["https://www.castorama.ru/tools/power-tools/rotary-hammers/"]

    def parse(self, response):
        # Задаем опции для запуска драйвера chrome
        options = Options()
        options.add_argument("start-maximized")
        options.add_experimental_option('excludeSwitches', ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        # Скрытый режим работы браузера вместо start-maximized
        # options.add_argument("--headless")

        # Запускаем chrome
        driver = webdriver.Chrome(options=options)
        # Переходим на страницу castorama с перфораторами
        driver.get(self.start_urls[0])

        # Ждем пока появиться элемент с выбором местоположения
        try:
            element = WebDriverWait(driver, 10).until(
                ec.presence_of_element_located((By.CLASS_NAME, "md-content-wrapper"))
            )
        except Exception as e:
            print(e)

        # Находим кнопку закрытия окна выбора местоположения
        button_close = driver.find_elements(By.XPATH, "//button[contains(@class, 'shop-switcher-modal-close-bt')]")
        # Закрываем окно
        button_close[0].click()

        # Ждем пока отработает java скрипт обновления списка после закрытия окна
        sleep(3)

        # Подгрузка всех скрытых товаров
        is_next = True
        while is_next:
            try:
                # Если кнопка Показать еще найдена
                view_more = driver.find_element(By.XPATH, "//a[contains(@class, 'product-list-show-more__link')]")
                # Нажимаем на кнопку
                view_more.click()
            except:
                # Если не найдена выходим из цикла
                is_next = False

        # Получаем список перфораторов
        goods_list = driver.find_elements(By.XPATH, "//li[contains(@class, 'product-card')]")
        print(f'Количество продуктов на странице: {len(goods_list)}')

        # Если список пустой значит скорее всего нас заблокированли
        if not goods_list:
            print("Скорее всего доступ заблокирован из-за большого количества запросов!")
            exit()


        # Запускаем обработку каждого перфоратора методом parse_good
        for good in goods_list:
            yield from self.parse_good(good)

        # Закрываем chrome
        driver.close()

# Метод получает информацию о товаре
    def parse_good(self, good):
        # Инициализируем загрузчик классом элементов определенных в файле items.py
        loader = ItemLoader(item=ParserGoodsItem())

        # Отправляем на обработку наименование товара
        good_name = good.find_element(By.XPATH, ".//a[contains(@class, 'product-card__name')]").text
        loader.add_value('name', good_name)
        # Отправляем на обработку ссылку на товар
        good_link = good.find_element(By.XPATH, ".//a[@class='product-card__img-link']").get_attribute("href")
        loader.add_value('url', good_link)
        # Получаем список цен на товар
        good_price_list = good.find_elements(By.XPATH, ".//span[@class='price']")
        loader.add_value('price', good_price_list)
        # Получаем закодированную ссылку на фото товара
        good_photo_link = good.find_element(By.XPATH, ".//img[contains(@class, 'product-card__img')]"). \
            get_attribute("src")
        loader.add_value('photo', good_photo_link)
        yield loader.load_item()

