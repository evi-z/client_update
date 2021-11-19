import os
import sys
import time
import socket
import json
import configparser

from kkm_values import *
from scripts_fun import *
from subprocess import run, PIPE

logger = get_logger(__name__)  # Инициализируем logger

INSTALLER_LIBRARY_MODULE_NAME = 'installer_libary.py'

for i in range(2):  # 2 попытки
    try:  # Пытаемся импортировать модуль
        import pyshtrih

        break
    except ModuleNotFoundError:  # Если нет
        logger.warning(f'Скрипт {get_basename(__file__)} не смог импортировать модуль pyshtrih, попытка установки')

        run([sys.executable, os.path.join(os.getcwd(), INSTALLER_LIBRARY_MODULE_NAME), 'pyshtrih'])


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


def get_first_connection():
    devices = pyshtrih.discovery()  # Ищем ККМ

    return devices


# Получаем список аргументов коммандной строки
arg = get_argv_list(sys.argv)

pharmacy = arg[0]  # Аптека
kassa = arg[1]  # Касса

device = None
if len(arg) == 2:  # Если переданы только Аптека и Касса
    devices = get_first_connection()  # Первичный поиск ККМ

    if devices:  # Если ККМ найден
        device = devices[0]  # Получаем первый (он всё-равно один)
        save_kkm_connect_data(STRIX_KKM, device.port, device.baudrate)  # Сохраняем данные по ККМ

elif len(arg) == 4:  # Если переданы COM-порт и Скорость
    com_port = arg[2]  # COM порт
    baudrate = arg[3]  # Скорость

    devices = pyshtrih.discovery(port=com_port, baudrate=baudrate)  # Подключаемся к ККМ

    if not devices:  # Если всё равно не найдено
        devices = get_first_connection()  # Пытаемся найти

        if devices:  # Если ККМ найден
            device = devices[0]  # Получаем первый (он всё-равно один)
            save_kkm_connect_data(STRIX_KKM, device.port, device.baudrate)  # Сохраняем данные по ККМ
        else:  # Если не найден даже в первичной инициализации
            os.remove(KKM_CONFIG_FILE_NAME)  # Удаляем конфигурационный файл

    else:  # Если найден
        device = devices[0]  # Получаем первый (он всё-равно один)

else:  # Неверные аргументы коммандной строки
    sys.exit(0)

if not device:  # Если не найден
    logger.error(f'Скрипт {get_basename(__file__)} не нашёл ККМ, работа прервана')
    sys.exit(0)

logger.info(f'Скрипт {get_basename(__file__)} обнаружил ККМ и начал работу '
            f'(COM: {device.port}, Скорость: {device.baudrate})')

device.connect()  # Коннектим к ККМ

# Константы таблицы
TABLE_FISCAL_STORAGE_NUMBER = 18  # Номер таблицы Fiscal Storage
FIELD_RNM_NUMBER = 3  # Поле РН ККТ
FIELD_INN_NUMBER = 2  # Поле ИНН
FIELD_USER_NUMBER = 7  # Поле Юр. Лицо
FIELD_ADDRESS_NUMBER = 9  # Поле Адрес

# Чтение таблиц (словарные предсавления)
rnm = device.read_table(TABLE_FISCAL_STORAGE_NUMBER, 1, FIELD_RNM_NUMBER, str)  # РН ККТ
address = device.read_table(TABLE_FISCAL_STORAGE_NUMBER, 1, FIELD_ADDRESS_NUMBER, str)  # Адрес
ur_lic = device.read_table(TABLE_FISCAL_STORAGE_NUMBER, 1, FIELD_USER_NUMBER, str)  # Юр. лицо
inn = device.read_table(TABLE_FISCAL_STORAGE_NUMBER, 1, FIELD_INN_NUMBER, str)  # ИНН

# Значения
rnm = rnm['Значение'].strip()
address = address['Значение'].strip()
ur_lic = ur_lic['Значение'].strip()
inn = inn['Значение'].strip()

# Сбор данных
fn_stat = device.fs_state()  # Статус ФН
fn_time = device.fs_expiration_time()  # Срок действия ФН
fn_ofd = device.fs_info_exchange()  # Статус обмена с ОФД
fn_count_unrec = device.fs_unconfirmed_document_count()  # ФД без квитанции
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
    UR_LIC: ur_lic,
    INN_KEY: inn
}

try:
    send_data(data_dict)  # Отправляем данные на сервер
except (ConnectionRefusedError, ConnectionResetError):
    logger.error(f'Скрипт {get_basename(__file__)} не смог отправить данные на север')
