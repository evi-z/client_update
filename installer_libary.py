import os
import sys
import time
import json
from pathlib import Path
from subprocess import run, PIPE, Popen, CalledProcessError, check_call, DEVNULL

from bin.values import *


# TODO Установка по аргументу cmd устарела
# Возвращает список аргументов коммандной строки
def get_argv_list(argv):
    if argv[1:]:  # Если есть аргументы коммандной строки
        argv_list = argv[1:]  # Исключаем первый элемент

        return argv_list


# Возвращает список установленных библиотек
def get_all_install_library():
    res = run([sys.executable, '-m', 'pip', 'list', '--format=json'], stderr=PIPE, stdout=PIPE, stdin=PIPE)
    lib_list = json.loads(res.stdout.decode())  # Загружаем из JSON

    return lib_list


# Проверяет, установлена ли библиотека
def check_current_lib_install(lib):
    lib_list = get_all_install_library()  # Обновляем актуальный список библиотек

    for el in lib_list:  #
        if el.get('name') == lib:  # Если имя соответсвует, возвращает версию
            return el.get('version')
    else:
        return False  # Иначе False


# Получаем список аргументов коммандной строки
argv_list = get_argv_list(sys.argv)


# Флаг Тихого режима
silent_flag = False
if argv_list:  # Если есть аргументы коммандной строки - Тихий режим
    silent_flag = True

if silent_flag:  # Если тихий режим
    for lib in argv_list:  # Устанавливаем переданные в cmd библиотеки
        run([sys.executable, '-m', 'pip', 'install', lib], shell=True, stdout=PIPE, stderr=PIPE, stdin=PIPE)
else:  # Устанавливаем все библиотеки
    for lib in APP_LIBRARY:
        run([sys.executable, '-m', 'pip', 'install', lib], shell=True)
