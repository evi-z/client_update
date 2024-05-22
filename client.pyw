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

from library_control import LibraryControl

lib_control = LibraryControl(
    logger_name=__name__,
    root_file_path=__file__
)

lib_control.check_app_lib_install()  # Контроль установки библиотек

try:
    from objects import *
    from funs.low_level_fun import *
    from bin.values import *
    from funs.fun import *
    from errors import *
except (ImportError, ModuleNotFoundError):  # Перехватываем исключения импорта в модулях
    lib_control.logger.critical('Критическая ошибка импорта необходимых модулей', exc_info=True)


settings = SettingsObject(
    lib_control_obj=lib_control,
    root_file_path=__file__
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
    settings.check_autorun()
except Exception:
    settings.logger.error('Ошибка добавления в автозагрузку', exc_info=True)

try:
    run_first_scripts()  # Инициализация "первичных" скриптов
except Exception:
    settings.logger.error(f'Ошибка в инициализации первичных скриптов:', exc_info=True)

# Инициалиция loader-a
try:
    loader = Loader(settings_obj=settings)  # Объект загрузчика
    if loader.need_init_loader():
        loader.start_threading()  # Запускаем поток проверки обновления
except Exception:
    settings.logger.error(f'Ошибка в инициализации loader:', exc_info=True)

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
        tvnc_obj = TightVNC(configuration_obj=configuration)
        tvnc_obj.check_running()  # Инициализирует службу TightVNC

        connection = SSHConnection(
            configuration_obj=configuration,
            tvnc_obj=tvnc_obj
        )  # Создаём объект подключения
        try:
            connection.get_data_for_port_forward()  # Получаем с сервера данные для проброса порта
        except Exception:
            configuration.settings.logger.error('Ошибка при получении данных для проброса порта', exc_info=True)
            time.sleep(random.randint(3, 6))
            continue

        connection.start_ssh_connection()  # Запускаем цикл соединения
        settings.logger.warning('Цикл выполнения был прерван, производится перезапуск')

    except asyncssh.misc.ChannelListenError:
        settings.logger.error('Проброс порта к серверу не удался')
        time.sleep(5)

    except socket.timeout:  # Ловим timeout
        settings.logger.error(
            f'Подключение к серверу {configuration.host} превысило время ожидания', exc_info=True)
        time.sleep(5)

    except ConnectionToPortDaemonError:  # Перехватываем снизу
        pass

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

    except SystemExit:  # Перехватываем завершение работы
        raise SystemExit

    except:
        logger.critical(f'Критическая ошибка программы', exc_info=True)
        time.sleep(3)
