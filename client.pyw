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

logger = get_logger(__name__)  # Инициализируем logger

# Если запущен не от адиминстратора
if not is_admin():
    logger.info('client перезапущен с правами администратора')
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
    logger.error(f'Ошибка в инициализации первичных скриптов: {e}')

# Инициалиция loader-a
try:
    if need_init_loader(sys.argv):
        import loader
except Exception as e:
    logger.error(f'Ошибка в инициализации loader: {e}')

try:
    HOST, GROUP, PHARMACY_OR_SUBGROUP, DEVICE_OR_NAME = init_config()  # Инициализируем конфиг
    init_client()  # Инициализация клиента
except Exception as e:
    logger.error(f'Ошибка в первичной инициализации', exc_info=True)

try:
    init_scripts((GROUP, PHARMACY_OR_SUBGROUP, DEVICE_OR_NAME))  # Инициализация побочных скриптов
except Exception as e:
    logger.error(f'Ошибка в инициализации побочных скриптов', exc_info=True)

try:  # Отлов закрытия сокета
    while True:
        try:  # Отлов ошибок
            start_client()  # Выполняем подготовку

            # Словарь инициализации client
            init_dict = {GROUP_KEY: GROUP,
                         PHARMACY_KEY: PHARMACY_OR_SUBGROUP,
                         DEVICE_KEY: DEVICE_OR_NAME}
            hello_dict = get_hello_dict(PORT_MODE, init_dict)  # Получаем словарь приветствия с init_dict

            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

            port_conn = choice_port(PORT_LIST)  # Получаем случайный порт из списка
            sock.connect((HOST, port_conn))  # Подключение к серверу

            logger.info(f'Произведено подключение к серверу {HOST} по порту {port_conn}')  # Пишем лог

            timeout = random.randint(15, 25)  # Таймаут в очереди от 15 до 25 секунд (чтоб не DDOS-ить)
            sock.settimeout(timeout)  # Ставим таймаут в очереди

            sock.send(hello_dict.encode())  # Отправка словаря приветсвия на сервер
            connect_dict = get_data_from_socket(sock)  # Получаем словарь подключения

            serv_port = int(connect_dict[PORT_KEY])  # Выделенный порт (str!)
            ssh_port = connect_dict[SSH_PORT_KEY]  # Порт SSH
            ssh_user = connect_dict[USER_KEY]  # Логин
            ssh_password = connect_dict[PASSWORD_KEY]  # Пароль
            ssh_host = connect_dict[SERVER_KEY]  # Хост
            check_bd_write_demon_port = connect_dict[CHECK_BD_WRITE_KEY]  # Порт демона check_bd

            tvnserver_process = start_tvnserver()  # Создаём процесс tvnserver

            try:  # Пытаемся пробросить порт
                loop = asyncio.get_event_loop()
                loop.run_until_complete(new_ssh_connection(
                    ssh_host=ssh_host,
                    ssh_port=ssh_port,
                    serv_port=serv_port,
                    local_port=LOCAL_VNC_PORT,
                    ssh_username=ssh_user,
                    ssh_password=ssh_password,
                    check_bd_demon_port=check_bd_write_demon_port,
                    init_dict=init_dict,  # Словарь описания (группа, аптека/подгруппа, устройство/имя)
                ))
            except (OSError, asyncssh.Error) as exc:  # Ошибка проброса порта
                logger.error(f'Проброс порта SSH не удался: {exc}', exc_info=True)
                time.sleep(5)  # timeout
            except ReconnectForRewriteDBException:  # Если от сервера пришёл ответ об отсутсвии в БД
                logger.warning('От сервера пришёл ответ об отсутсвии записи в БД')
                time.sleep(5)

            logger.warning('Цикл выполнения был прерван, производится перезапуск')

        except socket.timeout:  # Ловим timeout
            logger.error(
                f'Подключение к серверу {HOST} по порту {port_conn} превысило время ожидания в {timeout} секунд')
            time.sleep(5)

        except (ConnectionRefusedError, ConnectionResetError):  # Подключение сброшенно со стороны сервера
            logger.error(f'Подлючение к серверу {HOST} по порту {port_conn} было сброшенно со стороны сервера')

            sleep_time = random.randint(5, 20)  # Ставим время от 5 до 20 для повторного подключения
            time.sleep(sleep_time)

        except socket.gaierror:
            print_incorrect_settings(f'Некореектный адрес ({HOST_PHARM})')

        except ClientException:  # Программная ошибка (отлавливаемая)
            logger.info('Программа завершена')
            sys.exit(0)

        except Exception as e:
            logger.error(f'Неустановленная ошибка', exc_info=True)
            time.sleep(3)

        except:
            logger.critical(f'Критическая ошибка программы', exc_info=True)
            time.sleep(3)

finally:
    sock.close()
