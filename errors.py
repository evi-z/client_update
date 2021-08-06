class ClientException(Exception):
    """ Базовое исключение """
    pass


class RestartPlinkCountException(ClientException):
    """ Вызвыается, если было превышено кол-во допустимых перезапусков plink-а """
    pass
