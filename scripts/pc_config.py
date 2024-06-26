import os
import platform
import sys
from pathlib import Path

import cpuinfo
import psutil
import ctypes
import socket
import json
import subprocess
from subprocess import run, PIPE

import requests

from scripts_fun import *

logger = get_logger(__name__)  # Инициализируем logger


# Ключи словаря приветствия
MODE_DICT_KEY = 'mode'
DATA_DICT_KEY = 'data'

EOF = '#'


PAGE_DISK_USAGE_DATA = '/vnc_monitoring/'


# Удаляет все пустые элементы в списке
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
    error = []
    try:
        for el in ls_out:
            sp = el.split(':')
            name = sp[0].strip()
            data = sp[1].strip()
            tupl_list_out.append((name, data))
            return tupl_list_out
    except IndexError:
        return error


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


# Возвращает текущий адрес хоста
def get_host():
    path_to_config = Path(__file__).parent.parent.resolve().joinpath(CONFIG_NAME)
    if not path_to_config.is_file():
        logger.error(f'Не обнаружен файл конфига {CONFIG_NAME}')
        sys.exit(1)

    config = configparser.ConfigParser()
    config.read(path_to_config)
    host = config.get('Connect', 'host')  # Не динамические параметры ...

    return host.strip()


# Отправляет данные на сервер
def send_data(config_dict: dict):
    host = get_host()
    url = 'http://' + host + PAGE_DISK_USAGE_DATA

    response = requests.post(url, json=config_dict)
    logger.info(f'Данные о мониторинге отправлены по адресу {url} ({response.status_code})')


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
MOTHERBOARD_DICT_KEY = 'mother'
DRIVER_DICT_KEY = 'version'
ONE_S_VERSION_DICT_KEY = 'one_s_version'
ARCHITECTURE_DICT_KEY = 'architecture'
NET_SPEED_DICT_KEY = 'net_speed'


def main():
    # Узнаем версию драйвера ККТ
    try:
        program_files_86 = os.environ.get('ProgramFiles(x86)', '')
        program_files = os.environ.get('ProgramW6432', '')

        if os.path.exists(os.path.join(program_files_86, r'SHTRIH-M\DrvFR5\Bin\DrvFR.dll')):
            path_to_drvr = os.path.join(program_files_86, r'SHTRIH-M\DrvFR5\Bin\DrvFR.dll')
            path_to_drvr = path_to_drvr.replace('\\', '\\\\')
        elif os.path.exists(os.path.join(program_files, r'SHTRIH-M\DrvFR5\Bin\DrvFR.dll')):
            path_to_drvr = os.path.join(program_files, r'SHTRIH-M\DrvFR5\Bin\DrvFR.dll')
            path_to_drvr = path_to_drvr.replace('\\', '\\\\')
        else:
            path_to_drvr = None

        if path_to_drvr is not None:
            version_command = fr'wmic datafile where name="{path_to_drvr}" get version /value'
            version = str(subprocess.check_output(version_command, shell=True)).split('\\n')[2].replace('\\r', '').split('=')[1].split('\\')[0]
        else:
            version = 'Undefined'
    except Exception:
        version = 'Undefined'

    # Узнаем версию 1С
    try:
        program_files_86 = os.environ.get('ProgramFiles(x86)', '')
        program_files = os.environ.get('ProgramW6432', '')

        if os.path.exists(os.path.join(program_files_86, r'1cv8\common\1cestart.exe')):
            path_to_one_s = os.path.join(program_files_86, r'1cv8\common\1cestart.exe')
            path_to_one_s = path_to_one_s.replace('\\', '\\\\')
        elif os.path.exists(os.path.join(program_files, r'1cv8\common\1cestart.exe')):
            path_to_one_s = os.path.join(program_files, r'1cv8\common\1cestart.exe')
            path_to_one_s = path_to_one_s.replace('\\', '\\\\')
        else:
            path_to_one_s = None

        if path_to_one_s is not None:
            version_command = fr'wmic datafile where name="{path_to_one_s}" get version /value'
            one_s_version = str(subprocess.check_output(version_command, shell=True)).split('\\n')[2].replace('\\r', '').split('=')[1].split('\\')[0]
        else:
            one_s_version = 'Undefined'
    except Exception:
        one_s_version = 'Undefined'

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
    command = 'PowerShell "Get-PhysicalDisk | fl -Property MediaType, Size, FriendlyName, BusType"'
    res = run(command, shell=True, stdout=PIPE, stdin=PIPE, stderr=PIPE)

    disk_data = res.stdout.decode()
    disk_data = ps_inp_disk_data_to_list(disk_data)

    # Разрешение экрана
    horizontal = ctypes.windll.user32.GetSystemMetrics(0)
    vertical = ctypes.windll.user32.GetSystemMetrics(1)
    # Узнаем название монитора
    try:
        monitor_name_command = 'wmic desktopmonitor get Name /value'
        monitor_name = str(subprocess.check_output(monitor_name_command, shell=True)).split('\\n')[2].replace('\\r', '').split('=')[1].split('\\')[0]

    except Exception:
        monitor_name = ''
    screen_resolution = f'{horizontal}x{vertical} {monitor_name}'

    # Платформа
    platform_ver = platform.win32_ver()
    try:
        arch_command = 'wmic os get osarchitecture /value'
        platform_arch = str(subprocess.check_output(arch_command, shell=True)).split('\\n')[2].replace('\\r', '').split('=')[1].split('\\')[0]
        friendly_arch = f'x{platform_arch[:-1]}'
    except Exception:
        friendly_arch = 'Unknown'

    # Скорость сети
    try:
        net_command = 'wmic NIC where NetEnabled=true get Speed /value'
        net_speed = str(subprocess.check_output(net_command, shell=True)).split('\\n')[2].replace('\\r', '').split('=')[1]
        friendly_net_speed = int(net_speed) // 1000000
    except Exception:
        friendly_net_speed = None

    # Материнская плата
    try:
        man_moth = 'WMIC BASEBOARD GET Manufacturer /VALUE'.split()
        manufacturer = str(subprocess.check_output(man_moth, shell=True)).split('\\n')[2].replace('\\r', '').split('=')[1]
        prod_moth = 'WMIC BASEBOARD GET Product /VALUE'.split()
        product = str(subprocess.check_output(prod_moth, shell=True)).split('\\n')[2].replace('\\r', '').split('=')[1]
        mother = manufacturer + ' ' + product
    except Exception:
        mother = 'Unknown'

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
        PC_NAME: pc_name,
        MOTHERBOARD_DICT_KEY: mother,
        DRIVER_DICT_KEY: version,
        ONE_S_VERSION_DICT_KEY: one_s_version,
        ARCHITECTURE_DICT_KEY: friendly_arch,
        NET_SPEED_DICT_KEY: friendly_net_speed
    }

    try:
        send_data(configuration_dict)  # Отправляет данные на сервер
    except Exception:
        logger.error(f'Скрипт {get_basename(__file__)} не смог отправить данные на север')


if __name__ == '__main__':
    try:
        main()
    except Exception:
        logger.error('Monitoring завершился с ошибкой', exc_info=True)

