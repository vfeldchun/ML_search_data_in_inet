# Загружаем необходимые библиотеки
import requests
from lxml import html
from datetime import date, datetime
import json
import time
import logging
from logging.handlers import RotatingFileHandler
import pymongo


######################################################################################################
# Блок настройки логирования
######################################################################################################

# Создайте обработчик для записи данных в файл
handler = RotatingFileHandler(filename='Logs/news_parser.log', maxBytes=100000, backupCount=10, encoding='UTF-8')

# Создайте Logger
logger = logging.getLogger(__name__)
# Определяем уровень логирования
logger.setLevel(logging.INFO)

# Создайте Formatter для форматирования сообщений в логе
logger_formatter = logging.Formatter('%(name)s - %(levelname)s - %(message)s')
# Добавьте Formatter в обработчик
handler.setFormatter(logger_formatter)

# Добавляем обработчик в Logger
logger.addHandler(handler)


######################################################################################################
# Блок объявления некоторых глобальных констант и переменных
######################################################################################################

# Получим текущую дату и преобразуем ее в строку
CURRENT_DATE = str(date.today())

# Создаем временный словарь который будет содержать данные для одной новости
tmp_news_dict = {
    'news_headline': '',
    'news_date': '',
    'news_link': '',
    'news_source': ''
}


#######################################################################################################
# Блок объявления функций
#######################################################################################################


def get_request_dom(url, request_method):
    # Функция выполняет запрос по полученному url и возвращает ответ преобразованный в HTML
    # Определим заголовок для выполнения запроса
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                      'Chrome/109.0.0.0 Safari/537.36 '
    }

    response = None

    if request_method == 'get':
        # Выполним запрос по переданному url
        response = requests.get(url=url, headers=headers)

    elif request_method == 'post':
        # Выполним запрос по переданному url
        response = requests.post(url=url, headers=headers)
        # вернем преобразование полученного ответа из текста в html

    if response.ok:
        # выполним преобразование полученного ответа из текста в html
        dom = html.fromstring(response.text)
        # Если вернулся код 429 то
        if str(dom) == '429':
            # логируем время и код ошибки
            dt = date.strftime('[%Y-%b-%d %H:%M:%S]')
            logger.warning(f"{dt} URL: {response.url}  вернул ошибку: {dom} слишком много запросов от пользователя")
            return str(dom)
        # В противном случае возвращаем
        else:
            # вернем преобразование полученного ответа из текста в html
            return dom
    else:
        # Возвращаем код ошибки
        dt = date.strftime('[%Y-%b-%d %H:%M:%S]')
        logger.warning(f"{dt} Запрос url {request_method.url} вернул ошибку: {response.status_code}")
        return response.status_code


def get_final_list_of_news(news_headlines, news_links,
                           news_dates, news_sources,
                           is_single_date=False):

    # Создаем пустой список который будет содержать данные по всем новостям найденным на новостном сайте
    news_data_list = []

    # Наполним список данными
    for i in range(len(news_headlines)):
        # Вносим заголовок новости
        tmp_news_dict['news_headline'] = news_headlines[i]

        if is_single_date:
            # Вносим одинаковую дату для всех новостей
            tmp_news_dict['news_date'] = news_dates
        else:
            # Вносим дату новости
            tmp_news_dict['news_date'] = news_dates[i]

        # Вносим ссылку на новость
        tmp_news_dict['news_link'] = news_links[i]

        # Вносим источник новости
        tmp_news_dict['news_source'] = news_sources[i]

        # Добавляем словарь в список
        news_data_list.append(tmp_news_dict.copy())

    # Возвращаем готовый список словарей новостей
    return news_data_list.copy()

def save_json_to_file(prefix_of_name, news_list_of_dict):
    # Сформируем имя файла
    file_name = prefix_of_name + CURRENT_DATE + '.json'

    # Сохраним полученный список новостей в json формате
    with open(file_name, 'a') as outfile:
        json.dump(news_list_of_dict, outfile)


def get_lenta_news(url, xpath_headlines, xpath_links, xpath_dates, xpath_sources):

    # Отправляем запрос на url и получаем ответ на запрос в формате HTML
    lenta_dom = get_request_dom(url, request_method='get')

    # Обработка ошибок исполнения запроса
    if type(lenta_dom) != html.HtmlElement:
        return []

    # Обработка заголовков новостей lenta.ru
    #############################################################################################
    # найдем и сохраним список заголовков новостей
    lenta_headlines_list = lenta_dom.xpath(xpath_headlines)

    # Обработка ссылок на новости lenta.ru
    ##############################################################################################
    # Получим и сохраним список ссылок на новости с сайта lenta.ru
    lenta_links_list = lenta_dom.xpath(xpath_links)

    # Так как для большинства новостей в таге href содержится только относительный путь к новости
    # зададим начальную часть url
    lenta_main_link_part = 'https://lenta.ru'

    # В списке ссылок встречаются два типа ссылок:
    #   1. Относительная ссылка на новость, размещенную на сайте lenta.ru
    #   2. Полный url в случае если новость размещена на другом сайте. Видимо это дочерний сайт lenta.ru - moslenta.ru
    # Преобразуем все относительные ссылки в полный url для первого типа ссылок
    for i in range(len(lenta_links_list)):
        if lenta_links_list[i].find('https') < 0:
            lenta_links_list[i] = lenta_main_link_part + lenta_links_list[i]

    # Обработка дат новостей lenta.ru
    ##############################################################################################
    # Получим список времени для каждой новости
    # На сайте lenta.ru указывается только время новости, а не дата
    lenta_dates_list = lenta_dom.xpath(xpath_dates)

    # Преобразуем список полученных объектов dom в список времени
    # и выполним преобразование для каждого элемента списка в строковое представление в формате 'дата время'
    for i in range(len(lenta_dates_list)):
        lenta_dates_list[i] = CURRENT_DATE + ' ' + lenta_dates_list[i].text_content()

    # Обработка источников новостей lenta.ru
    #############################################################################################
    # Для определения источника новости lenta.ru необходимо перейти по ссылке в саму новость
    # и найти в тексте источник, который классифицируется классом - source
    # ссылки на новость возьмем из списка lenta_links_list

    # Создадим список источников новостей
    lenta_sources_list = []

    for i in range(len(lenta_links_list)):
        # Для новостей дочернего сайта moslenta.ru будем считать источником данный сайт
        # поэтому обрабатываем ссылки только для сайта lenta.ru
        if lenta_links_list[i].find('/lenta.ru') >= 0:
            # Получаем содержание новости в формате HTML
            lenta_news_dom = get_request_dom(url=lenta_links_list[i], request_method='get')

            # Обработка ошибок исполнения запроса
            if type(lenta_news_dom) != html.HtmlElement:
                return []

            # найдем источник новости
            lenta_news_src = lenta_news_dom.xpath(xpath_sources)

            # Если источник есть
            if len(lenta_news_src) > 0:
                # Добавим источник в список
                lenta_sources_list.append(lenta_news_src[0].text_content())
            # В противном случае
            else:
                # Добавляем в источник lenta.ru
                lenta_sources_list.append('lenta.ru')
        else:
            # найдем наименование сайта источника
            t_src = (lenta_links_list[i].split('/'))[2]
            # и добавим в список
            lenta_sources_list.append(t_src)

        # Во избежание получения 429 ошибки введем задержку в 2 секунды
        time.sleep(2)

    # Формируем список словарей новостей lenta.ru
    ##########################################################################################
    # Вызываем функцию формирования списка словарей новостей
    lenta_list_of_dict = get_final_list_of_news(lenta_headlines_list,
                                                lenta_links_list,
                                                lenta_dates_list,
                                                lenta_sources_list)

    # Если полученный список словарей не пустой возвращаем список словарей
    if len(lenta_list_of_dict) > 0:
        return lenta_list_of_dict
    # В противном случае возвращаем No News
    else:
        return list('No News')


def get_mail_news(url, xpath_headlines, xpath_links, xpath_dates, xpath_sources):

    # Отправляем запрос на url и получаем ответ на запрос в формате HTML
    mail_dom = get_request_dom(url, request_method='get')

    # Обработка ошибок исполнения запроса
    if type(mail_dom) != html.HtmlElement:
        return []

    # Обработка заголовков новостей mail.ru
    #############################################################################################

    # найдем и сохраним список заголовков новостей с заголовками на картинках
    mail_headlines_list_pic = mail_dom.xpath(xpath_headlines[0])
    # найдем и сохраним список заголовков новостей без картинок
    mail_headlines_list_no_pic = mail_dom.xpath(xpath_headlines[1])

    # Преобразуем список объектов dom в список заголовков для заголовков с картинками
    for i in range(len(mail_headlines_list_pic)):
        # заодно удалим служебные символы из заголовков
        mail_headlines_list_pic[i] = (mail_headlines_list_pic[i].text_content()).replace('\xa0', ' ')

    # Преобразуем список объектов dom в список заголовков для заголовков без картинок
    for i in range(len(mail_headlines_list_no_pic)):
        # заодно удалим служебные символы из заголовков
        mail_headlines_list_no_pic[i] = (mail_headlines_list_no_pic[i].text_content()).replace('\xa0', ' ')

    # Объединим списки заголовков в один
    mail_headlines_list = mail_headlines_list_pic + mail_headlines_list_no_pic

    # Обработка ссылок на новости mail.ru
    ##############################################################################################
    # найдем и сохраним список ссылок на новости с заголовками на картинках
    mail_links_list_pic = mail_dom.xpath(xpath_links[0])
    # найдем и сохраним список заголовков новостей без картинок
    mail_links_list_no_pic = mail_dom.xpath(xpath_links[1])

    # Объединим списки ссылок в один
    mail_links_list = mail_links_list_pic + mail_links_list_no_pic

    # Обработка дат новостей mail.ru
    ##############################################################################################
    # Для обработки дат новостей сайта mail.ru необходимо зайти по ссылки на каждую новость
    # после чего найти дату новости

    # Обработаем даты для новостей.
    # Создадим список дат новостей
    mail_dates_list = []

    for i in range(len(mail_links_list)):
        # Выполним запрос новости mail.ru и получим ответ в формате HTML
        mail_one_news_dom = get_request_dom(url=mail_links_list[i], request_method='get')

        # Обработка ошибок исполнения запроса
        if type(mail_one_news_dom) != html.HtmlElement:
            return []

        # Найдем дату новости
        mail_one_date = mail_one_news_dom.xpath(xpath_dates)

        # Если дату удалось найти
        if len(mail_one_date) > 0:
            # Преобразуем дату к более читаемому формату
            t_date = mail_one_date[0].split('T')
            t_time = t_date[1].split(':')
            mail_one_date = t_date[0] + ' ' + t_time[0] + ':' + t_time[1]
        # В противном случае
        else:
            # запишем пустую строку что будет означать что дата не найдена
            mail_one_date = ''

        # Запишем дату в список дат новостей
        mail_dates_list.append(mail_one_date)
        # Так как mail.ru защищаясь от DDOS атак ограничивает количество запросов к сайту,
        # и возвращает ошибку 429 то перед каждым запросом введем задержку в 2 секунды
        time.sleep(2)

    # Обработка источников новостей mail.ru
    #############################################################################################
    # Для обработки источников новостей сайта mail.ru необходимо зайти по ссылки на каждую новость
    # после чего найти источник новости

    # Обработаем источники новостей.
    # Создадим список источников новостей
    mail_sources_list = []

    for i in range(len(mail_links_list)):
        # Выполним запрос новости mail.ru и получаем ответ в формате HTML
        mail_one_src_dom = get_request_dom(url=mail_links_list[i], request_method='get')

        # Обработка ошибок исполнения запроса
        if type(mail_one_src_dom) != html.HtmlElement:
            return []

        # Найдем источник новости
        mail_one_src = mail_one_src_dom.xpath(xpath_sources)

        # Если источник найден
        if len(mail_one_src) > 0:
            # Запишем источник в список
            mail_sources_list.append(mail_one_src[0].text_content())
        # В противном случае
        else:
            # Запишем как источник mail.ru
            mail_sources_list.append('mail.ru')

        # Так как mail.ru защищаясь от DDOS атак ограничивает количество запросов к сайту,
        # и возвращает ошибку 429 то перед каждым запросом введем задержку в 2 секунды
        time.sleep(2)

    # Формируем список словарей новостей mail.ru
    ##########################################################################################
    # Вызываем функцию формирования списка словарей новостей
    mail_list_of_dict = get_final_list_of_news(mail_headlines_list,
                                               mail_links_list,
                                               mail_dates_list,
                                               mail_sources_list)

    # Если полученный список словарей не пустой возвращаем список словарей
    if len(mail_list_of_dict) > 0:
        return mail_list_of_dict
    # В противном случае возвращаем No News
    else:
        return list('No News')


def get_dzen_news(url, xpath_headlines, xpath_links, xpath_sources):

    # Выполним запрос к сайту dzen.ru
    # Для dzen, как и в целом для сайтов яндекса нужно вызывать метод post a не get.
    # Отправляем запрос на url и получаем ответ на запрос в формате HTML
    dzen_dom = get_request_dom(url, request_method='post')

    # Обработка ошибок исполнения запроса
    if type(dzen_dom) != html.HtmlElement:
        return []

    # Обработка заголовков новостей dzen.ru
    #############################################################################################
    # найдем и сохраним список заголовков новостей на dzen
    dzen_headlines_list = dzen_dom.xpath(xpath_headlines)

    # Преобразуем список объектов dom в список заголовков
    for i in range(len(dzen_headlines_list)):
        # заодно удалим служебные символы из заголовков и обрежем пробелы в конце строк
        dzen_headlines_list[i] = (dzen_headlines_list[i].text_content()).replace('\xa0', ' ').strip()

    # Обработка ссылок на новости dzen.ru
    ##############################################################################################

    # найдем и сохраним список ссылок на новости
    dzen_links_list = dzen_dom.xpath(xpath_links)

    # Обработка дат новостей dzen.ru
    ##############################################################################################
    # Я не нашел даты для новостей так как dzen их не указывает поэтому принимаем за дату новости дату парсинга.

    # Обработаем даты для новостей.
    # Сформируем дату парсинга новостей которой и заполним финальный список словарей
    dzen_news_date = CURRENT_DATE + ' 12:00'

    # Обработка источников новостей dzen.ru
    #############################################################################################
    # Для обработки источников новостей сайта dzen.ru необходимо зайти по ссылки на каждую новость
    # после чего найти источник новости

    # Обработаем источники новостей

    # Создадим список источников новостей
    dzen_sources_list = []

    for i in range(len(dzen_links_list)):
        # Выполним запрос новости dzen.ru и получим ответ в формате HTML
        dzen_one_src_dom = get_request_dom(url=dzen_links_list[i], request_method='post')

        # Обработка ошибок исполнения запроса
        if type(dzen_one_src_dom) != html.HtmlElement:
            return []

        # Найдем источник новости
        dzen_one_src = dzen_one_src_dom.xpath(xpath_sources)

        # Если источник найден то
        if len(dzen_one_src) > 0:
            # Запишем источник в список
            dzen_sources_list.append(dzen_one_src[0].text_content())
        # В противном случае
        else:
            # Указываем как источник dzen
            dzen_sources_list.append('dzen.ru')

        # Во избежание получения 429 ошибки введем задержку в 2 секунды
        time.sleep(2)

    # Формируем список словарей новостей dzen.ru
    ##########################################################################################
    # Вызываем функцию формирования списка словарей новостей
    dzen_list_of_dict = get_final_list_of_news(dzen_headlines_list,
                                               dzen_links_list,
                                               dzen_news_date,
                                               dzen_sources_list,
                                               is_single_date=True)

    # Если полученный список словарей не пустой возвращаем список словарей
    if len(dzen_list_of_dict) > 0:
        return dzen_list_of_dict
    # В противном случае возвращаем No News
    else:
        return list('No News')

############################################################################################################
# Основное тело программы
############################################################################################################


if __name__ == '__main__':

    # Записываем в лог время начала работы парсера
    start_datetime = CURRENT_DATE + ' ' + str((datetime.now()).hour) + ':' + str((datetime.now()).minute)
    logger.info(f"Парсер новостей начал работу: {start_datetime}")

    # Создадим список url новостных сайтов
    news_sites_urls_dict = {
        'lenta': 'https://lenta.ru/parts/news/',
        'mail': 'https://news.mail.ru/',
        'dzen': 'https://dzen.ru/'
    }

############################################################################################################
    # Создадим словари путей xpath
############################################################################################################

    # идентификатор пути xpath с заголовком новости
    xpath_news_headlines_dict = {
        'lenta': "//div/ul/li/a/h3[@class='card-full-news__title']/text()",
        # На сайте mail.ru есть два типа заголовков новостей:
        #   1. Заголовок размещенный на картинке
        #   2. Заголовок без картинки
        # Поэтому для сайта mail.ru будет два xpath
        'mail': ["//div/span/span[@class='photo__captions']/span[contains(@class, 'photo__title')]",
                 "//div/ul/li[@class='list__item']/span/a"],
        'dzen': "//div/ul/li/a/div/span"
    }

    # индентификаторы пути xpath к источнику новости
    xpath_news_source_dict = {
        # Для получения источника на сайте Лента.ру нужно перейти по ссылке на саму новость и потом по пути xpath ниже
        # найти источник. К сожалению встречаются новости в которых несмотря на наличие внешнего источника
        # вытащить данные об источнике крайне сложно так как крайне редко, но клас source не используется
        'lenta': "//div/p/a[@class='source']",
        # источник новости на mail можно найти только после открытия самой страницы новости по следующему xpath
        'mail': "//div[contains(@class, 'breadcrumbs')]/span/span/a/span",
        'dzen': "//div[@class='news-story__head']/a/span[@class='news-story__subtitle-text']"
    }

    # идентификатор пути xpath к ссылке на новость
    xpath_news_links_dict = {
        'lenta': "//div/ul/li[@class='parts-page__item']/a[@class='card-full-news _parts-news']/@href",
        # На сайте mail.ru есть два типа ссылок на новости:
        # 1. Ссылки размещенные на картинке
        # 2. Ссылки без картинки
        # Поэтому для сайта mail.ru будет два xpath
        'mail': ["//div/span/a[@class='photo__inner link-holder' and contains(@href, 'https://')]/@href",
                 "//div/ul/li[@class='list__item']/span/a/@href"],
        'dzen': "//div/ul/li/a/@href"
    }

    # идентификатор пути xpath к дате новости
    xpath_news_date_dict = {
        'lenta': "//div/ul/li/a/div/time[@class='card-full-news__info-item card-full-news__date']",
        # дату новости на mail можно найти только после открытия самой страницы новости по следующему xpath
        'mail': "//div[contains(@class, 'breadcrumbs')]/span/span/span/@datetime",
        # В дзен нет дат новостей поэтому заполним текущей датой
        'dzen': ""
    }

#########################################################################################################
    # Создадим БД и коллекции в MangoDB
#########################################################################################################

    # Подключимся к локальной MangoDB
    my_mdb_client = pymongo.MongoClient("mongodb://localhost:27017/")
    # Создадим или откроем БД newsdb
    my_news_db = my_mdb_client["newsdb"]

    # Создадим коллекцию для новостей lenta.ru
    mycol_lenta = my_news_db["lenta"]

    # Создадим коллекцию для новостей mail.ru
    mycol_mail = my_news_db["mail"]

    # Создадим коллекцию для новостей dzen.ru
    mycol_dzen = my_news_db["dzen"]

#########################################################################################################
    # Обработка новостей с сайта lenta.ru
#########################################################################################################

    # Измерим время обработки новостей
    # точка отсчета времени
    start = time.time()

    # Инициализируем список новостей
    lenta_news_list_of_dict = []

    # зададим признак ошибки обработки
    lenta_err = False

    try:
        # Вызываем функцию обработки новостей для сайта lenta.ru
        lenta_news_list_of_dict = get_lenta_news(news_sites_urls_dict['lenta'],
                                                 xpath_news_headlines_dict['lenta'],
                                                 xpath_news_links_dict['lenta'],
                                                 xpath_news_date_dict['lenta'],
                                                 xpath_news_source_dict['lenta'])
    except Exception as e:
        # логируем время и ошибку
        dt = date.strftime('[%Y-%b-%d %H:%M:%S]')
        err_msg = f'При обработке новостей на lenta.ru произошла ошибка: {e}'
        logger.error(f"{dt} {err_msg}")
        lenta_err = True

    if not lenta_err:
        # Сохраним полученный список новостей в json формате в файл
        save_json_to_file('jsons/lenta_news_', lenta_news_list_of_dict)

        logger.info(f'Количество найденных статей на lenta.ru: {len(lenta_news_list_of_dict)}')

        # Запишем в базу MangoDB newsdb словари с новостями lenta
        # Что бы избежать дубликатов новостей запись в базу.
        # Проверим что в БД нет таких новостей

        # Выгрузим из БД только заголовки
        lenta_db_news_list = list(mycol_lenta.find({'news_headline': {'$exists': True}}, {'_id': False}))

        # Создадим пустой список новостей для вставки в БД
        lenta_diff_list_to_insertion = []

        # Для каждого словаря из полученного после парсинга списка
        for item in lenta_news_list_of_dict:
            # Проверим есть ли новость в БД
            if item not in lenta_db_news_list:
                # Если есть добавим словарь в список для вcтавки
                lenta_diff_list_to_insertion.append(item)

        # Внесем полученный список новостей в БД
        x = mycol_lenta.insert_many(lenta_diff_list_to_insertion)
        news_count = len(lenta_diff_list_to_insertion)

        logger.info(f'Запись {news_count} новостей в базу данных newsdb коллекция lenta завершено!')

#########################################################################################################
    # Обработка новостей с сайта mail.ru
#########################################################################################################

    # Инициализируем список новостей
    mail_news_list_of_dict = []

    # зададим признак ошибки обработки
    mail_err = False

    try:
        # Вызываем функцию обработки новостей для сайта mail.ru
        mail_news_list_of_dict = get_mail_news(news_sites_urls_dict['mail'],
                                               xpath_news_headlines_dict['mail'],
                                               xpath_news_links_dict['mail'],
                                               xpath_news_date_dict['mail'],
                                               xpath_news_source_dict['mail'])
    except Exception as e:
        # логируем время и ошибку
        dt = date.strftime('[%Y-%b-%d %H:%M:%S]')
        err_msg = f'При обработке новостей на mail.ru произошла ошибка: {e}'
        logger.error(f"{dt} {err_msg}")
        mail_err = True

    if not mail_err:
        # Сохраним полученный список новостей в json формате в файл
        save_json_to_file('jsons/mail_news_', mail_news_list_of_dict)

        logger.info(f'Количество найденных статей на mail.ru: {len(mail_news_list_of_dict)}')

        # Запишем в базу MangoDB newsdb словари с новостями mail
        # Что бы избежать дубликатов новостей запись в базу.
        # Проверим что в БД нет таких новостей

        # Выгрузим из БД только заголовки
        mail_db_news_list = list(mycol_mail.find({'news_headline': {'$exists': True}}, {'_id': False}))

        # Создадим пустой список новостей для вставки в БД
        mail_diff_list_to_insertion = []

        # Для каждого словаря из полученного после парсинга списка
        for item in mail_news_list_of_dict:
            # Проверим есть ли новость в БД
            if item not in mail_db_news_list:
                # Если есть добавим словарь в список для вcтавки
                mail_diff_list_to_insertion.append(item)

        # Внесем полученный список новостей в БД
        x = mycol_mail.insert_many(mail_diff_list_to_insertion)
        news_count = len(mail_diff_list_to_insertion)

        logger.info(f'Запись {news_count} новостей в базу данных newsdb коллекция mail завершено!')

#########################################################################################################
    # Обработка новостей с сайта dzen.ru
#########################################################################################################

    # Инициализируем список новостей
    dzen_news_list_of_dict = []

    # зададим признак ошибки обработки
    dzen_err = False

    try:
        # Вызываем функцию обработки новостей для сайта mail.ru
        dzen_news_list_of_dict = get_dzen_news(news_sites_urls_dict['dzen'],
                                               xpath_news_headlines_dict['dzen'],
                                               xpath_news_links_dict['dzen'],
                                               xpath_news_source_dict['dzen'])
    except Exception as e:
        # логируем время и ошибку
        dt = date.strftime('[%Y-%b-%d %H:%M:%S]')
        err_msg = f'При обработке новостей на dzen.ru произошла ошибка: {e}'
        logger.error(f"{dt} {err_msg}")
        dzen_err = True

    if not dzen_err:
        # Сохраним полученный список новостей в json формате в файл
        save_json_to_file('jsons/dzen_news_', dzen_news_list_of_dict)

        logger.info(f'Количество найденных статей на dzen.ru: {len(dzen_news_list_of_dict)}')

        # Запишем в базу MangoDB newsdb словари с новостями dzen
        # Что бы избежать дубликатов новостей запись в базу.
        # Проверим что в БД нет таких новостей

        # Выгрузим из БД только заголовки
        dzen_db_news_list = list(mycol_dzen.find({'news_headline': {'$exists': True}}, {'_id': False}))

        # Создадим пустой список новостей для вставки в БД
        dzen_diff_list_to_insertion = []

        # Для каждого словаря из полученного после парсинга списка
        for item in dzen_news_list_of_dict:
            # Проверим есть ли новость в БД
            if item not in dzen_db_news_list:
                # Если есть добавим словарь в список для вcтавки
                dzen_diff_list_to_insertion.append(item)

        # Внесем полученный список новостей в БД
        x = mycol_dzen.insert_many(dzen_diff_list_to_insertion)
        news_count = len(dzen_diff_list_to_insertion)

        logger.info(f'Запись {news_count} новостей в базу данных newsdb коллекция dzen завершено!')

    # время обработки новостей
    end = round((time.time() - start) / 60, 2)
    logger.info(f'Время обработки новостей: {end} минут!')

    # Записываем в лог время завершения работы парсера
    stop_datetime = str(date.today()) + ' ' + str((datetime.now()).hour) + ':' + str((datetime.now()).minute)
    logger.info(f"Парсер новостей закончил работу: {stop_datetime}")
