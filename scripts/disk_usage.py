import datetime
import os
import time
import subprocess
import psutil
import json
import sys
import socket
from os import path
from pathlib import Path
import glob

import requests

from scripts_fun import *

PAGE_DISK_USAGE_DATA = '/vnc_disk_usage/'

logger = get_logger(__name__)  # Инициализируем logger


# # Создаёт словарь приветствия и кодирует в JSON
# def get_hello_dict(mode, data=None):
#     hello_dict = {MODE_DICT_KEY: mode,
#                   DATA_DICT_KEY: data}
#
#     hello_json = json.dumps(hello_dict) + EOF  # Кодируем в JSON с EOF
#
#     return hello_json
#
#
# Отправляет данные на сервер

# Возвращает текущий адрес хоста
def get_host():
    path_to_config = Path(__file__).parent.parent.resolve().joinpath(CONFIG_NAME)
    if not path_to_config.is_file():
        logger.error(f'Не обнаружен файл конфига {CONFIG_NAME}')
        sys.exit(1)

    config = configparser.ConfigParser()
    config.read(path_to_config)
    host = config.get('Connect', 'host')  # Не динамические параметры ...

    return host.strip()


# Отправляет данные на сервер
def send_data(config_dict: dict):
    host = get_host()
    url = 'http://' + host + PAGE_DISK_USAGE_DATA

    response = requests.post(url, json=config_dict)
    logger.info(f'Данные о дисках и бекапах отправлены по адресу {url} ({response.status_code})')


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


# Проверяет вес БД 1С [ФАЙЛОВАЯ БАЗА]
def check_file_db_size():
    _base_size = None
    try:
        system_drive = list(Path(__file__).parents)[-1]  # Логический диск
        path_to_retail = Path(os.path.join(system_drive, 'retail'))
        if path_to_retail.exists():  # Если папка с базой существует
            listdir = os.listdir(path_to_retail)  # Список файлов

            _base_size = {}
            for file in listdir:  # Проходим по файлам
                if file == '1Cv8.1CD':  # Если файл базы
                    base_file = os.path.join(path_to_retail, file)  # Пишем путь
                    size = os.path.getsize(base_file)  # Размер файла
                    _base_size['retail'] = bytes_to_gb(size)  # Преобразуем размер базы

                if file.startswith('_$NEW$_'):  # Битый файл обновления
                    new_file = os.path.join(path_to_retail, file)  # Путь к файлу
                    file_attr = os.stat(new_file)  # Атрибуты файла

                    create_datetime = datetime.fromtimestamp(file_attr.st_ctime)  # Дата и время создания файла
                    delta = datetime.now() - create_datetime  # Разница во времени

                    if delta.days:  # Если прошли сутки (24 часа)
                        try:
                            os.remove(new_file)  # Удаляем файл
                        except Exception:  # Если не поучается удалить
                            pass

            if not _base_size:  # Чтоб не отдавать пустой словарь
                _base_size = None

    except Exception:  # В случае ошибки - возвращаем None
        return None

    return _base_size


# Проверяет вес БД 1С [SQL база]
def check_sql_db_size():
    _base_size = None
    try:
        # Стандартный путь к БД
        path_to_sql_database_str = r'C:\Program Files (x86)\Microsoft SQL Server\MSSQL12.RETAIL\MSSQL\DATA'
        db_path = Path(path_to_sql_database_str)  # Объект Path

        if db_path.exists():  # Если директория существует
            listdir = os.listdir(db_path)  # Список файлов

            _base_size = {}
            for file in listdir:
                if file.startswith('retail.'):  # Файл БД
                    base_file = os.path.join(db_path, file)  # Путь к файлу
                    size = os.path.getsize(base_file)  # Размер файла
                    _base_size['retail'] = bytes_to_gb(size)  # Сохраняем

                if file.startswith('retail_log.'):  # Файл логов
                    base_file = os.path.join(db_path, file)
                    size = os.path.getsize(base_file)  # Размер файла
                    _base_size['retail_log'] = bytes_to_gb(size)  # Сохраняем

    except Exception:  # В случае ошибки - возвращаем None
        return None

    return _base_size


def main():
    arg = get_argv_list(sys.argv)
    PATH_TO_CRYSTALD_DIR = r'C:\Program Files\CrystalDiskInfo'

    pharmacy = arg[0]
    device = arg[1]

    logger.info(f'Скрипт {get_basename(__file__)} начал работу')

    # Ключи словаря конфигурации
    PHARMACY_DICT_KEY = 'pharmacy'
    DEVICE_DICT_KEY = 'device'
    BASE_SIZE_KEY = 'base_size'
    BASE_SIZE_NEW_KEY = 'base_size_dict'
    DISK_LIFE_KEY = 'disk_life'
    DISK_TEMPERATURE_KEY = 'disk_temperature'
    TOM_DICT_KEY = 'tom_data'
    TOM_TOTAL_SIZE_KEY = 'total'
    TOM_FREE_SIZE_KEY = 'free'
    TOM_PERCENT_KEY = 'percent'

    PATH_FROM_BASE = 'С:\\retail'  # Путь к БД
    C_DRIVE = 'C:\\'

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
            TOM_PERCENT_KEY: usage.percent  # Процент занятого места
        }

    base_size = None  # Заглушка
    try:
        if int(device) in (1, 99):  # Если 1 касса или сервер [ФАЙЛОВАЯ БАЗА]
            base_size = check_file_db_size()

        if int(device) == 99 and base_size is None:  # Если сервер и размер базы неизвестен [SQL база]
            base_size = check_sql_db_size()
    except Exception:  # Если не будет данных о БД, пережить можно будет
        pass

    # Узнаем состояние диска
    try:
        if os.path.exists(fr'{PATH_TO_CRYSTALD_DIR}\Smart'):
            path1 = fr'{PATH_TO_CRYSTALD_DIR}\Smart'
            content = os.listdir(path1)
            files = []

            for file in content:
                if os.path.isdir(os.path.join(path1, file)):
                    files.append(os.path.join(path1, file))

            files = sorted(files, key=lambda x: os.path.getmtime(x), reverse=True)
            path_to_smart = files[0] + '\\' + 'Smart.ini'
            smart_data = {}
            with open(path_to_smart) as config:
                for field in config:
                    sp = field.replace('\n', '').split('=')
                    name, val = sp[0].strip(), sp[-1].strip()
                    smart_data[name] = val
            if smart_data.get('Life') is not None:
                disk_life = str(smart_data.get('Life')).replace('"', '') + '%'
            else:
                disk_life = str(smart_data.get('HealthStatus')).replace('"', '')
            disk_temperature = str(smart_data.get('Temperature')).replace('"', '') + '°C'
        else:
            disk_life = 'Unknown'
            disk_temperature = 'Unknown'
    except Exception:
        disk_life = 'Unknown'
        disk_temperature = 'Unknown'

    disk_usage_dict = {
        PHARMACY_DICT_KEY: pharmacy,
        DEVICE_DICT_KEY: device,
        TOM_DICT_KEY: tom_dict,
        BASE_SIZE_NEW_KEY: base_size,
        DISK_LIFE_KEY: disk_life,
        DISK_TEMPERATURE_KEY: disk_temperature,
    }

    try:
        send_data(disk_usage_dict)  # Отправляет данные на сервер
    except (ConnectionRefusedError, ConnectionResetError):
        logger.error(f'Скрипт {get_basename(__file__)} не смог отправить данные на север')


if __name__ == '__main__':
    try:
        main()
    except Exception:
        logger.error(f'В скрипте {get_basename(__file__)} произошла необрабатываемая ошибка', exc_info=True)