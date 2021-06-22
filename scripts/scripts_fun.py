import os
from datetime import datetime
import configparser

from kkm_values import *

RUNTIME_DIR = 'runtime'
LOG_NAME = 'script_log.txt'


# Пишет логи
def print_log(text):
    try:
        with open(os.path.join(RUNTIME_DIR, LOG_NAME), 'a', encoding='cp1251') as logfile:
            logfile.write(f'[{datetime.now().strftime("%X %d/%m/%y")}]: {text}\n')
    except FileNotFoundError:
        os.mkdir(RUNTIME_DIR)
        print_log(text)


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
