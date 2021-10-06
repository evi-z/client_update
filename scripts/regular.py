import datetime
import os
import win32com.client

from bin.values import *

try:  # Для автокомплита
    from objects import *
except (ImportError, ModuleNotFoundError):
    pass

script_name = 'regular.py'  # Имя скрипта


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