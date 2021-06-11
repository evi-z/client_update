import signal
import os

from bin.values import *
from funs.low_level_fun import *
from funs.fun import *


# Удаляет pid_file
def delete_pid_file():
    os.remove(PID_FILE_PATH)


# Если запущен не от адиминстратора
if not is_admin():

    path_to_client = get_correct_path()  # Получаем корректный путь
    arg = sys.argv[1:]  # Аргументы коммандной строки

    argv_to_ex = [path_to_client]  # Список для ShellExecuteW
    if arg:  # Если есть аргументы - добавляем
        argv_to_ex.extend(arg)

    # Перезапускаем интрепретатор с правами админа
    windll.shell32.ShellExecuteW(0, 'runas', sys.executable, ' '.join(argv_to_ex), None, 1)
    sys.exit(0)  # Завершаем работу этого скрипта

# Узнаём, запущен ли client и получаем его proc (psutil)
runs, proc = get_client_run()

if runs:  # Если client запущен - завершаем
    os.kill(proc.pid, signal.SIGTERM)
    delete_pid_file()  # Удаляем pid file
    print_log('client заверщён посредством утилиты quit.py')

start_taskkill()  # Завершаем побочный софт
