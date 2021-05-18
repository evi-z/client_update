import json
import socket
import configparser

from values import *

# TODO Зависимость от config
HOST = '85.143.156.89'
SQL_DEMON_PORT = 12342
PRIVETIK = 'ТЕСТ АПДЕЙТА'


# Возвращает данные в JSON формате с EOF
def get_data_for_send(data):
    data_json = json.dumps(data) + EOF  # Кодирует данные в JSON с EOF
    data_json_encode = data_json.encode()  # Преобразует в byte для отправки

    return data_json_encode


# Создаёт словарь приветствия и кодирует в JSON
def get_hello_dict(mode, data=None):
    hello_dict = {MODE_DICT_KEY: mode,
                  DATA_DICT_KEY: data}

    hello_json = json.dumps(hello_dict) + EOF  # Кодируем в JSON с EOF

    return hello_json


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
    data = json.loads(data_json)  # Декодируем из JSON

    return data


# Получает короткий словарь
def connect_to_sql():
    try:
        hello_dict = get_hello_dict(SETTINGS_MODE)  # Получаем словарь приветсвия дял SETTINGS_MODE

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((HOST, SQL_DEMON_PORT))

        sock.send(hello_dict.encode())

        """
       Структура словаря:
       {'pharmacy_dict': {Аптека: [Устройство, Устройство, ...], ...},
        'office_dict':   {Подгруппа: [Имя, Имя, ...], ...}}
       """
        table = get_data_from_socket(sock)  # Получаем краткий словарь

        pharmacy_dict = table[PHARMACY_DICT_KEY]  # Краткий словарь аптек
        office_dict = table[OFFICE_DICT_KEY]  # Краткий словарь офиса

        print(pharmacy_dict, office_dict)
        return pharmacy_dict, office_dict

    finally:
        sock.close()


# Создаёт settings.ini
def createConfig(group, pharmacy, device):
    config = configparser.ConfigParser()
    config.add_section(APP_SECTION)
    config.set(APP_SECTION, GROUP_PHARM, group)
    config.set(APP_SECTION, PHARMACY_OR_SUBGROUP_PHARM, pharmacy)
    config.set(APP_SECTION, DEVICE_OR_NAME_PHARM, device)

    config.add_section(CONNECT_SECTION)
    config.set(CONNECT_SECTION, HOST_PHARM, HOST)
    config.set(CONNECT_SECTION, PORT_DEMON_PHARM, str(PORT_DEMON_PORT))

    with open(CONFIG_NAME, 'w') as config_file:
        config.write(config_file)

