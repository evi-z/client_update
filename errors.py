class ClientException(Exception):
    """ Базовое исключение """
    pass


class ReconnectException(ClientException):
    """ Общее исключение, которе вызывается для повторного проброса порта """
    pass


class ReconnectForReconnectTimeException(ReconnectException):
    """ Вызывается по истечении времени подключенного соединения """
    pass


class ReconnectForRewriteDBException(ReconnectException):
    """ Вызывается, если от сервера получен ответ об отсутсвии записи в БД """
    pass


class RegKeyNotFound(ClientException):
    """ Вызывается в случае отсутствия ключа в реестре"""
    pass


class NotDataForConnection(ClientException):
    def __str__(self):
        return 'Невозможно установить соединение, так как отсутсвуют данные для подключения с сервера.\n' \
               'Перед пробросом порта необходимо вызвать get_data_for_port_forward() для получения актуальных данных'


class ConnectionToPortDaemonError(ClientException):
    """ Вызывается в случае невозможности подключится к port_demon """
    pass


