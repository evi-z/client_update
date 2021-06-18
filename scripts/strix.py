import os
import sys
import time
import socket
import json

from scripts_fun import *
from subprocess import run, PIPE

INSTALLER_LIBRARY_MODULE_NAME = 'installer_libary.py'
SCRIPTS_DIR_NAME = 'scripts'

for i in range(2):  # 2 попытки
    try:  # Пытаемся импортировать модуль
        import pyshtrih
        break
    except ModuleNotFoundError:  # Если нет
        print_log(f'Скрипт {get_basename(__file__)} не смог импортировать модуль pyshtrih, попытка установки')

        run([sys.executable, os.path.join(os.getcwd(), SCRIPTS_DIR_NAME,INSTALLER_LIBRARY_MODULE_NAME), 'pyshtrih'])

# Данные с сервера TODO
HOST = '85.143.156.89'
KKM_DEMON_PORT = 11718

# Ключи словаря приветствия
MODE_DICT_KEY = 'mode'
DATA_DICT_KEY = 'data'

EOF = '#'

CONFIGURATION_MODE = 'configuration'
KKM_STRIX_MODE = 'kkm_strix'


# Создаёт словарь приветствия и кодирует в JSON
def get_hello_dict(mode, data=None):
    hello_dict = {MODE_DICT_KEY: mode,
                  DATA_DICT_KEY: data}

    hello_json = json.dumps(hello_dict) + EOF  # Кодируем в JSON с EOF

    return hello_json


# Отправляет данные на сервер
def send_data(config_dict):
    hello_dict = get_hello_dict(KKM_STRIX_MODE, config_dict)  # Получаем словарь приветсвия

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((HOST, KKM_DEMON_PORT))

    sock.send(hello_dict.encode())  # Отправляем данные

    sock.close()


# Возвращает список аргументов коммандной строки
def get_argv_list(argv):
    if argv[1:]:  # Если есть аргументы коммандной строки
        argv_list = argv[1:]  # Исключаем первый элемент

        return argv_list

    else:  # Если нет, завершаем работу
        sys.exit(0)


# Получаем список аргументов коммандной строки
arg = get_argv_list(sys.argv)

pharmacy = arg[0]
kassa = arg[1]

# Ключи словаря
PHARMACY_KEY = 'pharmacy'
KASSA_KEY = 'device'
RNM_KEY = 'rnm'  # РН ККТ
MODEL_KEY = 'model'  # Название устройства
FN_KEY = 'fn'  # Номер ФН
FN_TIME_KEY = 'fn_time'  # Срок действия ФН
ADDRESS_KEY = 'address'  # Адрес
UNCORR_FD_COUNT_KEY = 'uncorr_fd_count'  # Колличество неподтвержённых ФД
LAST_OFD_UNCORR_DOC_NUM_KEY = 'last_ofd_uncorr_doc_num'  # Номер документа для ОФД первого в очереди
LAST_OFD_UNCORR_DOC_TIME_KEY = 'last_ofd_uncorr_doc_time'  # Дата и время документа для ОФД первого в очереди
LAST_FD_NUM_KEY = 'last_fd_num'  # Номер последнего ФД
INN_KEY = 'inn'  # ИНН

devices = pyshtrih.discovery()  # Ищем ККМ

if not devices:  # Если не найден
    print_log(f'Скрипт {get_basename(__file__)} не нашёл ККМ, работа прервана')
    sys.exit(0)

device = devices[0]  # Получаем первый (он всё-равно один)
device.connect()  # Коннектим к ККМ

# Наименования таблиц
TABLE_FISCAL_STORAGE_NAME = 'FISCAL STORAGE'
FIELD_RNM_NAME = 'RNM'
FIELD_ADDRESS_NAME = 'ADDRESS'

# Константы таблицы
TABLE_FISCAL_STORAGE_NUMBER = 18  # Номер таблицы Fiscal Storage
FIELD_RNM_NUMBER = 3  # Поле РН ККТ
FIELD_ADDRESS_NUMBER = 9  # Поле Адрес

# Чтение таблиц (словарные предсавления)
rnm = device.read_table(TABLE_FISCAL_STORAGE_NUMBER, 1, FIELD_RNM_NUMBER, str)  # РН ККТ
address = device.read_table(TABLE_FISCAL_STORAGE_NUMBER, 1, FIELD_ADDRESS_NUMBER, str)  # Адрес

# Значения
rnm = rnm['Значение']
address = address['Значение']

# Сбор данных
fn_stat = device.fs_state()  # Статус ФН
fn_time = device.fs_expiration_time()  # Срок действия ФН
fn_ofd = device.fs_info_exchange()  # Статус обмена с ОФД
fn_count_unrec = device.fs_unconfirmed_document_count()  # ФД без квитанции
full_state = device.full_state()  # Длинный запрос
model = device.model()  # Модель

device.disconnect()  # Отключаемся от ККМ

# Словарь данных
data_dict = {
    PHARMACY_KEY: pharmacy,
    KASSA_KEY: kassa,
    MODEL_KEY: model['Название устройства'],
    RNM_KEY: rnm,
    FN_KEY: fn_stat['Номер ФН'].decode(),
    FN_TIME_KEY: fn_time['Срок действия'].isoformat(),
    ADDRESS_KEY: address,
    UNCORR_FD_COUNT_KEY: fn_count_unrec['Количество неподтверждённых ФД'],
    LAST_OFD_UNCORR_DOC_NUM_KEY: fn_ofd['Номер документа для ОФД первого в очереди'],
    LAST_OFD_UNCORR_DOC_TIME_KEY: fn_ofd['Дата и время документа для ОФД первого в очереди'].isoformat(),
    LAST_FD_NUM_KEY: fn_stat['Номер последнего ФД'],
    INN_KEY: full_state['ИНН']
}

try:
    send_data(data_dict)  # Отправляем данные на сервер
except (ConnectionRefusedError, ConnectionResetError):
    print_log(f'Скрипт {get_basename(__file__)} не смог отправить данные на север')
