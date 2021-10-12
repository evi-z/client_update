import logging
import subprocess
import time
from datetime import datetime
from datetime import time as dtime
import winreg as reg
from subprocess import run, Popen, PIPE, STDOUT, DEVNULL
from threading import Thread
import json
import configparser
import socket
import random
import sys
import os
import asyncio

from bin.values import *
from funs.low_level_fun import *
from errors import *
from objects import *

logger = get_logger(__name__)  # TODO Переделать под SettingObj

for _ in range(2):  # 2 попытки
    try:  # Отлов отстутвия загружаемых модулей
        import psutil
        import asyncssh

        break
    except ModuleNotFoundError as e:
        from library_control import *
        lib_control = LibraryControl(
            logger_name=__name__,
            root_file_path=os.path.join(ROOT_PATH, CLIENT_MODULE_NAME)
        )

        lib_control.check_app_lib_install()  # Проверяем, установлены ли библиотеки


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
    hello_dict = {
        MODE_DICT_KEY: mode,
        DATA_DICT_KEY: data
    }

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
    # Импотрируем настройки в реестр
    path_to_reg_file = os.path.join(ROOT_PATH, VNC_SERVICE_REG_FILE)  # Полный путь к файлу

    # НЕ ТРОГАЙ ЭТОТ КОД! ОН РАБОТАЕТ ТОЛЬКО С DEVNULL, ИНЧАЕ ВИСНИТ ТУТ
    run(f'reg import "{path_to_reg_file}"', shell=True, stdout=DEVNULL, stderr=STDOUT)

    tvns_file = os.path.join(ROOT_PATH, TVNSERVER_FILE_PATH)  # Абсолютный путь к tvns
    # СЛУЖБА НЕ РЕГИСТРИРУЕТСЯ БЕЗ ПРАВ АДМИНИСТРАТОРА !
    run([tvns_file, '-reinstall', '-silent'], stderr=PIPE, stdout=PIPE, stdin=PIPE)  # Регистрируем службу


# Инициализирует всевозможные обращения к коммандной строке
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
    start_taskkill()  # Завершает процесс tvnserver


# Завершает процессы, если запущенны
def start_taskkill():
    run(f'taskkill /f /im {TVNSERVER_NAME}', shell=True, stdin=PIPE, stdout=PIPE, stderr=PIPE)


# Запускает tvnserver и возвращает объект
def start_tvnserver():
    tvnserver_process = Popen([os.path.join(ROOT_PATH, TVNSERVER_FILE_PATH), '-start', '-silent'],
                              stdin=PIPE, stdout=PIPE, stderr=PIPE)

    if not tvnserver_process.returncode:  # Если процесс запущен корректно (0)
        logger.info(f'Запущена служба {TVNSERVER_NAME}')


# Возвращает случайный порт из списка
def choice_port(_port_list):
    return random.choice(_port_list)


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


def init_scripts(configuration: ConfigurationsObject):
    try:
        comm = 'python -m pip install pypiwin32'
        module_named = 'pywin32'

        subprocess.run(comm, shell=True, stderr=DEVNULL, stdout=DEVNULL)
        configuration.settings.library_install(module_named)
    except Exception:
        pass

    # pc_config
    pc_config = PcConfigScript(configuration_obj=configuration)  # Объект скрипта pc_config
    if pc_config.need_init_script():  # Если необходим запуск скрипта
        pc_config.run()  # Запускаем

    # kkm
    kkm = KKMScript(configuration_obj=configuration)  # Объект скрипта kkm
    if kkm.need_init_script():  # Если необходим запуск скрипта
        kkm.start_thread()  # Запускает поток

    # disk_usage
    disk_usgae = DiskUsageScript(configuration_obj=configuration)  # Объект скрипта disk_usage
    if disk_usgae.need_init_script():
        disk_usgae.start_thread()

    # regular
    regular = RegularScript(configuration_obj=configuration)  # Объект скрипта regular
    if regular.need_init_script():
        regular.start_thread()  # Запускаем поток

    # sheduler
    app_sheduler = AppScheduler(configuration_obj=configuration)
    if app_sheduler.need_init_script():
        app_sheduler.start_thread()  # Запускаем поток


# Завершат программу, предварительно завершив сопровождающий софт
def client_correct_exit(ex):
    start_taskkill()  # Завершаем сопровождающий софт
    raise ex  # Вызываем исключение


# Новый способ подключения поредством SSH
async def new_ssh_connection(*, ssh_host=None, ssh_port=None, serv_port=None, local_port=None,
                             ssh_username=None, ssh_password=None, check_bd_demon_port=None, init_dict=None):
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
        # Переодично проверяет, есть ли запись в БД
        await check_writing_in_database(conn, ssh_host=ssh_host, check_bd_demon_port=check_bd_demon_port,
                                        init_dict=init_dict)
        await listener.wait_closed()  # Ожидаем закрытия


# Связывается с сервером и проверяет, есть ли запись в БД
async def check_writing_in_database(conn, *, ssh_host=None, check_bd_demon_port=None, init_dict=None):
    while True:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            sock.connect((ssh_host, check_bd_demon_port))  # Подключение к серверу

            # Создаём словарь с режимом check_bd и словарём описания
            send_data = get_hello_dict(CHECK_BD_MODE, init_dict)
            sock.send(send_data.encode())  # Отправка словаря приветсвия на сервер

            online_status = get_data_from_socket(sock)  # Статус записи в БД

            if not online_status:  # Если не в сети
                conn.disconnect(asyncssh.DISC_BY_APPLICATION, '')  # Закрываем соединение (на всякий)
                raise ReconnectForRewriteDBException  # Вызываем исключение
        except (ConnectionRefusedError, ConnectionResetError):  # Если DB демон не работает
            logger.warning('Удалённая проверка наличия в БД не удалась')

        await asyncio.sleep(MINUTES_BEFORE_CHECK_DB_WRITING * 60)


# Возвращает адрес сервера (используется в settings)
def get_host():
    if not os.path.exists(CONFIG_FILE_PATH):  # Если файла конфигурации не существует
        return DEFAULT_HOST  # Возвращаем предустановленное значение

    config = configparser.ConfigParser()
    config.read(CONFIG_FILE_PATH)  # Читаем файл конфигурации

    host = config.get(CONNECT_SECTION, HOST_PHARM)  # Считываем параметр адреса сервера

    return host


# Инициализация конфига
def init_config(settings: SettingsObject):
    # Инициализируем объект посредством файла конфигурации
    configuration_obj = ConfigurationsObject.init_from_config_file(settings=settings)  # Объект конфигурации
    configuration_obj.check_correct_config_parm()  # Проверяет актуальность параметров

    return configuration_obj
