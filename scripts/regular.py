import datetime
import os
import win32com.client

from bin.values import *

try:  # Для автокомплита
    from objects import *
except (ImportError, ModuleNotFoundError):
    pass

script_name = 'regular.py'  # Имя скрипта

NOT_FOUND_FLAG = 'not_found'
UNCORRECT_FLAG = 'uncorrect'
CORRECT_FLAG = 'correct'


# Возвращает время задачи, либо None
def get_task_shedule_datetime():
    # Планировщик задач
    scheduler = win32com.client.Dispatch('Schedule.Service')  # Подключаемся к службе планировщика
    scheduler.Connect()

    TASK_ACTION_EXEC = 0  # Признак типа задачи "Запуск программы"
    TASK_TRIGGER_DAILY = 2  # Тип триггера "Запускать задачу в определённое время"

    n = 0
    folders = [scheduler.GetFolder('\\')]  # Получаем все папки
    needed_task = None  # Тут будет необходимая задача (если будет)
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
                'time': dat.time().isoformat()
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


def script(configuration: ConfigurationsObject):
    configuration.settings.logger.info(f'Запущен побочный скрипт {script_name}')

    desktop_path = os.path.join(os.getenv('USERPROFILE'), 'Desktop')  # Путь к робочему столу
    path_to_ammy_admin = os.path.join(ROOT_PATH, SOFT_DIR_NAME, AMMY_ADMIN_NAME)  # Путь к AmmyAdmin
    path_to_clear_1c = os.path.join(ROOT_PATH, SOFT_DIR_NAME, CLEAR_1C_NAME)  # Путь к батнику Чистка 1С

    if os.path.exists(path_to_ammy_admin):  # Если существует
        try:
            os.symlink(path_to_ammy_admin, os.path.join(desktop_path, 'AA'))
        except (OSError, FileExistsError):  # Если нет прав, либо ссылка уже существует
            pass

    if os.path.exists(path_to_clear_1c):
        try:
            os.symlink(path_to_clear_1c, os.path.join(desktop_path, 'Чистка 1C'))
        except (OSError, FileExistsError):  # Если нет прав, либо ссылка уже существует
            pass

    res = get_task_shedule_datetime()
    print(res)