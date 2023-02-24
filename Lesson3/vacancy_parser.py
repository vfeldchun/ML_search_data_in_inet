# Импортируем необходимые библиотеки
import requests
import pprint
from time import sleep
from copy import deepcopy
from bs4 import BeautifulSoup as bs
from fake_useragent import UserAgent
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
handler = RotatingFileHandler(filename='Logs/vacanсy_parser.log', maxBytes=100000, backupCount=10, encoding='UTF-8')

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

# Зададим переменную поиска
KEY_SEARCH_STRING = 'Python'

# Зададим типовую структуру вакансии для наполнения списка вакансий
tmp_vacancy_dict = {
    # Наименование вакансии
    'vacancy': '',
    # Зарплата включая минимум, максимум и валюту
    'salary': {'min_salary': 0., 'max_salary': 0., 'currency': ''},
    # Ссылка на описание вакансии
    'vacancy_link': '',
    # источник вакансии
    'vacancy_source': 'hh.ru',
    # Наименование работодателя
    'name_of_employer': '',
    # Место работы (город или удаленка)
    'city_of_work': '',
    # условия работы - полный день, удаленка
    'type_of_work': ''
}

#######################################################################################################
# Блок объявления функций
#######################################################################################################


# Функция выделения цифр зарплаты из строки
def get_digit_from_string(source_string):
    str_to_list = source_string.split()
    idx_numeric_list = []
    number_string = ''

    for i in range(len(str_to_list)):
        if str_to_list[i].isdigit():
            idx_numeric_list.append(i)

    for idx in idx_numeric_list:
        number_string += str_to_list[idx]

    return float(number_string)


# Функция определения валюты в строке и ее возврат
def get_currency(currency_string):
    if currency_string.lower().find('руб') >= 0:
        return 'Руб.'
    elif currency_string.find('₽') >= 0:
        return 'Руб.'
    elif currency_string.find('$') >= 0:
        return 'USD'

    return ''


# Функция выделения из строки значений зарплаты и волюты и возврата словаря из этих данных
def get_salary_dict(salary_string):
    if salary_string.lower().startswith('по'):
        return {'min_salary': 0.0,
                'max_salary': 0.0,
                'currency': ''}.copy()
    elif salary_string.lower().startswith('от'):
        return {'min_salary': get_digit_from_string(salary_string),
                'max_salary': 0.0,
                'currency': get_currency(salary_string)}.copy()
    elif salary_string.lower().startswith('до'):
        return {'min_salary': 0.0,
                'max_salary': get_digit_from_string(salary_string),
                'currency': get_currency(salary_string)}
    else:
        if salary_string.find('—') != -1:
            two_numbers_string_list = salary_string.split('—')
            return {'min_salary': get_digit_from_string(two_numbers_string_list[0]),
                    'max_salary': get_digit_from_string(two_numbers_string_list[1]),
                    'currency': get_currency(salary_string)}
        else:
            return {'min_salary': 0.0,
                    'max_salary': get_digit_from_string(salary_string),
                    'currency': get_currency(salary_string)}


def get_request_bs(url, params):
    # Функция выполняет запрос по полученному url и возвращает ответ преобразованный в HTML
    # Определим заголовок для выполнения запроса
    # Определим заголовок для выполнения запроса к сайтам
    user_agent = UserAgent()
    headers = {'User-Agent': user_agent.chrome}

    response = None

    # Выполним запрос по переданному url
    response = requests.get(url=url, headers=headers, params=params)

    if response.ok:
        # выполним преобразование полученного ответа из текста в html
        response_bs = bs(response.text, 'html.parser')
        # Если вернулся код 429 то
        if str(response_bs) == '429':
            # логируем время и код ошибки
            dt = datetime.now().strftime('[%Y-%b-%d %H:%M:%S]')
            logger.warning(f"{dt} URL: {response.url}  вернул ошибку: {response_bs} слишком "
                           f"много запросов от пользователя")
            return list(str(response_bs))
        # В противном случае возвращаем
        else:
            # вернем преобразование полученного ответа из текста в html
            return response_bs
    else:
        # Возвращаем код ошибки
        dt = datetime.now().strftime('[%Y-%b-%d %H:%M:%S]')
        logger.warning(f"{dt} Запрос url {response.url} вернул ошибку: {response.status_code}")
        return list(str(response.status_code))


def get_headhunter_vacancies(headhunter_url, headhunter_request_params, npages):
    # С данного сайта получить данные вакансий можно через api в json формате
    # Инициализируем список словарей для хранения вакансий
    headhunter_vacancy_list = []

    # Организуем цикл сбора информации
    for i in range(npages):
        # Чтобы избежать ошибки о превышении количества запросов
        sleep(2)

        # Заносим в параметры запроса номер страницы
        headhunter_request_params['page'] = str(i)

        # Выполним запрос к сайту, ответ преобразуем в json а затем в список
        headhunter_respond = requests.get(url=headhunter_url, params=headhunter_request_params)
        headhunter_respond_json_list = (headhunter_respond.json())['items']

        if headhunter_respond.ok:
            # Для каждой вакансии
            for one_vacancy in headhunter_respond_json_list:
                # Заполняем словарь вакансии
                tmp_vacancy_dict['vacancy'] = one_vacancy['name']

                if one_vacancy['salary'] is None:
                    tmp_vacancy_dict['salary']['min_salary'] = 0.0
                    tmp_vacancy_dict['salary']['max_salary'] = 0.0
                    tmp_vacancy_dict['salary']['currency'] = ''
                else:
                    if one_vacancy['salary']['from'] is None:
                        tmp_vacancy_dict['salary']['min_salary'] = 0.0
                    else:
                        tmp_vacancy_dict['salary']['min_salary'] = float(one_vacancy['salary']['from'])

                    if one_vacancy['salary']['to'] is None:
                        tmp_vacancy_dict['salary']['max_salary'] = 0.0
                    else:
                        tmp_vacancy_dict['salary']['max_salary'] = float(one_vacancy['salary']['to'])

                    tmp_vacancy_dict['salary']['currency'] = one_vacancy['salary']['currency']

                tmp_vacancy_dict['vacancy_link'] = one_vacancy['alternate_url']
                tmp_vacancy_dict['name_of_employer'] = one_vacancy['employer']['name']
                tmp_vacancy_dict['city_of_work'] = one_vacancy['area']['name']
                tmp_vacancy_dict['type_of_work'] = one_vacancy['schedule']['name']

                # Добавляем вакансю в список вакансий
                headhunter_vacancy_list.append(deepcopy(tmp_vacancy_dict))
        else:
            break

    return headhunter_vacancy_list


def save_json_to_file(prefix_of_name, news_list_of_dict):
    # Сформируем имя файла
    file_name = prefix_of_name + CURRENT_DATE + '.json'

    # Сохраним полученный список новостей в json формате
    with open(file_name, 'a') as outfile:
        json.dump(news_list_of_dict, outfile)


def get_superjob_vacancies(superjob_url, superjob_request_params, npages):

    # Инициализируем список словарей для хранения вакансий
    superjob_vacancy_list = []
    tmp_vacancy_dict['vacancy_source'] = 'superjob.ru'

    # Организуем цикл сбора информации
    for i in range(1, npages):
        # Чтобы избежать ошибки о превышении количества запросов
        sleep(2)

        # Заносим в параметры запроса номер страницы
        superjob_request_params['page'] = str(i)

        # Выполним запрос к сайту, ответ преобразуем в html а затем в список
        superjob_respond_bs = get_request_bs(url=superjob_url, params=superjob_request_params)

        if len(superjob_respond_bs) > 1:
            # Соберем в один список результаты полиска вакансий
            tag_div_vacancy_list = superjob_respond_bs.select('div._1bobf.f-test-vacancy-item')

            for tag_vacancy in tag_div_vacancy_list:
                # Теперь определим нужные блоки формы вакансии
                superjob_one_vacancy = tag_vacancy.select('span a')

                # Получим наименование вакансии
                tmp_vacancy_dict['vacancy'] = superjob_one_vacancy[0].text
                # Получим ссылку на вакансию
                tmp_vacancy_dict['vacancy_link'] = 'https://www.superjob.ru' + superjob_one_vacancy[0]['href']

                # Получим работодателя
                # Встречаються обьявления без указания работодателя в заголовке
                if len(superjob_one_vacancy) > 1 :
                    tmp_vacancy_dict['name_of_employer'] = superjob_one_vacancy[1].text
                else:
                    tmp_vacancy_dict['name_of_employer'] = 'Смотрите по ссылке на описание вакансии'

                # Получим город работы
                if (tag_vacancy.select('span div div'))[0].text == 'Удаленная работа':
                    tmp_vacancy_dict['city_of_work'] = ''
                    tmp_vacancy_dict['type_of_work'] = (tag_vacancy.select('span div div'))[0].text
                else:
                    tmp_vacancy_dict['city_of_work'] = (tag_vacancy.select('span div div'))[0].text
                    tmp_vacancy_dict['type_of_work'] = 'офис'

                # Занесем информацию по зарплате
                superjob_vacancy_salary = (tag_vacancy.select('div.f-test-text-company-item-salary span'))[0].text
                vacancy_salary = superjob_vacancy_salary.replace('\xa0', ' ')

                # Обработаем данные по зарплате
                salary_dict = get_salary_dict(vacancy_salary)
                if len(salary_dict) > 0:
                    tmp_vacancy_dict['salary']['min_salary'] = salary_dict['min_salary']
                    tmp_vacancy_dict['salary']['max_salary'] = salary_dict['max_salary']
                    tmp_vacancy_dict['salary']['currency'] = salary_dict['currency']
                else:
                    tmp_vacancy_dict['salary']['min_salary'] = 0.0
                    tmp_vacancy_dict['salary']['max_salary'] = 0.0
                    tmp_vacancy_dict['salary']['currency'] = ''

                superjob_vacancy_list.append(deepcopy(tmp_vacancy_dict))

        else:
            return superjob_respond_bs

    return superjob_vacancy_list


def get_rabotaru_vacancies(rabotaru_url, rabotaru_request_params, npages):

    # Инициализируем список словарей для хранения вакансий
    rabotaru_vacancy_list = []
    tmp_vacancy_dict['vacancy_source'] = 'rabota.ru'

    # Организуем цикл сбора информации
    for i in range(1, npages):
        # Чтобы избежать ошибки о превышении количества запросов
        sleep(2)

        # Заносим в параметры запроса номер страницы
        rabotaru_request_params['page'] = str(i)

        # Выполним запрос к сайту, ответ преобразуем в html а затем в список
        rabotaru_respond_bs = get_request_bs(url=rabotaru_url, params=rabotaru_request_params)

        if len(rabotaru_respond_bs) > 1:
            # Получим все блоки описания вакансий
            rabotaru_tag_vacancy_list = rabotaru_respond_bs.select('div article.vacancy-preview-card')

            # Обработаем все вакансии
            for one_vacancy_tag in rabotaru_tag_vacancy_list:
                # Получим наименование вакансии
                tmp_vacancy_dict['vacancy'] = (one_vacancy_tag.select('a.vacancy-preview-card__title_border')[0].text)\
                                                                      .replace('\n', '').strip()

                # Получим ссылку на вакансию
                tmp_vacancy_dict['vacancy_link'] = 'https://www.rabota.ru' + \
                                            one_vacancy_tag.select('a.vacancy-preview-card__title_border')[0]['href']

                # Получим работодателя
                # Редко нопопадаються формы без указания работадателя
                if len(one_vacancy_tag.select('span.vacancy-preview-card__company-name')) > 0:
                    tmp_vacancy_dict['name_of_employer'] = (
                        one_vacancy_tag.select('span.vacancy-preview-card__company-name')[0].text)\
                                               .replace('\n', '').strip()
                else:
                    tmp_vacancy_dict['name_of_employer'] = ''

                # Получим город работы и тип работы
                if one_vacancy_tag.select('span.vacancy-preview-location__address-text')[0].text == 'Удаленная работа':
                    tmp_vacancy_dict['city_of_work'] = ''
                    tmp_vacancy_dict['type_of_work'] = 'Удаленная работа'
                else:
                    citi_of_work = (one_vacancy_tag.select('span.vacancy-preview-location__address-text')[0].text)\
                                                .replace('\n', '').strip()

                    if citi_of_work.find('Москва') == -1:
                        tmp_vacancy_dict['city_of_work'] = citi_of_work + ', Москва'
                    else:
                        tmp_vacancy_dict['city_of_work'] = citi_of_work

                    tmp_vacancy_dict['type_of_work'] = 'офис'

                # Обработаем данные по зарплате
                vacancy_salary = (one_vacancy_tag.select('div.vacancy-preview-card__salary a')[0].text)\
                                                         .replace('\xa0', ' ')

                salary_dict = get_salary_dict(vacancy_salary)

                if len(salary_dict) > 0:
                    tmp_vacancy_dict['salary']['min_salary'] = salary_dict['min_salary']
                    tmp_vacancy_dict['salary']['max_salary'] = salary_dict['max_salary']
                    tmp_vacancy_dict['salary']['currency'] = salary_dict['currency']
                else:
                    tmp_vacancy_dict['salary']['min_salary'] = 0.0
                    tmp_vacancy_dict['salary']['max_salary'] = 0.0
                    tmp_vacancy_dict['salary']['currency'] = ''

                rabotaru_vacancy_list.append(deepcopy(tmp_vacancy_dict))

        else:
            return superjob_respond_bs


    return rabotaru_vacancy_list



############################################################################################################
# Основное тело программы
############################################################################################################


if __name__ == '__main__':

    # Записываем в лог время начала работы парсера
    start_datetime = CURRENT_DATE + ' ' + str((datetime.now()).hour) + ':' + str((datetime.now()).minute)
    logger.info(f"Парсер вакансий начал работу: {start_datetime}")

    # Зададим словарь url сайтов поиска работы
    url_of_headhunter_companies = {
        'HeadHunter': 'https://api.hh.ru/vacancies',
        'Superjob': 'https://www.superjob.ru/vacancy/search/',
        'Работа.ру': 'https://www.rabota.ru/vacancy/'
    }

    # Зададим словарь параметров для запросов на сайте HeadHunter
    headhunter_request_params = {
        'text': KEY_SEARCH_STRING,
        'area': '1',
        'items_on_page': '20',
        'page': '0'
    }

    # Зададим словарь параметров для запросов на сайте Superjob
    superjob_request_params = {
        'keywords': KEY_SEARCH_STRING,
        'geo%5Bt%5D%5B0%5D': '4',
        'page': '0'
    }

    # Зададим словарь параметров для запросов на сайте Работа.ру
    rabotaru_request_params = {
        'query': KEY_SEARCH_STRING,
        'sort': 'relevance',
        'page': '0'
    }

############################################################################################################
    # Подключимся и создадим структуру БД в MangoDB
############################################################################################################

    # Подключимся к локальной MongoDB
    local_mdb_client = pymongo.MongoClient('mongodb://localhost:27017/')
    # Создадим/Подключимся к БД vacancy_db
    vacancy_db = local_mdb_client['vacancy_db']
    # Создадим/Подключим коллекции по именам источников вакансий
    headhunter_collection = vacancy_db['headhunter']
    superjob_collection = vacancy_db['superjob']
    rabotaru_collection = vacancy_db['rabotaru']

############################################################################################################
    # Обработка вакансий разработчика python для города Москвы с сайта HeadHunter
############################################################################################################

    # hh защищается от стандартного парсинга и выдает ошибку 404 или 403
    # Парсинг hh будет реализован через стандартный hh api

    # Измерим время обработки вакансий
    # точка отсчета времени
    start = time.time()

    # Инициализируем список вакансий
    headhunter_vacancy_list = []
    # Инициализируем маркер ошибки
    hh_err = False

    # Получим список вакансий hh
    try:
        headhunter_vacancy_list = get_headhunter_vacancies(url_of_headhunter_companies['HeadHunter'],
                                                           headhunter_request_params,
                                                           npages=40)
    except Exception as e:
        # логируем время и ошибку
        dt = datetime.now().strftime('[%Y-%b-%d %H:%M:%S]')
        err_msg = f'При обработке вакансий на headhunter.ru произошла ошибка: {e}'
        logger.error(f"{dt} {err_msg}")
        hh_err = True

    if not hh_err:
        # Сохраним полученный список вакансий в json формате в файл
        save_json_to_file('jsons/hh_vacancy_', headhunter_vacancy_list)

        logger.info(f'Количество найденных вакансий на hh.ru: {len(headhunter_vacancy_list)}')

        # Запишем в базу MangoDB vacancy_db словари с вакансиями hh
        # Что бы избежать дубликатов вакансий запись в базу, проверим что в БД нет таких вакансий

        # Выгрузим из БД только заголовки
        headhunter_db_vacancy_list = list(headhunter_collection.find({'vacancy': {'$exists': True}},
                                                                     {'_id': False}))

        # Создадим пустой список вакансий для вставки в БД
        headhunter_diff_list_to_insertion = []

        # Для каждого словаря из полученного после парсинга списка
        for item in headhunter_vacancy_list:
            # Проверим есть ли вакансия в БД
            if item not in headhunter_db_vacancy_list:
                # Если нет, добавим словарь в список для вставки
                headhunter_diff_list_to_insertion.append(item)

        # Если были обнаружены новые ваканчии то
        if len(headhunter_diff_list_to_insertion) > 0:
            # Внесем полученный список вакансий в БД
            x = headhunter_collection.insert_many(headhunter_diff_list_to_insertion)
            vacancy_count = len(headhunter_diff_list_to_insertion)

            logger.info(f'Запись {vacancy_count} вакансий в базу данных vacancy_db коллекция headhunter завершено!')

        # Очищаем все списки данных
        headhunter_vacancy_list.clear()
        headhunter_diff_list_to_insertion.clear()

#########################################################################################################
    # Обработка вакансий разработчика python для города Москвы с сайта Superjob
#########################################################################################################

    # Инициализируем список вакансий
    superjob_vacancy_list = []
    # Инициализируем маркер ошибки
    superjob_err = False

    # Получим список вакансий hh
    try:
        superjob_vacancy_list = get_superjob_vacancies(url_of_headhunter_companies['Superjob'],
                                                           superjob_request_params,
                                                           npages=4)
    except Exception as e:
        # логируем время и ошибку
        dt = datetime.now().strftime('[%Y-%b-%d %H:%M:%S]')
        err_msg = f'При обработке вакансий на superjob.ru произошла ошибка: {e}'
        logger.error(f"{dt} {err_msg}")
        superjob_err = True

    if not superjob_err:
        # Сохраним полученный список вакансий в json формате в файл
        save_json_to_file('jsons/superjob_vacancy_', superjob_vacancy_list)

        logger.info(f'Количество найденных вакансий на superjob.ru: {len(superjob_vacancy_list)}')

        # Запишем в базу MangoDB vacancy_db словари с вакансиями superjob
        # Что бы избежать дубликатов вакансий при записе в базу, проверим что в БД нет таких вакансий

        # Выгрузим из БД только заголовки
        superjob_db_vacancy_list = list(superjob_collection.find({'vacancy': {'$exists': True}},
                                                                     {'_id': False}))

        # Создадим пустой список вакансий для вставки в БД
        superjob_diff_list_to_insertion = []

        # Для каждого словаря из полученного после парсинга списка
        for item in superjob_vacancy_list:
            # Проверим есть ли вакансия в БД
            if item not in superjob_db_vacancy_list:
                # Если нет, добавим словарь в список для вставки
                superjob_diff_list_to_insertion.append(item)

        if len(superjob_diff_list_to_insertion) > 0:
            # Внесем полученный список вакансий в БД
            x = superjob_collection.insert_many(superjob_diff_list_to_insertion)
            vacancy_count = len(superjob_diff_list_to_insertion)

            logger.info(f'Запись {vacancy_count} вакансий в базу данных vacancy_db коллекция superjob завершено!')

        # Очищаем все списки данных
        superjob_vacancy_list.clear()
        superjob_diff_list_to_insertion.clear()


#########################################################################################################
    # Обработка вакансий разработчика python для города Москвы с сайта Работа.ру
#########################################################################################################

    # Инициализируем список вакансий
    rabotaru_vacancy_list = []
    # Инициализируем маркер ошибки
    rabotaru_err = False

    # Получим список вакансий hh
    try:
        rabotaru_vacancy_list = get_rabotaru_vacancies(url_of_headhunter_companies['Работа.ру'],
                                                           rabotaru_request_params,
                                                           npages=6)
    except Exception as e:
        # логируем время и ошибку
        dt = datetime.now().strftime('[%Y-%b-%d %H:%M:%S]')
        err_msg = f'При обработке вакансий на rabotaru.ru произошла ошибка: {e}'
        logger.error(f"{dt} {err_msg}")
        rabotaru_err = True

    if not rabotaru_err:
        # Сохраним полученный список вакансий в json формате в файл
        save_json_to_file('jsons/rabotaru_vacancy_', rabotaru_vacancy_list)

        logger.info(f'Количество найденных вакансий на rabota.ru: {len(rabotaru_vacancy_list)}')

        # Запишем в базу MangoDB vacancy_db словари с вакансиями rabotaru
        # Что бы избежать дубликатов вакансий при записе в базу, проверим что в БД нет таких вакансий

        # Выгрузим из БД только заголовки
        rabotaru_db_vacancy_list = list(rabotaru_collection.find({'vacancy': {'$exists': True}},
                                                                     {'_id': False}))

        # Создадим пустой список вакансий для вставки в БД
        rabotaru_diff_list_to_insertion = []

        # Для каждого словаря из полученного после парсинга списка
        for item in rabotaru_vacancy_list:
            # Проверим есть ли вакансия в БД
            if item not in rabotaru_db_vacancy_list:
                # Если нет, добавим словарь в список для вставки
                rabotaru_diff_list_to_insertion.append(item)

        if len(rabotaru_diff_list_to_insertion) > 0:
            # Внесем полученный список вакансий в БД
            x = rabotaru_collection.insert_many(rabotaru_diff_list_to_insertion)
            vacancy_count = len(rabotaru_diff_list_to_insertion)

            logger.info(f'Запись {vacancy_count} вакансий в базу данных vacancy_db коллекция rabotaru завершено!')

        # Очищаем все списки данных
        rabotaru_vacancy_list.clear()
        rabotaru_diff_list_to_insertion.clear()


##################################################################################################################
    # Завершение работы
##################################################################################################################

    # время обработки новостей
    end = round((time.time() - start) / 60, 2)
    logger.info(f'Время обработки новостей: {end} минут!')

    # Записываем в лог время завершения работы парсера
    stop_datetime = str(date.today()) + ' ' + str((datetime.now()).hour) + ':' + str((datetime.now()).minute)
    logger.info(f"Парсер вакансий закончил работу: {stop_datetime}")

