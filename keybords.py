from utils import create_keyboard
from aiogram import  types
main_list = ['/Факультеты']
admin_list = ['/Активировать', '/Деактивировать', '/start']
mobile_block = ['Главное меню', 'Закончить', 'Назад']
gender_list = ['М', 'Ж', 'отмена']
start_button = create_keyboard(['/start'])
back_button = create_keyboard(['Назад'])
cancel_button = create_keyboard(['отмена'])
registration_button = create_keyboard(['/Зарегистрироваться'])
main_button = create_keyboard(main_list)
admin_button = create_keyboard(admin_list)
mobile_button = create_keyboard(mobile_block)
gender_button = create_keyboard(gender_list)
revome_keyboard = types.ReplyKeyboardRemove()