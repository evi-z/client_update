import psutil
import json
import sys
import socket

from scripts_fun import *

# TODO Здоровенный
HOST = '85.143.156.89'
CONFIGURATION_DEMON_PORT = 11617
DISK_USAGE_MODE = 'disk_usage'

logger = get_logger(__name__)  # Инициализируем logger


# Создаёт словарь приветствия и кодирует в JSON
def get_hello_dict(mode, data=None):
    hello_dict = {MODE_DICT_KEY: mode,
                  DATA_DICT_KEY: data}

    hello_json = json.dumps(hello_dict) + EOF  # Кодируем в JSON с EOF

    return hello_json


# Отправляет данные на сервер
def send_configuration_data(config_dict):
    hello_dict = get_hello_dict(DISK_USAGE_MODE, config_dict)

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((HOST, CONFIGURATION_DEMON_PORT))

    sock.send(hello_dict.encode())

    sock.close()


# Преобразует байты в гигабайты
def bytes_to_gb(byte):
    M = 1024 ** 3

    return byte / M


# Возвращает список аргументов коммандной строки
def get_argv_list(argv):
    if argv[1:]:  # Если есть аргументы коммандной строки
        argv_list = argv[1:]  # Исключаем первый элемент

        return argv_list

    else:  # Если нет, завершаем работу
        sys.exit(0)


arg = get_argv_list(sys.argv)

pharmacy = arg[0]
device = arg[1]

logger.info(f'Скрипт {get_basename(__file__)} начал работу')

# Ключи словаря конфигурации
PHARMACY_DICT_KEY = 'pharmacy'
DEVICE_DICT_KEY = 'device'

TOM_DICT_KEY = 'tom_data'
TOM_TOTAL_SIZE_KEY = 'total'
TOM_FREE_SIZE_KEY = 'free'
TOM_PERCENT_KEY = 'percent'

tom_dict = {}  # Данные о дисках
for tom in psutil.disk_partitions():  # Проходим по диску
    tom_name = tom.device  # Имя диска
    try:
        usage = psutil.disk_usage(tom_name)  # Статистика диска
    except OSError:  # Не системный диск
        continue

    friendly_name = tom_name.split('\\')[0]  # Экранируем бэкслеши
    tom_dict[friendly_name] = {
        TOM_TOTAL_SIZE_KEY: int(bytes_to_gb(usage.total)),  # Общая память
        TOM_FREE_SIZE_KEY: int(bytes_to_gb(usage.free)),  # Свободная память
        TOM_PERCENT_KEY: usage.percent   # Процент занятого места
    }


disk_usage_dict = {
    PHARMACY_DICT_KEY: pharmacy,
    DEVICE_DICT_KEY: device,
    TOM_DICT_KEY: tom_dict
}

try:
    send_configuration_data(disk_usage_dict)  # Отправляет данные на сервер
except (ConnectionRefusedError, ConnectionResetError):
    logger.error(f'Скрипт {get_basename(__file__)} не смог отправить данные на север')
