import logging
import os
import sys
import time
from http import HTTPStatus
from logging import StreamHandler

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

logging.basicConfig(
    level=logging.DEBUG,
    filename='main.log',
    filemode='w'
)


def check_tokens():
    """Проверка глобальных переменных перед запуском бота."""
    if PRACTICUM_TOKEN and TELEGRAM_TOKEN and TELEGRAM_CHAT_ID is not None:
        return True
    logger.critical(exc.NoBotVariableError, exc_info=True)
    raise exc.NoBotVariableError('Отсутствует переменная окружения')


def send_message(bot, message):
    """Отправка сообщения с информацией о домашней работы."""
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
        logger.debug('Сообщение удачно отправлено')
    except Exception as error:
        logger.error(error)


def get_api_answer(timestamp):
    """Получение API ответа от ЯндексПрактикума."""
    payload = {'from_date': timestamp}
    try:
        response = requests.get(ENDPOINT, headers=HEADERS, params=payload)
    except requests.RequestException as error:
        logger.error(f'Ошибка при обращении к API: {error}')
        return None

    if response.status_code != HTTPStatus.OK:
        logger.error(f'Запрос к API получил код ошибки:'
                     f' {response.status_code}')
        raise requests.exceptions.HTTPError('HTTP статус не равен 200.')

    try:
        return response.json()
    except ValueError as error:
        logger.error(f'Ошибка при преобразовании ответа в JSON: {error}')
        return None


def check_response(response):
    """Проверка на соответствие с документацией API/
    ответа от ЯндексПрактикума.
    """
    if not isinstance(response, dict):
        message = 'Неправильный тип данных в API ответе'
        logging.error(message)
        send_message(telegram.Bot(token=TELEGRAM_TOKEN), message)
        raise TypeError
    homeworks = response.get('homeworks')
    if homeworks is None:
        message = 'В ответе отсутствует ключ homerowks'
        logging.error(message)
        send_message(telegram.Bot(token=TELEGRAM_TOKEN), message)
        raise Exception
    if not isinstance(homeworks, list):
        message = 'В ответе API ключ homeworks не в виде списка'
        logging.error(message)
        send_message(telegram.Bot(token=TELEGRAM_TOKEN), message)
        raise TypeError
    return homeworks


def parse_status(homework):
    """Получение статуса домашней работы с API ответа."""
    try:
        status = homework.get('status')
        verdict = HOMEWORK_VERDICTS.get(status)
    except ValueError:
        logger.error(ValueError)
        return 'Статус отсутствует'
    if status not in HOMEWORK_VERDICTS:
        logger.error(ValueError)
        raise ValueError
    if 'homework_name' not in homework:
        logger.error(ValueError)
        raise ValueError
    verdict = HOMEWORK_VERDICTS.get(status)
    homework_name = homework.get('homework_name')
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def main():
    """Запуск работы бота по отслеживанию статуса домашней работы."""
    check_tokens()
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    timestamp = 1549962000
    previous_status = None
    homeworks_count = None

    while True:
        try:
            homework_list = get_api_answer(timestamp)
            check_response(homework_list)
            target_homework = homework_list['homeworks'][0]
            if (target_homework['status'] != previous_status
               or len(homework_list['homeworks']) > homeworks_count):
                message = parse_status(target_homework)
                previous_status = target_homework['status']
                homeworks_count = len(homework_list['homeworks'])
                send_message(bot, message)
            else:
                logger.debug('Нету новых статусов по домашней работе')

        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            send_message(bot, message)
        time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    main()
