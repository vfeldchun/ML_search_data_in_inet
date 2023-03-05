# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy
from itemloaders.processors import MapCompose, Compose, TakeFirst


# Функция обработки списка цен и преобразования цен в float
def get_price_dict(value):
    # Если есть и текущая и старая цена
    if len(value) > 1:
        good_current_price = float(value[0].text.split()[0] + value[0].text.split()[1])
        good_old_price = float(value[1].text.split()[0] + value[1].text.split()[1])
    # Если есть только текущая цена
    else:
        good_current_price = float(value[0].text.split()[0] + value[0].text.split()[1])
        good_old_price = '0.0'

    price_dict = {'current': good_current_price,
                  'old': good_old_price}

    return [price_dict]


# Инициализация класса атрибутов собираемых о товаре и методов их предобработки
class ParserGoodsItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    name = scrapy.Field(output_processor=TakeFirst())
    photo = scrapy.Field(output_processor=TakeFirst())
    url = scrapy.Field(output_processor=TakeFirst())
    price = scrapy.Field(input_processor=Compose(get_price_dict), output_processor=TakeFirst())
    _id = scrapy.Field()
