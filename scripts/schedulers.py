import datetime
import subprocess
import time
from subprocess import Popen, DEVNULL

import win32com.client

from bin.values import *
from objects import *

# Ключи словаря конфигурации
PHARMACY_DICT_KEY = 'pharmacy'
DEVICE_DICT_KEY = 'device'
TASK_DATA_KEY = 'task_data'
REBOOT_TIME = 'reboot_time'

# Параметры task sheduler
NOT_FOUND_FLAG = 'not_found'
UNCORRECT_FLAG = 'uncorrect'
CORRECT_FLAG = 'correct'


# Возвращает развёрнутый словарь задачи планировщика
def get_task_shedule_dict():
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
    flag = task_dict.get('flag')  # Извлекаем флаг таска

    # Словарь для отправки
    send_dict = {
        PHARMACY_DICT_KEY: configuration.pharmacy_or_subgroup,
        DEVICE_DICT_KEY: configuration.device_or_name,
        TASK_DATA_KEY: task_dict
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

    if flag == CORRECT_FLAG:  # Если корректно
        return task_dict.get('time')  # Возвращаем время таска
    else:
        return None


# Отправляем данные о последнем ребуте IIS
def send_iis_restart_data(configuration: ConfigurationsObject):
    LAST_REBOOT_DATA_MODE = 'last_reboot'

    init_dict = {
        PHARMACY_DICT_KEY: configuration.pharmacy_or_subgroup,
        DEVICE_DICT_KEY: configuration.device_or_name,
        REBOOT_TIME: datetime.datetime.now().isoformat()
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


# Перезапускает службу IIS
def iis_restart(configuration: ConfigurationsObject):
    configuration.settings.logger.info('Служба IIS перезапущена')
    Popen('iisreset /RESTART', shell=True, stdout=DEVNULL, stderr=DEVNULL)   # Ребутим IIS
    send_iis_restart_data(configuration)  # Отправляем данные на сервер
    time.sleep(1)


# Возвращает время задачи, либо None
def script(configuration: ConfigurationsObject, scheduler: AppScheduler):
    configuration.settings.logger.info(f'Корректировка настроек планировщика')

    if int(configuration.device_or_name) in (1, 99):  # Если первая касса, либо сервер
        task_time = need_init_iisrestart(configuration)  # Вернёт время, если необходима задача

        # Если вернулось время и в списке аптек
        if task_time:
            task_time = datetime.time.fromisoformat(task_time)  # Преобразуем к time
            # Вычитаем из времени 10 минут
            time_for_restart_iis = datetime.timedelta(hours=task_time.hour, minutes=task_time.minute,
                                                      seconds=task_time.second) - datetime.timedelta(minutes=10)
            time_for_restart_iis_str = str(abs(time_for_restart_iis))  # Преобразуем время к строке

            # Лечит запись виндовского планировщика на ночное время
            if len(time_for_restart_iis_str.split(':')[0]) == 1:
                time_for_restart_iis_str = '0' + time_for_restart_iis_str  # Прибавляем 0

            # Создаёт задачу
            scheduler.scheduler.every().day.at(time_for_restart_iis_str).do(iis_restart, configuration=configuration)
            configuration.settings.logger.info(f'Создана задача перезапуска IIS в '
                                               f'планировщике ({time_for_restart_iis_str})')
