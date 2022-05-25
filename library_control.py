import logging
import time
from subprocess import run, Popen, DEVNULL, PIPE, CalledProcessError, check_call
import sys
import json
import importlib
from threading import Thread
import ctypes

from bin.values import *


MB_SYSTEMMODAL = 0x00001000
MSBOX_INFORMATION = 0x00000040


def _show_msbox(text: str, style: hex = MSBOX_INFORMATION, *, top: bool = True, title: str = 'Nevis VNClient'):
    if top:  # Поверх всех окон
        style += MB_SYSTEMMODAL

    Thread(
        target=lambda: ctypes.windll.user32.MessageBoxW(0, text, title, style)
    ).start()


# Контролирует корректность загрузки библиотек
class LibraryControl:
    def __init__(self, *, logger_name: str, root_file_path: str):
        self.logger = self.get_logger(logger_name)
        self.lib_list = self.get_all_install_library()  # Получаем спсиок установленных библиотек
        self.root_file_path = root_file_path

        self.logger.info(f'Запущен NevisVNClient (v.{APP_VERSION})')

    # Возвращает объект логгера
    def get_logger(self, name=__name__):
        logger = logging.getLogger(name)  # Инициализируем объект логгера с именем программы
        logger.setLevel(logging.INFO)  # Уровень логгирования
        logger.addHandler(self.init_logger())  # Добавляем

        return logger

    # Инициализирует объект логгера
    def init_logger(self):
        try:
            fh = logging.FileHandler(LOG_FILE_PATH, 'a', ENCODING_APP)  # Файл лога
        except FileNotFoundError:  # Если нет директории runtime
            os.mkdir(os.path.join(ROOT_PATH, RUNTIME_DIR_NAME))  # Создаём папку runtime
            fh = logging.FileHandler(LOG_FILE_PATH, 'a', ENCODING_APP)  # Файл лога

        str_format = '[%(asctime)s]: %(levelname)s - %(name)s - (%(filename)s).%(funcName)s(%(lineno)d) ' \
                     '=> %(message)s'  # Формат вывода
        date_format = '%X %d/%m/%y'  # Формат даты/времени
        formatter = logging.Formatter(fmt=str_format, datefmt=date_format)
        fh.setFormatter(formatter)  # Устанавливаем форматирование

        return fh  # Возвращаем настроенный логгер

    # Получает и возвращает актуальный список аптек
    def get_all_install_library(self):
        try:
            _ = check_call(
                [sys.executable, '-m', 'pip', '--version'], stderr=DEVNULL, stdout=DEVNULL, stdin=DEVNULL
            )
        except CalledProcessError:
            self.logger.critical(MESSAGE_NOT_INSTALL_PIP)
            _show_msbox(MESSAGE_NOT_INSTALL_PIP)
            sys.exit(1)

        res = run([sys.executable, '-m', 'pip', 'list', '--format=json'], stderr=PIPE, stdout=PIPE, stdin=PIPE)
        stdout = res.stdout.decode().strip()

        try:  # Я не уверен
            lib_list = json.loads(stdout)  # Загружаем из JSON
        except Exception:
            sp = stdout.split('\r\n')
            stdout = sp[0]
            lib_list = json.loads(stdout)  # Загружаем из JSON

        return lib_list

    # Устанавливает библиотеку
    def install_library(self, library: str, *, version=None):
        try:
            install_command = [sys.executable, '-m', 'pip', 'install']  # Стандартная комманда установки
        except json.decoder.JSONDecodeError:  # Если не установлен pip
            self.logger.critical('На ПК не найден менеджер пакетов pip. Вероятнее всего, Python установлен некорректно\n'
                                 'Это исправляется переустановкой Python с установкой Visual C++ Redistributable for '
                                 'Visual Studio 2015 (см. инструкцию по утановке Nevis VNClient)')
            sys.exit(0)  # Завершает работу

        if version is None:  # Если версия не передана
            install_command.append(library)  # Добавляем имя либы
        else:
            lib_with_version = library + '==' + version  # Делаем строку
            install_command.append(lib_with_version)

        self.logger.info(f'Установка библиотеки {library}')
        run(install_command, stdout=DEVNULL, stderr=DEVNULL)  # Устанавливаем библиотеки

    # Проверяет, установлена ли библиотека
    def check_current_lib_install(self, lib, *, reload_library=False):
        if reload_library:  # Если нужно актуализировать список
            self.lib_list = self.get_all_install_library()  # Обновляем актуальный список библиотек

        for el in self.lib_list:  #
            if el.get('name') == lib:  # Если имя соответсвует, возвращает версию
                return el.get('version')
        else:
            return False  # Иначе False

    # Перезапускает программу
    def app_reboot(self):
        command_list = [sys.executable, self.root_file_path]  # Комманда перезапуска
        command_list += sys.argv[1:]  # Добавляем аргументы коммандной строки

        Popen(command_list)  # Перезапускает клиента
        time.sleep(1)  # Таймаут
        sys.exit(0)  # Завершение работы

    # Проверяет, установлены ли библиотеки приложения
    def check_app_lib_install(self, *, install=True, app_reboot=True):
        install_new_lib_flag = False  # Флаг установки библиотеки

        for lib in APP_LIBRARY:
            stat = self.check_current_lib_install(lib)  # Проверяем, установленна ли библиотека

            if install and not stat:  # Если вернулся None
                self.logger.warning(f'Библиотека {lib} не найдена')
                self.install_library(lib)  # Устанавливаем библиотеку
                install_new_lib_flag = True  # Флаг установки

        if app_reboot and install_new_lib_flag:
            self.logger.info(f'Перезарпуск программы для валидации установленных библиотек ({self.root_file_path})')
            self.app_reboot()

