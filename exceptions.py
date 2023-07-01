class NoBotVariableError(Exception):
    """Исключение отсутствия varialbe."""

    pass


class NoHomeworkNameInHomeworkError(Exception):
    """Исключение отсутствия ключа HomeworkName."""

    pass


class NoKeysInResponseError(Exception):
    """Исключение отсутствия ключей в response."""

    pass


class HttpAnswerError(Exception):
    """Исключение неверного ответа Http."""

    pass


class BotSendMessageError(Exception):
    """Исключение неудачной отпрвки сообщения."""

    pass


class ApiCallError(Exception):
    """Исключение неудачной отпрвки сообщения."""

    pass


class JsonConvertError(Exception):
    """Исключение неудачной отпрвки сообщения."""

    pass
