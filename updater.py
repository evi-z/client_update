import os.path
import sys
import shutil
from subprocess import Popen, PIPE
from zipfile import ZipFile
from funs.low_level_fun import *
from funs.fun import *

logger = get_logger(__name__)


# Открывает клиента и завершает работу
def reload_client():
    # Первый аргумент - путь к клиенту (ГОСПОДИ БОЖЕ, СДЕЛАЙ ИМЕНОВАННЫЕ ПАРАМЕТРЫ, ПРОШУ)
    Popen([sys.executable, os.path.join(ROOT_PATH, 'client.pyw')])
    logger.info(f'Обновление завершено, попытка запуска {CLIENT_MODULE_NAME}')
    sys.exit(0)


def update_program():
    with ZipFile(os.path.join(UPDATE_PATH, 'update.zip'), 'r') as zipfile:
        zipfile.extractall(path=ROOT_PATH)
    reload_client()


update_program()
