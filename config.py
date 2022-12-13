import os
from dotenv import load_dotenv
import logging

load_dotenv()
API_TOKEN_TELEGRAM = os.getenv('API_TOKEN_TELEGRAM')
URL_API = os.getenv('URL_API')
HEADERS = {'Authorization': os.getenv('API_TOKEN')}
NAME_BOT = os.getenv('NAME_BOT')


def set_logging():
    logging.basicConfig(
        level=logging.INFO,
        filename='my_bot.log',
        format=(
            '%(asctime)s [%(levelname)s] | '
            '(%(filename)s).%(funcName)s:%(lineno)d | %(message)s'
        ),
    )
