import asyncio
import configparser
import datetime
from decimal import Decimal, InvalidOperation
import json
import logging
import os
import random
import shutil
import socket
import sys
import winreg as reg
import time
from importlib import import_module
from subprocess import Popen, PIPE, run, STDOUT, DEVNULL
from threading import Thread

from bin.values import *
from errors import *

for _ in range(2):  # 2 попытки
    try:
        import psutil
        import asyncssh
        import git.exc
        import schedule
        from git import Repo
        from glob import glob
        import win32com.client

        break
    except (ImportError, ModuleNotFoundError):
        from library_control import *

        lib_control = LibraryControl(
            logger_name=__name__,
            root_file_path=os.path.join(ROOT_PATH, CLIENT_MODULE_NAME)
        )

        lib_control.check_app_lib_install()  # Проверяем, установлены ли библиотеки

# Объект работы с реестром
class RegData:
    def __init__(self):
        self.reg_root_path = REG_ROOT_PATH  # Путь программы в реестре
        self._open_reg()  # Открывет, либо создаёт раздел реестра

    # Открывает раздел реестра
    def _open_reg(self):
        try:  # Пытаемся открыть раздел реестра
            self.reg_key = reg.OpenKey(reg.HKEY_CURRENT_USER, self.reg_root_path, 0, reg.KEY_ALL_ACCESS)
        except FileNotFoundError:  # Если раздела не существует
            self._first_init_reg_key()  # Проводим первичную инициализацию

        self._set_app_version()  # Пишем в реестр актуальную версию программы

    # Первичная инициализация раздела реестра
    def _first_init_reg_key(self):
        # Созаём раздел реестра
        self.reg_key = reg.CreateKeyEx(reg.HKEY_CURRENT_USER, self.reg_root_path, 0, reg.KEY_ALL_ACCESS)

    # Пишет в реестр актуальную версию программы
    def _set_app_version(self):
        reg.SetValueEx(self.reg_key, REG_VERSION_KEY, 0, reg.REG_SZ, APP_VERSION)  # Версия программы

    # Возвращает словарь параметров реестра
    def get_reg_dict(self):
        count_keys = reg.QueryInfoKey(self.reg_key)[1]  # Колличество ключей раздела реестра

        reg_dict = {}  # Словаь ключей реестра
        for index in range(count_keys):  # Проходим по ключам
            key, value, types = reg.EnumValue(self.reg_key, index)
            reg_dict[key] = value  # Пишем ключ - значение

        return reg_dict

    # Возвращает значение параметра реестра (вызывает RegKeyNotFound, если ключа нет)
    def get_reg_value(self, key):
        reg_dict = self.get_reg_dict()  # Словарь параметров реестра

        try:  # Птыаемся извлечь ключ
            value = reg_dict[key]
        except KeyError:  # Если ключа нет
            raise RegKeyNotFound  # Вызывает исключение

        return value

    # Устанавливает значение в реестр (по пути REG_ROOT)
    def set_reg_key(self, key, value, *, reg_type=reg.REG_SZ):
        reg.SetValueEx(self.reg_key, key, 0, reg_type, value)  # Устанавливаем значение в реестр


# Объект настроек программы
class SettingsObject:
    def __init__(self, *, lib_control_obj, root_file_path: str):
        self.reg_data = RegData()  # Объект работы с реестром
        self.lib_control = lib_control_obj  # Объект контроля либ
        self.logger = lib_control_obj.logger  # Переводим логгер в настройки
        self.root_file_path = root_file_path  # Атрибут __file__ клиента

        self._set_last_app_run()  # Устанавливем время последнего запуска программы в реестр

    # Пишет критическую ошибку инициализации настроек и завершает программу
    def print_incorrect_settings(self, text: str, *, stand_print=True):
        if stand_print:
            text = 'Некорректная инициализация файла конфигурации!\n' + f'{text}\n'
        else:
            text = f'{text}\n'

        self.logger.critical(text)  # Пишем лог ошибки
        sys.exit(0)  # Завершаем работу

    # Возвращает список аргументов коммандной строки
    @staticmethod
    def get_argv_list(*, argv=None):
        if argv is None:
            argv = sys.argv

        if argv[1:]:  # Если есть аргументы коммандной строки
            argv_list = argv[1:]  # Исключаем первый элемент
            return argv_list
        else:  # Если нет, возвращаем пустой список
            return []

    # Пишет в реестр время последнего запуска программы
    def _set_last_app_run(self):
        now = str(datetime.datetime.now().isoformat())  # Текущее время
        self.reg_data.set_reg_key(REG_LAST_APP_RUN, now)

    # Возвращает время последнего запуска из реестра
    def _get_last_app_reboot_from_reg(self):
        try:
            return self.reg_data.get_reg_value(REG_LAST_APP_RUN)
        except RegKeyNotFound:  # Если ключа вдруг нет
            return None

    # Перезапускает программу
    def reboot_app(self):
        Popen([sys.executable, self.root_file_path])  # Перезапуск программы
        time.sleep(0.5)  # Таймаут
        sys.exit(0)  # Завершает заботу

    # Возвращает, необходимо ли перезапустить программу
    def check_need_reboot_app(self):
        # Получаем время полседнего подключения из реестра
        last_reconnect = self._get_last_app_reboot_from_reg()  # Получаем время последнего ребута из реестра
        if last_reconnect is None:  # Если ключа в реестре нет  TODO Аккуратно
            return True  # Просто завершаем задачу (МОЖНО БЫЛО БЫ РЕБУТИТЬ, НО МАЛО ЛИ ЧТО)

        last_reconnect = datetime.datetime.fromisoformat(last_reconnect)  # Преобразуем к datetime
        now = datetime.datetime.now()  # Текущее время
        reconnect_delta = now - last_reconnect  # Разница во времени

        # Если после перезапуска прошло больше допустимого времени
        if reconnect_delta.total_seconds() > SECONDS_FROM_LAST_APP_REBOOT:
            return True
        else:
            return False


# Объект конфигурации
class ConfigurationsObject:
    def __init__(self, *, group, pharmacy_or_subgroup, device_or_name, host, settings: SettingsObject):
        self.group = group  # Группа
        self.pharmacy_or_subgroup = pharmacy_or_subgroup  # Аптека или Подгруппа
        self.device_or_name = device_or_name  # Устролство или Имя
        self.host = host  # Адрес сервера

        self.settings = settings  # Объект настроек программы (SettingsObject)

    # Инициализирует конигурацию посредством файла конфигурации и возвращает объект конфигурации
    @classmethod
    def init_from_config_file(cls, *, settings: SettingsObject, path_to_config=CONFIG_FILE_PATH, only_check=False):
        if not only_check:
            if not os.path.exists(CONFIG_FILE_PATH):  # Если файла конфигурации не существует
                cls._create_config_file()  # Создаёт файл конфигурации

                settings.print_incorrect_settings(f'Файл конфигурации {CONFIG_NAME} отсутсвовал\n'
                                                  'Он был создан по пути:\n'
                                                  f'{CONFIG_FILE_PATH}\n\n'
                                                  'Перед последующим запуском проинициализируйте его вручную, либо '
                                                  'посредством утилиты "Настройка клиента"', stand_print=False)

        config = configparser.ConfigParser()
        config.read(CONFIG_FILE_PATH)  # Читаем файл конфигурации

        # App
        group = int(config.get(APP_SECTION, GROUP_PHARM))
        pharmacy_or_subgroup = config.get(APP_SECTION, PHARMACY_OR_SUBGROUP_PHARM)
        device_or_name = config.get(APP_SECTION, DEVICE_OR_NAME_PHARM)

        # Connect
        host = config.get(CONNECT_SECTION, HOST_PHARM)

        # Создаёт объект конфигурации
        configuration_obj = cls(
            host=host,
            group=group,
            pharmacy_or_subgroup=pharmacy_or_subgroup,
            device_or_name=device_or_name,
            settings=settings
        )

        return configuration_obj  # Возвращаем объект конфигурации

    # Создаёт пустой файл конфигурации
    @staticmethod
    def _create_config_file(*, path_to_config=CONFIG_FILE_PATH):
        config = configparser.ConfigParser()

        # Секция APP
        config.add_section(APP_SECTION)
        config.set(APP_SECTION, GROUP_PHARM, str(0))  # Группа
        config.set(APP_SECTION, PHARMACY_OR_SUBGROUP_PHARM, '')  # Аптека или Подгруппа
        config.set(APP_SECTION, DEVICE_OR_NAME_PHARM, '')  # Устройство или Имя

        # Секция CONNECT
        config.add_section(CONNECT_SECTION)

        config.set(CONNECT_SECTION, HOST_PHARM, DEFAULT_HOST)  # Адрес сервера (пишем предустановленный)

        with open(CONFIG_FILE_PATH, 'w') as config_file:  # Создаём файл конфигурации
            config.write(config_file)  # Записываем

    # Инициализирует проверку актуальности параметров
    def check_correct_config_parm(self):
        if self.group == GROUP_PHARMACY_INT:  # Если группа - Аптека
            self.actual_parm_for_pharmacy()  # Проверяем актуальность параметров

        elif self.group == GROUP_OFFICE_INT:  # Если группа - Офис
            self.actual_pharm_for_office()  # Проверяем актуальность параметров

        else:  # Если группа неккорекктна
            self.settings.print_incorrect_settings('Некорректная группа\n'
                                                   'Допустимые группы:\n'
                                                   '0 - Аптеки\n'
                                                   '1 - Офис')

    # Проверяет актуальность параметров для аптек
    def actual_parm_for_pharmacy(self):
        device_list = list(DEVICE_DICT.values())  # Допустимые значения устройств

        self.pharmacy_or_subgroup = self.pharmacy_or_subgroup.replace(',', '.')  # Экранируем запятую

        try:  # Пытаемся преобразовать к Decimal
            Decimal(self.pharmacy_or_subgroup)  # Проверяем на корректность
        except (ValueError, InvalidOperation):
            self.settings.print_incorrect_settings(f'Номер аптеки должен быть числом '
                                                   f'[{PHARMACY_OR_SUBGROUP_PHARM} != {self.pharmacy_or_subgroup}]')

        # Проверка на соответсвие списка устройств
        if self.device_or_name not in device_list:
            self.settings.print_incorrect_settings(f'Неккоректное устройсво ({DEVICE_OR_NAME_PHARM})\n'
                                                   'Допустимый диапазон устройств для аптек:\n'
                                                   f'{device_list}')

    # Прверяет актуальность параметров для офиса
    def actual_pharm_for_office(self):
        if not self.pharmacy_or_subgroup:  # Если отсутсвует подгруппа
            self.settings.print_incorrect_settings(f'Не указанна подгруппа ({PHARMACY_OR_SUBGROUP_PHARM})')

        if not self.device_or_name:  # Если отсутствует наименование
            self.settings.print_incorrect_settings(f'Не указанно наименование ({DEVICE_OR_NAME_PHARM})')

        if len(self.pharmacy_or_subgroup) > 80:
            self.settings.print_incorrect_settings(f'Наименование подгруппы не должно превышать '
                                                   f'80 символов ({PHARMACY_OR_SUBGROUP_PHARM})')

        if len(self.device_or_name) > 80:
            self.settings.print_incorrect_settings(f'Имя не должно превышать 80 символов ({DEVICE_OR_NAME_PHARM})')

    # Возвращает словарь для инициализации клиента на сервере
    def get_initialization_dict(self) -> dict:
        initialization_dict = {
            GROUP_KEY: self.group,
            FIRST_IDENTIFIER: self.pharmacy_or_subgroup,
            SECOND_IDENTIFIER: self.device_or_name
        }

        return initialization_dict


# Объект загрузчика
class Loader:
    def __init__(self, *, settings_obj: SettingsObject):
        self.settings = settings_obj  # Объект настроек программы
        self.url_repository = f'https://@github.com/fckgm/client_update.git'  # Адрес репозитория
        self.update_git_path = UPDATE_GIT_PATH  # Путь к локальному репозиторию
        self.first_init_repo = False  # Булево первичной инициализации
        self.thread_name = 'LoaderThread'  # Имя потока
        self.uptime = MINUTES_BEFORE_CHECK_LOADER  # Как часто необходимо проверять обновления
        self.reg_key = REG_LAST_RUN_LOADER  # Ключ в реестре

        try:
            # Создаём файл конфигурации только для чтения (НУЖЕН ДЛЯ TEST_UPDATE)
            self.configuration = ConfigurationsObject.init_from_config_file(
                settings=self.settings,
                only_check=True
            )
        except Exception:  # В случае ошибки пишем None
            self.configuration = None

    # Возвращает булево, необходимо ли инициализировать loader
    @staticmethod
    def need_init_loader() -> bool:
        argv_list = SettingsObject.get_argv_list(argv=sys.argv)  # Получаем список аргументов коммандной строки

        if DONT_NEED_INIT_LOADER_ARG in argv_list:  # Если есть флаг в списке
            return False
        else:  # Иначе
            return True

    # Инициализация репозитория обновления
    def _init_loader(self):
        try:
            self.repo = Repo(self.update_git_path)  # Создаём репозиторий
        except (git.exc.NoSuchPathError, git.exc.InvalidGitRepositoryError):  # Если нет директории или она некорректна
            self.repo = self._init_update_repository()  # Инициализируем репозиторий
            self.first_init_repo = True  # Первое обновление

    # Проводит первичную настройку репозитория
    def _init_update_repository(self, try_remove_flag=False):  # Флаг попытки удаления старого репозитория
        self.settings.logger.info('Первичная инициализаиця репозитория обновления')
        try:
            repo_init = Repo.clone_from(self.url_repository, UPDATE_GIT_PATH)  # Клонируем репозиторий
        except git.exc.GitCommandError:  # Ошибка клонирования (некоректная деинсталяция)
            self.settings.logger.warning('Ошибка клонирования git репозитория. Попытка очистки старых версий программы')
            assert not try_remove_flag, 'Попытка очистить репозиторий не удалась'
            shutil.rmtree(UPDATE_GIT_PATH)  # Удаляем старый репозиторий
            time.sleep(1)  # На всякий
            # Устанавливаем флаг попытки удаления и заново вызываем функцию
            repo_init = self._init_update_repository(True)

        return repo_init

    # Запускает updater-a
    def _run_updater(self):
        # Первый [1] аргумент - путь к client (root_file_path)
        # Второй [2] аргумент - аргумент корректности запуска
        Popen([sys.executable, os.path.join(ROOT_PATH, UPDATER_MODULE_NAME), self.settings.root_file_path,
               UPDATER_RUN_ARG])
        time.sleep(1)

    # Запуск обновления
    def _start(self):
        self._init_loader()  # Инициализируем репозиторий
        current_commit = self.repo.head.commit  # Получаем текущщий коммит
        self.repo.remotes.origin.pull()  # git pull
        self._set_last_run()  # Устанавливаем время запуска в реестр

        # Если коммиты различаются, либо первое обновление
        if current_commit != self.repo.head.commit or self.first_init_repo:
            self.settings.logger.info(f'Получено обновление, запуск {UPDATER_MODULE_NAME}')

            self._run_updater()  # Запускаем update-r
            sys.exit(0)  # Завершаем выполнение

    # Устанавливет значение последнего запуска в реестр
    def _set_last_run(self):
        now = str(time.time())  # Получаем текущее время (с начала эпохи)
        self.settings.reg_data.set_reg_key(self.reg_key, now)

    # Проверяет, необъодимо ли выполнить скрипт в потоке
    def _check_need_init(self, last_run):
        return SecondaryScripts.delta_need_init(last_run, self.uptime)  # Разница, между последним запуском и uptime

    # Поток проверки необходимости обновления
    def _thread(self):
        while True:
            try:
                # Пытаемся получить значение реестра
                last_run = float(self.settings.reg_data.get_reg_value(self.reg_key))
            except RegKeyNotFound:  # Если ключа нет
                self._start()  # Запускаем сбор данных
                continue

            # Если необходимо выполнить kkm_data, либо цикл только запущен
            if self._check_need_init(last_run) or self.start_flag:
                self._start()  # Инициализируем сбор данных

            self.start_flag = False  # Продолжаем по условию

            time.sleep(10 * 60)  # Проверяем каждые 10 минут

    # Единоразовая проверка обновления (ПОВЕРЬ, ТАК НАДО! НЕ ВПИХИВАЙ ЭТО В _thread!)
    def _once_run(self):
        try:
            # Пытаемся получить значение реестра
            last_run = float(self.settings.reg_data.get_reg_value(self.reg_key))
        except RegKeyNotFound:  # Если ключа нет
            self._start()  # Запускаем сбор данных
            self.start_flag = False  # Продолжаем по условию
            return  # Проверка не требуется

        # Если необходимо выполнить kkm_data, либо цикл только запущен
        if self._check_need_init(last_run) or self.start_flag:
            self._start()  # Инициализируем сбор данных

        self.start_flag = False  # Продолжаем по условию

    def _start_test_update(self):  # TODO Доделать
        pass

    def init_test_update(self):  # TODO Доделать
        if self.configuration.group != GROUP_PHARMACY_INT:  # Если не аптека
            return

        if self.check_need_init_test_update():
            pass

    # Проверяет, необходимо ли установить тестовое обновление
    def check_need_init_test_update(self):  # TODO Доделать
        init_dict = {
            PHARMACY_KEY: self.configuration.pharmacy_or_subgroup,
            DEVICE_KEY: self.configuration.device_or_name,
            APP_VERSION_KEY: APP_VERSION
        }

        hello_dict = SSHConnection.get_hello_dict(CHECK_TEST_CLIENT_UPDATE_MODE, init_dict)  # Словарь инициализации
        sock = SSHConnection.get_tcp_socket()  # Сокет
        sock.connect((self.configuration.host, 12113))  # TODO
        sock.send(hello_dict.encode())  # Отправляем данные

        need = SSHConnection.get_data_from_socket(sock)  # Получаем данные

        return need

    # Запуск потока обновления
    def start_threading(self):
        self.start_flag = True  # Флаг первой итерации (выполняется вне зависимости от параметров реестра)
        # Единожды выполняет загрузчик в основном потоке / Из-за непредсказуемости процессов, что будут идти параллельно
        self._once_run()

        thread = Thread(target=self._thread)  # Создаёт поток контроля
        thread.setName(self.thread_name)  # Задаём имя потоку
        thread.start()  # Запускает поток


# Объект инициализации и контроля службы TightVNC
class TightVNC:
    path_to_tvnc_file = os.path.join(ROOT_PATH, TVNSERVER_FILE_PATH)  # Абсолютный путь к TightVNC
    path_to_reg_file = os.path.join(ROOT_PATH, VNC_SERVICE_REG_FILE)  # Файл настройки службы

    def __init__(self, *, configuration_obj: ConfigurationsObject):
        self.configuration = configuration_obj

    # Инициализация службы Tight VNC
    def init_tight_vnc(self):
        # НЕ ТРОГАЙ ЭТОТ КОД! ОН РАБОТАЕТ ТОЛЬКО С DEVNULL, ИНЧАЕ ВИСНИТ ТУТ
        run(f'reg import "{self.path_to_reg_file}"', shell=True, stdout=DEVNULL,
            stderr=STDOUT)  # Регистрирует настройки

        if not os.path.exists(self.path_to_tvnc_file):  # Проверка существования службы
            self.configuration.settings.print_incorrect_settings(
                f'\nПо пути [{self.path_to_tvnc_file}] не найден файл службы TightVNC.\n'
                f'Вероятнее всего, антивирусная программа добавила этот файл в карантин.\n'
                f'Добавте директорию [{ROOT_PATH}] в исключения антивируса и повторите попытку.', stand_print=False
            )

        # СЛУЖБА НЕ РЕГИСТРИРУЕТСЯ БЕЗ ПРАВ АДМИНИСТРАТОРА !
        run([self.path_to_tvnc_file, '-reinstall', '-silent'], stderr=PIPE, stdout=PIPE, stdin=PIPE)

    # Убивает процесс службы Tight VNC
    @staticmethod
    def taskkill():
        run(f'taskkill /f /im {TVNSERVER_NAME}', shell=True, stdin=PIPE, stdout=PIPE, stderr=PIPE)

    # Запускает службу
    def start_service(self):
        self.taskkill()  # Убиваем процесс

        # СЛУЖБА НЕ ЗАПУСТИТСЯ БЕЗ ПРАВ АДМИНИСТРАТОРА
        self.tvnserver_process = Popen([self.path_to_tvnc_file, '-start', '-silent'],
                                       stdin=PIPE, stdout=PIPE, stderr=PIPE)

        if not self.tvnserver_process.returncode:  # Если процесс запущен корректно (returncode == 0)
            self.configuration.settings.logger.info(f'Запущена служба TightVNC')

    def check_running(self,):
        try:
            tvns_service = psutil.win_service_get(TVNSERVER_SERVICE_NAME)  # Получаем службу (если есть)

        except psutil.NoSuchProcess:  # Если такой службы нет
            self.configuration.settings.logger.error(
                'Служба TightVNC не зарегестрирована в система, попытка регистрации')

            # СЛУЖБА НЕ ПЕРЕГИСТРИРУЕТСЯ БЕЗ ПРАВ АДМИНИСТРАТОРА
            self.init_tight_vnc()  # Регистрируем службу
            self.check_running()  # Пробуем ещё раз

        if tvns_service.status() != 'running':  # Если служба не запущена
            self.configuration.settings.logger.warning('Служба TightVNC была остановлена, перезапуск')
            self.start_service()  # Перезапускаем tvns


# Объект инициализации побочных скриптов
class SecondaryScripts:
    def __init__(self, *, configuration_obj: ConfigurationsObject):
        self.configuration = configuration_obj  # Сохраняем конфигурацию
        self.script_name = None
        self.reg_key = None
        self.path_to_script = None

    # Возвращает булево, необходимо ли запустить скрипт, исходя из того, перезагружался ли компьютер
    @staticmethod
    def delta_need_init_from_pc_uptime(last_run):
        now = time.time()  # Текущее время (с начала эпохи)
        uptime = psutil.boot_time()  # Время, которе запущена ОС

        if now - last_run > now - uptime:
            return True
        else:
            return False

    # Возвращает булево, необходимо ли запустить скрипт, исходя из разницы времени (first_time > second_time)
    @staticmethod
    def delta_need_init(first_time, second_time):
        now = time.time()  # Текущее время (с начала эпохи)

        if now - first_time > second_time:
            return True
        else:
            return False


# Объект побочного скрипта pc_config
class PcConfigScript(SecondaryScripts):
    def __init__(self, configuration_obj: ConfigurationsObject):
        super().__init__(configuration_obj=configuration_obj)  # Инициализирует родителя

        self.script_name = PC_CONFIG_MODULE_NAME  # Имя скрипта
        self.reg_key = REG_LAST_RUN_PC_CONFIG_KEY  # Параметр в реестре (время последнего запуска)
        self.path_to_script = os.path.join(ROOT_PATH, SCRIPTS_DIR_NAME, self.script_name)  # Полный путь к скрипту

    # Устанавливет значение последнего запуска в реестр
    def _set_last_run(self):
        now = str(time.time())  # Получаем текущее время (с начала эпохи)
        self.configuration.settings.reg_data.set_reg_key(self.reg_key, now)

    # Запускает работу скрипта
    def run(self):
        # Отправляем номер аптеки и устройство аргументами коммандной строки
        Popen([sys.executable, self.path_to_script, self.configuration.pharmacy_or_subgroup,
               self.configuration.device_or_name])

        self.configuration.settings.logger.info(f'Был выполнен скрипт {self.script_name}')  # Пишем лог
        self._set_last_run()  # Устанавливет время последнего запуска в реестр
        time.sleep(0.5)  # Для корректной отработки Popen

    # Возвращает булево, необходимо ли выполнить скрипт
    def need_init_script(self):
        if self.configuration.group != GROUP_PHARMACY_INT:  # Если устройсто не Аптека
            return False

        try:
            # Пытаемся получить значение реестра
            last_run = float(self.configuration.settings.reg_data.get_reg_value(self.reg_key))
        except RegKeyNotFound:  # Если ключа нет
            return True

        return self.delta_need_init_from_pc_uptime(last_run)  # Разница, между последним запуском и перезагрузкой ПК


# Объект побочного скрипта kkm.py
class KKMScript(SecondaryScripts):
    def __init__(self, configuration_obj: ConfigurationsObject):
        super().__init__(configuration_obj=configuration_obj)  # Инициализирует родителя

        self.script_name = KKM_SCRIPT_MODULE_NAME  # Имя скрипта
        self.reg_key = REG_LAST_RUN_KKM_DATA_KEY  # Параметр в реестре (время последнего запуска)
        self.uptime = MINUTES_BEFORE_INIT_KKM_DATA  # Кол-во секунд между запусками
        self.thread_name = 'KKMThread'  # Имя потока
        self.path_to_script = os.path.join(ROOT_PATH, SCRIPTS_DIR_NAME, self.script_name)  # Полный путь к скрипту

    # Инициализирует запуск скрипта
    def _init_script(self):
        # Отправляем номер аптеки и устройство аргументами коммандной строки
        Popen([sys.executable, self.path_to_script, self.configuration.pharmacy_or_subgroup,
               self.configuration.device_or_name])

        self.configuration.settings.logger.info(f'Был выполнен скрипт {self.script_name}')  # Пишем лог
        self._set_last_run()  # Устанавливет время последнего запуска в реестр
        time.sleep(0.5)  # Для корректной отработки Popen

    # Проверяет, необъодимо ли выполнить скрипт в потоке
    def _check_need_init(self, last_run):
        return self.delta_need_init(last_run, self.uptime)  # Разница, между последним запуском и перезагрузкой ПК

    # Поток выполнения запуска скрипта
    def _script_thread(self):
        while True:
            try:
                # Пытаемся получить значение реестра
                last_run = float(self.configuration.settings.reg_data.get_reg_value(self.reg_key))
            except RegKeyNotFound:  # Если ключа нет
                self._init_script()  # Запускаем сбор данных
                continue

            if self._check_need_init(last_run):  # Если необходимо выполнить kkm_data
                self._init_script()  # Инициализируем сбор данных

            time.sleep(60 * 10)  # Засыпает на 10 минут

    # Устанавливет значение последнего запуска в реестр
    def _set_last_run(self):
        now = str(time.time())  # Получаем текущее время (с начала эпохи)
        self.configuration.settings.reg_data.set_reg_key(self.reg_key, now)

    # Возвращает булево, необходимо ли выполнить скрипт
    def need_init_script(self):
        if self.configuration.group != GROUP_PHARMACY_INT:  # Если устройсто не Аптека
            return False

        return True  # В остальных случаях

    # Запускает поток сбора данных
    def start_thread(self):
        kkm_thread = Thread(target=self._script_thread)  # Создаёт поток контроля данных ККМ
        kkm_thread.setName(self.thread_name)  # Задаём имя потоку
        kkm_thread.start()  # Запускает поток


# Объект побочного скрипта disk_usage.py
class DiskUsageScript(SecondaryScripts):
    def __init__(self, configuration_obj: ConfigurationsObject):
        super().__init__(configuration_obj=configuration_obj)  # Инициализирует родителя

        self.script_name = DISK_USAGE_MODULE_NAME  # Имя скрипта
        self.reg_key = REG_LAST_RUN_DISK_USAGE  # Параметр в реестре (время последнего запуска)
        self.uptime = MINUTES_BEFORE_INIT_DISK_USAGE  # Кол-во секунд между запусками
        self.thread_name = 'DiskUsageThread'  # Имя потока
        self.path_to_script = os.path.join(ROOT_PATH, SCRIPTS_DIR_NAME, self.script_name)  # Полный путь к скрипту

    # Устанавливет значение последнего запуска в реестр
    def _set_last_run(self):
        now = str(time.time())  # Получаем текущее время (с начала эпохи)
        self.configuration.settings.reg_data.set_reg_key(self.reg_key, now)

    # Инициализирует запуск скрипта
    def _init_script(self):
        # Отправляем номер аптеки и устройство аргументами коммандной строки
        Popen([sys.executable, self.path_to_script, self.configuration.pharmacy_or_subgroup,
               self.configuration.device_or_name])

        self.configuration.settings.logger.info(f'Был выполнен скрипт {self.script_name}')  # Пишем лог
        self._set_last_run()  # Устанавливет время последнего запуска в реестр
        time.sleep(0.5)  # Для корректной отработки Popen (возможно)

    # Проверяет, необъодимо ли выполнить скрипт в потоке
    def _check_need_init(self, last_run):
        return self.delta_need_init(last_run, self.uptime)  # Разница, между последним запуском и перезагрузкой ПК

    # Поток выполнения запуска скрипта
    def _script_thread(self):
        while True:
            try:
                # Пытаемся получить значение реестра
                last_run = float(self.configuration.settings.reg_data.get_reg_value(self.reg_key))
            except RegKeyNotFound:  # Если ключа нет
                self._init_script()  # Запускаем сбор данных
                continue

            if self._check_need_init(last_run):  # Если необходимо выполнить kkm_data
                self._init_script()  # Инициализируем сбор данных

            time.sleep(60 * 10)  # Засыпает на 10 минут

    # Возвращает булево, необходимо ли выполнить скрипт
    def need_init_script(self):
        if self.configuration.group != GROUP_PHARMACY_INT:  # Если устройсто не Аптека
            return False

        if self.configuration.device_or_name not in KASSA_DICT.values():  # Если устройство не в списке необходимых
            return False

        return True  # В остальных случаях

    # Запускает поток сбора данных
    def start_thread(self):
        thread = Thread(target=self._script_thread)  # Создаёт поток контроля данных ККМ
        thread.setName(self.thread_name)  # Задаём имя потоку
        thread.start()  # Запускает поток


# Объект скрипта regular (нового типа)
class RegularScript:
    def __init__(self, configuration_obj: ConfigurationsObject):
        self.configuration = configuration_obj  # Объект конфигурации

        self.module_name = 'regular'  # Наименование модуля
        self.reg_key = 'LastRunRegular'  # Параметр в реестре (время последнего запуска)
        self.uptime = 120 * 60  # Кол-во секунд между запусками
        self.thread_name = 'RegularThread'  # Имя потока

        try:  # Пытаемся импортировать модуль
            self.module = import_module(f'{SCRIPTS_DIR_NAME}.{self.module_name}')
        except ImportError:  # Если ошибка импорта
            self.configuration.settings.logger.error(f'Импорт модуля {self.module_name} не удался', exc_info=True)
            self.module = None  # Ставим None

    # Инициализирует запуск скрипта
    def _init_script(self):
        try:
            self.module.script(self.configuration)  # Пытаемся запустить скрипт
            self._set_last_run()  # Устанавливет время последнего запуска в реестр
        except Exception as e:
            self.configuration.settings.logger.error(f'Ошибка в работе модуля {self.module_name}: {e}')

    # Проверяет, необъодимо ли выполнить скрипт в потоке
    def _check_need_init(self, last_run):
        return SecondaryScripts.delta_need_init(last_run, self.uptime)  # Разница, между последним запуском и uptime

    # Поток выполнения запуска скрипта
    def _script_thread(self):
        while True:
            try:
                # Пытаемся получить значение реестра
                last_run = float(self.configuration.settings.reg_data.get_reg_value(self.reg_key))
            except RegKeyNotFound:  # Если ключа нет
                self._init_script()  # Запускаем сбор данных
                continue

            if self._check_need_init(last_run):  # Если необходимо выполнить
                self._init_script()  # Инициализируем работу

            time.sleep(60 * 10)  # Засыпает на 10 минут

    # Устанавливет значение последнего запуска в реестр
    def _set_last_run(self):
        now = str(time.time())  # Получаем текущее время (с начала эпохи)
        self.configuration.settings.reg_data.set_reg_key(self.reg_key, now)

    # Запускает поток выполнения скрипта
    def start_thread(self):
        if self.module is None:  # Если модуль не импортировался
            self.configuration.settings.logger.error(f'Ошибка в импорте модуля {self.module_name}')
            return

        thread = Thread(target=self._script_thread)  # Создаёт поток
        thread.setName(self.thread_name)  # Задаём имя потоку
        thread.start()  # Запускает поток

    # Возвращает булево, необходимо ли выполнить скрипт
    def need_init_script(self):
        if self.configuration.group != GROUP_PHARMACY_INT:  # Если устройсто не Аптека
            return False

        return True


class RetailBackup:
    def __init__(self, configuration_obj: ConfigurationsObject):
        self.configuration = configuration_obj  # Объект конфигурации

        self.module_name = 'retail_backup'  # Наименование модуля
        self.reg_key = 'LastRunRetailBackup'  # Параметр в реестре (время последнего запуска)
        self.uptime = 4 * 60 * 60  # Кол-во секунд между запусками
        self.thread_name = 'RetailBackup'  # Имя потока

        self.reg_key_backup = 'LastComZavBackRetail'
        self.backup_diff_time = 72 * 60 * 60  # Как часто делать бекапы

        try:  # Пытаемся импортировать модуль
            self.module = import_module(f'{SCRIPTS_DIR_NAME}.{self.module_name}')
        except ImportError:  # Если ошибка импорта
            self.configuration.settings.logger.error(f'Импорт модуля {self.module_name} не удался', exc_info=True)
            self.module = None  # Ставим None

    # Инициализирует запуск скрипта
    def _init_script(self):
        try:
            need_backup = False
            try:  # Время последнего бекапа
                back_copy_time_diff = float(self.configuration.settings.reg_data.get_reg_value(self.reg_key_backup))
                if SecondaryScripts.delta_need_init(back_copy_time_diff, self.backup_diff_time):
                    need_backup = True
            except RegKeyNotFound:
                need_backup = True

            self.module.script(self.configuration, need_backup)  # Пытаемся запустить скрипт
            self._set_last_run()  # Устанавливет время последнего запуска в реестр
        except Exception as e:
            self.configuration.settings.logger.error(f'Ошибка в работе модуля {self.module_name}: {e}')

    # Проверяет, необъодимо ли выполнить скрипт в потоке
    def _check_need_init(self, last_run):
        return SecondaryScripts.delta_need_init(last_run, self.uptime)  # Разница, между последним запуском и uptime

    # Поток выполнения запуска скрипта
    def _script_thread(self):
        while True:
            try:
                # Пытаемся получить значение реестра
                last_run = float(self.configuration.settings.reg_data.get_reg_value(self.reg_key))
            except RegKeyNotFound:  # Если ключа нет
                self._init_script()  # Запускаем сбор данных
                continue

            if self._check_need_init(last_run):  # Если необходимо выполнить
                self._init_script()  # Инициализируем работу

            time.sleep(60 * 10)  # Засыпает на 10 минут

    # Устанавливет значение последнего запуска в реестр
    def _set_last_run(self):
        now = str(time.time())  # Получаем текущее время (с начала эпохи)
        self.configuration.settings.reg_data.set_reg_key(self.reg_key, now)

    # Запускает поток выполнения скрипта
    def start_thread(self):
        if self.module is None:  # Если модуль не импортировался
            self.configuration.settings.logger.error(f'Ошибка в импорте модуля {self.module_name}')
            return

        thread = Thread(target=self._script_thread)  # Создаёт поток
        thread.setName(self.thread_name)  # Задаём имя потоку
        thread.start()  # Запускает поток

    # Возвращает булево, необходимо ли выполнить скрипт
    def need_init_script(self):
        if self.configuration.group != GROUP_PHARMACY_INT:  # Если устройсто не Аптека
            return False

        return True


# Объект планировщика
class AppScheduler:
    def __init__(self, *, configuration_obj: ConfigurationsObject):
        self.configuration = configuration_obj  # Объект конфигурации
        self.scheduler = schedule.Scheduler()  # Объект планировщика
        self.module_name = 'schedulers'  # Имя модуля
        self.thread_name = 'SchedulerThread'  # Имя потока

        try:  # Пытаемся импортировать модуль
            self.module = import_module(f'{SCRIPTS_DIR_NAME}.{self.module_name}')
        except ImportError:  # Если ошибка импорта
            self.configuration.settings.logger.error(f'Импорт модуля {self.module_name} не удался', exc_info=True)
            self.module = None  # Ставим None

    # Инициализирует работу планировщика
    def _init_static_sheduler(self):
        self.module.script(self.configuration, self)  # Инициализирет планировщик файлом scheduler

    # Цикл потока
    def _script_thread(self):
        # БЕЗ ЭТОГО НЕ БУДЕТ РАБОТАТЬ Scheduler Task В ПОБОЧНОМ ПОТОКЕ !
        win32com.client.pythoncom.CoInitializeEx(0)  # Инициализация COM-объектов в побочном потоке
        self._init_static_sheduler()  # Инициализируем работу планирощика

        while True:
            self.scheduler.run_pending()  # Запускает планировщик
            time.sleep(1)  # Таймаут секунда

    # Запускает планировщик
    def start_thread(self):
        if self.module is None:  # Если модуль не импортировался
            self.configuration.settings.logger.error(f'Ошибка в импорте модуля {self.module_name}')
            return

        thread = Thread(target=self._script_thread)  # Создаёт поток
        thread.setName(self.thread_name)  # Задаём имя потоку
        thread.start()  # Запускает поток

    # Возвращает булево, необходимо ли выполнить скрипт
    def need_init_script(self):
        if self.configuration.group != GROUP_PHARMACY_INT:  # Если устройсто не Аптека
            return False

        return True


# Объект соединения (проброса порта)
class SSHConnection:
    def __init__(self, *, configuration_obj: ConfigurationsObject, tvnc_obj: TightVNC):
        self.configuration = configuration_obj  # Объект конфигурации
        self.connect_dict = None  # Словрь данных с сервера для удалённого проброса порта
        self.tvnc = tvnc_obj  # Объект управлением службы Tight VNC

    # Возвращает новый объект сокета
    @staticmethod
    def get_tcp_socket() -> socket.socket:
        return socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    @staticmethod
    # Создаёт словарь приветствия и кодирует в JSON
    def get_hello_dict(mode, data=None):
        hello_dict = {
            MODE_DICT_KEY: mode,
            DATA_DICT_KEY: data
        }

        hello_json = json.dumps(hello_dict) + EOF  # Кодируем в JSON с EOF
        return hello_json

    # Получает JSON данные от сокета и возвращает декодированным
    @staticmethod
    def get_data_from_socket(sock: socket.socket):
        get_list = []
        while True:
            data = sock.recv(4096)  # Читаем данные по 4096 Б
            data = data.decode()  # Декодируем

            if data.endswith(EOF):  # Ловим символ завершения
                data = data.split(EOF)  # Бьём строку по этому смволу
                get_list.append(data[0])  # Добавляем данные без EOF
                break

            get_list.append(data)

        data_json = ''.join(get_list)  # Объединяем в строку
        data = json.loads(data_json)  # Декодируем в словарь

        return data

    # Устанавливает время последнего переподключения в реестр
    def _set_last_reconnect_in_reg(self):
        now = str(datetime.datetime.now().isoformat())  # Текущее время
        self.configuration.settings.reg_data.set_reg_key(REG_LAST_RECONNECT, now)

    # Возвращает время последнего подключения из реестра
    def _get_last_reconnect_from_reg(self):
        try:
            return self.configuration.settings.reg_data.get_reg_value(REG_LAST_RECONNECT)
        except RegKeyNotFound:  # Если ключа вдруг нет
            return None

    # Завершает все задачи в асинхронном цикле
    def _close_all_connection_tasks(self):
        # Получаем все незавершённые задачи
        tasks = [task for task in asyncio.all_tasks(self.loop) if not task.done()]
        for task in tasks:  # Проходим по задачам
            task.cancel()  # Завершаем задачу

        time.sleep(1)  # На всякий

    # Запуск подключения посредством SSH
    async def _ssh_connection(self):
        async with asyncssh.connect(
                self.configuration.host,
                port=self.ssh_port,
                username=self.ssh_user,
                password=self.ssh_password,
                known_hosts=None  # Отключить проверку на ключи
        ) as conn:
            conn.set_keepalive(5 * 60, 3)  # Устанавливаем keepalive в 5 минут c 3мя попытками
            listener = await conn.forward_remote_port('', self.remote_port, 'localhost',
                                                      LOCAL_VNC_PORT)  # Пробрасываем порт
            self._set_last_reconnect_in_reg()  # Устанавливаем время последнего переподключения в реестр
            self.configuration.settings.logger.info(f'Проброс порта {listener.get_port()} на {self.configuration.host} '
                                                    f'к локальному порту {LOCAL_VNC_PORT}')

            # check_reconnect_task = asyncio.create_task(self._check_reconnect_time(),
            #                                            name='check_reconnect_task')
            check_writing_in_database_task = asyncio.create_task(self._check_writing_in_database(conn),
                                                                 name='check_writing_in_database_task')
            check_tvnserver_run = asyncio.create_task(self._check_tvnserver_run(),
                                                      name='check_tvnserver_run')
            check_forward_port_closed = asyncio.create_task(self._check_forward_port_closed(listener),
                                                            name='check_forward_port_closed')
            check_app_reboot = asyncio.create_task(self._check_need_app_reboot(),
                                                   name='check_app_reboot')

            await check_tvnserver_run  # Проверка работы TightVNC
            await check_writing_in_database_task  # Проверка записи в БД (со стороны сервера)
            # await check_reconnect_task  # Перепроброс порта по времени
            await check_forward_port_closed  # Проверяет, не закрылся ли проброшенный порт
            await check_app_reboot  # Проверяет, необходимо ли перезапустить программу

    # Проверяет, необходимо ли перезапустить программу
    async def _check_need_app_reboot(self):
        while True:
            need_reboot = self.configuration.settings.check_need_reboot_app()  # Флаг о необходимости перезапуска
            if need_reboot:
                self.configuration.settings.logger.info(
                    'Производится перезапуск программы (превышение времени простоя)')
                self.configuration.settings.reboot_app()  # Перезапускает программу

            await asyncio.sleep(MINUTES_BEFORE_CHECK_APP_REBOOT)

    # Проверяет, не закрылся ли проброшенный порт
    async def _check_forward_port_closed(self, listener: asyncssh.SSHListener):
        await listener.wait_closed()  # Ожидает закрытия проброшенного порта
        self.configuration.settings.logger.warning('Соединение с сервером разовано, производится переподключение')
        self._close_all_connection_tasks()  # Если wait_close завершился - завершаем цикл

    # Проверяет, запущена ли служба TightVNC
    async def _check_tvnserver_run(self):
        while True:
            try:
                self.tvnc.check_running()  # Проверяем и устраняем ошибки работы службы
                await asyncio.sleep(MINUTES_BEFORE_CHECK_TVNS_SERVICE)  # Засыпаем

            except Exception:  # Отлавливаем тут все ошибки, не охота, чтоб программа падала тут
                self.configuration.settings.logger.error(
                    'Невозможен контроль службы TightVNC, цикл проверки прерван!')
                # Завершаем эту проверку, но оставляем программу работать (всё-таки это не только удалёнка)
                return

    # Связывается с сервером и проверяет, есть ли запись в БД
    async def _check_writing_in_database(self, conn: asyncssh.connect):
        while True:
            await asyncio.sleep(MINUTES_BEFORE_CHECK_DB_WRITING)  # Засыпаем

            sock = self.get_tcp_socket()  # Получаем сокет
            try:
                # Словарь инициализации для передачи на сервер
                init_dict = {
                    GROUP_KEY: self.configuration.group,
                    PHARMACY_KEY: self.configuration.pharmacy_or_subgroup,
                    DEVICE_KEY: self.configuration.device_or_name
                }

                sock.connect((self.configuration.host, self.check_bd_write_demon_port))  # Подключение к серверу

                # Создаём словарь с режимом check_bd и словарём описания
                send_data = self.get_hello_dict(CHECK_BD_MODE, init_dict)
                sock.send(send_data.encode())  # Отправка словаря приветсвия на сервер

                online_status = self.get_data_from_socket(sock)  # Статус записи в БД

                if not online_status:  # Если не в сети
                    conn.disconnect(asyncssh.DISC_BY_APPLICATION, '')  # Закрываем соединение (на всякий)
                    sock.close()  # Закрываем сокет

                    self.configuration.settings.logger.warning('От сервера пришёл ответ об отсутсвии записи в БД')
                    self._close_all_connection_tasks()  # Завершаем цикл

            except (ConnectionRefusedError, ConnectionResetError):  # Если DB демон не работает
                self.configuration.settings.logger.warning('Удалённая проверка наличия в БД не удалась')

    # Получает с сервера данные для проброса порта (возвращает и сохраняет connection_dict)
    def get_data_for_port_forward(self) -> dict:
        # Словарь инициализации client
        init_dict = {
            GROUP_KEY: self.configuration.group,
            PHARMACY_KEY: self.configuration.pharmacy_or_subgroup,
            DEVICE_KEY: self.configuration.device_or_name,
            APP_VERSION_KEY: APP_VERSION
        }

        hello_dict = self.get_hello_dict(PORT_MODE, init_dict)  # Получаем словарь приветствия с init_dict

        sock = self.get_tcp_socket()  # Получаем TCP сокет
        port_conn = random.choice(PORT_LIST)  # Получаем случайный порт из списка

        try:
            sock.connect((self.configuration.host, port_conn))  # Подключение к серверу
        except (ConnectionRefusedError, ConnectionResetError):
            self.configuration.settings.logger.error(
                f'Подлючение к серверу {self.configuration.host} по порту {port_conn} '
                f'было сброшенно со стороны сервера')

            raise ConnectionToPortDaemonError  # Вызываем для перехвата сверху

        self.configuration.settings.logger.info(f'Произведено подключение к серверу {self.configuration.host} '
                                                f'по порту {port_conn}')  # Пишем лог
        timeout = random.randint(15, 25)  # Таймаут в очереди от 15 до 25 секунд (чтоб не DDOS-ить)
        sock.settimeout(timeout)  # Ставим таймаут в очереди

        sock.send(hello_dict.encode())  # Отправка словаря приветсвия на сервер
        self.connect_dict = self.get_data_from_socket(sock)  # Получаем словарь подключения

        self.remote_port = int(self.connect_dict[PORT_KEY])  # Выделенный порт (str!)
        self.ssh_port = self.connect_dict[SSH_PORT_KEY]  # Порт SSH
        self.ssh_user = self.connect_dict[USER_KEY]  # Логин
        self.ssh_password = self.connect_dict[PASSWORD_KEY]  # Пароль
        self.check_bd_write_demon_port = self.connect_dict[CHECK_BD_WRITE_KEY]  # Порт демона check_bd

        sock.close()  # Закрываем сокет
        return self.connect_dict  # Не имеет смысла, но пусть будет

    # Запускает основной цикл программы
    def start_ssh_connection(self):
        if self.connect_dict is None:  # Если нет актуальных данных
            raise NotDataForConnection  # Вызывает исключение

        self.tvnc.start_service()  # Запускаем службу Tight VNC

        self.loop = asyncio.new_event_loop()  # Создаём цикл
        asyncio.set_event_loop(self.loop)
        # TODO Либо оставить get_event_loop, либо добавить set_event_loop

        try:
            self.loop.run_until_complete(self._ssh_connection())  # Запускаем

        except (OSError, asyncssh.Error) as exc:  # Ошибка проброса порта
            self.configuration.settings.logger.error(f'Проброс порта SSH не удался: {exc}', exc_info=True)
            time.sleep(3)  # timeout

        except asyncio.CancelledError:  # Исключение отменённой задачи
            pass

        finally:
            self.loop.close()  # Завершает цикл событий
