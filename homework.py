import logging
import os
import sys
import time
from http import HTTPStatus
from logging import StreamHandler
from pathlib import Path

import requests
import telegram
from dotenv import load_dotenv

import exceptions as exc

load_dotenv()


PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_PERIOD = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


HOMEWORK_VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}

logger = logging.getLogger(__name__)
handler = StreamHandler(stream=sys.stdout)
logger.addHandler(handler)

if __name__ == '__main__':
    logging.basicConfig(
        level=logging.DEBUG,
        filename=Path(__file__).resolve().parent / 'main.log',
        filemode='a'
    )


def check_tokens():
    """Проверка глобальных переменных перед запуском бота."""
    token_list = [PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID]
    if not all(token_list):
        raise exc.NoBotVariableError(
            'Отсутству(-ют)ет переменн(-ые)ая окружения'
        )


def send_message(bot, message):
    """Отправка сообщения с информацией о домашней работы."""
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
        logger.debug('Сообщение удачно отправлено')
    except telegram.error.TelegramError as error:
        error_text = (
            f'Не получилось отравить сообщение{message} из-за ошибки: {error}'
        )
        logger.error(
            error_text
        )
        raise error(error_text)


def get_api_answer(timestamp):
    """Получение API ответа от ЯндексПрактикума."""
    payload = {'from_date': timestamp}
    try:
        response = requests.get(ENDPOINT, headers=HEADERS, params=payload)
    except requests.RequestException as error:
        raise error(f'Ошибка при обращении к API: {error}')

    if response.status_code != HTTPStatus.OK:
        raise requests.exceptions.HTTPError(
            f'Запрос к API получил код ошибки:'
            f' {response.status_code}'
        )

    try:
        return response.json()
    except ValueError as error:
        raise error(f'Ошибка при преобразовании ответа в JSON: {error}')


def check_response(response):
    """Проверка на соответствие с документацией API.
    ответа от ЯндексПрактикума.
    """
    if not isinstance(response, dict):
        raise TypeError(f'Тип данных в API ответе не dict, a {type(response)}')
    if ('homeworks' or 'current_date') not in response:
        message = (
            'В ответе отсутствует ключ(и) "homeworks" и(или) "current_date"'
        )
        raise exc.NoKeysInResponseError(message)
    homeworks = response.get('homeworks')
    if not isinstance(homeworks, list):
        message = (f'В ответе API ключ homeworks не в виде list,'
                   f'а в ввиде {type(homeworks)}')
        raise TypeError(message)
    return homeworks


def parse_status(homework):
    """Получение статуса домашней работы с API ответа."""
    status = homework.get('status')
    if status not in HOMEWORK_VERDICTS:
        raise ValueError('Статус домашней работы не совпадает с документацией')
    verdict = HOMEWORK_VERDICTS.get(status)
    if 'homework_name' not in homework:

        raise exc.NoHomeworkNameInHomeworkError(
            'Ключ homework_name отсутствует в API ответе'
        )
    verdict = HOMEWORK_VERDICTS.get(status)
    homework_name = homework['homework_name']
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def main():
    """Запуск работы бота по отслеживанию статуса домашней работы."""
    try:
        check_tokens()
    except exc.NoBotVariableError:
        logger.critical(exc.NoBotVariableError, exc_info=True)
        sys.exit(1)

    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    timestamp = int(time.time()) - RETRY_PERIOD
    previous_error = None
    homeworks_dicts = {}

    while True:
        try:
            homework_list = get_api_answer(timestamp)
            check_response(homework_list)
            target_homework = homework_list['homeworks'][0]
            homework_name = target_homework.get('homework_name')
            status = target_homework.get('status')
            if (homework_name, status) not in homeworks_dicts.items():
                message = parse_status(target_homework)
                homeworks_dicts.update({homework_name: status})
                send_message(bot, message)
            else:
                logger.debug('Нету новых статусов по домашней работе')

        except IndexError:
            logger.debug(f'Список домашних заданий за период {timestamp} пуст')

        except Exception as error:
            if str(previous_error) != str(error):
                message = f'Сбой в работе программы: {error}'
                previous_error = error
                logger.error(message)
                send_message(bot, message)

        finally:
            time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    main()
