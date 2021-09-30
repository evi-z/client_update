import logging
from ctypes import windll
import sys
import os
import random
import socket
import time
import winreg as reg
import asyncio
import traceback

from funs.low_level_fun import *
from bin.values import *
from funs.fun import *
from errors import *

settings = init_settings(
    logger_name=__name__,
    root_file_path=__file__,
)  # Инициализируем настройки

# Если запущен не от адиминстратора
if not is_admin():
    settings.logger.info('client перезапущен с правами администратора')
    path_to_client = get_correct_path()  # Получаем корректный путь до client
    arg = sys.argv[1:]  # Аргументы коммандной строки

    argv_to_ex = [path_to_client]  # Список для ShellExecuteW
    if arg:  # Если есть аргументы - добавляем
        argv_to_ex.extend(arg)

    # Перезапускаем интрепретатор с правами админа
    windll.shell32.ShellExecuteW(0, 'runas', sys.executable, ' '.join(argv_to_ex), None, 1)
    sys.exit(0)  # Завершаем работу этого скрипта

try:
    run_first_scripts()  # Инициализация "первичных" скриптов
except Exception as e:
    settings.logger.error(f'Ошибка в инициализации первичных скриптов: {e}')

# Инициалиция loader-a
try:
    loader = Loader(settings_obj=settings)  # Объект загрузчика
    if loader.need_init_loader():
        loader.start_threading()  # Запускаем поток проверки обновления
except Exception as e:
    settings.logger.error(f'Ошибка в инициализации loader: {e}')

try:
    configuration = init_config(settings)  # Инициализируем объект конфигурации
    init_client()  # Инициализация клиента
except Exception as e:
    settings.logger.error(f'Ошибка в первичной инициализации', exc_info=True)

try:
    init_scripts(configuration)  # Инициализация побочных скриптов
except Exception as e:
    settings.logger.error(f'Ошибка в инициализации побочных скриптов', exc_info=True)

while True:
    try:  # Отлов ошибок
        connection = SSHConnection(configuration_obj=configuration)  # Создаём объект подключения
        connection.get_data_for_port_forward()  # Получаем с сервера данные для проброса порта
        connection.start_ssh_connection()  # Запускаем цикл соединения

        settings.logger.warning('Цикл выполнения был прерван, производится перезапуск')

    except socket.timeout:  # Ловим timeout
        settings.logger.error(
            f'Подключение к серверу {configuration.host} превысило время ожидания', exc_info=True)
        time.sleep(5)

    except (ConnectionRefusedError, ConnectionResetError):  # Подключение сброшенно со стороны сервера
        settings.logger.error(f'Подлючение к серверу {configuration.host} было сброшенно со стороны сервера')

        sleep_time = random.randint(5, 20)  # Ставим время от 5 до 20 для повторного подключения
        time.sleep(sleep_time)

    except socket.gaierror:
        settings.logger.error(f'Некореектный адрес [{HOST_PHARM}]')
        time.sleep(5)

    except ClientException:  # Программная ошибка (отлавливаемая)
        logger.info('Программа завершена')
        sys.exit(0)

    except Exception as e:
        logger.error(f'Неустановленная ошибка', exc_info=True)
        time.sleep(3)

    except:
        logger.critical(f'Критическая ошибка программы', exc_info=True)
        time.sleep(3)
