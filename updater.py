import os.path
import sys
import shutil
from glob import glob
from git import Repo

from fun import *


# Создаёт бекапы обновляемых файлов
def create_backup(backup_list):
    try:
        os.mkdir(BACKUP_DIR_PATH)  # Создаём папку backup
    except FileExistsError:  # Если папка существует
        pass  # TODO

    for name in backup_list:  # Проходим по списку, который надо скопировать
        try:
            shutil.copy(os.path.join(ROOT_PATH, name), os.path.join(ROOT_PATH, BACKUP_DIR_PATH, name))
            print('Бекапим: ', os.path.join(ROOT_PATH, name))
        except FileNotFoundError:
            sp_name = name.split('\\')  # Разбиваем имя по сепаратору
            print(sp_name)

            prom_path_list = []
            if len(sp_name) > 1:  # Если в имене есть промежуточные директорию
                for i in range(len(sp_name) - 1):  # Проходим по индексам, кроме последнего (имя конечного файла)
                    current_dir = sp_name[i]  # Директория, которую необходимо создать
                    # Создаём промежуточную директорию
                    try:
                        os.mkdir(os.path.join(ROOT_PATH, BACKUP_DIR_PATH, '\\'.join(prom_path_list), current_dir))
                    except FileExistsError:  # Если директория уже существует
                        prom_path_list.append(current_dir)  # Добовляем директорию в промежуточные
                        continue

                    prom_path_list.append(current_dir)  # Добовляем директорию в промежуточные

                shutil.copy(os.path.join(ROOT_PATH, name), os.path.join(ROOT_PATH, BACKUP_DIR_PATH, name))  # Бекапим
                print('Бекапим: ', os.path.join(ROOT_PATH, name))
                continue
            print('Игнорим: ', os.path.join(ROOT_PATH, name))


# Получаем список файлов, которые обновились
repo = Repo(UPDATE_GIT_PATH)  # Подключаемся к репозиторию

update_files_str = repo.git.show("--pretty=", "--name-only", repo.head.commit)

update_files_list_with_slash = update_files_str.split('\n')  # Список обновлённых файлов (со слешами)

# Заменяем слеши на бэкслеши в путях
git_files_list = replace_slash_to_backslash(update_files_list_with_slash)

print(f"Git: {git_files_list}")

# Список относительных (от bin\update) файлов в bin\update
files_in_dir = [file.replace(f'{UPDATE_GIT_PATH}\\', '') for file in
                glob(f'{UPDATE_GIT_PATH}/**', recursive=True)]
remove_simple_element(files_in_dir)  # Удаляем пустые элементы

print(f'Файлы: {files_in_dir}')

# Список файлов для замены с относительными путями (bin\update)
update_current_list_otn = list(set(git_files_list) & set(files_in_dir))
# Список файлов с абсолютными путями
update_current_list = [os.path.join(UPDATE_GIT_PATH, name) for name in update_current_list_otn]

print('Замена:', update_current_list)

create_backup(update_current_list_otn)  # Делаем бекапы (по относительным путям!)

with open(os.path.join(RUNTIME_DIR_NAME, UPD_FILE_NAME), 'w') as upd_file:  # Создаём upd file
    pass


