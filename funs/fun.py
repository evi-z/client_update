import logging
import time
from datetime import datetime
from datetime import time as dtime
import winreg as reg
from subprocess import run, Popen, PIPE, STDOUT, DEVNULL
from threading import Thread

from bin.values import *
from funs.low_level_fun import *
from errors import *

import json
import configparser
import socket
import random
import sys
import os
import asyncio

logger = get_logger(__name__)


for _ in range(2):  # 2 попытки
    try:  # Отлов отстутвия загружаемых модулей
        import psutil
        import asyncssh

        break
    except ModuleNotFoundError as e:
        logger.info(f'Ошибка в импорте загружаемых модулей: {e}')
        need_modules_list = ('psutil', 'asyncssh')  # Список импорта
        logger.info(f'Попытка установки дополнительных модулей: {need_modules_list}')
        library_install(need_modules_list)  # Установка недостающих модулей
        time.sleep(3)  # timeout
        pass


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
# TODO Проверка, включен ли бранд
def run_init_cmd():
    # Отключение брандмауэра (админ)
    firewall_res = run('netsh advfirewall set allprofiles state off',
                       shell=True, stderr=PIPE, stdout=PIPE, stdin=PIPE)

    if not firewall_res.returncode:  # Ловим returncode = 0
        logger.info('Брандмауэр отключен')


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


# Завершает процессы, если запущенны TODO ## DEPRECATED ##
def start_taskkill():
    # run(f'taskkill /f /im {PLINK_NAME}', shell=True, stdin=PIPE, stdout=PIPE, stderr=PIPE)
    run(f'taskkill /f /im {TVNSERVER_NAME}', shell=True, stdin=PIPE, stdout=PIPE, stderr=PIPE)


# # Проверяет, запущен ли tvnserver classic (режим совместимости)
# def tvnserver_classic_running():
#     try:  # Отлов ошибки psutil
#         for proc in psutil.process_iter():
#             if TVNSERVER_CLASSIC_NAME in proc.name():
#                 return True
#
#         return False
#     except Exception as e:
#         logger.error(f'Ошибка в идентефикации процесса {TVNSERVER_CLASSIC_NAME}')


# Запускает tvnserver и возвращает объект
def start_tvnserver():
    tvnserver_process = Popen([os.path.join(ROOT_PATH, TVNSERVER_FILE_PATH), '-start', '-silent'],
                              stdin=PIPE, stdout=PIPE, stderr=PIPE)

    if not tvnserver_process.returncode:  # Если процесс запущен корректно (0)
        logger.info(f'Запущена служба {TVNSERVER_NAME}')

    return tvnserver_process


# # Создаёт plink из шаблона и возвращает объект TODO ## DEPRECATED ##
# def start_plink(command):
#     plink_process = Popen(command, shell=True, stderr=STDOUT, stdout=DEVNULL)
#
#     # Пишем log
#     if not plink_process.returncode:  # Если процесс запущен корректно (0)
#         logger.info(f'Запущенн процесс {PLINK_NAME} с идентификатором {plink_process.pid}')
#
#     return plink_process


# # Импортирует ключи реестра  TODO ## DEPRECATED ##
# def import_key():
#     run(f'reg import {os.path.join(ROOT_PATH, KEY_REG_PATH)}', shell=True, stdin=PIPE, stdout=PIPE, stderr=PIPE)


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

    logger.critical(text)  # Пишем лог
    sys.exit(0)  # Завершаем работу


# Возвращает случайный порт из списка
def choice_port(_port_list):
    return random.choice(_port_list)


# # Пишет лог о завершении child-процессов TODO ## DEPRECATED ##
# def print_restart_log(retcode, process_name, pid, restart_count):
#     if retcode:  # Если retcode не 0
#         logger.info(f'Процесс {process_name} с идентификатором {pid} завершён некорекктно (код: {retcode}), '
#                   f'произведён перезапуск. Перезапусков в сессии: {restart_count}')
#
#     else:  # Если 0
#         logger.info(f'Процесс {process_name} с идентификатором {pid} завершён, произведён перезапуск. '
#                   f'Перезапусков в сессии: {restart_count}')


# Проверяет, не запущенн ли уже client
def control_clone_client():
    runs, proc = get_client_run()  # Узнаём, запущен ли client и получаем proc (psutil)
    if runs:  # Если запущен
        proc.terminate()  # Завершение работы процесса
        logger.info(f'Попытка запуска второй копии client, процесс {proc.pid} завершён')

    write_pid_file()  # Пишем pid
    logger.info(f'Запущен client с идентификатором {os.getpid()}')  # Пишем лог


# Возвращает, запущен ли client и proc (psutil), если запущен
def get_client_run():
    if os.path.exists(PID_FILE_PATH):  # Если pid-файл существует
        with open(PID_FILE_PATH, 'r') as pid_file:
            pid_from_file = int(pid_file.read())  # Читаем pid из файла

            for proc in psutil.process_iter():  # Проходим по работающим процессам
                # Если уже запущен процесс с таким идентификатором и имя процесса совпадает с cmd (shell)
                if pid_from_file == proc.pid and PROCESS_NAME_CLIENT in proc.name():
                    return True, proc

    return False, None


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

    reg_dict = get_reg_dict()  # Получаем словрь ключей реестра и флаг первичной инициализации

    if group == GROUP_PHARMACY_INT:  # Если группа - Аптеки
        try:  # Получаем время последнего запуска
            last_run = float(reg_dict[REG_LAST_RUN_KEY])  # Получаем время последнего запуска
        except KeyError:  # Если ключа нет
            init_ip_config((pharmacy_or_subgroup, device_or_name))  # Выполняем
            set_last_run()  # Устанавливаем время последнего запуска
            init_scripts(init_tuple)  # Перевызываем функцию
            return

        if need_init_pc_config(last_run):  # Если необходимо выполнить pc_config
            init_ip_config((pharmacy_or_subgroup, device_or_name))  # Выполняем

        # Инициализация сбора данных о ККМ
        kkm_thread = Thread(target=init_kkm_thread,
                            args=(init_tuple,))  # Создаёт поток контроля данных ККМ
        kkm_thread.setName('KKMThread')  # Задаём имя потоку
        kkm_thread.start()  # Запускает поток

        # Инициализация сбора данных о дисках и бекапах
        disk_usage_thread = Thread(target=init_disk_usage_thread,
                                   args=(init_tuple,))  # Создаёт поток контроля данных о дисках и бекапах
        disk_usage_thread.setName('DiskUsageThread')  # Задаём имя потопку
        disk_usage_thread.start()  # Запускаем поток

    set_last_run()  # Устанавливаем время последнего запуска


# Инициализирует работу disk_usage скрипта
def init_disk_usage_data(init_tuple):
    pharmacy, device = init_tuple

    # Отправляем номер аптеки и устройство аргументами коммандной строки
    Popen([sys.executable, os.path.join(ROOT_PATH, SCRIPTS_DIR_NAME, DISK_USAGE_MODULE_NAME), pharmacy, device])

    logger.info(f'Был выполнен скрипт {DISK_USAGE_MODULE_NAME}')  # Пишем лог
    set_disk_usage_last_run()  # Пишем в реестр последний запуск
    time.sleep(1)  # Необходимо для корректой отработки


# Инициализирует работу kkm скрипта
def init_kkm_data(init_tuple):
    pharmacy, kassa = init_tuple

    # Отправляем номер аптеки и устройство аргументами коммандной строки
    Popen([sys.executable, os.path.join(ROOT_PATH, SCRIPTS_DIR_NAME, KKM_SCRIPT_MODULE_NAME), pharmacy, kassa])

    logger.info(f'Был выполнен скрипт {KKM_SCRIPT_MODULE_NAME}')  # Пишем лог
    set_kkm_data_last_run()  # Пишем в реестр
    time.sleep(1)  # Необходимо для корректой отработки


# Инициализирует работу ip_config скрипта
def init_ip_config(init_tuple):
    pharmacy, device = init_tuple

    # Отправляем номер аптеки и устройство аргументами коммандной строки
    Popen([sys.executable, os.path.join(ROOT_PATH, SCRIPTS_DIR_NAME, PC_CONFIG_MODULE_NAME), pharmacy, device])

    logger.info(f'Был выполнен скрипт {PC_CONFIG_MODULE_NAME}')  # Пишем лог
    time.sleep(1)  # Необходимо для корректой отработки


# Возращает, необходимо ли инициализировать pc_config, искходя из времени последнего запуска
def need_init_pc_config(last_run):
    now = time.time()  # Текущее время (с начала эпохи)
    uptime = psutil.boot_time()  # Время, которе запущена ОС

    # Если после перезагрузки не было сканирования
    if now - last_run > now - uptime:
        return True
    else:
        return False


# Проверяет, необходимо ли выполнить сбор данных о ККМ
def need_init_kkm_data(last_run):
    now = time.time()  # Текущее время (с начала эпохи)

    # Если время прошедшее с отправки меньше, чем зарегестрированное
    if now - last_run > MINUTES_BEFORE_INIT_KKM_DATA * 60:
        return True
    else:
        return False


# Проверяет, необходимо ли выполнить сбор данных о дисках и бекапах
def need_init_disk_usage(last_run):
    now = time.time()  # Текущее время (с начала эпохи)

    # Если время прошедшее с отправки меньше, чем зарегестрированное
    if now - last_run > MINUTES_BEFORE_INIT_DISK_USAGE * 60:
        return True
    else:
        return False


# Поток контроля отправки данных о ККМ
def init_kkm_thread(init_tuple):
    group, pharmacy_or_subgroup, device_or_name = init_tuple

    # Проверка инициализации kkm_data
    if device_or_name in KASSA_DICT.values():  # Если устройство есть в списке необходимых
        while True:
            reg_dict = get_reg_dict()  # Получаем словрь ключей реестра и флаг первичной инициализации

            try:
                last_run = float(reg_dict[REG_LAST_RUN_KKM_DATA_KEY])  # Получаем время последнего запуска
            except KeyError:  # Если запись в реестре отсутсвует
                init_kkm_data((pharmacy_or_subgroup, device_or_name))  # Инициализируем сбор данных
                continue

            need = need_init_kkm_data(last_run)
            if need:  # Если необходимо выполнить kkm_data
                init_kkm_data((pharmacy_or_subgroup, device_or_name))  # Инициализируем сбор данных
                logger.info(f'Сбор данных о ККМ по тикету')

            time.sleep(600)  # Засыпает на 10 минут

    else:  # Инициализация потока не требуется
        return


# Поток контроля отправки данных о дисках и бекапах
def init_disk_usage_thread(init_tuple):
    group, pharmacy_or_subgroup, device_or_name = init_tuple

    while True:
        reg_dict = get_reg_dict()  # Получаем словрь ключей реестра и флаг первичной инициализации

        try:
            last_run = float(reg_dict[REG_LAST_RUN_DISK_USAGE])  # Получаем время последнего запуска
        except KeyError:  # Если запись в реестре отсутсвует
            init_disk_usage_data((pharmacy_or_subgroup, device_or_name))  # Инициализируем сбор данных
            continue

        if need_init_disk_usage(last_run):  # Если необходимо выполнить disk_usage
            init_disk_usage_data((pharmacy_or_subgroup, device_or_name))  # Инициализируем сбор данных
            logger.info(f'Сбор данных о дисках и бекапах по тикету')

        time.sleep(600)  # Засыпает на 10 минут


# Завершат программу, предварительно завершив сопровождающий софт
def client_correct_exit(ex):
    start_taskkill()  # Завершаем сопровождающий софт
    raise ex  # Вызываем исключение


# Завепшает работу клиента по причине многократного перезапуска plink-a
def exit_because_plink():
    logger.info(f'Клиент завершил работу по причине многокраного перезапуска {PLINK_NAME} (более '
                f'{MAX_COUNT_RESTART_PLINK} раз).\n'
                f'Возможно, у вас не прописаны исключения антивируса, либо {PLINK_NAME} добавлен в карантин.\n'
                f'Проверьте корректность настроек антивируса и повторите запуск.')
    client_correct_exit(RestartPlinkCountException)  # Передаём исключение


# Новый способ подключения поредством SSH
async def new_ssh_connection(*, ssh_host=None, ssh_port=None, serv_port=None, local_port=None,
                             ssh_username=None, ssh_password=None):
    async with asyncssh.connect(
            ssh_host,
            port=ssh_port,
            username=ssh_username,
            password=ssh_password,
            known_hosts=None  # Отключить проверку на ключи
    ) as conn:
        conn.set_keepalive(5 * 60, 3)  # Устанавливаем keepalive в 5 минут c 3мя попытками
        listener = await conn.forward_remote_port('', serv_port, 'localhost', local_port)  # Пробрасываем порт
        logger.info(f'Проброс порта {listener.get_port()} на {ssh_host} к локальному порту {local_port}')
        await listener.wait_closed()  # Ожидаем закрытия


# Возвращает адрес сервера (используется в settings)
def get_host():
    if not os.path.exists(CONFIG_FILE_PATH):  # Если файла конфигурации не существует
        return DEFAULT_HOST  # Возвращаем предустановленное значение

    config = configparser.ConfigParser()
    config.read(CONFIG_FILE_PATH)  # Читаем файл конфигурации

    host = config.get(CONNECT_SECTION, HOST_PHARM)  # Считываем параметр адреса сервера

    return host


# Создаёт конфиг
def create_config():
    config = configparser.ConfigParser()

    # Секция APP
    config.add_section(APP_SECTION)

    config.set(APP_SECTION, GROUP_PHARM, str(0))  # Группа
    config.set(APP_SECTION, PHARMACY_OR_SUBGROUP_PHARM, '')  # Аптека или Подгруппа
    config.set(APP_SECTION, DEVICE_OR_NAME_PHARM, '')  # Устройство или Имя

    # Секция CONNECT
    config.add_section(CONNECT_SECTION)

    config.set(CONNECT_SECTION, HOST_PHARM, DEFAULT_HOST)  # Адрес сервера (пишем предустановленный)

    with open(CONFIG_FILE_PATH, 'w') as config_file:  # Создаём файл конфигурации
        config.write(config_file)  # Записываем


# Инициализация конфига
def init_config():
    if not os.path.exists(CONFIG_FILE_PATH):  # Если файла конфигурации не существует
        create_config()  # Создаём файл конфигурации

        print_incorrect_settings(f'Файл конфигурации {CONFIG_NAME} отсутсвовал\n'
                                 'Он был создан по пути:\n'
                                 f'{CONFIG_FILE_PATH}\n\n'
                                 'Перед последующим запуском проинициализируйте его вручную, либо посредством '
                                 'утилиты "Настройка клиента"', stand_print=False)

    config = configparser.ConfigParser()
    config.read(CONFIG_FILE_PATH)  # Читаем файл конфигурации

    # App
    group = int(config.get(APP_SECTION, GROUP_PHARM))
    pharmacy_or_subgroup = config.get(APP_SECTION, PHARMACY_OR_SUBGROUP_PHARM)
    device_or_name = config.get(APP_SECTION, DEVICE_OR_NAME_PHARM)

    # Connect
    host = config.get(CONNECT_SECTION, HOST_PHARM)

    # Проверяет корректность параметров файла конфигурации
    init_correct_config_parm(group, pharmacy_or_subgroup, device_or_name)

    return host, group, pharmacy_or_subgroup, device_or_name
