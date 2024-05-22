# import datetime
# import os
# import pathlib
# import random
# import subprocess
# import sys
# import time
# import traceback
# import types
# from subprocess import Popen, DEVNULL
# import winreg as reg
#
# from typing import Union
# import win32com.client
#
# import send_http
# from bin.values import *
from objects import *
# from send_http import *
#
# # Ключи словаря конфигурации
# PHARMACY_DICT_KEY = 'pharmacy'
# DEVICE_DICT_KEY = 'device'
# TASK_DATA_KEY = 'task_data'
# BACKUP_DATA_KEY = 'backup_data'
# REG_DATA_KEY = 'reg_data'
#
# # Параметры task sheduler
# NOT_FOUND_FLAG = 'not_found'
# UNCORRECT_FLAG = 'uncorrect'
# CORRECT_FLAG = 'correct'
#
# # Параметры backup
# BACKUP_NAME = 'backup_name'
# CREATION_TIME = 'creation_time'
# FULL_BASE_BACKUP = 'full_base'
# ZIP_BASE_BACKUP = 'zip_base'
#
# # NEW
# MAIN_SCHEDULER = 'schedule'
#
# ACTION_SAVE_REG_TASK = 'reg_task'
# ACTION_SAVE_BACKUP_DATA_MODE = 'backup_data_mode'
# ACTION_STOP_IIS = 'iis_stop'
#
# # TODO DEBUG
# # DEBUG = True
# # TEST_TIME = '12:00:50'
#
#
# # Возвращает случайное время регзадание
# def get_random_regtask_datetime():
#     now = datetime.datetime.now()
#     st_hour = random.choice([23, 0, 0])  # 1/3 Стартовый час
#
#     # Стартовое время
#     countdown_time = datetime.datetime(year=now.year, day=now.day, month=now.month, hour=st_hour, minute=0, second=0)
#
#     range_minuts = 60 if st_hour == 23 else 120  # Прибавляемые минуты
#     trigger_time = countdown_time + datetime.timedelta(minutes=random.randrange(0, range_minuts),
#                                                        seconds=random.randrange(0, 60))  # Прибавляем случайное время
#
#     return trigger_time
#
#
# # Ищет необходимую задачу в Планировщике событий
# def find_schedule_regtask():
#     scheduler = win32com.client.Dispatch('Schedule.Service')  # Подключаемся к службе планировщика
#     scheduler.Connect()
#
#     TASK_ACTION_EXEC = 0  # Признак типа задачи "Запуск программы"
#
#     folders = [scheduler.GetFolder('\\')]  # Папки (задачи)
#     needed_task = None  # Тут будет необходимая задача (если будет)
#
#     while folders:  # Проходим по всем папкам в корне
#         cur_folder = folders.pop(0)  # Удаляем папку из списка и работаем с ней
#         folders += list(cur_folder.GetFolders(0))  # Подпапки (?)
#         tasks = list(cur_folder.GetTasks(1))  # Получаем задачи
#
#         for task in tasks:  # Проходим по зпдачам
#             actions = task.Definition.Actions  # Действия задачи
#
#             for action_index in range(1, actions.Count + 1):  # Проходим по действиям
#                 cur_action = actions.Item(action_index)  # Конкретное действие
#
#                 if cur_action.Type == TASK_ACTION_EXEC:  # Если действие - запуск исполняемого файла
#                     path_to_exec = cur_action.Path  # Путь к исполняемому файлу
#                     path_to_exec = path_to_exec.strip('"')  # Убираем кавчки
#
#                     if path_to_exec.endswith('reg.bat'):
#                         needed_task = task  # Пишем задачу
#                         break
#
#                 else:  # Если нет - ищем дальше
#                     continue
#
#             if needed_task:
#                 break
#
#         if needed_task:
#             break
#     else:
#         return None
#
#     return needed_task
#
#
# # Инициализирует настройку регзадания в планировщике
# def init_reg_task() -> dict:
#     old_task = find_schedule_regtask()  # Получаем старую задачу
#
#     # Автор - флаг, создавалась ли уже задача RM
#     AUTO_REMOTE_AUTHOR = 'AUTO_REMOTE'
#
#     # if not DEBUG:  # TODO
#     if not old_task:  # Если задача не найдена
#         return {
#             'flag': NOT_FOUND_FLAG
#         }
#
#     author = old_task.Definition.RegistrationInfo.Author  # Получаем автора задачи
#     if author == AUTO_REMOTE_AUTHOR:  # Если уже создавали - ничего не делать
#         # Актуализация данных
#         time_task = old_task.Definition.Triggers.Item(1).StartBoundary
#         time_task = datetime.datetime.fromisoformat(time_task).time().isoformat()  # Преобразуем к time
#         path_to_reg_bat = old_task.Definition.Actions.Item(1).Path
#
#         return {
#             'flag': CORRECT_FLAG,
#             'time': time_task,
#             'path': path_to_reg_bat
#         }
#
#     scheduler = win32com.client.Dispatch('Schedule.Service')
#     scheduler.Connect()
#     root_folder = scheduler.GetFolder('\\')  # Корневая директория
#     task_def = scheduler.NewTask(0)  # Создаём новую задачу
#
#     # Триггер задачи
#     trigger_time = get_random_regtask_datetime()  # Случайное время регзадания
#     TASK_TRIGGER_DAILY = 2  # Запуск каждый день
#     trigger = task_def.Triggers.Create(TASK_TRIGGER_DAILY)  # Создаём задачу
#
#     # if TEST_TIME:  # TODO
#     #     ti = [int(el) for el in TEST_TIME.split(':')]
#     #     now = datetime.datetime.now()
#     #     trigger_time = datetime.datetime(year=now.year, month=now.month, day=now.day,
#     #                                      hour=ti[0], minute=ti[1], second=ti[2])
#
#     trigger.StartBoundary = trigger_time.isoformat()  # Время запуска
#
#     task_def.Actions = old_task.Definition.Actions  # Присваеваем новой задачи старое действие
#
#     # Параметры задачи
#     task_def.RegistrationInfo.Description = 'Обновление 1С, создание бекапов базы'
#     task_def.RegistrationInfo.Author = AUTO_REMOTE_AUTHOR
#     task_def.Settings.Enabled = True
#
#     # Регистрируем задачу
#     TASK_NAME = 'Регзадание 1С'
#     TASK_CREATE_OR_UPDATE = 6  # Создать, либо обновить
#     TASK_LOGON_NONE = 0
#     root_folder.RegisterTaskDefinition(
#         TASK_NAME,
#         task_def,
#         TASK_CREATE_OR_UPDATE,
#         '',  # Без пользователя
#         '',  # Без пароля
#         TASK_LOGON_NONE)
#
#     # if not DEBUG:  # TODO
#     try:
#         root_folder.DeleteTask(old_task.Name, 0)  # Удаляем предыдущую задачу [АДМИНИСТРАТОР]
#     except Exception:  # Если не удалось удалить старую задачу
#         pass
#
#     path_to_reg_bat = task_def.Actions.Item(1).Path  # Путь к батнику
#     return {
#         'flag': CORRECT_FLAG,
#         'time': trigger_time.time().isoformat(),
#         'path': path_to_reg_bat
#     }
#
#
# # Инициализирует работу скрипта
# def init_scheduler(configuration: ConfigurationsObject) -> Union[dict, None]:
#     task_dict = init_reg_task()  # Инициализируем регзадание
#
#     reg_dict = check_reg_param()  # Получаем параметры из реестра (если есть)
#     task_dict[REG_DATA_KEY] = reg_dict  # Пишем данные из реестра
#     send_http.send_data(
#         method=METHOD_SAVE,
#         identifier=configuration.get_initialization_dict(),
#         main=MAIN_SCHEDULER,
#         action=ACTION_SAVE_REG_TASK,
#         data=task_dict,
#         logger=configuration.settings.logger
#     )  # Отправляем данные на сервер
#
#     return task_dict if task_dict.get('flag') == CORRECT_FLAG else None
#
#
# # Отправляем данные об остановке IIS
# def send_iis_stop_data(configuration: ConfigurationsObject):
#     send_data(
#         method=METHOD_SAVE,
#         identifier=configuration.get_initialization_dict(),
#         main=MAIN_SCHEDULER,
#         action=ACTION_STOP_IIS,
#         data=datetime.datetime.now().isoformat(),
#         logger=configuration.settings.logger
#     )
#
#
# # Создаёт ярлык запуска IIS на рабочем столе
# def create_iis_start_link():
#     desktop_path = os.path.join(os.getenv('USERPROFILE'), 'Desktop')  # Путь к робочему столу
#
#     path_to_iis_start_script = os.path.join(ROOT_PATH, SCRIPTS_DIR_NAME, IIS_START_SCRIP_NAME)
#     if os.path.exists(path_to_iis_start_script):
#         try:
#             os.symlink(path_to_iis_start_script, os.path.join(desktop_path, 'ЗАПУСТИТЬ IIS'))
#         except (OSError, FileExistsError):  # Если нет прав, либо ссылка уже существует
#             pass
#
#
# # Удаляет ярлык запуска IIS с рабочего стола
# def delete_iis_start_link():
#     desktop_path = os.path.join(os.getenv('USERPROFILE'), 'Desktop')  # Путь к робочему столу
#     path_to_link = os.path.join(desktop_path, 'ЗАПУСТИТЬ IIS')
#
#     if os.path.exists(path_to_link):
#         try:
#             os.remove(path_to_link)
#         except (OSError, FileExistsError):  # Если нет прав, либо ссылка уже существует
#             pass
#
#
# # Останавливает службу IIS и отправляет данные об этом на сервер
# def iis_stop(configuration: ConfigurationsObject):
#     configuration.settings.logger.info('Служба IIS остановлена')
#     Popen('iisreset /STOP', shell=True, stdout=DEVNULL, stderr=DEVNULL)  # Останавливаем IIS
#
#     try:
#         create_iis_start_link()  # Создаём линк запуска IIS
#     except Exception:
#         configuration.settings.logger.error(
#             'Не удалось создать ссылку на запуск служб IIS в период её отключения', exc_info=True
#         )
#
#     send_iis_stop_data(configuration)  # Отправляем данные на сервер
#
#
# # Запускает службу IIS
# def iis_start(configuration: ConfigurationsObject, path_to_backup: Union[Path, None]):
#     configuration.settings.logger.info('Служба IIS запущена')
#     Popen('iisreset /START', shell=True, stdout=DEVNULL, stderr=DEVNULL)  # Запускаем IIS
#
#     try:
#         delete_iis_start_link()  # Удаляем ссылку запуска IIS
#     except Exception:
#         pass
#
#     send_backup_data(configuration, path_to_backup)  # Отправляем данные по бекапам
#     time.sleep(1)
#
#
# # Получает данные о последнем бекапе
# def get_base_backup_data(path_to_backup: Path):
#     listdir = os.listdir(path_to_backup)  # Список файлов
#
#     zip_list = []  # Список zip-архивов
#     base_list = []  # Список полновесных бекапов
#     for file in listdir:  # Проходим по файлам
#         if file.endswith('.zip'):  # Если zip-архив
#             zip_list.append(path_to_backup / file)
#
#         if file.endswith('.1CD'):  # Если полновесная база
#             base_list.append(path_to_backup / file)
#
#         if os.path.isdir(path_to_backup / file):  # Если папка
#             base_list.append(path_to_backup / file)
#
#     last_zip_time = 0
#     last_zip_file = None
#     for path_to_file in zip_list:  # Проходим по zip базам (если есть)
#         creation_time = path_to_file.stat().st_mtime  # Время последней модификации
#
#         if creation_time > last_zip_time:  # Если время больше
#             last_zip_time = creation_time  # Пишем время (для сравнения)
#             last_zip_file = path_to_file  # Пишем файл
#
#     last_base_time = 0
#     last_base_file = None
#     for path_to_file in base_list:  # Проходим по полновесным базам (если есть)
#         creation_time = path_to_file.stat().st_mtime  # Время последней модификации
#
#         if creation_time > last_base_time:  # Если время больше
#             last_base_time = creation_time  # Пишем время (для сравнения)
#             last_base_file = path_to_file  # Пишем файл
#
#     full_base_dict = None
#     if last_base_file:  # Если есть полновесная база
#         full_base_dict = {
#             BACKUP_NAME: str(last_base_file),
#             CREATION_TIME: datetime.datetime.fromtimestamp(last_base_time).isoformat()
#         }
#
#     zip_base_dict = None
#     if last_zip_file:  # Если есть zip база
#         zip_base_dict = {
#             BACKUP_NAME: str(last_zip_file),
#             CREATION_TIME: datetime.datetime.fromtimestamp(last_zip_time).isoformat()
#         }
#
#     return {  # Возвращает данные по базам
#         FULL_BASE_BACKUP: full_base_dict,
#         ZIP_BASE_BACKUP: zip_base_dict
#     }
#
#
# # Отправляет данные по бекапам на сервер
# def send_backup_data(configuration: ConfigurationsObject, path_to_backup: Union[Path, None]):
#     if path_to_backup is None:  # Если пути нет - ничего не делаем
#         return
#
#     backup_data = get_base_backup_data(path_to_backup)  # Получаем данные по бекапам
#     send_http.send_data(
#         method=METHOD_SAVE,
#         identifier=configuration.get_initialization_dict(),
#         main=MAIN_SCHEDULER,
#         action=ACTION_SAVE_BACKUP_DATA_MODE,
#         data=backup_data,
#         logger=configuration.settings.logger
#     )  # Отправляем данные на сервер
#
#
# # Проверяет параметры в Report (печать DataMatrix)
# def check_reg_param():
#     path_to_reg_report_1c = [
#         (reg.HKEY_CURRENT_USER, r'SOFTWARE\1C\1Cv8\Report')
#     ]
#
#     hku_subkeys = []
#     k = reg.OpenKey(reg.HKEY_USERS, '')  # Открываем корень HKU
#     count_keys = reg.QueryInfoKey(k)[0]  # Колличество ключей раздела реестра
#     for index in range(count_keys):
#         sub_key = reg.EnumKey(k, index)
#         hku_subkeys.append(sub_key)
#
#     for sub_key in hku_subkeys:
#         path_to_reg_report_1c.append((reg.HKEY_USERS, sub_key + r'\SOFTWARE\1C\1Cv8\Report'))
#
#     k = None
#     for key, sub_key in path_to_reg_report_1c:  # Ищем ключ в реестре
#         try:
#             k = reg.OpenKey(key, sub_key, 0, reg.KEY_ALL_ACCESS)
#             break
#         except FileNotFoundError:
#             pass
#
#     if k is None:  # Если не найден ключ
#         return None
#
#     count_keys = reg.QueryInfoKey(k)[1]  # Колличество ключей раздела реестра
#     reg_dict = {}  # Словаь ключей реестра
#     for index in range(count_keys):  # Проходим по ключам
#         key, value, types = reg.EnumValue(k, index)
#         reg_dict[key] = value  # Пишем ключ - значение
#
#     return reg_dict
#
#
# # Возвращает путь к бекапам, либо None
# def get_path_for_backup(reg_data: dict, task_dict: dict) -> Union[Path, None]:
#     path_to_backup = reg_data.get('PathBackUP')  # Извлекает путь к бекапу из реестра (если есть)
#     if not path_to_backup:
#         path_to_reg = task_dict.get('path')  # Извлекает путь к бекапу из файла регазадания
#         if not path_to_reg:
#             return None
#
#         path_to_backup = Path(path_to_reg).parent  # Получаем путь к директории
#
#     else:
#         path_to_backup = Path(path_to_backup)
#
#     return path_to_backup
#
#
# # Прибовляет / вычитает время и возвращает валидным
# def add_or_sub_time_for_win_scheduler(*, start_time: datetime.time, sign: str,
#                                       hour: int = 0, minute: int = 0, second: int = 0) -> str:
#     start_time_timedelta = datetime.timedelta(
#         hours=start_time.hour, minutes=start_time.minute, seconds=start_time.second
#     )  # Приводим к timedelta
#
#     time_diff = datetime.timedelta(hours=hour, minutes=minute, seconds=second)  # Прибовляемое / вычитаемое время
#
#     if sign == '+':
#         new_time = start_time_timedelta + time_diff
#
#     elif sign == '-':
#         new_time = start_time_timedelta - time_diff
#
#     else:  # Не должно быть
#         return '00:00:00'
#
#     new_time_str = str(new_time)
#
#     # Лечим -1 +1 days
#     if not 0 < new_time.total_seconds() <= 60 * 60 * 24:
#         new_time_str = new_time_str.split(',')[-1].strip()
#
#     # Лечит запись виндовского планировщика на ночное время
#     if len(new_time_str.split(':')[0]) == 1:
#         new_time_str = '0' + new_time_str  # Прибавляем 0
#
#     return new_time_str
#
#
# # Запускает батник регзадания
# def run_reg_bat(path_to_reg_bat: str):
#     Popen(f'"{path_to_reg_bat}"', shell=True)  # Запускаем батник
#     time.sleep(0.5)
#
#
# EVERY_DAY_PHARMACY = [
#     3.0, 4.0, 10.0, 11.1, 12.0, 20.0, 23.0, 38.0, 45.0, 53.0, 63.0, 76.0, 84.0, 89.0, 111.0, 132.0, 135.0, 188.0,
#     224.0, 250.0, 262.0, 268.0, 287.0, 288.0, 292.0, 303.0, 360.0, 361.0, 395.0, 403.0, 458.0, 469.0, 546.0, 547.0,
#     548.0, 549.0, 595.0, 596.0, 606.0
# ]


# Возвращает время задачи, либо None
def script(configuration: ConfigurationsObject, scheduler: AppScheduler):
    return
    # if int(configuration.device_or_name) in (1, 99):  # Если первая касса, либо сервер
    #     Popen('iisreset /START', shell=True, stdout=DEVNULL, stderr=DEVNULL)  # Запускаем IIS
    # time.sleep(1)
    #     configuration.settings.logger.info(f'Корректировка настроек планировщика')
    #
    #     task_dict = init_scheduler(configuration)
    #     if task_dict is None:
    #         configuration.settings.logger.info('Регзадание не обнаружено, корректировка настроек не требуется')
    #         return
    #
    #     reg_data = task_dict.get(REG_DATA_KEY, {})  # Данные реестра
    #
    #     # === Отправка данных по бекапам =====
    #     path_to_backup = None
    #     try:
    #         path_to_backup = get_path_for_backup(reg_data, task_dict)  # Получаем данные по бекапам (либо None)
    #         send_backup_data(configuration=configuration, path_to_backup=path_to_backup)
    #     except Exception:
    #         configuration.settings.logger.error(
    #             'Не удалось отправить данные о бекапах базы на сервер', exc_info=True
    #         )
    #
    #     type_ib = reg_data.get('TypeIB')  # Получаем тип БД
    #     if type_ib == 'Server':
    #         configuration.settings.logger.info('1С подключена к SQL БД, настройка планировщика не требуется')
    #         return  # Завершаем работу
    #
    #     if float(configuration.pharmacy_or_subgroup) in EVERY_DAY_PHARMACY:  # Проверка на круглосутки
    #         configuration.settings.logger.info(
    #             'Аптека из списка круглосуточных, корректировака настроек планировщика прервана')
    #         return
    #
    #     backup_type = reg_data.get('BackUPType')  # Как настроено бекапирование
    #     if backup_type == 'ТехПерерыв':
    #         configuration.settings.logger.info(
    #             'Настройки резервного копирования соответсвуют круглосуточной аптеки, настройка планировщика завершена'
    #         )
    #         return
    #
    #     task_time = task_dict.get('time')  # Извлекает время
    #     if task_time:  # Если есть время регзадания и аптека не круглосуточная
    #         task_time = datetime.time.fromisoformat(task_time)  # Преобразуем к time
    #
    #         # === Создаём задачу перезапуска IIS ===
    #         # Вычитаем из времени 10 минут (ОСТАНОВКА IIS)
    #         time_for_stop_iis = add_or_sub_time_for_win_scheduler(
    #             start_time=task_time, sign='-', minute=10
    #         )
    #
    #         # Прибовляем 1 час (ЗАПУСК IIS)
    #         time_for_start_iis = add_or_sub_time_for_win_scheduler(
    #             start_time=task_time, sign='+', hour=1
    #         )
    #
    #         time_for_run_bat = add_or_sub_time_for_win_scheduler(
    #             start_time=task_time, sign='+', hour=1, minute=5
    #         )
    #
    #         path_to_reg_bat = task_dict.get('path')  # Путь к bat-файлу регзадания
    #         # Создаём задачи
    #         scheduler.scheduler.every().day.at(time_for_stop_iis).do(iis_stop, configuration=configuration)
    #         scheduler.scheduler.every().day.at(time_for_start_iis).do(iis_start, configuration=configuration,
    #                                                                   path_to_backup=path_to_backup)
    #         scheduler.scheduler.every().day.at(time_for_run_bat).do(run_reg_bat, path_to_reg_bat=path_to_reg_bat)
    #
    #         configuration.settings.logger.info(
    #             f'Создана задача остановки IIS в планировщике [{time_for_stop_iis} - {time_for_start_iis}]'
    #         )
