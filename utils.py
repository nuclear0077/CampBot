import httpx
import logging
from http import HTTPStatus
from exceptions import UnexpectedAnswer
from config import HEADERS

from aiogram import types

logger = logging.getLogger(__name__)


def create_keyboard(key_list):
    """Функция для создания клавиатуры
        Args:
            key_list (list): список кнопок
        Return:
            ReplyKeyboardMarkup: обьект клавиатуры с набором кнопок
    """
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, selective=True)
    for key in key_list:
        keyboard.add(key)
    return keyboard


class WorkerApi:
    def __init__(self, url) -> None:
        self.__url = url

    @staticmethod
    def __get_api_answer(url, *args, **kwargs):
        """Функция для отправки get запроса url
        Args:
            url (str): адрес куда отправляем запрос
            args: список аргументов
            kwargs: список именованных аргументов для отправки передачи параметров в запрос
        Return:
            answer(httpx.Response): ответ API
        Raises:
            httpx.HTTPError: проброс ошибок API
        """
        try:
            logger.debug(f"поступил запрос на получение данных \nurl: {url}\nargs: {args}\nkwargs: {kwargs}")
            answer = httpx.get(url, params=kwargs, headers=HEADERS)
            logger.debug(f"API вернул ответ: {answer.status_code}\n текст:{answer.json()}")
            return answer
        except httpx.HTTPError as error:
            raise httpx.HTTPError(error) from error

    @staticmethod
    def __post_api_answer(url, *args, **kwargs):
        """Функция для отправки post запроса url
        Args:
            url (str): адрес куда отправляем запрос
            args: список аргументов
            kwargs: список именованных аргументов (data) для отправки передачи данных в запрос
        Return:
            answer(httpx.Response): ответ API
        Raises:
            httpx.HTTPError: проброс ошибок API
        """
        try:
            logger.debug(f"поступил запрос на отправку данных \nurl: {url}\nargs: {args}\nkwargs: {kwargs}")
            answer = httpx.post(url, data=kwargs.get('data'), headers=HEADERS)
            logger.debug(f"API вернул ответ: {answer.status_code}\n текст:{answer.json()}")
            return answer
        except httpx.HTTPError as error:
            raise httpx.HTTPError(error) from error

    @staticmethod
    def __patch_api_answer(url, *args, **kwargs):
        """Функция для отправки patch запроса url
        Args:
            url (str): адрес куда отправляем запрос
            args: список аргументов
            kwargs: список именованных аргументов (data_update) для отправки передачи данных в запрос
        Return:
            answer(httpx.Response): ответ API
        Raises:
            httpx.HTTPError: проброс ошибок API
        """
        try:
            logger.debug(f"поступил запрос на частичное обновление данных \nurl: {url}\nargs: {args}\nkwargs: {kwargs}")
            answer = httpx.patch(url, data=kwargs.get('data_update'), headers=HEADERS)
            logger.debug(f"API вернул ответ: {answer.status_code}\n текст:{answer.json()}")
            return answer
        except httpx.HTTPError as error:
            raise httpx.HTTPError(error) from error

    def create_user(self, user_data):
        """Функция для формирования url и
        отправки запроса на регистрацию
        Args:
            user_data (dict): пользовательская информация с ключами
            (user_id, fist_name, last_name, age, gender, city)
            для регистрация пользователя в базе данных
        Returns:
            HTTPStatus.CREATED (int): статус регистрации 201
        Raises:
            httpx.RequestError: ошибка когда статус не равен 201
            """
        url = f'{self.__url}users/'
        logger.debug(f'Поступил запрос создания пользователя'
                     f'\nСформирован URL: {url}\n'
                     f'Поступили следующие данные: {user_data}')
        response = self.__post_api_answer(url, data=user_data)
        if not response.status_code == HTTPStatus.CREATED:
            raise httpx.RequestError
        return HTTPStatus.CREATED

    def information_update(self, data_update):
        """Функция для формирования url и
        отправки запроса на обновление информации о пользователе
        Args:
            data_update (dict): информация для обновления с ключами
            (user_id, department)
        Returns:
            bool: в случае успеха True иначе False
        Raises:
            UnexpectedAnswer: кастомный exception с неопределенным статусом
            """
        logger.debug(f"Поступил запрос на обновление "
                     f"информации о пользователе {data_update.get('user_id')}")
        url = f"{self.__url}users/{data_update.pop('user_id')}/"
        logger.debug(f'\nСформирован URL: {url}\n'
                     f'Поступили следующие данные: {data_update}')
        response = self.__patch_api_answer(url, data_update=data_update)
        if response.status_code == HTTPStatus.OK:
            return True
        elif response.status_code == HTTPStatus.NOT_FOUND:
            return False
        else:
            raise UnexpectedAnswer(f'Неожиданный ответ API {response.status_code}')

    @staticmethod
    def prepare_data(response):
        """Функция для проверки существования ключей в ответе
        Args:
            response (list): ответ
        Returns:
            prepare_data (list) or None: если ключ существует
            возвращается словарь иначе None
        Raises:
            KeyError: В ответе API нет ключа типов обучения
            TypeError: когда на вход подали не словарь
        """
        logger.debug('Проверяем поступившие данные')
        if not isinstance(response, list):
            raise TypeError(f'Неверный формат ответа, ожидаем список, поступил {type(response)}')
        prepare_data = {}
        for resp in response:
            if not isinstance(resp, dict):
                raise TypeError(f'Неверный формат данных, ожидаем словарь, , поступил {type(resp)}')
            if resp.get('id') is None:
                raise KeyError('В ответе API нет ключа id')
            if resp.get('name') is None:
                raise KeyError('В ответе API нет ключа name')
            pid, values = resp.values()
            prepare_data[values] = pid
        return prepare_data

    def get_client_data(self, user_id):
        """Функция для формирования url и
        отправки запроса на получения пользователя
        Args:
            user_id (int): id пользователя телеграм
        Returns:
            response (dict): обьект словаря с ключом is_exist
            """
        url = f'{self.__url}users/{user_id}/'
        logger.debug(f'Поступил запрос на получение'
                     f'информации о пользователе {user_id}'
                     f'\nСформирован URL: {url}\n'
                     )
        response = self.__get_api_answer(url)
        if response.status_code not in [HTTPStatus.OK, HTTPStatus.NOT_FOUND]:
            raise UnexpectedAnswer('Неожиданный ответ')
        status = response.status_code == HTTPStatus.OK
        response = response.json()
        response['is_exist'] = status
        return response


    def get_type_education(self):
        """Функция для формирования url и
        отправки запроса на получение типов образования
        Returns:
            prepare_data (dict): словарь в формате имя обучения:id
        Raises:
            UnexpectedAnswer: когда ответ != 200
            """
        url = f"{self.__url}type/"
        logger.debug(f'Поступил запрос на получение'
                     f'информации о списке образования'
                     f'\nСформирован URL: {url}\n'
                     )
        response = self.__get_api_answer(url)
        if response.status_code == HTTPStatus.OK:
            return self.prepare_data(response.json())
        raise UnexpectedAnswer(f'Неожиданный ответ {response.status_code}')

    def get_faculties(self, type_pid):
        """Функция для формирования url и
        отправки запроса на получение факультетов по типу образования
        Args:
            type_pid (int): id типа образования
        Returns:
            prepare_data (dict): словарь в формате имя факультет:id
        Raises:
            UnexpectedAnswer: когда ответ != 200
            """
        url = f"{self.__url}faculties/{type_pid}/"
        logger.debug(f'Поступил запрос на получение'
                     f'информации о списке факультетов'
                     f'по типу образования с id: {type_pid}'
                     f'\nСформирован URL: {url}\n'
                     )
        response = self.__get_api_answer(url)
        if response.status_code == HTTPStatus.OK:
            return self.prepare_data(response.json())
        raise UnexpectedAnswer(f'Неожиданный ответ {response.status_code}')

    def get_profiles(self, type_pid, faculite_pid):
        """Функция для формирования url и
        отправки запроса на получение профилей по типу образования и факультету
        Args:
            type_pid (int): id типа образования
            faculite_pid (int): id факультета
        Returns:
            prepare_data (dict): словарь в формате имя профиль:id
        Raises:
            UnexpectedAnswer: когда ответ != 200
            """
        url = f"{self.__url}profiles/{type_pid}/{faculite_pid}/"
        logger.debug(f'Поступил запрос на получение'
                     f'информации о списке профилей'
                     f'по типу образования c id: {type_pid}'
                     f'факультета с id: {faculite_pid}'
                     f'\nСформирован URL: {url}\n'
                     )
        response = self.__get_api_answer(url)
        if response.status_code == HTTPStatus.OK:
            return self.prepare_data(response.json())
        raise UnexpectedAnswer(f'Неожиданный ответ {response.status_code}')

    def get_description(self, type_pid, faculite_pid, profile_pid):
        """Функция для формирования url и
        отправки запроса на получение описания профилей по типу образования и факультету
        Args:
            type_pid (int): id типа образования
            faculite_pid (int): id факультета
            profile_pid (int): id профиля
        Returns:
             description (str): сообщение профиля
        Raises:
            UnexpectedAnswer: когда ответ != 200
            """
        url = f"{self.__url}descriptions/{type_pid}/{faculite_pid}/{profile_pid}/"
        logger.debug(f'Поступил запрос на получение'
                     f'информации о профилей'
                     f'по типу образования c id: {type_pid}'
                     f'факультета с id: {faculite_pid}'
                     f'профиля с id: {profile_pid}'
                     f'\nСформирован URL: {url}\n'
                     )
        response = self.__get_api_answer(url)
        if response.status_code == HTTPStatus.OK:
            return list(self.prepare_data(response.json()))[0]
        raise UnexpectedAnswer(f'Неожиданный ответ {response.status_code}')
