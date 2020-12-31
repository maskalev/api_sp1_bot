import logging
import os
import time

import requests
import telegram
from dotenv import load_dotenv

load_dotenv()

PRAKTIKUM_TOKEN = os.getenv('PRAKTIKUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
URL = 'https://praktikum.yandex.ru/api/user_api/homework_statuses/'
VERDICTS_BY_STATUSES = {
    'reviewing': 'Работа взята в ревью. Скоро станет известен '
                 'результат.',
    'rejected': 'К сожалению в работе нашлись ошибки.',
    'approved': 'Ревьюеру всё понравилось, можно приступать к '
                'следующему уроку.',
}

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s, %(levelname)s, %(name)s, '
                           '%(message)s')


def parse_homework_status(homework):
    """
    Return reviewer's verdict on the current homework (rejected of approved)
    :param homework: dict
    :return: str
    """
    homework_name = homework.get('homework_name')
    if homework_name is None:
        return 'У работы нет имени. Обратись к ревьюверу или куратору.'
    homework_status = homework.get('status')
    if homework_status is None:
        return (f'Проверь статус работы "{homework_name}" и обратись к '
                f'ревьюверу или куратору.')
    verdict = VERDICTS_BY_STATUSES.get(homework_status)
    if verdict is None:
        return (f'Проверь статус работы "{homework_name}" и обратись к '
                f'ревьюверу или куратору.')
    return f'У вас проверили работу "{homework_name}"!\n\n{verdict}'


def get_homework_statuses(current_timestamp):
    """
    Return json of homeworks from specified time
    :param current_timestamp: int
    :return: dict
    """
    current_timestamp = current_timestamp or int(time.time())
    headers = {
        'Authorization': f'OAuth {PRAKTIKUM_TOKEN}',
    }
    params = {
        'from_date': current_timestamp,
    }
    try:
        homework_statuses = requests.get(URL, headers=headers, params=params)
        return homework_statuses.json()
    except ConnectionError:
        logging.error(msg='Ошибка соединения с API Практикума')
    except ValueError:
        logging.error(msg='Ошибка получения JSON')
    return {}


def send_message(message, bot_client):
    """
    Send reviewer's verdict to specified Telegram chat
    :param message: str
    :param bot_client: telegram.bot.Bot
    :return: telegram.message.Message
    """
    return bot_client.send_message(chat_id=CHAT_ID, text=message)


def main():
    telegram_bot = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time())
    while True:
        try:
            new_homework = get_homework_statuses(current_timestamp)
            if new_homework.get('homeworks'):
                send_message(parse_homework_status(new_homework.get(
                    'homeworks')[0]), telegram_bot)
            current_timestamp = new_homework.get('current_date',
                                                 current_timestamp)
            time.sleep(300)
        except Exception as e:
            logging.exception(msg=f'Бот столкнулся с ошибкой: {e}')
            time.sleep(5)


if __name__ == '__main__':
    main()
