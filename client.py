import loader
import os

import json
import time
from subprocess import run, PIPE, Popen

from values import *
from fun import *

import random
import socket

# Порты демонов port_demon
PORT_DEMON_ONE_PORT = 14421
PORT_DEMON_TWO_PORT = 14422
PORT_DEMON_THREE_PORT = 14423
PORT_DEMON_FOUR_PORT = 14424
PRIVKI = 'Привки'

# Кортеж портов
# TODO Сделать для config
PORT_LIST = (PORT_DEMON_ONE_PORT, PORT_DEMON_TWO_PORT, PORT_DEMON_THREE_PORT, PORT_DEMON_FOUR_PORT)

HOST = '85.143.156.89'  # Адрес сервера

GROUP = 0
PHARMACY_OR_SUBGROUP = ''
DEVICE_OR_NAME = ''


# Создаёт конфиг
def create_config():
    config = configparser.ConfigParser()

    # Секция APP
    config.add_section(APP_SECTION)

    config.set(APP_SECTION, GROUP_PHARM, str(GROUP))
    config.set(APP_SECTION, PHARMACY_OR_SUBGROUP_PHARM, PHARMACY_OR_SUBGROUP)
    config.set(APP_SECTION, DEVICE_OR_NAME_PHARM, DEVICE_OR_NAME)

    # Секция CONNECT
    config.add_section(CONNECT_SECTION)

    config.set(CONNECT_SECTION, HOST_PHARM, HOST)
    # config.set(CONNECT_SECTION, PORT_DEMON_PHARM, str(SRV_PORT))

    with open(CONFIG_NAME, 'w') as config_file:
        config.write(config_file)


# Инициализация конфига
def init_config():
    global GROUP, PHARMACY_OR_SUBGROUP, DEVICE_OR_NAME, HOST

    if not os.path.exists(CONFIG_NAME):  # Если файла конфигурации не существует
        create_config()  # Создаём файл конфигурации

        print_incorrect_settings('Файл конфигурации settings.ini отсутсвовал\n'
                                 'Он был создан по пути:\n'
                                 f'{ROOT_PATH}\n\n'
                                 'Перед последующим запуском проинициализируйте его вручную, либо посредством '
                                 'утилиты "Настройки клиента"', stand_print=False)

    config = configparser.ConfigParser()
    config.read(CONFIG_NAME)  # Читаем файл конфигурации

    # App
    GROUP = int(config.get(APP_SECTION, GROUP_PHARM))
    PHARMACY_OR_SUBGROUP = config.get(APP_SECTION, PHARMACY_OR_SUBGROUP_PHARM)
    DEVICE_OR_NAME = config.get(APP_SECTION, DEVICE_OR_NAME_PHARM)

    # Connect
    HOST = config.get(CONNECT_SECTION, HOST_PHARM)
    # SRV_PORT = config.get(CONNECT_SECTION, PORT_DEMON_PHARM)


# # Актуализация параметров для обоих групп
# def actual_parm_for_all():
#     global SRV_PORT
#
#     # Проверка на целочисленность порта
#     try:
#         SRV_PORT = int(SRV_PORT)
#     except ValueError:
#         print_incorrect_settings('Некорректный номер порта')


# Проверяет актуальность параметров для аптек
def actual_parm_for_pharmacy():  # TODO
    device_list = ['0', '1', '2', '3', '4', '5', '99']

    # Временно. Защита MySQL
    if not PHARMACY_OR_SUBGROUP.isdigit():
        print_incorrect_settings('Номер аптеки должен быть целым числом')

    # Защита UNSIGNED INT на сервере
    if int(PHARMACY_OR_SUBGROUP) >= 65535:
        print_incorrect_settings('Некорректный номер аптеки')

    # Проверка на соответсвие списка устройств
    if DEVICE_OR_NAME not in device_list:
        print_incorrect_settings('Неккоректное устройсво\n'
                                 'Допустимый диапазон устройств:\n'
                                 f'{device_list}')


# Прверяет актуальность параметров для офиса
def actual_pharm_for_office():
    if len(PHARMACY_OR_SUBGROUP) > 80:
        print_incorrect_settings('Наименование подгруппы не должно превышать 80 символов')

    if len(DEVICE_OR_NAME) > 80:
        print_incorrect_settings('Имя не должно превышать 80 символов')


# Выбирает порт из списка и возращает
def choice_port():
    port_choice = random.choice(PORT_LIST)

    return port_choice


init_config()  # Инициализируем config

# actual_parm_for_all()  # Актуализируем основные параметры

if GROUP == GROUP_PHARMACY_INT:  # Если группа - аптека
    # print('Аптека', PHARMACY_OR_SUBGROUP, DEVICE_OR_NAME, HOST, SRV_PORT)

    actual_parm_for_pharmacy()  # Проверяем актуальность параметров

elif GROUP == GROUP_OFFICE_INT:  # Если группа - офис
    # print('Офис', PHARMACY_OR_SUBGROUP, DEVICE_OR_NAME, HOST, SRV_PORT)

    actual_pharm_for_office()

else:  # Если группа - неккорекктна
    print('Неверная группа')

control_clone_client()  # Проверям, не запущенн ли уже

try:  # Отлов закрытия сокета
    while True:
        try:  # Отлов ошибок
            start_client()  # Выполняем подготовку

            init_dict = {GROUP_KEY: GROUP, PHARMACY_KEY: PHARMACY_OR_SUBGROUP,
                         DEVICE_KEY: DEVICE_OR_NAME}  # Словарь инициализации
            hello_dict = get_hello_dict(PORT_MODE, init_dict)  # Получаем словарь приветствия с init_dict

            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

            port_conn = choice_port()  # Получаем случайный порт
            sock.connect((HOST, port_conn))  # Подключение к серверу

            print_log(f'Произведено подключение к серверу {HOST} по порту {port_conn}')  # Пишем лог

            # TODO Асинхронность
            timeout = random.randint(20, 30)  # Таймаут в очереди от 20 до 30 секунд (чтоб не DDOS-ить)
            sock.settimeout(timeout)  # Ставим таймаут в очереди

            sock.send(hello_dict.encode())  # Отправка словаря приветсвия на сервер

            connect_dict = get_data_from_socket(sock)  # Получаем словарь подключения

            port = connect_dict[PORT_KEY]  # Выделенный порт
            vnc_port = connect_dict[VNC_PORT_KEY]  # Порт VNC
            ssh_port = connect_dict[SSH_PORT_KEY]  # Порт SSH
            user = connect_dict[USER_KEY]  # Логин
            password = connect_dict[PASSWORD_KEY]  # Пароль
            server = connect_dict[SERVER_KEY]  # Хост

            print_log(f'Получен порт {port} для прокидывания SSH со стороны сервера')

            # Прокидываем порт VNC
            command = [os.path.join(ROOT_PATH, PLINK_FILE_PATH), '-N', '-R', f'{port}:localhost:{vnc_port}', '-P',
                       f'{ssh_port}', '-pw', f'{password}', '-l', f'{user}', '-batch', f'{server}']

            # Создаём процесс plink.exe
            plink_process = start_plink(command)

            if not plink_process.returncode:  # Если процесс запущен корректно
                print_log(f'Запущенн процесс {PLINK_NAME} с идентификатором {plink_process.pid}')

            while True:  # Следим

                if plink_process.poll():  # Если процесс почему-то завершён
                    print_log(f'Процесс {PLINK_NAME} с идентификатором {plink_process.pid} завершён некорекктно, '
                              f'произведён перезапуск')
                    break

                time.sleep(15)  # Каждые 15 секунд проверяем, запущен ли plink

        except socket.timeout:  # Ловим timeout
            print_log(f'Подключение к серверу {HOST} по порту {port_conn} превысило время ожидания в {timeout} секунд')

        except ConnectionRefusedError:  # Подключение сброшенно со стороны сервера
            print_log(f'Подлючение к серверу {HOST} по порту {port_conn} было сброшенно со стороны сервера')

            sleep_time = random.randint(5, 20)  # Ставим время от 5 до 20 для повторного подключения
            time.sleep(sleep_time)
finally:
    sock.close()
