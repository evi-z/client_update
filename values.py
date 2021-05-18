# Ключи словаря port_demon
import os.path

PORT_KEY = 'port'
VNC_PORT_KEY = 'vnc_port'
SSH_PORT_KEY = 'ssh_port'
USER_KEY = 'user'
PASSWORD_KEY = 'password'
SERVER_KEY = 'server'

PORT_DEMON_PORT = 14422

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

# Наименования файлов
CONFIG_NAME = 'settings.ini'
LOG_NAME = 'log.txt'
PLINK_NAME = 'plink.exe'
TVNSERVER_NAME = 'tvnserver.exe'
PID_FILE_NAME = 'pid'
UPD_FILE_NAME = 'upd'

# Сопровождающие файлы
KEY_REG_NAME = 'key.reg'
VNC_SRV_REG_NAME = 'vnc_serv.reg'


PROCESS_NAME_CLIENT = 'python'

# Директории программы
RUNTIME_DIR_NAME = 'runtime'
MODULES_DIR_NAME = 'modules'
BIN_DIR_NAME = 'bin'
SOFT_DIR_NAME = 'soft'

# Пути к файлам
# Относительные
ROOT_PATH = os.getcwd()  # Директория программы
PID_FILE_PATH = os.path.join(RUNTIME_DIR_NAME, PID_FILE_NAME)
LOG_FILE_PATH = os.path.join(RUNTIME_DIR_NAME, LOG_NAME)
PLINK_FILE_PATH = os.path.join(SOFT_DIR_NAME, PLINK_NAME)
TVNSERVER_FILE_PATH = os.path.join(SOFT_DIR_NAME, TVNSERVER_NAME)
KEY_REG_PATH = os.path.join(BIN_DIR_NAME, KEY_REG_NAME)
VNC_SRV_REG_PATH = os.path.join(BIN_DIR_NAME, VNC_SRV_REG_NAME)

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
PORT_DEMON_PHARM = 'port_demon'

# Представления устройств (для Настроек клиента)
KOMZAV = 'КомЗав'
KASSA1 = 'Касса 1'
KASSA2 = 'Касса 2'
KASSA3 = 'Касса 3'
KASSA4 = 'Касса 4'
KASSA5 = 'Касса 5'
MINISERVER = 'Сервер'

DEVICE_DICT = {KOMZAV: '0',
               KASSA1: '1',
               KASSA2: '2',
               KASSA3: '3',
               KASSA4: '4',
               KASSA5: '5',
               MINISERVER: '99'}

# Текстовое представление групп
GROUP_PHARMACY_TEXT = 'Аптеки'
GROUP_OFFICE_TEXT = 'Офис'

# Целочисленные представления групп
GROUP_PHARMACY_INT = 0
GROUP_OFFICE_INT = 1

EOF = '#'
