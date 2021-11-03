import datetime
import os
import pathlib
import random
import subprocess
import sys
import time
from subprocess import Popen, DEVNULL
import winreg as reg

from typing import Union

import win32com.client

from bin.values import *
from objects import *

# Ключи словаря конфигурации
PHARMACY_DICT_KEY = 'pharmacy'
DEVICE_DICT_KEY = 'device'
TASK_DATA_KEY = 'task_data'
REBOOT_TIME_KEY = 'reboot_time'
BACKUP_DATA_KEY = 'backup_data'
REG_DATA_KEY = 'reg_data'

# Параметры task sheduler
NOT_FOUND_FLAG = 'not_found'
UNCORRECT_FLAG = 'uncorrect'
CORRECT_FLAG = 'correct'

# Параметры backup
BACKUP_NAME = 'backup_name'
CREATION_TIME = 'creation_time'
FULL_BASE_BACKUP = 'full_base'
ZIP_BASE_BACKUP = 'zip_base'


# Возвращает развёрнутый словарь задачи планировщика
def get_task_shedule_dict() -> dict:
    # Планировщик задач
    scheduler = win32com.client.Dispatch('Schedule.Service')  # Подключаемся к службе планировщика
    scheduler.Connect()

    TASK_ACTION_EXEC = 0  # Признак типа задачи "Запуск программы"
    TASK_TRIGGER_DAILY = 2  # Тип триггера "Запускать задачу в определённое время"

    n = 0
    folders = [scheduler.GetFolder('\\')]  # Получаем все папки
    needed_task = None  # Тут будет необходимая задача (если будет)
    path_to_exec = None  # Путь к батнику (если есть)
    while folders:  # Проходим по всем папкам в корне
        cur_folder = folders.pop(0)  # Удаляем папку из списка и работаем с ней
        folders += list(cur_folder.GetFolders(0))  # ?
        tasks = list(cur_folder.GetTasks(1))  # Получаем задачи
        n += len(tasks)

        for task in tasks:  # Проходим по зпдачам
            actions = task.Definition.Actions  # Действия задачи

            for action_index in range(1, actions.Count + 1):  # Проходим по действиям
                cur_action = actions.Item(action_index)  # Конкретное действие

                if cur_action.Type == TASK_ACTION_EXEC:  # Если действие - запуск исполняемого файла
                    path_to_exec = cur_action.Path  # Путь к исполняемому файлу
                    path_to_exec = path_to_exec.strip('"')  # Убираем кавычки
                    if path_to_exec.endswith('reg.bat'):
                        needed_task = task  # Пишем задачу
                        break
                else:  # Если нет - ищем дальше
                    continue

            if needed_task:
                break

        if needed_task:
            break

    if needed_task:  # Если задача найдена
        triggers = needed_task.Definition.Triggers  # Триггеры задачи
        if triggers.Count > 1:  # Если болье одного триггера
            return {
                'flag': UNCORRECT_FLAG,
                'description': f'Установленно более одного триггера на задание ({triggers.Count})'
            }

        cur_trigger = triggers.Item(1)  # Конкретный триггер
        trigger_datetime = None
        if cur_trigger.Type == TASK_TRIGGER_DAILY:  # Если корректный тригер (Ежедневное выполнение)
            trigger_datetime = cur_trigger.StartBoundary  # Время выполнения задачи
            dat = datetime.datetime.fromisoformat(trigger_datetime)  # Преобразуем к datetime

            return {
                'flag': CORRECT_FLAG,
                'state': needed_task.State,
                'time': dat.time().isoformat(),
                'path': path_to_exec
            }

        else:  # Некорректный триггер задачи
            return {
                'flag': UNCORRECT_FLAG,
                'description': f'Некорректный триггер задачи ({cur_trigger.Type})'
            }
    else:  # Если не найдена
        return {
            'flag': NOT_FOUND_FLAG
        }


# Возвращает, необходимо ли инициализировать задачу по перезапуску IIS (также отправляет данные на сервер)ы
def need_init_iisrestart(configuration: ConfigurationsObject):
    REG_TASK_MODE = 'reg_task'  # Режим работы проверки регзадания

    task_dict = get_task_shedule_dict()  # Получаем данные по задаче
    reg_dict = check_reg_param()  # Получаем параметры из реестра (если есть)

    task_dict[REG_DATA_KEY] = reg_dict

    # Словарь для отправки
    send_dict = {
        PHARMACY_DICT_KEY: configuration.pharmacy_or_subgroup,
        DEVICE_DICT_KEY: configuration.device_or_name,
        TASK_DATA_KEY: task_dict,
    }

    try:
        hello_dict = SSHConnection.get_hello_dict(REG_TASK_MODE, send_dict)  # Словарь приветсвия
        sock = SSHConnection.get_tcp_socket()  # Создаём сокет

        sock.connect((configuration.host, SCHEDULER_DEMON_PORT))  # Устанавливаем соединение
        sock.send(hello_dict.encode())  # Отправляем данные
        sock.close()  # Закрываем сокет

    except Exception:
        configuration.settings.logger.error('Не удалось отправить на сервер данные по регзаданию планировщика',
                                            exc_info=True)

    flag = task_dict.get('flag')  # Извлекаем флаг таска
    if flag == CORRECT_FLAG:  # Если корректно
        return task_dict  # Возвращаем время таска
    else:
        return None


# Отправляем данные о последнем ребуте IIS
def send_iis_reboot_data(configuration: ConfigurationsObject):
    LAST_REBOOT_DATA_MODE = 'last_reboot'

    init_dict = {
        PHARMACY_DICT_KEY: configuration.pharmacy_or_subgroup,
        DEVICE_DICT_KEY: configuration.device_or_name,
        REBOOT_TIME_KEY: datetime.datetime.now().isoformat()
    }

    try:
        hello_dict = SSHConnection.get_hello_dict(LAST_REBOOT_DATA_MODE, init_dict)  # Словарь приветсвия
        sock = SSHConnection.get_tcp_socket()  # Создаём сокет

        sock.connect((configuration.host, SCHEDULER_DEMON_PORT))  # Устанавливаем соединение
        sock.send(hello_dict.encode())  # Отправляем данные
        sock.close()  # Закрываем сокет

        configuration.settings.logger.info('Данные по ребуту IIS отправленны на сервер')
    except Exception:
        configuration.settings.logger.error('Не удалось отправить на сервер время последнего перезапуска IIS',
                                            exc_info=True)


# Создаёт ярлык запуска IIS на рабочем столе
def create_iis_start_link():
    desktop_path = os.path.join(os.getenv('USERPROFILE'), 'Desktop')  # Путь к робочему столу

    path_to_iis_start_script = os.path.join(ROOT_PATH, SCRIPTS_DIR_NAME, IIS_START_SCRIP_NAME)
    if os.path.exists(path_to_iis_start_script):
        try:
            os.symlink(path_to_iis_start_script, os.path.join(desktop_path, 'ЗАПУСТИТЬ IIS'))
        except (OSError, FileExistsError):  # Если нет прав, либо ссылка уже существует
            pass


# Удаляет ярлык запуска IIS с рабочего стола
def delete_iis_start_link():
    desktop_path = os.path.join(os.getenv('USERPROFILE'), 'Desktop')  # Путь к робочему столу
    path_to_link = os.path.join(desktop_path, 'ЗАПУСТИТЬ IIS')

    if os.path.exists(path_to_link):
        try:
            os.remove(path_to_link)
        except (OSError, FileExistsError):  # Если нет прав, либо ссылка уже существует
            pass


# Останавливает службу IIS и отправляет данные об этом на сервер
def iis_stop(configuration: ConfigurationsObject):
    configuration.settings.logger.info('Служба IIS остановлена')
    Popen('iisreset /STOP', shell=True, stdout=DEVNULL, stderr=DEVNULL)  # Останавливаем IIS

    try:
        create_iis_start_link()
    except Exception:
        configuration.settings.logger.error(
            'Не удалось создать ссылку на запуск служб IIS в период её отключения', exc_info=True
        )

    time.sleep(random.randint(0, 5 * 60) + random.random()) # Засыпает на случайное время перед отправкой

    send_iis_reboot_data(configuration)  # Отправляем данные на сервер

    time.sleep(1)


# Запускает службу IIS
def iis_start(configuration: ConfigurationsObject, path_to_backup: Union[Path, None]):
    configuration.settings.logger.info('Служба IIS запущена')
    Popen('iisreset /START', shell=True, stdout=DEVNULL, stderr=DEVNULL)  # Запускаем IIS

    try:
        delete_iis_start_link()  # Удаляем ссылку запуска IIS
    except Exception:
        pass

    time.sleep(random.randint(0, 5 * 60) + random.random())  # Засыпает на случайное время

    try:
        send_backup_data(configuration, path_to_backup)  # Отправляем данные по бекапам
    except Exception:
        configuration.settings.logger.info(
            'Не удалось отправить данные по бекапам на сервер', exc_info=True
        )


# Получает данные о последнем бекапе
def get_base_backup_data(path_to_backup: Path):
    listdir = os.listdir(path_to_backup)  # Список файлов

    zip_list = []  # Список zip-архивов
    base_list = []  # Список полновесных бекапов
    for file in listdir:  # Проходим по файлам
        if file.endswith('.zip'):  # Если zip-архив
            zip_list.append(path_to_backup / file)

        if file.endswith('.1CD'):  # Если полновесная база
            base_list.append(path_to_backup / file)

        if os.path.isdir(path_to_backup / file):  # Если папка
            base_list.append(path_to_backup / file)

    last_zip_time = 0
    last_zip_file = None
    for path_to_file in zip_list:  # Проходим по zip базам (если есть)
        creation_time = path_to_file.stat().st_mtime  # Время последней модификации

        if creation_time > last_zip_time:  # Если время больше
            last_zip_time = creation_time  # Пишем время (для сравнения)
            last_zip_file = path_to_file  # Пишем файл

    last_base_time = 0
    last_base_file = None
    for path_to_file in base_list:  # Проходим по полновесным базам (если есть)
        creation_time = path_to_file.stat().st_mtime  # Время последней модификации

        if creation_time > last_base_time:  # Если время больше
            last_base_time = creation_time  # Пишем время (для сравнения)
            last_base_file = path_to_file  # Пишем файл

    full_base_dict = None
    if last_base_file:  # Если есть полновесная база
        full_base_dict = {
            BACKUP_NAME: str(last_base_file),
            CREATION_TIME: datetime.datetime.fromtimestamp(last_base_time).isoformat()
        }

    zip_base_dict = None
    if last_zip_file:  # Если есть zip база
        zip_base_dict = {
            BACKUP_NAME: str(last_zip_file),
            CREATION_TIME: datetime.datetime.fromtimestamp(last_zip_time).isoformat()
        }

    return {  # Возвращает данные по базам
        FULL_BASE_BACKUP: full_base_dict,
        ZIP_BASE_BACKUP: zip_base_dict
    }


# Отправляет данные по бекапам на сервер
def send_backup_data(configuration: ConfigurationsObject, path_to_backup: Union[Path, None]):
    if path_to_backup is None:  # Если пути нет - ничего не делаем
        return

    BACKUP_DATA_MODE = 'backup_data_mode'

    backup_data = get_base_backup_data(path_to_backup)  # Получаем данные по бекапам
    init_dict = {
        PHARMACY_DICT_KEY: configuration.pharmacy_or_subgroup,
        DEVICE_DICT_KEY: configuration.device_or_name,
        BACKUP_DATA_KEY: backup_data
    }

    try:
        hello_dict = SSHConnection.get_hello_dict(BACKUP_DATA_MODE, init_dict)  # Словарь приветсвия
        sock = SSHConnection.get_tcp_socket()  # Создаём сокет

        sock.connect((configuration.host, SCHEDULER_DEMON_PORT))  # Устанавливаем соединение
        sock.send(hello_dict.encode())  # Отправляем данные
        sock.close()  # Закрываем сокет

        configuration.settings.logger.info('Данные по бекапам базы отправленны на сервер')
    except Exception:
        configuration.settings.logger.error('Не удалось отправить на сервер данные по бекапам базы',
                                            exc_info=True)


# Проверяет параметры в Report (печать DataMatrix)
def check_reg_param():
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

    return reg_dict


# Возвращает путь к бекапам, либо None
def get_path_for_backup(reg_data: dict, task_dict: dict) -> Union[Path, None]:
    path_to_backup = reg_data.get('PathBackUP')  # Извлекает путь к бекапу из реестра (если есть)
    if not path_to_backup:
        path_to_reg = task_dict.get('path')  # Извлекает путь к бекапу из файла регазадания
        if not path_to_reg:
            return None

        path_to_backup = Path(path_to_reg).parent  # Получаем путь к директории

    else:
        path_to_backup = Path(path_to_backup)

    return path_to_backup


EVERY_DAY_PHARMACY = [
    3.0, 4.0, 10.0, 11.1, 12.0, 20.0, 23.0, 38.0, 45.0, 53.0, 63.0, 76.0, 84.0, 89.0, 111.0, 132.0, 135.0, 188.0,
    224.0, 250.0, 262.0, 268.0, 287.0, 288.0, 292.0, 303.0, 360.0, 361.0, 395.0, 403.0, 458.0, 469.0, 546.0, 547.0,
    548.0, 549.0, 595.0, 596.0, 606.0
]


# Возвращает время задачи, либо None
def script(configuration: ConfigurationsObject, scheduler: AppScheduler):
    if int(configuration.device_or_name) in (1, 99):  # Если первая касса, либо сервер
        configuration.settings.logger.info(f'Корректировка настроек планировщика')

        task_dict = need_init_iisrestart(configuration)  # Вернёт словарь, если необходима задача
        reg_data = task_dict.get(REG_DATA_KEY, {})

        if reg_data is None:
            reg_data = {}

        # === Отправка данных по бекапам =====
        path_to_backup = None
        try:
            path_to_backup = get_path_for_backup(reg_data, task_dict)  # Получаем данные по бекапам (либо None)
            send_backup_data(configuration=configuration, path_to_backup=path_to_backup)
        except Exception:
            configuration.settings.logger.error(
                'Не удалось отправить данные о бекапах базы на сервер', exc_info=True
            )

        # if not reg_data:
        #     configuration.settings.logger.info('Ключ Report в реестре не обнаружен, настройка планировщика прервана')

        type_ib = reg_data.get('TypeIB')  # Получаем тип БД
        if type_ib == 'Server':
            configuration.settings.logger.info('1С подключена к SQL БД, настройка планировщика не требуется')
            return  # Завершаем работу

        if float(configuration.pharmacy_or_subgroup) in EVERY_DAY_PHARMACY:  # Проверка на круглосутки
            configuration.settings.logger.info(
                'Аптека из списка круглосуточных, корректировака настроек планировщика прервана')
            return

        backup_type = reg_data.get('BackUPType')  # Как настроено бекапирование
        # if not backup_type:
        #     configuration.settings.logger.info(
        #         'Не обнаружен тип резервного копирования, настройка планировщика прервана')
        #     return

        if backup_type == 'ТехПерерыв':
            configuration.settings.logger.info(
                'Настройки резервного копирования соответсвуют круглосуточной аптеки, настройка планировщика завершена'
            )
            return

        task_time = task_dict.get('time')  # Извлекает время
        if task_time:  # Если есть время регзадания и аптека не круглосуточная
            task_time = datetime.time.fromisoformat(task_time)  # Преобразуем к time

            # === Создаёт задачу перезапуска IIS ===
            task_time_timedelta = datetime.timedelta(hours=task_time.hour, minutes=task_time.minute,
                                                     seconds=task_time.second)
            # Вычитаем из времени 10 минут (ОСТАНОВКА IIS)
            time_for_stop_iis = task_time_timedelta - datetime.timedelta(minutes=10)

            time_for_stop_iis_str = str(time_for_stop_iis)
            if time_for_stop_iis.total_seconds() < 0:  # Если -1 days
                time_for_stop_iis_str = time_for_stop_iis_str.split(',')[-1].strip()

            # Лечит запись виндовского планировщика на ночное время
            if len(time_for_stop_iis_str.split(':')[0]) == 1:
                time_for_stop_iis_str = '0' + time_for_stop_iis_str  # Прибавляем 0

            # Прибовляем 1 час (ЗАПУСК IIS)
            time_for_start_iis = task_time_timedelta + datetime.timedelta(hours=1)
            # time_for_start_iis = time_for_stop_iis + datetime.timedelta(seconds=30)  # Для отладки

            time_for_start_iis_str = str(time_for_start_iis)
            if time_for_start_iis.total_seconds() >= 60 * 60 * 24:
                time_for_start_iis_str = time_for_start_iis_str.split(',')[-1].strip()

            if len(time_for_start_iis_str.split(':')[0]) == 1:
                time_for_start_iis_str = '0' + time_for_start_iis_str  # Прибавляем 0

            # Создаём задачи
            scheduler.scheduler.every().day.at(time_for_stop_iis_str).do(iis_stop, configuration=configuration)
            scheduler.scheduler.every().day.at(time_for_start_iis_str).do(iis_start, configuration=configuration,
                                                                          path_to_backup=path_to_backup)

            configuration.settings.logger.info(
                f'Создана задача остановки IIS в планировщике [{time_for_stop_iis_str} - {time_for_start_iis_str}]'
            )
