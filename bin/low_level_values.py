import os
import sys
from pathlib import Path

# Low-level значения
APP_VERSION = '1.0.0'

# Аргументы коммандной строки
UPDATER_RUN_ARG = '-ur'  # Параметр запуска updater-a
DONT_NEED_INIT_LOADER_ARG = '-wl'  # Не загружать loader

# Пути реестра
REG_ROOT_PATH = r'Software\NevisVNClient'

# Ключи реестра
REG_VERSION_KEY = 'Version'
REG_LAST_RUN_KEY = 'LastRun'
REG_LAST_RUN_KKM_DATA_KEY = 'LastRunKKMData'

# Значения реестра
REG_TRUE = '1'
REG_FALSE = '0'

# Директории
FIRST_RUN_DIR_NAME = '_first_run'
FIRST_POPEN_DIR_NAME = '_first_popen'

# Пути
ROOT_PATH = os.getcwd()  # Директория программы
PATH_TO_PYTHON_ROOT_DIR = os.path.join(Path(sys.executable).parent)  # Путь к директории Python
PATH_TO_PYTHON = os.path.join(PATH_TO_PYTHON_ROOT_DIR, 'python.exe')  # Путь к интропретатору
PATH_TO_PYTHON_NO_CONSOLE = os.path.join(PATH_TO_PYTHON_ROOT_DIR, 'pythonw.exe')  # Путь к no-console python-у
