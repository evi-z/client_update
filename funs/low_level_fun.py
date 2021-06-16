import os
import sys
import time
import winreg as reg
import platform
from ctypes import windll
from subprocess import run, PIPE, Popen

from bin.low_level_values import *


# Проверяет, запущенн ли client от имени администратора
def is_admin():
    try:  # Пытаемся вернуть True admin-mode
        return windll.shell32.IsUserAnAdmin()
    except:  # Иначе возвращаем False
        return False


# Возвращает список аргументов коммандной строки
def get_argv_list(argv):
    if argv[1:]:  # Если есть аргументы коммандной строки
        argv_list = argv[1:]  # Исключаем первый элемент

        return argv_list

    else:  # Если нет, возвращаем пустой список
        return []


# Возвращает, требуется ли загружать loader client-у
def need_init_loader(argv):
    argv_list = get_argv_list(argv)

    if DONT_NEED_INIT_LOADER_ARG in argv_list:  # Если есть флаг в списке
        return False
    else:  # Иначе
        return True


# Первичная инициализация ключей реестра с возвратом ключа
def first_init_reg_keys():
    k = reg.CreateKeyEx(reg.HKEY_CURRENT_USER, REG_ROOT_PATH, 0, reg.KEY_ALL_ACCESS)

    reg.SetValueEx(k, REG_VERSION_KEY, 0, reg.REG_SZ, APP_VERSION)  # Версия программы

    return k


# Возвращает словарь реестра программы
def get_reg_dict():
    first_init_flag = False  # Флаг первичной инициализации
    try:  # Пытаемя открыть раздел еестра
        k = reg.OpenKey(reg.HKEY_CURRENT_USER, REG_ROOT_PATH, 0, reg.KEY_ALL_ACCESS)

    except FileNotFoundError:  # Если раздела не существует
        k = first_init_reg_keys()  # Проводим первичную инициализацию
        first_init_flag = True  # Устанавливаем флаг первичной инициализации в True

    count_keys = reg.QueryInfoKey(k)[1]  # Колличество ключей раздела реестра

    reg_dict = {}  # Словаь ключей реестра
    for index in range(count_keys):  # Проходим по ключам
        key, value, types = reg.EnumValue(k, index)
        reg_dict[key] = value  # Пишем ключ - значение

    return reg_dict, first_init_flag


# Устанавливает значение в реестр (по пути REG_ROOT)
def set_reg_key(key, value):
    k = reg.OpenKey(reg.HKEY_CURRENT_USER, REG_ROOT_PATH, 0, reg.KEY_ALL_ACCESS)

    reg.SetValueEx(k, key, 0, reg.REG_SZ, value)  # Устанавливаем значение в реестр


# Устанавливает время последнего запуска программы в реестр
def set_last_run():
    now = str(time.time())  # Получаем текущее время (с начала эпохи)
    set_reg_key(REG_LAST_RUN_KEY, now)  # Устанавливаем в реестр


# Запускает "первичныe скрипты"
def run_first_scripts():
    first_popen()
    first_run()


# Запускает первичные скрипты и дожидается завершения
def first_run():
    listdir = os.listdir(FIRST_RUN_DIR_NAME)  # Список файлов в _first_run
    # Список скриптов в директории
    listscripts = [file for file in listdir if file.endswith('.py') or file.endswith('.pyw')]

    for script in listscripts:
        if script.endswith('.py'):  # Стандартный интропретатор
            run([PATH_TO_PYTHON, os.path.join(FIRST_RUN_DIR_NAME, script)], shell=True,
                stdout=PIPE, stderr=PIPE, stdin=PIPE)

        if script.endswith('pyw'):  # No-Console
            run([PATH_TO_PYTHON_NO_CONSOLE, os.path.join(FIRST_RUN_DIR_NAME, script)], shell=True,
                stdout=PIPE, stderr=PIPE, stdin=PIPE)


# Запускает первичные скрипты и продолжает работу
def first_popen():
    listdir = os.listdir(FIRST_POPEN_DIR_NAME)  # Список файлов в _first_popen
    # Список скриптов в директории
    listscripts = [file for file in listdir if file.endswith('.py') or file.endswith('.pyw')]

    for script in listscripts:
        if script.endswith('.py'):  # Стандартный интропретатор
            Popen([PATH_TO_PYTHON, os.path.join(FIRST_POPEN_DIR_NAME, script)], shell=True,
                  stdout=PIPE, stderr=PIPE, stdin=PIPE)

        if script.endswith('pyw'):  # No-Console
            Popen([PATH_TO_PYTHON_NO_CONSOLE, os.path.join(FIRST_POPEN_DIR_NAME, script)], shell=True,
                  stdout=PIPE, stderr=PIPE, stdin=PIPE)


# Проверяет, не содержит ли путь к клиенту пробельных символов
def path_to_client_with_space():
    path_to_script = sys.argv[0]  # Пусть к клиенту

    if ' ' in path_to_script:  # Если есть пробелы в пути
        return True
    else:
        return False


# Возвращяет корректный путь до клиента (экранирование пробелов в пути)
def get_correct_path():
    if path_to_client_with_space():  # Если в пути есть пробелы
        path_to_script = f'"{sys.argv[0]}"'  # Пишем в кавычках
    else:
        path_to_script = sys.argv[0]

    return path_to_script
