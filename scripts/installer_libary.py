import os
import sys
import time
from pathlib import Path
from subprocess import run, PIPE, Popen


# Возвращает список аргументов коммандной строки
def get_argv_list(argv):
    if argv[1:]:  # Если есть аргументы коммандной строки
        argv_list = argv[1:]  # Исключаем первый элемент

        return argv_list


# Получаем список аргументов коммандной строки
argv_list = get_argv_list(sys.argv)

# Флаг Тихого режима
silent_flag = False
if argv_list:  # Если есть аргументы коммандной строки - Тихий режим
    silent_flag = True

# Пути
PATH_TO_PYTHON_DIR = os.path.join(Path(sys.executable).parent)  # Путь к директории Python
PATH_TO_ROOT = Path(os.getcwd()).parent  # Путь к директории программы (если запускаем из-под script)
PATH_TO_PIP = os.path.join(PATH_TO_PYTHON_DIR, 'Scripts', 'pip.exe')  # Путь к pip

# Экранируем скобки
if ' ' in PATH_TO_PIP:
    PATH_TO_PIP = f'"{PATH_TO_PIP}"'

time.sleep(0.2)

# Установка библиотек pip
list_full_lib = ['asyncssh', 'PyQt5', 'psutil', 'py-cpuinfo', 'GitPython', 'pyshtrih', 'schedule']

if silent_flag:  # Если тихий режим
    for lib in argv_list:  # Устанавливаем переданные в cmd библиотеки
        run(f'{PATH_TO_PIP} install {lib}', shell=True, stdout=PIPE, stderr=PIPE, stdin=PIPE)
else:  # Устанавливаем все библиотеки
    for lib in list_full_lib:
        run(f'{PATH_TO_PIP} install {lib}', shell=True)