import os
import sys
import socket
import configparser
import json

from kkm_values import *
from scripts_fun import *

try:
    from libfptr10 import IFptr
except ModuleNotFoundError:
    print_log(f'Скрипт {get_basename(__file__)} не смог импортировать модуль libfptr10.py')


# Возвращает список аргументов коммандной строки
def get_argv_list(argv):
    if argv[1:]:  # Если есть аргументы коммандной строки
        argv_list = argv[1:]  # Исключаем первый элемент

        return argv_list

    else:  # Если нет, завершаем работу
        sys.exit(0)


# Создаёт словарь приветствия и кодирует в JSON
def get_hello_dict(mode, data=None):
    hello_dict = {MODE_DICT_KEY: mode,
                  DATA_DICT_KEY: data}

    hello_json = json.dumps(hello_dict) + EOF  # Кодируем в JSON с EOF

    return hello_json


# Отправляет данные на сервер
def send_data(config_dict):
    hello_dict = get_hello_dict(KKM_STRIX_MODE, config_dict)  # Получаем словарь приветсвия

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((HOST, KKM_DEMON_PORT))

    sock.send(hello_dict.encode())  # Отправляем данные

    sock.close()


# Первичный поиск ККМ
def get_first_connection(fptr):
    # Список альтернативных скоростей
    baudrate_alternative_list = [IFptr.LIBFPTR_PORT_BR_1200, IFptr.LIBFPTR_PORT_BR_2400, IFptr.LIBFPTR_PORT_BR_4800,
                                 IFptr.LIBFPTR_PORT_BR_9600, IFptr.LIBFPTR_PORT_BR_19200, IFptr.LIBFPTR_PORT_BR_38400,
                                 IFptr.LIBFPTR_PORT_BR_57600, IFptr.LIBFPTR_PORT_BR_230400,
                                 IFptr.LIBFPTR_PORT_BR_460800,
                                 IFptr.LIBFPTR_PORT_BR_921600]

    for com_port in range(1, 15):  # Проходим по портам от 1 до 15 на скорости 115200
        settings = {
            IFptr.LIBFPTR_SETTING_MODEL: IFptr.LIBFPTR_MODEL_ATOL_AUTO,  # Автоматическое определение модели
            IFptr.LIBFPTR_SETTING_PORT: IFptr.LIBFPTR_PORT_COM,  # Работа с АТОЛ по COM-порту
            IFptr.LIBFPTR_SETTING_COM_FILE: str(com_port),  # Номер порта ККМ
            IFptr.LIBFPTR_SETTING_BAUDRATE: IFptr.LIBFPTR_PORT_BR_115200  # Скорость (115200)
        }

        fptr.setSettings(settings)  # Устанавливаем нстройки
        fptr.open()  # Открывает соединение с ККМ

        if fptr.isOpened():  # Если есть соединение
            settings_dict = fptr.getSettings()  # Получаем настройки
            # Сохраняем настройки подключения
            save_kkm_connect_data(ATOL_KKM, settings_dict['ComFile'], settings_dict['BaudRate'])
            return fptr
    else:
        for com_port in range(1, 15):  # Проходим по портам от 1 до 15
            for baudrate in baudrate_alternative_list:  # Проходим по альтернативным скоростям
                settings = {
                    IFptr.LIBFPTR_SETTING_MODEL: IFptr.LIBFPTR_MODEL_ATOL_AUTO,  # Автоматическое определение модели
                    IFptr.LIBFPTR_SETTING_PORT: IFptr.LIBFPTR_PORT_COM,  # Работа с АТОЛ по COM-порту
                    IFptr.LIBFPTR_SETTING_COM_FILE: str(com_port),  # Номер порта ККМ
                    IFptr.LIBFPTR_SETTING_BAUDRATE: baudrate  # Скорость
                }

                fptr.setSettings(settings)  # Устанавливаем нстройки
                fptr.open()  # Открывает соединение с ККМ

                if fptr.isOpened():  # Если есть соединение
                    settings_dict = fptr.getSettings()  # Получаем настройки
                    # Сохраняем настройки подключения
                    save_kkm_connect_data(ATOL_KKM, settings_dict['ComFile'], settings_dict['BaudRate'])
                    return fptr
    return fptr


fptr = IFptr('')  # Поиск драйвера по стандартным путям

# Получаем список аргументов коммандной строки
arg = get_argv_list(sys.argv)

pharmacy = arg[0]  # Номер аптеки
kassa = arg[1]  # Касса


if len(arg) == 2:  # Если переданы только Аптека и Касса
    fptr = get_first_connection(fptr)  # Первичный поиск

elif len(arg) == 4:  # Если переданы COM-порт и Скорость
    com_port = arg[2]  # Номер COM порта
    baudrate = arg[3]  # Скорость

    settings = {
        IFptr.LIBFPTR_SETTING_MODEL: IFptr.LIBFPTR_MODEL_ATOL_AUTO,  # Автоматическое определение модели
        IFptr.LIBFPTR_SETTING_PORT: IFptr.LIBFPTR_PORT_COM,  # Работа с АТОЛ по COM-порту
        IFptr.LIBFPTR_SETTING_COM_FILE: str(com_port),  # Номер порта ККМ
        IFptr.LIBFPTR_SETTING_BAUDRATE: baudrate  # Скорость
    }

    fptr.setSettings(settings)  # Устанавливаем нстройки
    fptr.open()  # Открывает соединение с ККМ

    if not fptr.isOpened():  # Если всё равно нет соединения
        fptr = get_first_connection(fptr)  # Попытка поиска
        if not fptr.isOpened():  # Если первичная инициализация не прошла
            os.remove(KKM_CONFIG_FILE_NAME)  # Удаляем вайл конфигурации

else:  # Неверные аргументы коммандной строки
    sys.exit(0)


if not fptr.isOpened():  # Если по итогу нет соединения
    print_log(f'Скрипт {get_basename(__file__)} не нашёл ККМ, работа прервана')
    sys.exit(0)

_settings = fptr.getSettings()
print_log(f'Скрипт {get_basename(__file__)} обнаружил ККМ и начал работу '
          f'(COM: COM{_settings["ComFile"]}, Скорость: {_settings["BaudRate"]})')

# Установка параметра общей информации
fptr.setParam(IFptr.LIBFPTR_PARAM_DATA_TYPE, IFptr.LIBFPTR_DT_STATUS)
fptr.queryData()

model = fptr.getParamString(IFptr.LIBFPTR_PARAM_MODEL_NAME)  # Название модели

# Регистрационные данны
fptr.setParam(IFptr.LIBFPTR_PARAM_FN_DATA_TYPE, IFptr.LIBFPTR_FNDT_REG_INFO)
fptr.fnQueryData()

rnm = fptr.getParamString(1037)  # РН ККТ
inn = fptr.getParamString(1018)  # ИНН
address = fptr.getParamString(1009)  # Адрес

# Статус информационного обмена
fptr.setParam(IFptr.LIBFPTR_PARAM_FN_DATA_TYPE, IFptr.LIBFPTR_FNDT_OFD_EXCHANGE_STATUS)
fptr.fnQueryData()

uncorr_fd_count = fptr.getParamInt(IFptr.LIBFPTR_PARAM_DOCUMENTS_COUNT)  # Колличество неподтвержённых ФД
# Номер документа для ОФД первого в очереди
last_ofd_uncorr_doc_num = fptr.getParamInt(IFptr.LIBFPTR_PARAM_DOCUMENT_NUMBER)
# Дата и время документа для ОФД первого в очереди
last_ofd_uncorr_doc_time = fptr.getParamDateTime(IFptr.LIBFPTR_PARAM_DATE_TIME)

# Информация о ФН
fptr.setParam(IFptr.LIBFPTR_PARAM_FN_DATA_TYPE, IFptr.LIBFPTR_FNDT_FN_INFO)
fptr.fnQueryData()

fn = fptr.getParamString(IFptr.LIBFPTR_PARAM_SERIAL_NUMBER)  # Номер ФН

# Срок действия ФН
fptr.setParam(IFptr.LIBFPTR_PARAM_FN_DATA_TYPE, IFptr.LIBFPTR_FNDT_VALIDITY)
fptr.fnQueryData()

fn_time = fptr.getParamDateTime(IFptr.LIBFPTR_PARAM_DATE_TIME)

# Последний ФД
fptr.setParam(IFptr.LIBFPTR_PARAM_FN_DATA_TYPE, IFptr.LIBFPTR_FNDT_LAST_DOCUMENT)
fptr.fnQueryData()

last_fd_num = fptr.getParamInt(IFptr.LIBFPTR_PARAM_DOCUMENT_NUMBER)

data_dict = {
    PHARMACY_KEY: pharmacy,
    KASSA_KEY: kassa,
    MODEL_KEY: model,
    RNM_KEY: rnm,
    FN_KEY: fn,
    FN_TIME_KEY: fn_time.isoformat(),
    ADDRESS_KEY: address,
    UNCORR_FD_COUNT_KEY: uncorr_fd_count,
    LAST_OFD_UNCORR_DOC_NUM_KEY: last_ofd_uncorr_doc_num,
    LAST_OFD_UNCORR_DOC_TIME_KEY: last_ofd_uncorr_doc_time.isoformat(),
    LAST_FD_NUM_KEY: last_fd_num,
    INN_KEY: inn
}


fptr.close()  # Закрытие соединения
del fptr  # Деинсталяция экземпляра драйвера

try:
    send_data(data_dict)  # Отправляем данные на сервер
except (ConnectionRefusedError, ConnectionResetError):
    print_log(f'Скрипт {get_basename(__file__)} не смог отправить данные на север')
