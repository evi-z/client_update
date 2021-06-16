import os.path
import shutil

import git.exc
from git import Repo
from glob import glob
from subprocess import run, PIPE

from bin.values import *
from funs.fun import *

# Адрес репозитория
URL_REPOSITORY = 'https://github.com/fckgm/client_update.git'


# Проводит первичную настройку репозитория
def init_update_repository():
    print_log('Первичная инициализаиця репозитория обновления')
    repo_init = Repo.clone_from(URL_REPOSITORY, UPDATE_GIT_PATH)  # Клонируем репозиторий

    return repo_init


first_upd_flag = False  # Флаг первого обновления
try:
    repo = Repo(UPDATE_GIT_PATH)  # Подключаемся к репозиторию

except (git.exc.NoSuchPathError, git.exc.InvalidGitRepositoryError):  # Если нет директории или она некорректна
    repo = init_update_repository()  # Проводим первичную настройку
    first_upd_flag = True  # Первое обновление

current_commit = repo.head.commit  # Получаем текущщий коммит
repo.remotes.origin.pull()  # git pull

if current_commit != repo.head.commit or first_upd_flag:  # Если коммиты различаются, значит обновился
    print_log(f'Получено обновление, запуск {UPDATER_MODULE_NAME}')

    Popen([sys.executable, os.path.join(ROOT_PATH, UPDATER_MODULE_NAME), UPDATER_RUN_ARG])  # Запускаем update-r
    sys.exit(0)  # Завершаем выполнение







