from datetime import datetime
from subprocess import run, PIPE, Popen

from values import *

import json
import configparser
import psutil
import socket
import sys
import os


# Завершает программу и пишет лог, если переданн текст
def exit(text=None):
    if text:
        print_log(text)

    sys.exit(0)


# Получает JSON данные от сокета и возвращает декодированным
def get_data_from_socket(sock):
    get_list = []
    while True:
        data = sock.recv(4096)  # Читаем данные по 4096 Б
        data = data.decode()  # Декодируем

        if data.endswith(EOF):  # Ловим символ завершения
            data = data.split(EOF)  # Бьём строку по этому смволу
            get_list.append(data[0])  # Добавляем данные без EOF
            break

        get_list.append(data)

    data_json = ''.join(get_list)  # Объединяем в строку
    data = json.loads(data_json)  # Декодируем в словарь

    return data


# Создаёт словарь приветствия и кодирует в JSON
def get_hello_dict(mode, data=None):
    hello_dict = {MODE_DICT_KEY: mode,
                  DATA_DICT_KEY: data}

    hello_json = json.dumps(hello_dict) + EOF  # Кодируем в JSON с EOF

    return hello_json


# Создаёт новый процесс из шаблона и возвращает объект
def start_plink(command):
    plink_process = Popen(command, stderr=PIPE, stdout=PIPE, stdin=PIPE)

    return plink_process


# Выполняет необходимые стартовые действия в нужном порядке
def start_client():
    start_taskkill()
    import_key()
    start_tvnserver()


# Завершает процессы, если запущенны
def start_taskkill():
    run(f'taskkill /f /im {TVNSERVER_NAME}', shell=True, stdin=PIPE, stdout=PIPE, stderr=PIPE)
    run(f'taskkill /f /im {PLINK_NAME}', shell=True, stdin=PIPE, stdout=PIPE, stderr=PIPE)


# Запускаем tvnserver
def start_tvnserver():
    Popen(f'start {os.path.join(os.getcwd(), TVNSERVER_FILE_PATH)}',
          shell=True, stdin=PIPE, stdout=PIPE, stderr=PIPE)


# Импортирует ключи реестра
def import_key():
    # TODO Предусмотреть смену адреса сервера!
    reg_list_path = [KEY_REG_PATH, VNC_SRV_REG_PATH]
    for name in reg_list_path:
        run(f'reg import {os.path.join(os.getcwd(), name)}',
            shell=True, stdin=PIPE, stdout=PIPE, stderr=PIPE)


# Пишет критическую ошибку инициализации настроек и завершает программу
def print_incorrect_settings(text, stand_print=True):
    if stand_print:
        text = 'Некорректная инициализация файла конфигурации!\n' + f'{text}\n'
    else:
        text = f'{text}\n'

    print_log(text)
    exit()


# Пишет логи
def print_log(text):
    try:  # Пытаемся записать логи
        with open(os.path.join(os.getcwd(), LOG_FILE_PATH), 'a') as logfile:
            logfile.write(f'[{datetime.now().strftime("%X %d/%m/%y")}]: {text}\n')
    except FileNotFoundError:  # Если папки не существует
        mkdrir_runtime()  # Создаём папку
        print_log(text)


# Создаёт директорию runtime
def mkdrir_runtime():
    run(f'mkdir {os.path.join(os.getcwd(), RUNTIME_DIR_NAME)}',
        shell=True, stderr=PIPE, stdout=PIPE, stdin=PIPE)


# Проверяет, не запущенн ли уже client
def control_clone_client():
    if os.path.exists(PID_FILE_PATH):  # Если pid-файл существует
        with open(PID_FILE_PATH, 'r') as pid_file:
            pid_from_file = int(pid_file.read())  # Читаем pid из файла

            for proc in psutil.process_iter():   # Проходим по работающим процессам
                # Если уже запущен процесс с таким идентификатором и имя процесса совпадает
                if pid_from_file == proc.pid and PROCESS_NAME_CLIENT in proc.name():
                    exit(f'Попытка запуска второй копии client. Уже запущен процесс {proc.name()} с '
                         f'идентификатором {pid_from_file}, работа завершена')  # Завершаем работу программы

            write_pid_file()  # Пишем pid
            print_log(f'Запущен client с идентификатором {os.getpid()}')  # Пишем лог

    else:  # Если не существует
        write_pid_file()  # Пишем pid
        print_log(f'Запущен client с идентификатором {os.getpid()}')  # Пишем лог


# Создаёт (перезаписывает) PID файл
def write_pid_file():
    try:  # Пытаемся записать файл
        with open(PID_FILE_PATH, 'w') as pid_file:
            pid_file.write(str(os.getpid()))

    except FileNotFoundError:  # Если нет директории
        mkdrir_runtime()  # Создаём директорию
        write_pid_file()  # Записываем PID


# Удаляет все пустые элементыв списке
def remove_simple_element(ls):
    while True:
        try:
            ls.remove('')
        except ValueError:
            return


# Возвращает список, заменив в элементах слеши на бэкслеши
def replace_slash_to_backslash(ls):
    list_with_backslash = []
    for el in ls:
        if '/' in el:
            sp = el.split('/')
            new_name = '\\'.join(sp)
            list_with_backslash.append(new_name)

        else:
            list_with_backslash.append(el)

    return list_with_backslash