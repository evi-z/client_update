import datetime
import os
import pprint
from pathlib import Path

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

    # Сторонний софт для заказа ###
    try:
        if int(configuration.device_or_name) != 0:
            return
    except Exception:
        return

    if os.path.exists('_ord_programs'):
        return

    try:
        homepath = str(Path.home())
        program_files_86 = os.environ.get('ProgramFiles(x86)', '')
        program_files = os.environ.get('ProgramW6432', '')

        programs_dict = {
            'СИА': r'C:\SIAWIN',
            'WinPrice': [
                os.path.join(program_files, r'Katren\WinPrice2'), os.path.join(program_files_86, r'Katren\WinPrice2')],
            'Роста': r'С:\Tamda',
            'Пульс': os.path.join(homepath, r'Documents\Аптека-Заказ'),
            'Профит-Мед': [
                os.path.join(program_files, 'ПрофитМед Клиент'), os.path.join(program_files_86, 'ПрофитМед Клиент')
            ],
            'Протек (Эпика)': r'C:\ePrica',
            'Гранд-Капитал': r'C:\Grand-Capital\Orders\bin',
            'БСС': [
                os.path.join(program_files, r'БСС\Программа заказа'), os.path.join(program_files_86, r'БСС\Программа заказа')
            ]
        }

        setup_dict = {}
        for name, _path in programs_dict.items():
            path_list = _path
            if isinstance(_path, str):
                path_list = [_path]

            for path in path_list:
                if os.path.exists(path):
                    setup_dict[name] = True
                    break
            else:
                setup_dict[name] = False

        send_dict = {
            'pharmacy': configuration.pharmacy_or_subgroup,
            'setup_dict': setup_dict
        }

        import urllib
        import urllib.request
        url = 'http://85.143.156.89/orders_program/'

        data = urllib.parse.urlencode(send_dict).encode('utf-8')
        req = urllib.request.Request(url, data)
        with urllib.request.urlopen(req) as response:
            _ = response.read()

        with open('_ord_programs', 'w') as _:
            pass

        try:
            os.remove('_order_programs')
        except Exception:
            pass

    except Exception:
        configuration.settings.logger.error(
            'При сборе данных о сторонних праграммах поставщиков произошла ошибка', exc_info=True
        )