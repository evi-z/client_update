import ctypes
import datetime
import json
import os
import pathlib
import shutil
import socket
import subprocess
import threading
import traceback
import winreg as reg
from ctypes import windll
import sys
import time
from subprocess import run, PIPE
import locale
import logging

MB_SYSTEMMODAL = 0x00001000
MB_ICONINFORMATION = 0x00000040
MB_ICONERROR = 0x00000010


RUNTIME_DIR = 'runtime'
LOG_NAME = 'retail_backup.log'
ENCODING_APP = 'utf8'


# Инициализирует logger
def init_logger():
    try:
        fh = logging.FileHandler(os.path.join(RUNTIME_DIR, LOG_NAME), 'a', ENCODING_APP)  # Файл лога
    except FileNotFoundError:  # Если нет директории runtime
        os.mkdir(RUNTIME_DIR)  # Создаём папку runtime
        fh = logging.FileHandler(os.path.join(RUNTIME_DIR, LOG_NAME), 'a', ENCODING_APP)  # Файл лога
    str_format = '[%(asctime)s]: %(levelname)s - %(name)s - (%(filename)s).%(funcName)s(%(lineno)d) ' \
                 '=> %(message)s'  # Формат вывода
    date_format = '%X %d/%m/%y'  # Формат даты/времени
    formatter = logging.Formatter(fmt=str_format, datefmt=date_format)
    fh.setFormatter(formatter)  # Устанавливаем форматирование

    return fh  # Возвращаем настроенный логгер


# Возвращает объект logger-a
def get_logger(name):
    logger = logging.getLogger(name)  # Инициализируем объект логгера с именем программы
    logger.setLevel(logging.INFO)  # Уровень логгирования
    logger.addHandler(init_logger())  # Добавляем

    return logger


logger = get_logger(__name__)  # Инициализируем logger


# Проверяет параметры в Report (печать DataMatrix)
def get_backup_path():
    path_to_reg_report_1c = [
        (reg.HKEY_CURRENT_USER, r'SOFTWARE\1C\1Cv8\Report')
    ]

    hku_subkeys = []
    k = reg.OpenKey(reg.HKEY_USERS, '')  # Открываем корень HKU
    count_keys = reg.QueryInfoKey(k)[0]  # Колличество ключей раздела реестра
    for index in range(count_keys):
        sub_key = reg.EnumKey(k, index)
        hku_subkeys.append(sub_key)

    for sub_key in hku_subkeys:
        path_to_reg_report_1c.append((reg.HKEY_USERS, sub_key + r'\SOFTWARE\1C\1Cv8\Report'))

    k = None
    for key, sub_key in path_to_reg_report_1c:  # Ищем ключ в реестре
        try:
            k = reg.OpenKey(key, sub_key, 0, reg.KEY_ALL_ACCESS)
            break
        except FileNotFoundError:
            pass

    if k is None:  # Если не найден ключ
        return None

    count_keys = reg.QueryInfoKey(k)[1]  # Колличество ключей раздела реестра
    reg_dict = {}  # Словаь ключей реестра
    for index in range(count_keys):  # Проходим по ключам
        key, value, types = reg.EnumValue(k, index)
        reg_dict[key] = value  # Пишем ключ - значение

    return reg_dict.get('PathBackUP')


def first_kassa() -> dict:
    backup_path = get_backup_path()
    if not backup_path:
        logger.error('Не обнаружен путь бекапов')
        return {
            'status': 'error',
            'status_code': 'NOT_FOUND_BACKUP_PATH',
            'description': 'Не обнаружен путь бекапов'
        }
    # Имя общего пользователя
    system_language = locale.windows_locale[ctypes.windll.kernel32.GetUserDefaultUILanguage()]

    all_user = 'Все'
    if system_language != 'ru_RU':
        all_user = 'All'

    # Права на папку
    res = run(
        ['icacls', backup_path, '/grant', f'{all_user}:(OI)(CI)F'], stdout=PIPE, stderr=PIPE, stdin=PIPE
    )
    if res.returncode:
        logger.error('Не удалось дать общий доступ для папки бекапов:\n' + res.stderr.decode('utf-8'))

    # Расширенные права общего доступа
    res = run(['net', 'share', 'BackupRetail'], stdout=PIPE, stderr=PIPE, stdin=PIPE)
    if not res.returncode:  # Уже назначены
        return {
            'status': 'success',
            'path': backup_path
        }

    res = run(
        ['net', 'share', f'BackupRetail={backup_path}', f'/GRANT:{all_user},FULL'],
        stdout=PIPE, stderr=PIPE, stdin=PIPE
    )

    if res.returncode:
        try:
            stderr = res.stderr.decode('utf-8')
        except Exception:
            stderr = 'Unknown'

        logger.error('Не удалось расшарить папку бекапов:\n' + stderr)
        return {
            'status': 'error',
            'status_code': 'CANT_SHARE_FOLDER',
            'description': 'Не удалось расшарить папку бекапов'
        }

    logger.info(f'Папка "{backup_path}" успешно расшарена')
    return {
        'status': 'success',
        'path': backup_path
    }


def create_msbox(text: str, *, title: str = 'Внимание', style: hex = MB_ICONINFORMATION):
    threading.Thread(  # Показываем MsBOX
        target=lambda: ctypes.windll.user32.MessageBoxW(0, text, title, MB_SYSTEMMODAL + style)
    ).start()


def send_data(send_dict: dict):
    import urllib
    import urllib.request
    url = 'http://85.143.156.89/retail_backup/'

    data = urllib.parse.urlencode(send_dict).encode('utf-8')
    req = urllib.request.Request(url, data)
    with urllib.request.urlopen(req) as response:
        _ = response.read()


def comzav():
    path_conn_dict = {}
    for pcname in ['Kassa1', 'Server']:
        path = fr'\\{pcname}\BackupRetail'
        try:
            listdir = os.listdir(path)
            break
        except PermissionError:
            logger.error(f'Отказано в досупе к расположению (PermissionError) "{path}"')
            return {
                'status': 'error',
                'status_code': 'SHARE_FOLDER_PERMISSION_ERROR',
                'description': f'Отказано в досупе к расположению "{path}"'
            }
        except Exception as ex:
            path_conn_dict[path] = str(ex)

    else:
        try:
            path_conn_description = json.dumps(path_conn_dict, indent=4, ensure_ascii=False)
        except Exception:
            path_conn_description = 'Unknown'

        logger.error('Сетевые расположения не найдены, скрипт завершён:\n' + path_conn_description)
        return {
            'status': 'error',
            'status_code': 'SHARE_FOLDER_NOT_FOUND',
            'description': 'Не найдено сетевое расположение бекапов базы'
        }

    backup_list = list(filter(lambda x: x.endswith('.zip'), listdir))
    backup_list = [os.path.join(path, file) for file in backup_list]

    # Поиск последнего бекапа
    last_time = 0
    last_backup = None
    for file in backup_list:
        filemtime = os.path.getmtime(file)
        if filemtime > last_time:
            last_time = filemtime
            last_backup = file

    path_to_local_backup = r'C:\BackupRetail'
    try:
        os.makedirs(path_to_local_backup)
    except FileExistsError:
        pass

    # Проверка свободного места
    backup_size = os.path.getsize(last_backup) / (2 ** 30)

    _, _, free_disk_space = shutil.disk_usage(__file__)
    free_disk_space /= (2 ** 30)
    if free_disk_space - 0.5 < backup_size:
        backup_local_list = os.listdir(path_to_local_backup)
        low_space_ret = {
                'status': 'error',
                'status_code': 'LOW_DISK_SPACE',
                'description': 'Слишком мало места на диске'
            }

        if not backup_local_list:  # Если нет локальных бекапов
            return low_space_ret

        backup_local_list = [os.path.join(path_to_local_backup, file) for file in backup_local_list]
        backup_local_list = sorted(backup_local_list, key=lambda x: os.path.getmtime(x))

        for file in backup_local_list:  # Удаляем старые бекапы
            try:
                os.remove(file)
                logger.info(f'Удалён старый бекап "{file}" для освобождения места на диске')
            except Exception:
                logger.error(
                    f'Не удалось удалить старый бекап "{file}" для освобождения места на диске', exc_info=True
                )

                return low_space_ret

            # Повторная проверка места
            _, _, free_disk_space = shutil.disk_usage(__file__)
            free_disk_space /= (2 ** 30)
            if free_disk_space - 0.5 < backup_size:
                continue
            else:
                break

    # Проверка уже существующих копий
    backup_local_list = os.listdir(path_to_local_backup)
    exists_backups = list(filter(lambda x: x == os.path.basename(last_backup), backup_local_list))
    if exists_backups:
        # Сверка размеров
        local_backup = os.path.join(path_to_local_backup, exists_backups[0])
        size_equal = os.path.getsize(local_backup) == os.path.getsize(last_backup)
        if size_equal:
            logger.error(f'Бекап "{last_backup}" уже существует в локальной директории')
            return {
                'status': 'warning',
                'status_code': 'LOCAL_BACKUP_EXISTS',
                'description': f'Локальный бекап уже существует ({local_backup})'
            }

    # Удаление старых бекапов
    if len(backup_local_list) > 2:
        backup_local_list = [os.path.join(path_to_local_backup, file) for file in backup_local_list]
        backup_local_list = sorted(backup_local_list, key=lambda x: os.path.getmtime(x), reverse=True)

        for file in backup_local_list[2:]:
            try:
                os.remove(file)
            except Exception:
                logger.warning(f'Не удалось удалить старый бекап "{file}"', exc_info=True)

    copy_time = get_copy_time()
    copy_time = f'{copy_time // 60} мин.' if copy_time >= 60 else f'{copy_time} сек.'
    start_text = 'Сейчас будет произведено копирование бекапа базы данных 1С на Ваш компьютер.\n' \
                 f'Примерное время копирования составит {copy_time}\n' \
                 'Не выключайте компьютер, а так же не пользуйтесь сетью. По окончании копирования ' \
                 'появится уведомительное окно.'

    create_msbox(start_text)

    logger.info(f'Начато копирование бекапа базы по пути "{last_backup}"')
    start_time = time.time()
    try:
        shutil.copy2(last_backup, path_to_local_backup)
    except Exception:
        logger.error(
            f'Не удалось скопировать бекап "{last_backup}" в локальную директорию "{path_to_local_backup}"',
            exc_info=True
        )
        create_msbox(
            'Во время копирования базы 1С произошла ошибка. Пожалуйста, сообщите об этом в IT Отдел',
            title='Ошибка', style=MB_ICONERROR
        )
        return {
            'status': 'error',
            'status_code': 'BACKUP_COPY_ERROR',
            'description': 'Ошибка во время копирования бекапа'
        }

    copy_time_new = time.time() - start_time
    save_copy_time(int(copy_time_new))

    logger.info(f'Копирование бекапа успешно завершено успешно завершено (time: {copy_time_new})')
    end_text = 'Копирование базы 1С успешно завершено, можете продолжать работу. Хорошего дня!'
    create_msbox(end_text, title='Успешно')

    return {
        'status': 'success',
        'copy_time': copy_time_new
    }


def get_copy_time() -> int:
    try:
        with open('_cptime', 'r') as cptime:
            time_ = int(cptime.read().strip())

        return time_
    except Exception:
        return 10 * 60


def save_copy_time(copy_time: int):
    with open('_cptime', 'w') as cptime:
        cptime.write(str(copy_time))


def script(configuration, need_backup: bool):
    configuration.settings.logger.info('Запущен скрипт RetailBackup')
    try:
        device = int(configuration.device_or_name)
    except ValueError:
        return

    if device == 1:
        res_dict = first_kassa()
    elif device == 0 and need_backup:
        res_dict = comzav()
        if res_dict.get('status') == 'success':
            now = str(time.time())
            configuration.settings.reg_data.set_reg_key('LastComZavBackRetail', now)  # Время последнего бекапа
    else:
        return

    req_data = {
        'pharmacy': configuration.pharmacy_or_subgroup,
        'device': configuration.device_or_name,
        'res_dict': res_dict
    }

    try:
        send_data(req_data)
    except Exception:
        logger.error('Не удалось отправить данные на сервер:\n' + str(req_data), exc_info=True)

