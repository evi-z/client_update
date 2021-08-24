class ClientException(Exception):
    """ Базовое исключение """
    pass


class ReconnectForRewriteDBException(ClientException):
    """Вызывается, если от сервера получен ответ об отсутсвии записи в БД"""
    pass
