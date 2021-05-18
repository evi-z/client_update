import os.path
import shutil

import git.exc
from git import Repo
from glob import glob
from subprocess import run, PIPE

from values import *
from fun import *

# Адрес репозитория
URL_REPOSITORY = 'https://github.com/fckgm/client_update.git'


# Проводит первичную настройку репозитория
def init_update_repository():
    repo_init = Repo.clone_from(URL_REPOSITORY, UPDATE_GIT_PATH)  # Клонируем репозиторий
    repo_init.close()  # Закрываем

while True:  # Обходим проверки
    try:
        repo = Repo(UPDATE_GIT_PATH)  # Подключаемся к репозиторию
        break

    except (git.exc.NoSuchPathError, git.exc.InvalidGitRepositoryError):  # Если нет директории или она некорректна
        init_update_repository()  # Проводим первичную настройку

current_commit = repo.head.commit  # Получаем текущщий коммит
repo.remotes.origin.pull()  # git pull

if current_commit != repo.head.commit:  # Если коммиты различаются, значит обновился
    run([sys.executable, os.path.join(ROOT_PATH, 'updater.py')])
    #sys.exit(0)  # Завершаем выполнение







