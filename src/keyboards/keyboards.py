from aiogram.types import (ReplyKeyboardMarkup, KeyboardButton, 
                          InlineKeyboardMarkup, InlineKeyboardButton)

# Главное меню
main = ReplyKeyboardMarkup(keyboard=[
    [
        KeyboardButton(text='Регистрация'),
        KeyboardButton(text='Авторизация')
    ],
    [
        KeyboardButton(text='Каталог'),
        KeyboardButton(text='Корзина')
    ],
    
    [KeyboardButton(text='В главное меню')]
], resize_keyboard=True)

# Клавиатура для корзины
cart_keyboard = ReplyKeyboardMarkup(keyboard=[
    [
        KeyboardButton(text='Оформить заказ'),
        KeyboardButton(text='Очистить корзину')
    ],
    [KeyboardButton(text='В главное меню')]
], resize_keyboard=True)

# Клавиатура для основных команд
main_command = InlineKeyboardMarkup(inline_keyboard=[
    [
        InlineKeyboardButton(text='Каталог', callback_data='catalog'),
        InlineKeyboardButton(text='Корзина', callback_data='cart')
    ],
    [
        InlineKeyboardButton(text='Контакты', callback_data='contacts'),
        InlineKeyboardButton(text='Локация', callback_data='location')
    ],
    [InlineKeyboardButton(text='Назад', callback_data='back')]
])

# Функция для построения каталога (предполагаю, что она у вас уже есть)
async def catalog_builder():
    catalog_kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text='Товар 1', callback_data='catalog_1'),
            InlineKeyboardButton(text='Товар 2', callback_data='catalog_2')
        ],
        [
            InlineKeyboardButton(text='Товар 3', callback_data='catalog_3'),
            InlineKeyboardButton(text='Товар 4', callback_data='catalog_4')
        ],
        [InlineKeyboardButton(text='Назад', callback_data='back')]
    ])

    return catalog_kb


send_contact = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text='Отправить номер телефона', request_contact=True)],
    [KeyboardButton(text='Отмена регистрации')]
], resize_keyboard=True)

send_location = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text='Отправить местоположение', request_location=True)],
    [KeyboardButton(text='Отмена регистрации')]
], resize_keyboard=True)

# Клавиатура для меню команд
menu_commands = ReplyKeyboardMarkup(keyboard=[
    [
        KeyboardButton(text='/start'),
        KeyboardButton(text='/menu'),
        KeyboardButton(text='/help')
    ],
    [
        KeyboardButton(text='/profile'),
        KeyboardButton(text='/settings'),
        KeyboardButton(text='/register')
    ],
    [KeyboardButton(text='В главное меню')]
], resize_keyboard=True)

# Клавиатура для отмены действия
cancel_kb = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text="Отменить редактирование")]
], resize_keyboard=True)

# Клавиатура для профиля
profile_keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [
        InlineKeyboardButton(text='✏️ Изменить имя', callback_data='edit_name'),
        InlineKeyboardButton(text='✉️ Изменить email', callback_data='edit_email')
    ],
    [
        InlineKeyboardButton(text='📱 Изменить телефон', callback_data='edit_phone'),
        InlineKeyboardButton(text='🔢 Изменить возраст', callback_data='edit_age')
    ],
    [
        InlineKeyboardButton(text='📷 Изменить фото', callback_data='edit_photo'),
        InlineKeyboardButton(text='📍 Изменить локацию', callback_data='edit_location')
    ],
    [InlineKeyboardButton(text='◀️ Назад', callback_data='back')]
])