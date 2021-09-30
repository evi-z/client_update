import os
import platform
import sys

import cpuinfo
import psutil
import ctypes
import socket
import json
from subprocess import run, PIPE

from scripts_fun import *

logger = get_logger(__name__)  # Инициализируем logger


# Ключи словаря приветствия
MODE_DICT_KEY = 'mode'
DATA_DICT_KEY = 'data'

EOF = '#'

# TODO Здоровенный
HOST = '85.143.156.89'
CONFIGURATION_DEMON_PORT = 11617

CONFIGURATION_MODE = 'configuration'


# Удаляет все пустые элементыв списке
def remove_simple_element(ls):
    while True:
        try:
            ls.remove('')
        except ValueError:
            return


# Преобразует байты в гигабайты
def bytes_to_gb(byte):
    M = 1024 ** 3

    return byte/M


# Оптимизирует вывод PowerShell
def optimize_power_shell_inp(str_out):
    str_sp = str_out.split('\r\n\r\n')
    remove_simple_element(str_sp)

    return str_sp


# Преобразует вывод PowerShell в список кортежей
def ps_inp_ram_type_to_list(str_out):
    ls_out = optimize_power_shell_inp(str_out)

    tupl_list_out = []
    for el in ls_out:
        sp = el.split(':')
        name = sp[0].strip()
        data = sp[1].strip()

        tupl_list_out.append((name, data))

        return tupl_list_out


# Преобразует вывод информации о дисках в список кортежей
def ps_inp_disk_data_to_list(str_out):
    ls_out = optimize_power_shell_inp(str_out)
    ls_out = [el.split('\r\n') for el in ls_out]

    tupl_list_out = []
    for disk in ls_out:
        tupl_curr_disk = []

        for parm in disk:
            sp = parm.split(':')
            name = sp[0].strip()
            data = sp[1].strip()

            tupl_curr_disk.append((name, data))

        tupl_list_out.append(tupl_curr_disk)

    return tupl_list_out


# Создаёт словарь приветствия и кодирует в JSON
def get_hello_dict(mode, data=None):
    hello_dict = {MODE_DICT_KEY: mode,
                  DATA_DICT_KEY: data}

    hello_json = json.dumps(hello_dict) + EOF  # Кодируем в JSON с EOF

    return hello_json


def send_configuration_data(config_dict):
    hello_dict = get_hello_dict(CONFIGURATION_MODE, config_dict)

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((HOST, CONFIGURATION_DEMON_PORT))

    sock.send(hello_dict.encode())

    sock.close()


# Возвращает список аргументов коммандной строки
def get_argv_list(argv):
    if argv[1:]:  # Если есть аргументы коммандной строки
        argv_list = argv[1:]  # Исключаем первый элемент

        return argv_list

    else:  # Если нет, возвращаем пустой список
        sys.exit(0)


arg = get_argv_list(sys.argv)  # Получаем список аргументов командной строки

pharmacy = arg[0]
device = arg[1]

logger.info(f'Скрипт {get_basename(__file__)} начал работу')

# Ключи словаря конфигурации
PHARMACY_DICT_KEY = 'pharmacy'
DEVICE_DICT_KEY = 'device'

RAM_DICT_KEY = 'ram'
RAM_TYPE_DICT_KEY = 'ram_type'
SWAP_DICT_KEY = 'swap'
MEMORY_DICT_KEY = 'memory'
DISK_DATA_DICT_KEY = 'disk_data'
SCREEN_RESOLUTION_DICT_KEY = 'screen_resolution'
PLATFORM_DICT_KEY = 'platform'
CPU_DICT_KEY = 'cpu'
PC_NAME = 'pc_name'

#  ОЗУ и Диски
ram = psutil.virtual_memory().total  # Оперативная память (Байты)
swap = psutil.swap_memory().total  # Файл подкачки


ram = round(bytes_to_gb(ram))
swap = round(bytes_to_gb(swap))

# Тип ОЗУ
# command = 'PowerShell "Get-WmiObject Win32_PhysicalMemory | fl MemoryType, SMBIOSMemoryType'
command = 'PowerShell "Get-WmiObject Win32_PhysicalMemory | fl SMBIOSMemoryType'
res = run(command, shell=True, stdout=PIPE, stdin=PIPE, stderr=PIPE)

ram_type = res.stdout.decode()
ram_type = ps_inp_ram_type_to_list(ram_type)

# Память со всех томов
memory = 0
for disk in psutil.disk_partitions():
    disk_name = disk.device
    try:
        memory += psutil.disk_usage(disk_name).total
    except OSError:
        pass

memory = round(bytes_to_gb(memory))

# Тип логических дисков и их размеры
command = 'PowerShell "Get-PhysicalDisk | fl -Property MediaType, Size, FriendlyName"'
res = run(command, shell=True, stdout=PIPE, stdin=PIPE, stderr=PIPE)

disk_data = res.stdout.decode()
disk_data = ps_inp_disk_data_to_list(disk_data)

# Разрешение экрана
horizontal = ctypes.windll.user32.GetSystemMetrics(0)
vertical = ctypes.windll.user32.GetSystemMetrics(1)
screen_resolution = f'{horizontal}x{vertical}'

# Платформа
platform_ver = platform.win32_ver()

# Процессор
try:  # Какая-то ошибка?
    cpu = cpuinfo.get_cpu_info()['brand_raw']
except KeyError:
    cpu = 'Unknown'

pc_name = platform.node()  # Имя компьютера

configuration_dict = {
    PHARMACY_DICT_KEY: pharmacy,
    DEVICE_DICT_KEY: device,
    RAM_DICT_KEY: ram,
    RAM_TYPE_DICT_KEY: ram_type,
    SWAP_DICT_KEY: swap,
    MEMORY_DICT_KEY: memory,
    DISK_DATA_DICT_KEY: disk_data,
    SCREEN_RESOLUTION_DICT_KEY: screen_resolution,
    PLATFORM_DICT_KEY: platform_ver,
    CPU_DICT_KEY: cpu,
    PC_NAME: pc_name
}

try:
    send_configuration_data(configuration_dict)  # Отправляет данные на сервер
except (ConnectionRefusedError, ConnectionResetError):
    logger.error(f'Скрипт {get_basename(__file__)} не смог отправить данные на север')
