import logging
import sys

from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from config import set_logging, URL_API, API_TOKEN_TELEGRAM, NAME_BOT
from utils import WorkerApi
from keybords import gender_list, start_button, cancel_button, registration_button, main_button, admin_button, \
    mobile_button, gender_button, revome_keyboard

from states import Registration, Activations, GetMessage

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler(sys.stdout)
logger.addHandler(handler)
bot = Bot(token=API_TOKEN_TELEGRAM)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)
dp.middleware.setup(LoggingMiddleware())

sclient = WorkerApi(url=URL_API)


def check_tokens():
    """Проверка загрузки переменных из venv."""
    logger.debug('Загружаем переменные из venv')
    if not URL_API:
        logger.critical('Нет токена URL_API')
    if not API_TOKEN_TELEGRAM:
        logger.critical('Нет токена API_TOKEN_TELEGRAM')
    if all((URL_API, API_TOKEN_TELEGRAM)):
        logger.debug('Все токены успешно получены')
        return None
    logger.critical('Приостанавливаем программу')
    sys.exit('Не найден токен')


async def send_error_message(user_id):
    await bot.send_message(user_id, 'Произошла ошибка попробуйте позже, для повторного ввода нажмите '
                                    'кнопку start', reply_markup=start_button)


@dp.message_handler(commands=['start'])
async def welcome(message: types.Message):
    """Функция для обработки команды start c проверкой
    существования пользователя в системе и активацией учетной
    записи """
    try:
        user_data = sclient.get_client_data(message.from_user.id)
        if not user_data.get('is_exist'):
            await message.answer('Вы не зарегистрированы, необходимо выполнить регистрацию',
                                 reply_markup=registration_button)
        elif user_data.get('is_exist') and not user_data.get('is_active'):
            await message.answer(f'Ваша учетная запись ожидает активации, Ваш ID {message.from_user.id}, сообщите БТ.',
                                 reply_markup=start_button)
        else:
            await message.answer(f'Добро пожаловать в информативный бот {NAME_BOT}', reply_markup=main_button)
    except Exception as exc:
        logger.exception(exc)
        await send_error_message(message.from_user.id)


@dp.message_handler(state='*', commands='cancel')
@dp.message_handler(Text(equals='отмена', ignore_case=True), state='*')
async def cancel_handler(message: types.Message, state: FSMContext):
    """Функция для отмены любого действия с завершением состояния"""
    current_state = await state.get_state()
    if current_state is None:
        return
    await state.finish()
    await message.reply('Вы отменили действие, для повторного запуска нажмите на кнопку',
                        reply_markup=start_button)


@dp.message_handler(commands=['Зарегистрироваться'])
async def cmd_start(message: types.Message):
    """Функция для регистрации пользователя
    в боте с проверкой на существовании в БД
    """
    try:
        user_data = sclient.get_client_data(message.from_user.id)
        if not user_data.get('is_exist'):
            await Registration.f_name.set()
            await message.answer(
                'На любом этапе регистрации вы можете от нее отказаться, написал мне отмена либо нажав '
                'на кубик рядом с кнопкой отправки сообщения')
            await message.answer('Введите имя, например Александр', reply_markup=revome_keyboard)
        else:
            await message.answer('Вы уже зарегистрированы, нажмите на кнопку start для перехода в главное меню',
                                 reply_markup=start_button)
    except Exception as exc:
        logger.exception(exc)
        await send_error_message(message.from_user.id)


@dp.message_handler(state=Registration.f_name)
async def getting_name(message: types.Message, state: FSMContext):
    """Функция для получения имени в состоянии f_name"""
    async with state.proxy() as data:
        data['first_name'] = message.text
    await Registration.next()
    await message.answer('Введите фамилию, например Смирнов', reply_markup=cancel_button)


@dp.message_handler(state=Registration.l_name)
async def getting_surname(message: types.Message, state: FSMContext):
    """Функция для получения фамилии в состоянии l_name"""
    async with state.proxy() as data:
        data['last_name'] = message.text
    await Registration.next()
    await message.answer('Введите возраст числом, например 25', reply_markup=cancel_button)


@dp.message_handler(lambda message: not message.text.isdigit(), state=Registration.age)
async def check_age(message: types.Message):
    """Проверка, что введено число для функции получения возраста"""
    return await message.answer('Вы ввели не число,введите повторно например 25', reply_markup=cancel_button)


@dp.message_handler(lambda message: message.text.isdigit(), state=Registration.age)
async def getting_gender(message: types.Message, state: FSMContext):
    """Функция для получения пола"""
    await Registration.next()
    await state.update_data(age=int(message.text))
    await message.answer('Укажите пол (кнопкой)', reply_markup=gender_button)


@dp.message_handler(lambda message: message.text not in gender_list, state=Registration.gender)
async def check_gender(message: types.Message):
    """Функция для проверки, что пол соответствует ожидаемому значению"""
    return await message.answer('Неизвестный пол. Укажите пол кнопкой на клавиатуре', reply_markup=gender_button)


@dp.message_handler(state=Registration.gender)
async def getting_city(message: types.Message, state: FSMContext):
    """"Функция для получения города"""
    async with state.proxy() as data:
        data['gender'] = message.text
        await Registration.next()
        await message.answer('Укажите ваш город:', reply_markup=revome_keyboard)


@dp.message_handler(state=Registration.city)
async def registration(message: types.Message, state: FSMContext):
    """Функция для регистрации пользователя в БД"""
    try:
        async with state.proxy() as data:
            data['city'] = message.text
            data['user_id'] = message.from_user.id
            await message.reply('Регистрируемся, ожидайте')
            sclient.create_user(user_data=data.as_dict())
            await message.answer('Ваша учетная запись ожидает активации,'
                                 f'Ваш ID {message.from_user.id}, сообщите его БТ'
                                 )
            await state.finish()
    except Exception as exc:
        logger.exception(exc)
        await send_error_message(message.from_user.id)
        await state.finish()


@dp.message_handler(commands=['admin'])
async def admin(message: types.Message):
    """Функция для проверки разрешений в административное меню"""
    try:
        user_data = sclient.get_client_data(message.from_user.id)
        if not user_data.get('is_exist'):
            await message.answer('Вы не зарегистированы, необходимо выполнить регистрацию',
                                 reply_markup=registration_button)
        elif user_data.get('admin'):
            await message.answer('Вы в административном меню, выберите действие на клавиатуре',
                                 reply_markup=admin_button)
        else:
            await message.answer("Неизвестная команда, перейдите в главное меню",
                                 reply_markup=start_button)
    except Exception as exc:
        logger.exception(exc)
        await send_error_message(message.from_user.id)


@dp.message_handler(commands=['Активировать'])
async def select_action(message: types.Message):
    """Функция для выбора действия в административном меню"""
    try:
        user_data = sclient.get_client_data(message.from_user.id)
        if user_data.get('admin'):
            await Activations.user_id.set()
            await message.answer('Укажите id пользователя',
                                 reply_markup=revome_keyboard)
    except Exception as exc:
        logger.exception(exc)
        await send_error_message(message.from_user.id)


@dp.message_handler(state=Activations.user_id)
async def select_user(message: types.Message, state: FSMContext):
    """Функция для получения user_id в состоянии Activations.user_id"""
    async with state.proxy() as data:
        data['user_id'] = message.text
        await Activations.next()
        await bot.send_message(message.from_user.id,
                               'Для активации учетной записи, отправьте номер отдела',
                               reply_markup=revome_keyboard)


@dp.message_handler(state=Activations.department)
async def activate_user(message: types.Message, state: FSMContext):
    """Функция для получения номера отедла в состоянии Activations.department
    и смены в БД информации у следующих полей department, is_active
    """
    try:
        async with state.proxy() as data:
            data['department'] = int(message.text)
            data['is_active'] = True
            status = sclient.information_update(data_update=data.as_dict())
            if status:
                await bot.send_message(data['user_id'], 'Ваша учетная запись активирована, нажмите на кнопку /start',
                                       reply_markup=start_button)
                await message.answer(
                    f"Учетная запись {data['user_id']} активирована, сообщение отправлено пользователю")
                await state.finish()
            else:
                await bot.send_message(message.from_user.id, 'Учетная запись с данным id не существует, проверьте id',
                                       reply_markup=admin_button)
                await state.finish()
    except ValueError as error:
        logger.exception(error)
        await bot.send_message(message.from_user.id, 'Введите номер отдела в числовом формате или нажмите отмена ',
                               reply_markup=cancel_button)
    except Exception as error:
        logger.exception(error)
        await send_error_message(message.from_user.id)
        await state.finish()


@dp.message_handler(Text(equals='Назад', ignore_case=True), state=GetMessage.last_state)
@dp.message_handler(Text(equals='Главное меню', ignore_case=True), state=GetMessage.last_state)
@dp.message_handler(Text(equals='Назад', ignore_case=True), state=GetMessage.faculty)
@dp.message_handler(Text(equals='Назад', ignore_case=True), state=GetMessage.profile)
async def menu_navigation(message: types.Message, state: FSMContext):
    """Функция для обработок кнопок назад, главное меню
    в состояниях last_state, faculty, profile
    первым делом получаем текущий статус, дальше проверяем,
    что текущий статус соответствует условию, дальше устанавливаем
    предыдущий статус и получаем соответствующую информацию
    от API и отправляем новый обьект кнопок пользователю."""
    try:
        current_state = await state.get_state()
        if current_state == 'GetMessage:faculty':
            await GetMessage.previous()
            async with state.proxy() as data:
                type_traning = sclient.get_type_education()
                data['data_dict'] = type_traning
                markup = types.ReplyKeyboardMarkup(resize_keyboard=True, selective=True)
                [markup.add(values) for values, pid in type_traning.items()]
            await message.answer("Выберите тип образования используя клавиатуру",
                                 reply_markup=markup)
        elif current_state == 'GetMessage:profile':
            await GetMessage.previous()
            async with state.proxy() as data:
                faculty_list = sclient.get_faculties(data['type_traning'])
                markup = types.ReplyKeyboardMarkup(resize_keyboard=True, selective=True)
                data['data_dict'] = faculty_list
                [markup.add(values) for values, pid in faculty_list.items()]
                markup.add('Назад')
                await message.answer("Выберите  факультет, используя клавиатуру", reply_markup=markup)
        elif current_state == 'GetMessage:last_state' and message.text == 'Назад':
            await GetMessage.previous()
            async with state.proxy() as data:
                profiles = sclient.get_profiles(data['type_traning'], data['faculty'])
                data['data_dict'] = profiles
                markup = types.ReplyKeyboardMarkup(resize_keyboard=True, selective=True)
                [markup.add(values) for values, pid in profiles.items()]
                markup.add('Назад')
                await message.answer("Выберите  направление, используя клавиатуру", reply_markup=markup)
        elif current_state == 'GetMessage:last_state' and message.text == 'Главное меню':
            await GetMessage.first()
            async with state.proxy() as data:
                type_traning = sclient.get_type_education()
                data['data_dict'] = type_traning
                markup = types.ReplyKeyboardMarkup(resize_keyboard=True, selective=True)
                [markup.add(values) for values, pid in type_traning.items()]
            await message.answer("Выберите тип образования используя клавиатуру",
                                 reply_markup=markup)
    except Exception as exc:
        logger.exception(exc)
        await send_error_message(message.from_user.id)
        await state.finish()


@dp.message_handler(commands=['Факультеты'])
async def getting_type_trainings(message: types.Message, state: FSMContext):
    """Функция для получения списка направлений для активированных пользователей"""
    try:
        user_data = sclient.get_client_data(message.from_user.id)
        if user_data.get('is_active'):
            async with state.proxy() as data:
                type_traning = sclient.get_type_education()
                data['data_dict'] = type_traning
                markup = types.ReplyKeyboardMarkup(resize_keyboard=True, selective=True)
                [markup.add(values) for values, pid in type_traning.items()]
            await message.answer("Выберите тип образования используя клавиатуру",
                                 reply_markup=markup)
            await GetMessage.type_traning.set()
        elif not user_data.get('is_exist'):
            await message.answer('Вы не зарегистрированы, необходимо выполнить регистрацию',
                                 reply_markup=registration_button)
        else:
            await message.answer(f"Ваша учетная запись ожидает активации,Ваш ID {message.from_user.id}, сообщите БТ.",
                                 reply_markup=start_button)
    except Exception as exc:
        logger.exception(exc)
        await send_error_message(message.from_user.id)
        await state.finish()


@dp.message_handler(state=GetMessage.type_traning)
async def getting_faculties(message: types.Message, state: FSMContext):
    """Функция для получения списка факультетов"""
    try:
        async with state.proxy() as data:
            data['type_traning'] = data['data_dict'].get(message.text)
            faculty_list = sclient.get_faculties(data['type_traning'])
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True, selective=True)
            data['data_dict'] = faculty_list
            [markup.add(values) for values, pid in faculty_list.items()]
            markup.add('Назад')
        await message.answer("Выберите  факультет, используя клавиатуру", reply_markup=markup)
        await GetMessage.next()
    except Exception as exc:
        logger.exception(exc)
        await send_error_message(message.from_user.id)
        await state.finish()


@dp.message_handler(state=GetMessage.faculty)
async def getting_profiles(message: types.Message, state: FSMContext):
    """Функция для получения списка профилей"""
    try:
        async with state.proxy() as data:
            data['faculty'] = data['data_dict'].get(message.text)
            profiles = sclient.get_profiles(int(data['type_traning']), int(data['faculty']))
            data['data_dict'] = profiles
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True, selective=True)
            [markup.add(values) for values, pid in profiles.items()]
            markup.add('Назад')
        await message.answer("Выберите направление, используя клавиатуру", reply_markup=markup)
        await GetMessage.next()
    except Exception as exc:
        logger.exception(exc)
        await send_error_message(message.from_user.id)
        await state.finish()


@dp.message_handler(state=GetMessage.profile)
async def getting_message(message: types.Message, state: FSMContext):
    """Функция для получения сообщения о профиле
    передаем api собранные раннее данные и получаем сообщение
    """
    try:
        async with state.proxy() as data:
            data['profile'] = data['data_dict'].get(message.text)
            description = sclient.get_description(data['type_traning'], data['faculty'], data['profile'])
            data['data_dict'] = description
        await bot.send_message(message.from_user.id, description, reply_markup=mobile_button)
        await GetMessage.next()
    except Exception as exc:
        logger.exception(exc)
        await send_error_message(message.from_user.id)
        await state.finish()


@dp.message_handler(state=GetMessage.last_state)
async def finish_getting_message(message: types.Message, state: FSMContext):
    """Функция для завершения статуса получения сообщения и выход в главное меню,
    а также возможности воспользоваться кнопкой назад"""
    try:
        await state.finish()
        await bot.send_message(message.from_user.id, f'Добро пожаловать в информативный бот {NAME_BOT}',
                               reply_markup=main_button)
    except Exception as exc:
        logger.exception(exc)
        await send_error_message(message.from_user.id)
        await state.finish()


@dp.message_handler(content_types=['text'])
async def getting_another_text(message):
    await bot.send_message(message.from_user.id, 'Я этого не понимаю, для перехода в главное меню нажмите на кнопку '
                                                 '/start', reply_markup=start_button)


def main():
    try:
        executor.start_polling(dp, skip_updates=True)
    except Exception as error:
        logger.exception(error)


if __name__ == '__main__':
    set_logging()
    main()
