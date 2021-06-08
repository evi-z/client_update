import logging
import time
from datetime import datetime
import winreg as reg
from subprocess import run, Popen, PIPE, STDOUT, DEVNULL

from bin.values import *
from funs.low_level_fun import *

import json
import configparser
import socket
import signal
import psutil
import random
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


# Инициализирует клиента (до цикла)
def init_client():
    control_clone_client()  # Проверям, не запущенн ли уже client
    init_tvns()  # Инициализирует службу TightVnc
    run_init_cmd()  # Побочные настройки cmd
    run_init_reg()  # Побочные настройки реестра


# Инициализирует TightVNC
def init_tvns():
    run(f'reg import {os.path.join(ROOT_PATH, VNC_SERVICE_REG_FILE)}',  # Импотрируем настройки в реестр
        shell=True, stderr=PIPE, stdout=PIPE, stdin=PIPE)

    tvns_file = os.path.join(ROOT_PATH, TVNSERVER_FILE_PATH)  # Абсолютный путь к tvns
    command_list = [
        f'{tvns_file} -install -silent',  # Регистрируем службу
    ]

    for command in command_list:  # Проходим по коммандам
        run(command, shell=True, stderr=PIPE, stdout=PIPE, stdin=PIPE)


# Инициализирует всевозможные обращения к коммандной строке
def run_init_cmd():
    # Отключение брандмауэра (админ)
    firewall_res = run('netsh advfirewall set allprofiles state off',
                       shell=True, stderr=PIPE, stdout=PIPE, stdin=PIPE)

    if not firewall_res.returncode:  # Ловим returncode = 0
        print_log('Брандмауэр отключен')


# Инициализирует побочные ключи реестра
def run_init_reg():
    abs_tvns_path = os.path.join(ROOT_PATH, TVNSERVER_FILE_PATH)  # Полный путь к tvns

    #  Реестр юзера
    k_user = reg.CreateKeyEx(reg.HKEY_CURRENT_USER, REG_PATH_TO_LAYER, 0, reg.KEY_ALL_ACCESS)
    reg.SetValueEx(k_user, abs_tvns_path, 0, reg.REG_SZ, RUNASADMIN_FLAG)  # Ставим флаг RUNASADMIN

    # Реестр машины (админ) (работает только на 34-битных)
    k_lm = reg.CreateKeyEx(reg.HKEY_CURRENT_USER, REG_PATH_TO_LAYER, 0, reg.KEY_ALL_ACCESS)
    reg.SetValueEx(k_lm, abs_tvns_path, 0, reg.REG_SZ, RUNASADMIN_FLAG)  # Ставим флаг RUNASADMIN


# Выполняет необходимые стартовые действия в нужном порядке (в цикле)
def start_client():
    start_taskkill()  # Завершает процессы plink и tvnserver
    import_key()  # Импортирует ключи в реестр


# Завершает процессы, если запущенны
def start_taskkill():
    run(f'taskkill /f /im {PLINK_NAME}', shell=True, stdin=PIPE, stdout=PIPE, stderr=PIPE)
    run(f'taskkill /f /im {TVNSERVER_NAME}', shell=True, stdin=PIPE, stdout=PIPE, stderr=PIPE)


# Проверяет, запущен ли tvnserver classic (режим совместимости)
def tvnserver_classic_running():
    try:  # Отлов ошибки psutil
        for proc in psutil.process_iter():
            if TVNSERVER_CLASSIC_NAME in proc.name():
                return True

        return False
    except Exception as e:
        print_error(f'Ошибка в идентефикации процесса {TVNSERVER_CLASSIC_NAME}')


# Запускает tvnserver и возвращает объект
def start_tvnserver():
    tvnserver_process = Popen([os.path.join(ROOT_PATH, TVNSERVER_FILE_PATH), '-start', '-silent'],
                              stdin=PIPE, stdout=PIPE, stderr=PIPE)

    if not tvnserver_process.returncode:  # Если процесс запущен корректно (0)
        print_log(f'Запущена служба {TVNSERVER_NAME}')

    return tvnserver_process


# Создаёт plink из шаблона и возвращает объект
def start_plink(command):
    plink_process = Popen(command, shell=True, stderr=STDOUT, stdout=DEVNULL)

    # Пишем log
    if not plink_process.returncode:  # Если процесс запущен корректно (0)
        print_log(f'Запущенн процесс {PLINK_NAME} с идентификатором {plink_process.pid}')

    return plink_process


# Импортирует ключи реестра
def import_key():
    run(f'reg import {os.path.join(ROOT_PATH, KEY_REG_PATH)}', shell=True, stdin=PIPE, stdout=PIPE, stderr=PIPE)


# Инициализирует проверку актуальности параметров
def init_correct_config_parm(group, pharmacy_or_subgroup, device_or_name):
    if group == GROUP_PHARMACY_INT:  # Если группа - Аптека
        actual_parm_for_pharmacy(pharmacy_or_subgroup, device_or_name)  # Проверяем актуальность параметров

    elif group == GROUP_OFFICE_INT:  # Если группа - Офис
        actual_pharm_for_office(pharmacy_or_subgroup, device_or_name)  # Проверяем актуальность параметров

    else:  # Если группа неккорекктна
        print_incorrect_settings('Некорректная группа\n'
                                 'Допустимые группы:\n'
                                 '0 - Аптеки\n'
                                 '1 - Офис')


# Проверяет актуальность параметров для аптек
def actual_parm_for_pharmacy(pharmacy, device):
    device_list = list(DEVICE_DICT.values())  # Допустимые значения устройств

    # Защита MySQL
    if not pharmacy.isdigit():
        print_incorrect_settings(f'Номер аптеки должен быть целым числом ({PHARMACY_OR_SUBGROUP_PHARM})')

    # Защита UNSIGNED SMALLINT на сервере
    if int(pharmacy) >= 65535:
        print_incorrect_settings(f'Некорректный номер аптеки ({PHARMACY_OR_SUBGROUP_PHARM})')

    # Проверка на соответсвие списка устройств
    if device not in device_list:
        print_incorrect_settings(f'Неккоректное устройсво ({DEVICE_OR_NAME_PHARM})\n'
                                 'Допустимый диапазон устройств для аптек:\n'
                                 f'{device_list}')


# Прверяет актуальность параметров для офиса
def actual_pharm_for_office(subgroup, name):
    if not subgroup:  # Если отсутсвует подгруппа
        print_incorrect_settings(f'Не указанна подгруппа ({PHARMACY_OR_SUBGROUP_PHARM})')

    if not name:  # Если отсутствует наименование
        print_incorrect_settings(f'Не указанно наименование ({DEVICE_OR_NAME_PHARM})')

    if len(subgroup) > 80:
        print_incorrect_settings(f'Наименование подгруппы не должно превышать '
                                 f'80 символов ({PHARMACY_OR_SUBGROUP_PHARM})')

    if len(name) > 80:
        print_incorrect_settings(f'Имя не должно превышать 80 символов ({DEVICE_OR_NAME_PHARM})')


# Пишет критическую ошибку инициализации настроек и завершает программу
def print_incorrect_settings(text, stand_print=True):
    if stand_print:
        text = 'Некорректная инициализация файла конфигурации!\n' + f'{text}\n'
    else:
        text = f'{text}\n'

    print_log(text)
    exit()


# Выбирает порт из списка и возращает
def choice_port(_port_list):
    port_choice = random.choice(_port_list)

    return port_choice


# Пишет логи
def print_log(text):
    try:  # Пытаемся записать логи
        with open(os.path.join(os.getcwd(), LOG_FILE_PATH), 'a', encoding='cp1251') as logfile:
            logfile.write(f'[{datetime.now().strftime("%X %d/%m/%y")}]: {text}\n')
    except FileNotFoundError:  # Если папки не существует
        mkdrir_runtime()  # Создаём папку
        print_log(text)


# Пишет лог о завершении child-процессов
def print_restart_log(retcode, process_name, pid):
    if retcode:  # Если retcode не 0
        print_log(f'Процесс {process_name} с идентификатором {pid} завершён некорекктно (код: {retcode}), '
                  f'произведён перезапуск')

    else:  # Если 0
        print_log(f'Процесс {process_name} с идентификатором {pid} завершён, произведён перезапуск')


# Пишет ошибку в лог
def print_error(text):
    print_log(f'[ОШИБКА] {text}')


# Создаёт директорию runtime
def mkdrir_runtime():
    os.mkdir(os.path.join(ROOT_PATH, RUNTIME_DIR_NAME))


# Проверяет, не запущенн ли уже client
def control_clone_client():
    if os.path.exists(PID_FILE_PATH):  # Если pid-файл существует
        with open(PID_FILE_PATH, 'r') as pid_file:
            pid_from_file = int(pid_file.read())  # Читаем pid из файла

            for proc in psutil.process_iter():  # Проходим по работающим процессам
                # Если уже запущен процесс с таким идентификатором и имя процесса совпадает с cmd (shell)
                if pid_from_file == proc.pid and PROCESS_NAME_CLIENT in proc.name():
                    proc.terminate()  # Завершение работы процесса
                    print_log(f'Попытка запуска второй копии client, процесс {proc.pid} завершён')

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


# Инициализирует работу побочных скриптов
def init_scripts(init_tuple):
    group, pharmacy_or_subgroup, device_or_name = init_tuple

    reg_dict = get_reg_dict()  # Получаем словрь ключей реестра

    last_run = float(reg_dict[REG_LAST_RUN_KEY])  # Время последнего запуска

    if group == GROUP_PHARMACY_INT and need_init_pc_config(last_run):  # Если группа Аптеки
        init_ip_config((pharmacy_or_subgroup, device_or_name))

    set_lsat_run()  # Устанавливает время последнего запуска


# Инициализирует работу ip_config скрипта
def init_ip_config(init_tuple):
    pharmacy, device = init_tuple

    # Отправляем номер аптеки и устройство аргументами коммандной строки
    Popen([sys.executable, os.path.join(ROOT_PATH, SCRIPTS_DIR_NAME, PC_CONFIG_MODULE_NAME), pharmacy, device])

    print_log(f'Был выполнен скрипт {PC_CONFIG_MODULE_NAME}')  # Пишем лог
    time.sleep(1)  # Необходимо для корректой отработки


# Возращает, необходимо ли инициализировать pc_config, искходя из времени последнего запуска
def need_init_pc_config(last_run):
    now = time.time()  # Текущее время
    uptime = psutil.boot_time()  # Время, которе запущена ОС

    # Если после перезагрузки не было сканирования
    if now - last_run > now - uptime:
        return True
    else:
        return False
