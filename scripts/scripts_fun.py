import os
from datetime import datetime

RUNTIME_DIR = 'runtime'
LOG_NAME = 'script_log.txt'


# Пишет логи
def print_log(text):
    try:
        with open(os.path.join(RUNTIME_DIR, LOG_NAME), 'a', encoding='cp1251') as logfile:
            logfile.write(f'[{datetime.now().strftime("%X %d/%m/%y")}]: {text}\n')
    except FileNotFoundError:
        os.mkdir(RUNTIME_DIR)
        print_log(text)


# Возвращает имя запущенного скрипта из атрибута __file__
def get_basename(_file):
    return os.path.basename(_file)