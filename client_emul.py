import json
import time
from subprocess import run, PIPE, Popen

from values import *
from fun import *

import socket
import os


HOST = '85.143.156.89'  # Адрес сервера
SRV_PORT = 14422  # Порт подключения

try:

    print('Эмуляция client\n')
    print('0. Аптеки\n'
          '1. Офис\n\n')

    while True:
        GROUP = int(input('#: '))

        if GROUP == 0:
            PHARMACY_OR_SUBGROUP = input('Аптека: ')
            DEVICE_OR_NAME = input('Устройство: ')
            break

        elif GROUP == 1:
            PHARMACY_OR_SUBGROUP = input('Подгруппа: ')
            DEVICE_OR_NAME = input('Имя: ')
            break

    init_dict = {GROUP_KEY: GROUP, PHARMACY_KEY: PHARMACY_OR_SUBGROUP,
                 DEVICE_KEY: DEVICE_OR_NAME}  # Словарь инициализации
    hello_dict = get_hello_dict(PORT_MODE, init_dict)  # Получаем словарь приветствия с init_dict

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((HOST, SRV_PORT))  # Подключение к серверу

    sock.send(hello_dict.encode())  # Отправка словаря приветсвия на сервер

    connect_dict = get_data_from_socket(sock)  # Получаем словарь подключения

    port = connect_dict[PORT_KEY]  # Выделенный порт
    vnc_port = connect_dict[VNC_PORT_KEY]  # Порт VNC
    ssh_port = connect_dict[SSH_PORT_KEY]  # Порт SSH
    user = connect_dict[USER_KEY]  # Логин
    password = connect_dict[PASSWORD_KEY]  # Пароль
    server = connect_dict[SERVER_KEY]  # Хост

    # Прокидываем порт VNC
    command = [os.path.join(os.getcwd(), PLINK_FILE_PATH), '-N', '-R', f'{port}:localhost:{vnc_port}', '-P',
               f'{ssh_port}', '-pw', f'{password}', '-l', f'{user}', '-batch', f'{server}']

    # Создаём процесс plink.exe
    run(command)

    os.system('pause')
finally:
    sock.close()



