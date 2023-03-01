# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter
from pymongo import MongoClient


class ParserShopPipeline:

    def __init__(self):
        # Подключаемся к локальной монго дб
        client = MongoClient('mongodb://localhost:27017/')
        # Создаем/Выбираем БД
        self.mongo_db = client.shop_products_db

    def process_item(self, item, spider):
        # Создаем/Выбираем коллекцию по имени текущего паука
        collection = self.mongo_db[spider.name]
        # Записываем полученные в pleer_ru.py атрибуты товара в  БД
        collection.insert_one(item)

        return item
