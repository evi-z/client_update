# Ключи словаря port_demon
import os
import sys
from pathlib import Path

# Low-level значения
APP_VERSION = '1.1.0'  # Версия программы
DEFAULT_HOST = '85.143.156.89'  # Предустановленный адрес сервера
ENCODING_APP = 'utf8'  # Кодировка программы

# Аргументы коммандной строки
UPDATER_RUN_ARG = '-ur'  # Параметр запуска updater-a
DONT_NEED_INIT_LOADER_ARG = '-wl'  # Не загружать loader

# Пути реестра
REG_ROOT_PATH = r'Software\NevisVNClient'

# Ключи реестра
REG_VERSION_KEY = 'Version'
REG_LAST_RUN_KEY = 'LastRun'
REG_LAST_RUN_KKM_DATA_KEY = 'LastRunKKMData'

# Бинарные значения реестра
REG_TRUE = '1'
REG_FALSE = '0'

# Директории
FIRST_RUN_DIR_NAME = '_first_run'
FIRST_POPEN_DIR_NAME = '_first_popen'
RUN_ONCE_DIR_NAME = '_run_once'

# Низкоуровневые пути
ROOT_PATH = os.getcwd()  # Директория программы
PATH_TO_PYTHON_ROOT_DIR = os.path.join(Path(sys.executable).parent)  # Путь к директории Python
PATH_TO_PYTHON = os.path.join(PATH_TO_PYTHON_ROOT_DIR, 'python.exe')  # Путь к интропретатору
PATH_TO_PYTHON_NO_CONSOLE = os.path.join(PATH_TO_PYTHON_ROOT_DIR, 'pythonw.exe')  # Путь к no-console python-у

# Ключи
PORT_KEY = 'port'
VNC_PORT_KEY = 'vnc_port'
SSH_PORT_KEY = 'ssh_port'
USER_KEY = 'user'
PASSWORD_KEY = 'password'
SERVER_KEY = 'server'

# Порты демонов port_demon
PORT_DEMON_ONE_PORT = 14421
PORT_DEMON_TWO_PORT = 14422
PORT_DEMON_THREE_PORT = 14423
PORT_DEMON_FOUR_PORT = 14424

# Кортеж портов
PORT_LIST = (PORT_DEMON_ONE_PORT, PORT_DEMON_TWO_PORT, PORT_DEMON_THREE_PORT, PORT_DEMON_FOUR_PORT)

LOCAL_VNC_PORT = 11115  # Порт Tight VNC Service

# Ключи словаря client TODO
GROUP_KEY = 'group'
PHARMACY_KEY = 'pharmacy'
DEVICE_KEY = 'device'

# Ключи словаря sql_demon
PHARMACY_DICT_KEY = 'pharmacy_dict'
OFFICE_DICT_KEY = 'office_dict'

# Ключи словаря приветствия
MODE_DICT_KEY = 'mode'
DATA_DICT_KEY = 'data'

# Режимы работы
PORT_MODE = 'port'
SETTINGS_MODE = 'settings'
CONFIGURATION_MODE = 'configuration'
KKM_STRIX_MODE = 'kkm_strix'

# Модули
UPDATER_MODULE_NAME = 'updater.py'
CLIENT_MODULE_NAME = 'client.pyw'
PC_CONFIG_MODULE_NAME = 'pc_config.py'
KKM_SCRIPT_MODULE_NAME = 'kkm.py'
INSTALLER_LIBRARY_MODULE_NAME = 'installer_libary.py'

# Наименования файлов
CONFIG_NAME = 'settings.ini'
LOG_NAME = 'log.txt'
PLINK_NAME = 'plink_client.exe'
TVNSERVER_NAME = 'tvnserver_client.exe'
TVNSERVER_CLASSIC_NAME = 'tvnserver.exe'
PID_FILE_NAME = 'pid'
PID_PLINK_FILE_NAME = 'pid_plink'
UPD_FILE_NAME = 'upd'

# Сопровождающие файлы
KEY_REG_NAME = 'key.reg'
VNC_SERVICE_REG_NAME = 'vnc_service.reg'

# Имена процессов
PROCESS_NAME_CLIENT = 'python'

# Пути реестра (и связанное)
REG_PATH_TO_LAYER = r'SOFTWARE\Microsoft\Windows NT\CurrentVersion\AppCompatFlags\Layers'
RUNASADMIN_FLAG = '~ RUNASADMIN'  # Флаг "запускать от админа"

# Директории программы
RUNTIME_DIR_NAME = 'runtime'
MODULES_DIR_NAME = 'modules'
BIN_DIR_NAME = 'bin'
SOFT_DIR_NAME = 'soft'
FUNS_DIR_NAME = 'funs'
SCRIPTS_DIR_NAME = 'scripts'

# Пути к файлам
# Относительные
CONFIG_FILE_PATH = os.path.join(ROOT_PATH, CONFIG_NAME)
PID_FILE_PATH = os.path.join(RUNTIME_DIR_NAME, PID_FILE_NAME)
PID_PLINK_FILE_PATH = os.path.join(RUNTIME_DIR_NAME, PID_PLINK_FILE_NAME)
LOG_FILE_PATH = os.path.join(RUNTIME_DIR_NAME, LOG_NAME)
PLINK_FILE_PATH = os.path.join(SOFT_DIR_NAME, PLINK_NAME)
TVNSERVER_FILE_PATH = os.path.join(SOFT_DIR_NAME, TVNSERVER_NAME)
KEY_REG_PATH = os.path.join(BIN_DIR_NAME, KEY_REG_NAME)
VNC_SERVICE_REG_FILE = os.path.join(BIN_DIR_NAME, VNC_SERVICE_REG_NAME)

# Абсолютные пути
UPDATE_GIT_PATH = os.path.join(ROOT_PATH, BIN_DIR_NAME, 'update')
BACKUP_DIR_PATH = os.path.join(ROOT_PATH, BIN_DIR_NAME, 'backup')

# Секции конфигурации
APP_SECTION = 'App'
CONNECT_SECTION = 'Connect'

# Параметры конфигурации
GROUP_PHARM = 'group'
PHARMACY_OR_SUBGROUP_PHARM = 'pharmacy_or_subgroup'
DEVICE_OR_NAME_PHARM = 'device_or_name'
HOST_PHARM = 'host'

# Представления устройств (для Настроек клиента)
KOMZAV = 'КомЗав'
KASSA1 = 'Касса 1'
KASSA2 = 'Касса 2'
KASSA3 = 'Касса 3'
KASSA4 = 'Касса 4'
KASSA5 = 'Касса 5'
KASSA6 = 'Касса 6'
KASSA7 = 'Касса 7'
MINISERVER = 'Сервер'
KOMZAV2 = 'КомЗав 2'
KOMZAV3 = 'КомЗав 3'

DEVICE_DICT = {KOMZAV: '0',
               KASSA1: '1',
               KASSA2: '2',
               KASSA3: '3',
               KASSA4: '4',
               KASSA5: '5',
               KASSA6: '6',
               KASSA7: '7',
               MINISERVER: '99',
               KOMZAV2: '102',
               KOMZAV3: '103'}

# Кассовое оборудование
KASSA_DICT = {key: val for key, val in DEVICE_DICT.items() if key not in (KOMZAV, KOMZAV2, KOMZAV3)}


# Текстовое представление групп
GROUP_PHARMACY_TEXT = 'Аптеки'
GROUP_OFFICE_TEXT = 'Офис'

# Целочисленные представления групп
GROUP_PHARMACY_INT = 0
GROUP_OFFICE_INT = 1

EOF = '#'

# Прочие параметры
MINUTES_BEFORE_INIT_KKM_DATA = 120   # Кол-во минут между запусками сбора данных о ККМ
MAX_COUNT_RESTART_PLINK = 20  # Максимальное кол-во перезапусков plink в одной сессии



