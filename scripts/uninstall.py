from subprocess import run, PIPE
from funs.low_level_fun import *
from bin.values import *
from ctypes import windll


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

run(f'taskkill /f /im {TVNSERVER_NAME}', shell=True, stdin=PIPE, stdout=PIPE, stderr=PIPE)
run(f'taskkill /f /im {PLINK_NAME}', shell=True, stdin=PIPE, stdout=PIPE, stderr=PIPE)
run(f'taskkill /f /im pythonw.exe', shell=True, stdin=PIPE, stdout=PIPE, stderr=PIPE)
