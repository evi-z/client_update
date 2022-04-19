# Ключи словаря port_demon
import os
import sys
from pathlib import Path

# Low-level значения
APP_VERSION = '1.1.15f'  # Версия программы
DEFAULT_HOST = '85.143.156.89'  # Предустановленный адрес сервера
ENCODING_APP = 'utf8'  # Кодировка программы

# Аргументы коммандной строки
UPDATER_RUN_ARG = '-ur'  # Параметр запуска updater-a
DONT_NEED_INIT_LOADER_ARG = '-wl'  # Не загружать loader

# Пути реестра
REG_ROOT_PATH = r'Software\NevisVNClient'

# Библиотеки программы
APP_LIBRARY = ['asyncssh', 'PyQt5', 'psutil', 'py-cpuinfo', 'GitPython', 'pyshtrih', 'schedule', 'pypiwin32', 'pywin32',
               'requests']

# Ключи реестра
REG_VERSION_KEY = 'Version'
REG_LAST_RUN_PC_CONFIG_KEY = 'LastRunPcConfig'
REG_LAST_RUN_KKM_DATA_KEY = 'LastRunKKMData'
REG_LAST_RUN_DISK_USAGE = 'LastDiskUsageRun'
REG_LAST_RUN_REGULAR = 'LastRunRegular'
REG_LAST_RUN_LOADER = 'LastRunLoader'
REG_LAST_RECONNECT = 'LastReconnects'
REG_LAST_APP_RUN = 'LastAppRun'

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
CHECK_BD_WRITE_KEY = 'check_bd_write_demon'

# # Порты демонов port_demon  TODO Устаревшие
PORT_DEMON_ONE_PORT = 14421
PORT_DEMON_TWO_PORT = 14422
PORT_DEMON_THREE_PORT = 14423
PORT_DEMON_FOUR_PORT = 14424

# Порты демонов port_demon
# PORT_DEMON_ONE_PORT = 14491
# PORT_DEMON_TWO_PORT = 14492
# PORT_DEMON_THREE_PORT = 14493
# PORT_DEMON_FOUR_PORT = 14494

# REMOTE_DEMON_PORT = 11592  TODO Не используется
CONFIGURATION_DEMON_PORT = 11617
SCHEDULER_DEMON_PORT = 17236

# Кортеж портов
# PORT_LIST = (12542,)  # TODO Тестовый порт
PORT_LIST = (PORT_DEMON_ONE_PORT, PORT_DEMON_TWO_PORT, PORT_DEMON_THREE_PORT, PORT_DEMON_FOUR_PORT)
LOCAL_VNC_PORT = 11115  # Порт Tight VNC Service

# Ключи словаря client
GROUP_KEY = 'group'
PHARMACY_KEY = 'pharmacy'
DEVICE_KEY = 'device'
APP_VERSION_KEY = 'app_version'

FIRST_IDENTIFIER = 'first_identifier'
SECOND_IDENTIFIER = 'second_identifier'

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
CHECK_BD_MODE = 'check_bd'
REMOTE_MODE = 'remote'
CHECK_TEST_CLIENT_UPDATE_MODE = 'test_client_update'

# Модули
UPDATER_MODULE_NAME = 'updater.py'
CLIENT_MODULE_NAME = 'client.pyw'  # TODO УСТАРЕЛО
PC_CONFIG_MODULE_NAME = 'pc_config.py'
KKM_SCRIPT_MODULE_NAME = 'kkm.py'
DISK_USAGE_MODULE_NAME = 'disk_usage.py'
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
AMMY_ADMIN_NAME = 'AA.exe'
CLEAR_1C_NAME = 'clear_1c.bat'
IIS_START_SCRIP_NAME = 'iis_start.py'

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

TVNSERVER_SERVICE_NAME = 'tvnserver'  # Имя службы TightVNC

# Прочие параметры
MINUTES_BEFORE_INIT_KKM_DATA = 240 * 60   # Кол-во минут между запусками сбора данных о ККМ
MINUTES_BEFORE_INIT_DISK_USAGE = 240 * 60  # Кол-во минут между запусками сбора данных о дисках и бекапах
MINUTES_BEFORE_CHECK_DB_WRITING = 30 * 60  # Количество минут между проверками о записи в БД
MINUTES_BEFORE_CHECK_APP_REBOOT = 10 * 60  # Количество минут между проверками о необходимости перезапуска программы
MINUTES_BEFORE_CHECK_TVNS_SERVICE = 1 * 60  # Колличество минут между проверками работы службы TightVNC
MINUTES_BEFORE_CHECK_LOADER = 30 * 60  # Колличество минут между проверками новых обновлений

SECONDS_FROM_LAST_APP_REBOOT = 6 * 60 * 60  # Кол-во секунд, допустимое с последнего перезапуска программы


