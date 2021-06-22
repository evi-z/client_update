import sys
import os
import configparser
from subprocess import run, PIPE

from kkm_values import *
from scripts_fun import *


# Константы
SCRIPTS_DIR_NAME = 'scripts'  # Корневая директория kkm.py
CLIENT_DIR_PATH = os.getcwd()  # Если запускается из под клиента, getcwd будет анолагичен ROOT_PATH


# Возвращает список аргументов коммандной строки
def get_argv_list(argv):
    if argv[1:]:  # Если есть аргументы коммандной строки
        argv_list = argv[1:]  # Исключаем первый элемент

        return argv_list

    else:  # Если нет, завершаем работу
        sys.exit(0)


# Получаем список аргументов коммандной строки
arg = get_argv_list(sys.argv)

pharmacy = arg[0]  # Номер аптеки
kassa = arg[1]  # Касса


# Первичная инициализация ККМ
def first_init_kkm():
    print_log(f'{get_basename(__file__)} проводит первичную инициализацию')
    for script in [ATOL_SCRIPT_NAME, STRIX_SCRIPT_NAME]:  # Запускаем скрипты поочерёдно
        run([sys.executable, os.path.join(CLIENT_DIR_PATH, SCRIPTS_DIR_NAME, script), pharmacy, kassa],
            shell=True, stderr=PIPE, stdout=PIPE, stdin=PIPE)


# Получает данные с ККМ
def get_kkm_configuration():
    if not os.path.exists(KKM_CONFIG_FILE_NAME):  # Если конфигурации нет
        first_init_kkm()  # Проводим первичную инициализацию

    else:
        kkm_config = configparser.ConfigParser()

        try:
            kkm_config.read(KKM_CONFIG_FILE_NAME)  # Читаем конфигурацию

            kkm = kkm_config.get(KKM_SECTION_NAME, KKM_NAME_PARM)  # Имя ККМ
            com_port = kkm_config.get(KKM_SECTION_NAME, KKM_COM_PORT_PARM)  # COM порт
            baudrate = kkm_config.get(KKM_SECTION_NAME, KKM_BAUDRATE_PARM)  # Скрость

        # Неверная конфигурация
        except (configparser.MissingSectionHeaderError, configparser.NoOptionError):
            first_init_kkm()  # Проводим первичную инициализацию
            return

        if kkm == ATOL_KKM:  # Если ККМ Атол
            print_log(f'Запущен {ATOL_SCRIPT_NAME} с сохранённой конфигурацией (COM: {com_port}, Скорость: {baudrate})')
            run([sys.executable, os.path.join(CLIENT_DIR_PATH, SCRIPTS_DIR_NAME, ATOL_SCRIPT_NAME),
                 pharmacy, kassa, com_port, baudrate],
                shell=True, stderr=PIPE, stdout=PIPE, stdin=PIPE)

            # Если после отработки скрипта был удалён файл конфигурации
            if not os.path.exists(KKM_CONFIG_FILE_NAME):
                first_init_kkm()  # Проводим первичную инициализацию

        elif kkm == STRIX_KKM:  # Если ККМ Штрих
            print_log(f'Запущен {STRIX_SCRIPT_NAME} с сохранённой конфигурацией (COM: {com_port}, Скорость: {baudrate})')
            run([sys.executable, os.path.join(CLIENT_DIR_PATH, SCRIPTS_DIR_NAME, STRIX_SCRIPT_NAME),
                 pharmacy, kassa, com_port, baudrate],
                shell=True, stderr=PIPE, stdout=PIPE, stdin=PIPE)

            # Если после отработки скрипта был удалён файл конфигурации
            if not os.path.exists(KKM_CONFIG_FILE_NAME):
                first_init_kkm()  # Проводим первичную инициализацию

        else:  # Если неверная конфигурация
            first_init_kkm()  # Проводим первичную инициализацию


get_kkm_configuration()  # Получаем данные ККМ
