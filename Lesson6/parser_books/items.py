# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

# Загружаем необходимые библиотеки
import scrapy
from itemloaders.processors import MapCompose, Compose, TakeFirst


# Функция удаляет из названия книги автора если он есть
def clean_name(value):
    try:
        value = value[0].split(':')[1].strip()
    except:
        return value[0]
    return value


# Функция возвращает только номер ISBN
def clear_isbn(value):
    try:
        value = value[0].split(':')[1].strip()
    except:
        value = '-'
        return value
    return value


# Функция возвращает количество страниц книги или 0 если информации нет
def clear_pages(value):
    try:
        value = value[0].split()[1].strip()
        value_number = [int(value)]
    except:
        value_number = [0.0]
        return value_number
    return value_number


# Функция возвращает стоимость книги в виде числа или 0 если информации нет
def get_number_from_string(value):
    try:
        value_string = value[0]
        value_number = [float(value_string)]
    except:
        value_number = [0.0]
        return value_number
    return value_number


# Функция возвращает '-' если переданное значение пустое или None
def fill_empty(value):
    if not value:
        return ['-']
    return value


# Функция выполняет декодирование ссылки и возвращает корректную ссылку на фото обложки
def get_photo_links(value):
    if value[0] != '-':
        temp_list = value[0].replace("\\", "").replace('{', '').replace('}', '').split(',')[0]\
                            .replace('[', '').split(':')
        value = [temp_list[1].replace("\"", '') + ':' + temp_list[2].replace("\"", '')]
    return value


# Инициализация класса атрибутов собираемых о книге и методов их предобработки
class ParserBooksItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    name = scrapy.Field(input_processor=Compose(clean_name), output_processor=TakeFirst())
    photo = scrapy.Field(input_processor=Compose(get_photo_links), output_processor=TakeFirst())
    url = scrapy.Field(output_processor=TakeFirst())
    authors = scrapy.Field(input_processor=Compose(fill_empty), output_processor=TakeFirst())
    translators = scrapy.Field(input_processor=Compose(fill_empty), output_processor=TakeFirst())
    price = scrapy.Field(input_processor=Compose(get_number_from_string), output_processor=TakeFirst())
    discounted_price = scrapy.Field(input_processor=Compose(get_number_from_string), output_processor=TakeFirst())
    isbn = scrapy.Field(input_processor=Compose(clear_isbn), output_processor=TakeFirst())
    pages = scrapy.Field(input_processor=Compose(clear_pages), output_processor=TakeFirst())
    rate = scrapy.Field(input_processor=Compose(get_number_from_string), output_processor=TakeFirst())
    _id = scrapy.Field()


