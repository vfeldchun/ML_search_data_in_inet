# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
# Импортируем необходимые библиотеки

from itemadapter import ItemAdapter
from scrapy.pipelines.images import ImagesPipeline
from scrapy import Request
from pymongo import MongoClient


# Инициализируем клас записи информации о книге в локальную БД Mongo
class ParserBooksPipeline:
    def __init__(self):
        # Подключаемся к локальной БД
        client = MongoClient('mongodb://localhost:27017/')
        # Создаем/Подключаемся к БД books_db
        self.mongo_db = client.books_db

    def process_item(self, item, spider):
        # Создаем/Подключаемся к коллекции с именем паука (Labirint_ru)
        collection = self.mongo_db[spider.name]
        # Вставляем в коллекцию информацию о книге
        collection.insert_one(item)

        return item


# Клас обработки и загрузки фотографий обложки на локальный диск
class BooksPhotosPipeline(ImagesPipeline):
    # Функция получения фото обложки
    def get_media_requests(self, item, info):
        # Если ссылка на фото существует
        if item['photo'] != '-':
            photo_link = item['photo']
            try:
                # Загружаем фото
                yield Request(photo_link)
            except Exception as e:
                print(e)
        else:
            print("Нет обложки")

    # Функция обработки мета данных о загруженном фото
    def item_completed(self, results, item, info):
        # Если фото существует
        if item['photo'] != '-':
            # Передаем в поле 'фото' словарь с мета-информацией о скаченой фото
            item['photo'] = dict([itm[1] for itm in results if itm[0]][0])
        else:
            item['photo'] = 'Нет фото обложки'
        return item

    # Функция формирования пути записи скаченных фотографий обложек
    def file_path(self, request=None, response=None, info=None, *, item):
        # Формируем имя первого подкаталога как номер ISBN
        subdir_name1 = 'isbn_' + item['isbn'].replace('-', '_')
        # Формируем имя второго подкаталога как размер картинки
        subdir_name2 = item['photo'].split('/')[5]
        # Получаем оригинальное имя файла фотографии из ссылки
        file_name = item['photo'].split('/')[-1].split('?')[0]
        # Формируем и отправляем относительный путь записи файла картинки
        photo_path = subdir_name1 + '/' + subdir_name2 + '/' + file_name
        return photo_path

