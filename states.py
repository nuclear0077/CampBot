from aiogram.dispatcher.filters.state import State, StatesGroup


class Registration(StatesGroup):
    """Класс для состояний регистрации
    f_name - запрос имени
    l_name - запрос фамилии
    age - запрос возраста
    gender - запрос пола
    city - запрос города
    """
    f_name = State()
    l_name = State()
    age = State()
    gender = State()
    city = State()


class Activations(StatesGroup):
    """Класс для состояний активации пользователя
    user_id - запрос ID Telegram
    department - номер отдела
    """
    user_id = State()
    department = State()


class GetMessage(StatesGroup):
    """Класс для получения итогового сообщения
    type_traning - запрос типа обучения
    faculty - запрос факультета
    profile - запрос профиля
    last_state - установка последнего статуса для переходов в меню
    """
    type_traning = State()
    faculty = State()
    profile = State()
    last_state = State()
