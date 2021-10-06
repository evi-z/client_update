import os
from datetime import datetime
import configparser
import logging

from kkm_values import *

RUNTIME_DIR = 'runtime'
LOG_NAME = 'script_log.txt'
ENCODING_APP = 'utf8'


# Инициализирует logger
def init_logger():
    try:
        fh = logging.FileHandler(os.path.join(RUNTIME_DIR, LOG_NAME), 'a', ENCODING_APP)  # Файл лога
    except FileNotFoundError:  # Если нет директории runtime
        os.mkdir(RUNTIME_DIR)  # Создаём папку runtime
        fh = logging.FileHandler(os.path.join(RUNTIME_DIR, LOG_NAME), 'a', ENCODING_APP)  # Файл лога
    str_format = '[%(asctime)s]: %(levelname)s - %(name)s - (%(filename)s).%(funcName)s(%(lineno)d) ' \
                 '=> %(message)s'  # Формат вывода
    date_format = '%X %d/%m/%y'  # Формат даты/времени
    formatter = logging.Formatter(fmt=str_format, datefmt=date_format)
    fh.setFormatter(formatter)  # Устанавливаем форматирование

    return fh  # Возвращаем настроенный логгер


# Возвращает объект logger-a
def get_logger(name):
    logger = logging.getLogger(name)  # Инициализируем объект логгера с именем программы
    logger.setLevel(logging.INFO)  # Уровень логгирования
    logger.addHandler(init_logger())  # Добавляем

    return logger


# Возвращает имя запущенного скрипта из атрибута __file__
def get_basename(_file):
    return os.path.basename(_file)


# Сохраняет удачное подключение
def save_kkm_connect_data(kkm_name, com_port, baudrate):
    # Создания конфига
    kkm_config = configparser.ConfigParser()
    kkm_config.add_section(KKM_SECTION_NAME)

    kkm_config.set(KKM_SECTION_NAME, KKM_NAME_PARM, kkm_name)  # Идентефикация ККМ
    kkm_config.set(KKM_SECTION_NAME, KKM_COM_PORT_PARM, com_port)  # Номер COM-порта
    kkm_config.set(KKM_SECTION_NAME, KKM_BAUDRATE_PARM, str(baudrate))  # Скорость

    with open(KKM_CONFIG_FILE_NAME, 'w') as config_file:
        kkm_config.write(config_file)
