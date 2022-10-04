import ctypes
import datetime
import errno
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
from pathlib import Path

MB_SYSTEMMODAL = 0x00001000
MB_ICONINFORMATION = 0x00000040
MB_ICONERROR = 0x00000010
first_kassa_back = ''

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


class ReportFileNotFound(Exception):
    """ Вызывается, когда отсутсвует файл type.ini от 1С"""


# Возвращает данные репорта (type.ini)
def get_1c_report_data() -> dict:
    public_path = os.environ['PUBLIC']
    path_to_report_file = os.path.join(public_path, 'type.ini')

    if not os.path.exists(path_to_report_file):
        logger.error(f'Файл репорта по пути "{path_to_report_file}" не найден')
        raise ReportFileNotFound

    report_data = {}
    try:
        with open(path_to_report_file, 'r', encoding='utf-8-sig') as report_file:
            for field in report_file:
                sp = field.replace('\n', '').split('=')
                name, val = sp[0].strip(), sp[-1].strip()
                report_data[name] = val
    except Exception:
        logger.error(f'Ошибка во время чтения файла репорта ("{path_to_report_file}")', exc_info=True)
        raise FileNotFoundError

    return report_data


def first_kassa() -> dict:
    global first_kassa_back
    try:
        report_data = get_1c_report_data()
    except ReportFileNotFound:
        logger.error('Не найден файл репорта (type.ini)')
        return {
            'status': 'error',
            'status_code': 'REPORT_FILE_NOT_FOUND',
            'description': 'Не найден файл репорта (type.ini)'
        }
    except FileNotFoundError:
        logger.error('Ошибка во время чтения файла репорта (type.ini)')
        return {
            'status': 'error',
            'status_code': 'REPORT_FILE_CANT_READ',
            'description': 'Ошибка во время чтения файла репорта (type.ini)'
        }

    type_db = report_data.get('TypeIB')
    if type_db == 'Server':
        backup_path = r'C:\SaveBases\Backup'
        first_kassa_back = backup_path
    elif type_db == 'File':
        backup_path = report_data.get('PathBackUP')
        first_kassa_back = backup_path
    else:
        logger.error(f'Неизвестный тип БД, описанный в репорте ({type_db})')
        return {
            'status': 'error',
            'status_code': 'TYPE_DB_UNKNOWN_FORMAT',
            'description': f'Неизвестный формат БД, описанный в репорте ({type_db})'
        }

    if not os.path.exists(backup_path):
        logger.error(f'Не существует путь к папке бекапов (type: {type_db} / path: "{backup_path}")')
        return {
            'status': 'error',
            'type_db': type_db,
            'status_code': 'BACKUP_PATH_NOT_EXISTS',
            'description': f'Не существует путь к папке бекапов ({backup_path})'
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
        try:
            stderr = res.stderr.decode()
        except Exception:
            stderr = 'Unknown'
        logger.error('Не удалось дать общий доступ для папки бекапов:\n' + stderr)

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
        'type_db': type_db,
        'path': backup_path
    }


def create_msbox(text: str, *, title: str = 'Внимание', style: hex = MB_ICONINFORMATION):
    threading.Thread(  # Показываем MsBOX
        target=lambda: ctypes.windll.user32.MessageBoxW(0, text, title, MB_SYSTEMMODAL + style)
    ).start()


def send_data(send_dict: dict):
    import urllib
    import urllib.request
    url = 'http://78.37.67.153/retail_backup/'

    data = urllib.parse.urlencode(send_dict).encode('utf-8')
    req = urllib.request.Request(url, data)
    with urllib.request.urlopen(req) as response:
        _ = response.read()


def get_db_pc_name() -> str:
    conf_path = Path().home().joinpath(r'AppData\Roaming\1C\1CEStart\ibases.v8i')
    if not conf_path.is_file():
        raise FileNotFoundError

    conn_row = ''
    with open(conf_path, 'r', encoding='utf-8') as file:
        for row in file:
            if row.startswith('Connect='):
                conn_row = row
                break
        else:
            raise ValueError

    from urllib.parse import urlparse
    conn_list = conn_row.strip('\n').split('=')
    if 'ws' in conn_list:
        addr = conn_list[-1]
        addr = addr[addr.index('"') + 1:addr.rindex('"')]

        url = urlparse(addr)
        pcname = url.netloc
        if not pcname:
            raise ValueError

        pcname = pcname.split(':')[0].strip()  # Отсеиваем порт (если есть)

        return pcname

    elif 'Srvr' in conn_list:
        addr = conn_list[2]
        addr = addr[addr.index('"') + 1:addr.rindex('"')]

        return addr
    else:
        raise ValueError

    # if 'ws' in conn_list:  # С второстепенной базы
    #     addr = conn_list[-1]
    #     addr = addr[addr.index('"') + 1:addr.rindex('"')]
    #
    #     url = urlparse(addr)
    #     pcname = url.netloc
    #     if pcname:
    #         return pcname
    #     else:
    #         raise ValueError
    #
    # if 'File' in conn_list:  # С главной кассы, файловая БД
    #     addr = conn_list[-1]
    #     addr = addr[addr.index('"') + 1:addr.rindex('"')]
    #     print(addr)
    #
    # if 'Srvr' in conn_list:
    #     srv = conn_list[2]
    #     bas = conn_list[-1]
    #     srv = srv[srv.index('"') + 1:srv.rindex('"')]
    #     bas = bas[bas.index('"') + 1:bas.rindex('"')]
    #     addr = f'{srv}\\{bas}'
    #
    #     param = f'/S "{addr}"'


def comzav():
    try:
        pcname = get_db_pc_name()
    except FileNotFoundError:
        logger.error('Файл конфигурации ibases.v8i не найден')
        return {
            'status': 'error',
            'status_code': 'IBASES_FILE_ERROR',
            'description': f'Файл конфигурации ibases.v8i не найден'
        }

    except ValueError:
        logger.error('Файл конфигурации ibases.v8i некорректен')
        return {
            'status': 'error',
            'status_code': 'IBASES_FILE_ERROR',
            'description': f'Файл конфигурации ibases.v8i некорректен'
        }
    if pcname == 'pos-server':  # проверка на линукс сервер
        remote_path = fr'\\{pcname}\share\backups\retail'
    else:
        remote_path = fr'\\{pcname}\BackupRetail'

    try:
        listdir = os.listdir(remote_path)
    except PermissionError:
        logger.error(f'Отказано в досупе к расположению (PermissionError) "{remote_path}"')
        return {
            'status': 'error',
            'status_code': 'SHARE_FOLDER_PERMISSION_ERROR',
            'description': f'Отказано в досупе к расположению ({remote_path})'
        }
    except Exception:
        logger.error(f'Сетевое расположение ({remote_path}) не найдены)')
        return {
            'status': 'error',
            'status_code': 'SHARE_FOLDER_NOT_FOUND',
            'description': 'Не найдено сетевое расположение бекапов базы'
        }

    # Отсеивание по размерам
    backup_list = [os.path.join(remote_path, file) for file in listdir]
    corr_backup_list = []
    for path in backup_list:
        size = 0
        if os.path.isfile(path):  # Архивные + SQL
            size = os.path.getsize(path) / (2 ** 30)

        if os.path.isdir(path):  # Полновестные
            size = sum(os.path.getsize(file) for file in Path(path).glob('**/*') if file.is_file()) / (2 ** 30)

        if size > .5:
            corr_backup_list.append(path)

    backup_list = corr_backup_list
    # Отсеиваем полновестные бекапы в день релиза
    backup_list = list(filter(lambda x: not x.endswith('.1CD'), backup_list))

    if not backup_list:
        logger.error(f'В удалённой директории бекапов ({remote_path}) отсутсвуют бекапы')
        return {
            'status': 'error',
            'status_code': 'BACKUP_FOLDER_IS_EMPTY',
            'description': f'В удалённой директории бекапов ({remote_path}) отсутсвуют бекапы'
        }

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

    # Проверка свободного места (кроме полновестных)
    backup_size = os.path.getsize(last_backup) / (2 ** 30)

    _, _, free_disk_space = shutil.disk_usage(__file__)
    free_disk_space /= (2 ** 30)
    if free_disk_space - 0.5 < backup_size and os.path.isfile(last_backup):
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
    if os.path.isfile(last_backup) and os.path.basename(last_backup) in backup_local_list:
        # Сверка размеров (кроме полновестных)
        local_backup = os.path.join(path_to_local_backup, os.path.basename(last_backup))

        size_equal = os.path.getsize(local_backup) == os.path.getsize(last_backup)
        if size_equal:
            logger.error(f'Бекап "{last_backup}" уже существует в локальной директории')
            return {
                    'status': 'error',
                    'status_code': 'LOCAL_BACKUP_EXISTS',
                    'description': f'Локальный бекап уже существует ({local_backup})'
                }
    elif os.path.isdir(last_backup) and os.path.basename(last_backup) + '.zip' in backup_local_list:
        logger.error(f'Бекап "{last_backup}" уже существует в локальной директории')
        return {
            'status': 'error',
            'status_code': 'LOCAL_BACKUP_EXISTS',
            'description': f'Локальный бекап уже существует (FULL SIZE)'
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
    fullsize = False
    try:
        if os.path.isfile(last_backup):
            shutil.copy2(last_backup, path_to_local_backup)

        elif os.path.isdir(last_backup):
            fullsize = True
           #  output_filename = os.path.join(path_to_local_backup, os.path.basename(last_backup))
           #  output_filename = os.path.join(remote_path, os.path.basename(last_backup))
           #  shutil.make_archive(output_filename, 'zip', last_backup)
           #  shutil.copy2(last_backup, path_to_local_backup)
            sys.exit()

    except OSError as ex:
        description = f'Ошибка во время копирования бекапа (fullsize: {fullsize})'
        log_text = f'Не удалось скопировать бекап "{last_backup}" в локальную директорию "{path_to_local_backup}"'
        if ex.errno == errno.ENOSPC:  # No space left on device
            description = f'Недостаточно места для создания временных файлов во время копирования [Errno {ex.errno}]'
            log_text = f'Недостаточно места для создания временных файлов во время копирования [Errno {ex.errno}]'

        elif ex.errno == errno.EACCES:  # Permission denied
            description = f'Нет доступа к удалённому бекапу (Permission denied) [Errno {ex.errno}]'
            log_text = f'Нет доступа к удалённому бекапу (Permission denied) [Errno {ex.errno}]'

        logger.error(log_text, exc_info=True)
        err_msgbox()

        try:
            os.remove(path_to_local_backup)
        except Exception:
            pass

        return {
            'status': 'error',
            'status_code': 'BACKUP_COPY_ERROR',
            'description': description
        }

    except Exception:
        logger.error(
            f'Не удалось скопировать бекап "{last_backup}" в локальную директорию "{path_to_local_backup}"',
            exc_info=True
        )
        err_msgbox()

        try:
            os.remove(path_to_local_backup)
        except Exception:
            pass

        return {
            'status': 'error',
            'status_code': 'BACKUP_COPY_ERROR',
            'description': f'Ошибка во время копирования бекапа (fullsize: {fullsize})'
        }

    copy_time_new = time.time() - start_time
    save_copy_time(int(copy_time_new))

    logger.info(f'Копирование бекапа успешно завершено успешно завершено (time: {copy_time_new})')
    end_text = 'Копирование базы 1С успешно завершено, можете продолжать работу. Хорошего дня!'
    create_msbox(end_text, title='Успешно')

    return {
        'status': 'success',
        'copy_time': copy_time_new,
        'fullsize': fullsize
    }


def err_msgbox():
    create_msbox(
        'Во время копирования базы 1С произошла ошибка. Можете продолжать работу, хорошего дня!',
        title='Ошибка', style=MB_ICONERROR
    )


def archive():  # архивирование последнего бэкапа на 1 кассе, если это папка
    listdir = os.listdir(first_kassa_back)  # получаем список папок
    backup_list = [os.path.join(first_kassa_back, file) for file in listdir]  # получаем пути
    backup_list = list(filter(lambda x: not x.endswith('.1CD'), backup_list))  # отсев в день релиза
    last_time = 0
    last_backup = None
    for file in backup_list:  # ищем последний бэкап
        filemtime = os.path.getmtime(file)
        if filemtime > last_time:
            last_time = filemtime
            last_backup = file
    if os.path.isdir(last_backup):  # если это папка, то архивируем
        shutil.make_archive(last_backup, 'zip', last_backup)
    else:
        pass


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

    try:
        if device in [1, 99]:
            res_dict = first_kassa()
            try:
                archive()  # пытаемся заархивить последний бэкап
            except Exception:
                pass
        elif device == 0 and need_backup:
            res_dict = comzav()
            if res_dict.get('status') == 'success' or res_dict.get('status_code') == 'BACKUP_COPY_ERROR':
                now = str(time.time())
                configuration.settings.reg_data.set_reg_key('LastComZavBackRetail', now)  # Время последнего бекапа
        else:
            return
    except Exception:
        logger.error('Необрабатываемая ошибка!', exc_info=True)
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

