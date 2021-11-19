import json
import logging
import time

for _ in range(2):  # 2 попытки
    try:
        import requests
    except (ImportError, ModuleNotFoundError):
        from library_control import *

        lib_control = LibraryControl(
            logger_name=__name__,
            root_file_path=os.path.join(ROOT_PATH, CLIENT_MODULE_NAME)
        )

        lib_control.check_app_lib_install()  # Проверяем, установлены ли библиотеки

URL_REQDATA = 'http://85.143.156.89/reqdata/'

# Хендлеры
HEADER_METHOD = '_method'
HEADER_MAIN = '_main'
HEADER_ACTION = '_action'
HEADER_IDENTIFIER = '_identifier'
HEADER_DATA = '_data'

# Методы
METHOD_SAVE = 'save'

# Коды
SUCCESS_CODE = 200


def send_data(*, method: str, identifier: dict, main: str, action: str, data, logger: logging.Logger):
    identifier = json.dumps(identifier)
    data = json.dumps(data)

    send = {
        HEADER_METHOD: method,
        HEADER_IDENTIFIER: identifier,
        HEADER_MAIN: main,
        HEADER_ACTION: action,
        HEADER_DATA: data
    }

    try:
        response = requests.post(URL_REQDATA, send)  # Отправляем данные
    except requests.exceptions.ConnectionError:
        if isinstance(logger, logging.Logger):
            logger.error(
                f"Передача данных на сервер провалилась - сервер недоступен "
                f"(method: {method}, main: {main}, actions: {action})"
            )

        return

    if response.status_code != SUCCESS_CODE:  # Если невалидный код
        if isinstance(logger, logging.Logger):
            logger.error(
                f'Сервер вернул невалидный код после передачи данных (method: {method}, main: {main}, actions: {action})\n'
                f'Код: {response.status_code} / Сообщение: {response.text}'
            )

