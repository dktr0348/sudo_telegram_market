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
    [
        KeyboardButton(text='Поделиться контактом'),
        KeyboardButton(text='Поделиться локацией')
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
    [KeyboardButton(text='отправить контакт', request_contact=True)]
], resize_keyboard=True)

send_location = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text='отправить локацию', request_location=True)]
], resize_keyboard=True)