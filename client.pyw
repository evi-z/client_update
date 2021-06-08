from ctypes import windll
import sys
import os
import random
import socket
import time
import winreg as reg

try:
    import psutil  # Проверка установки

    from funs.low_level_fun import *
    from bin.values import *
    from funs.fun import *
except ModuleNotFoundError as e:
    print_error(f'Критическая ошибка импорта модуля: {e}')
    sys.exit(0)

# Если запущен не от адиминстратора
if not is_admin():
    print_log(f'client перезапущен с правами администратора')

    # Перезапускаем интрепретатор с правами админа
    windll.shell32.ShellExecuteW(0, 'runas', sys.executable, ' '.join(sys.argv), None, 1)
    sys.exit(0)  # Завершаем работу этого скрипта


# Инициализация "первичных скриптов
try:
    run_first_scripts()
except FileNotFoundError:  # Если нет директорий
    pass
except Exception as e:
    print_error(f'Ошибка в инициализации первичного скрипта: {e}')

# Инициалиция loader-a
try:
    if need_init_loader(sys.argv):
        import loader
except Exception as e:
    print_error(f'Ошибка в инициализации loader: {e}')

# Время проверки переподключения
RECONNECT_CHECK_TIME = 90

# Порты демонов port_demon
PORT_DEMON_ONE_PORT = 14421
PORT_DEMON_TWO_PORT = 14422
PORT_DEMON_THREE_PORT = 14423
PORT_DEMON_FOUR_PORT = 14424

# Кортеж портов
PORT_LIST = (PORT_DEMON_ONE_PORT, PORT_DEMON_TWO_PORT, PORT_DEMON_THREE_PORT, PORT_DEMON_FOUR_PORT)

HOST = '85.143.156.89'  # Адрес сервера

# Параметры - заглушки
GROUP = 0
PHARMACY_OR_SUBGROUP = ''
DEVICE_OR_NAME = ''


# Создаёт конфиг
def create_config():
    config = configparser.ConfigParser()

    # Секция APP
    config.add_section(APP_SECTION)

    config.set(APP_SECTION, GROUP_PHARM, str(GROUP))  # Группа
    config.set(APP_SECTION, PHARMACY_OR_SUBGROUP_PHARM, PHARMACY_OR_SUBGROUP)  # Аптека или Подгруппа
    config.set(APP_SECTION, DEVICE_OR_NAME_PHARM, DEVICE_OR_NAME)  # Устройство или Имя

    # Секция CONNECT
    config.add_section(CONNECT_SECTION)

    config.set(CONNECT_SECTION, HOST_PHARM, HOST)  # Адрес сервера

    with open(CONFIG_FILE_PATH, 'w') as config_file:
        config.write(config_file)


# Инициализация конфига
def init_config():
    global GROUP, PHARMACY_OR_SUBGROUP, DEVICE_OR_NAME, HOST, PORT_LIST

    if not os.path.exists(CONFIG_FILE_PATH):  # Если файла конфигурации не существует
        create_config()  # Создаём файл конфигурации

        print_incorrect_settings('Файл конфигурации settings.ini отсутсвовал\n'
                                 'Он был создан по пути:\n'
                                 f'{CONFIG_FILE_PATH}\n\n'
                                 'Перед последующим запуском проинициализируйте его вручную, либо посредством '
                                 'утилиты "Настройка клиента"', stand_print=False)

    config = configparser.ConfigParser()
    config.read(CONFIG_FILE_PATH)  # Читаем файл конфигурации

    # App
    GROUP = int(config.get(APP_SECTION, GROUP_PHARM))
    PHARMACY_OR_SUBGROUP = config.get(APP_SECTION, PHARMACY_OR_SUBGROUP_PHARM)
    DEVICE_OR_NAME = config.get(APP_SECTION, DEVICE_OR_NAME_PHARM)

    # Connect
    HOST = config.get(CONNECT_SECTION, HOST_PHARM)

    # Проверяет корректность параметров файла конфигурации
    init_correct_config_parm(GROUP, PHARMACY_OR_SUBGROUP, DEVICE_OR_NAME)


try:
    init_config()  # Инициализация конфига
    init_client()  # Инициализация клиента
except Exception as e:
    print_error(f'Ошибка в первичной инициализации: {e}')

try:
    init_scripts((GROUP, PHARMACY_OR_SUBGROUP, DEVICE_OR_NAME))  # Инициализация побочных скриптов
except Exception as e:
    print_error(f'Ошибка в инициализации побочных скриптов: {e}')

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

            print_log(f'Произведено подключение к серверу {HOST} по порту {port_conn}')  # Пишем лог

            timeout = random.randint(15, 25)  # Таймаут в очереди от 15 до 25 секунд (чтоб не DDOS-ить)
            sock.settimeout(timeout)  # Ставим таймаут в очереди

            sock.send(hello_dict.encode())  # Отправка словаря приветсвия на сервер

            connect_dict = get_data_from_socket(sock)  # Получаем словарь подключения

            port = connect_dict[PORT_KEY]  # Выделенный порт
            ssh_port = connect_dict[SSH_PORT_KEY]  # Порт SSH
            user = connect_dict[USER_KEY]  # Логин
            password = connect_dict[PASSWORD_KEY]  # Пароль
            server = connect_dict[SERVER_KEY]  # Хост

            print_log(f'Получен порт {port} для прокидывания SSH со стороны сервера')

            # Создаём процесс tvnserver
            tvnserver_process = start_tvnserver()

            # Прокидываем порт VNC
            command = [os.path.join(ROOT_PATH, PLINK_FILE_PATH), '-N', '-R', f'{port}:localhost:{LOCAL_VNC_PORT}', '-P',
                       f'{ssh_port}', '-pw', f'{password}', '-l', f'{user}', '-batch', f'{server}']

            # Создаём процесс plink.exe
            plink_process = start_plink(command)

            while True:  # Следим

                plink_pool = plink_process.poll()
                if plink_pool is not None:  # Если процесс завершён
                    print_restart_log(plink_pool, PLINK_NAME, plink_process.pid)
                    break

                time.sleep(RECONNECT_CHECK_TIME)  # Проверяем, запущен ли plink и tvns

        except socket.timeout:  # Ловим timeout
            print_error(f'Подключение к серверу {HOST} по порту {port_conn} превысило время ожидания в {timeout} секунд')

        except ConnectionRefusedError:  # Подключение сброшенно со стороны сервера
            print_error(f'Подлючение к серверу {HOST} по порту {port_conn} было сброшенно со стороны сервера')

            sleep_time = random.randint(5, 20)  # Ставим время от 5 до 20 для повторного подключения
            time.sleep(sleep_time)
        except socket.gaierror:
            print_incorrect_settings(f'Некореектный адрес ({HOST_PHARM})')

        except Exception as e:
            print_error(f'Неустановленная ошибка: {e}')
            time.sleep(3)

        except:
            print_error('CRITICAL ERROR')
            time.sleep(3)

finally:
    sock.close()

