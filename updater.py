import os.path
import sys
import shutil
from glob import glob
from git import Repo
from subprocess import Popen, PIPE

from funs.low_level_fun import *
from funs.fun import *

logger = get_logger(__name__)

# TODO Срочно обновить updater, print error-a больше нет


# Создаёт бекапы обновляемых файлов
def create_backup(backup_list):
    try:
        os.mkdir(BACKUP_DIR_PATH)  # Создаём папку backup
    except FileExistsError:  # Если папка существует
        pass  # TODO

    for name in backup_list:  # Проходим по списку, который надо скопировать
        try:
            shutil.copy(os.path.join(ROOT_PATH, name), os.path.join(ROOT_PATH, BACKUP_DIR_PATH, name))  # Бекапим
        except FileNotFoundError:  # Тут может быть ошибка, если нет конечной папки
            sp_name = name.split('\\')  # Разбиваем имя по сепаратору

            prom_path_list = []
            if len(sp_name) > 1:  # Если в имене есть промежуточные директорию
                for i in range(len(sp_name) - 1):  # Проходим по индексам, кроме последнего (имя конечного файла)
                    current_dir = sp_name[i]  # Директория, которую необходимо создать
                    # Создаём промежуточную директорию
                    try:
                        os.mkdir(os.path.join(ROOT_PATH, BACKUP_DIR_PATH, '\\'.join(prom_path_list), current_dir))
                    except FileExistsError:  # Если директория уже существует
                        prom_path_list.append(current_dir)  # Добовляем директорию в промежуточные
                        continue  # Идём дальше

                    prom_path_list.append(current_dir)  # Добовляем директорию в промежуточные

                try:  # Пытаемся забекапить
                    shutil.copy(os.path.join(ROOT_PATH, name), os.path.join(ROOT_PATH, BACKUP_DIR_PATH, name))

                except FileNotFoundError:  # Если файла всё-равно не существует (вложенные новые)
                    continue  # Идём дальше


# Обновляет программу заранее скачанными файлами
def update_program(update_list, update_list_otn):
    new_file_list = [os.path.join(ROOT_PATH, name) for name in update_list_otn]  # Список путей перемещения

    what_upd_list = []  # Лист того, что обновилось
    for index in range(len(update_list)):  # Проходим по индексам
        try:  # Пытаемся скопировать файл с заменой
            shutil.copyfile(update_list[index], new_file_list[index])

            what_upd_list.append(new_file_list[index])  # Добавляем в лист обновления
            logger.info(f'Обновлён файл {new_file_list[index]}')  # Пишем лог
        except PermissionError:  # Ошибка доступа
            print_error(f'Ошибка доступа к файлу {new_file_list[index]}')

        except FileNotFoundError as e:  # Возникает, если отсутсвует конечная папка
            sp_file = update_list_otn[index].split('\\')

            prom_path_list = []  # Список промежуточных директорий
            if len(sp_file) > 1:  # Если в имени есть пути
                for i in range(len(sp_file) - 1):  # Проходим по индексам, кроме последнего (имя файла)
                    current_dir = sp_file[i]  # Директория, которую необходимо создать

                    try:  # Пытаемся создать директорию, учитывая промежутычные
                        os.mkdir(os.path.join(ROOT_PATH, '\\'.join(prom_path_list), current_dir))
                    except FileExistsError:  # Если директория уже существует
                        prom_path_list.append(current_dir)  # Добовляем директорию в промежуточные
                        continue  # Идём дальше

                    prom_path_list.append(current_dir)  # Добовляем директорию в промежуточные

                # Копируем файл
                shutil.copyfile(update_list[index], new_file_list[index])

                what_upd_list.append(new_file_list[index])  # Добавляем в лист обновления
                logger.info(f'Обновлён файл {new_file_list[index]}')  # Пишем лог

            else:  # Если по другой причине
                print_error(e)

    logger.info(f'Обновленны файлы: {what_upd_list}')  # Пишем лог об успешном обновлении


# Созадёт файл-флаг начала обновления
def create_upd_file():
    with open(os.path.join(RUNTIME_DIR_NAME, UPD_FILE_NAME), 'w') as upd_file:  # Создаём upd file
        pass


# Удаляет файл-флаг начала обновления
def remove_upd_file():
    os.remove(os.path.join(RUNTIME_DIR_NAME, UPD_FILE_NAME))  # Удаляем upd file


# Открывает клиента и завершает работу
def reload_client():
    # TODO Сделать, чтоб передавался sys.argv[0] из loader-a
    Popen([sys.executable, os.path.join(ROOT_PATH, CLIENT_MODULE_NAME), DONT_NEED_INIT_LOADER_ARG])
    logger.info(f'Обновление завершенно, попытка запуска {CLIENT_MODULE_NAME}')
    sys.exit(0)


try:
    assert sys.argv[-1] == UPDATER_RUN_ARG  # Проверяет, верно ли запущен updater

    # Получаем список файлов, которые обновились
    repo = Repo(UPDATE_GIT_PATH)  # Подключаемся к репозиторию

    # Получаем обновлённые файлы
    update_files_str = repo.git.show("--pretty=", "--name-only", repo.head.commit)
    update_files_list_with_slash = update_files_str.split('\n')  # Список обновлённых файлов (со слешами)

    # Заменяем слеши на бэкслеши в путях
    git_files_list = replace_slash_to_backslash(update_files_list_with_slash)
    # Список относительных (от bin\update) файлов и директорий в bin\update
    files_and_dir_in_dir_otn = [file.replace(f'{UPDATE_GIT_PATH}\\', '') for file in
                                glob(f'{UPDATE_GIT_PATH}/**', recursive=True)]
    remove_simple_element(files_and_dir_in_dir_otn)  # Удаляем пустые элементы

    # Убираем директории
    files_in_dir_otn = [file for file in files_and_dir_in_dir_otn
                        if os.path.isfile(os.path.join(UPDATE_GIT_PATH, file))]

    # Список файлов обновления с абсолютными путями (принципиально важны индексы!)
    files_in_dir = [os.path.join(UPDATE_GIT_PATH, name) for name in files_in_dir_otn]

    # Список файлов для замены с относительными путями (bin\update) (отсекает удалённые в git)
    update_current_list_otn = list(set(git_files_list) & set(files_and_dir_in_dir_otn))
    create_backup(update_current_list_otn)  # Делаем бекапы (по относительным путям!)

    create_upd_file()  # Создаём upd file
    update_program(files_in_dir, files_in_dir_otn)  # Обновляем файлы (нужны полные и относительные (bin\update) списки)
    remove_upd_file()  # Удаляем upd file

    reload_client()
except AssertionError:  # Ловим проверку
    logger.error(f'Попытка запуска {UPDATER_MODULE_NAME} вне цикла обновления')

except Exception as e:
    logger.error(f'Обновление не удалось', exc_info=True)
    reload_client()  # Запускаем client
