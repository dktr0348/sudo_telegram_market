from aiogram.types import (ReplyKeyboardMarkup, KeyboardButton, 
                          InlineKeyboardMarkup, InlineKeyboardButton)
from aiogram.utils.keyboard import InlineKeyboardBuilder
import src.database.requests as db
import logging
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

# Клавиатура для выбора категории
async def categories():
    try:
        all_categories = await db.get_categories()
        categories_list = [cat for cat in all_categories]
        
        keyboard = InlineKeyboardBuilder()
        
        if not categories_list:
            keyboard.add(InlineKeyboardButton(
                text="🏠 В главное меню",
                callback_data="back"
            ))
        else:
            for category in categories_list:
                keyboard.add(InlineKeyboardButton(
                    text=category.name,
                    callback_data=f'category_{category.id}'
                ))
            keyboard.add(InlineKeyboardButton(
                text="🏠 В главное меню",
                callback_data="back"
            ))
        
        return keyboard.adjust(2).as_markup()
    except Exception as e:
        logging.error(f"Ошибка при создании клавиатуры категорий: {e}")
        return None

# Клавиатура для выбора продукта
async def category_products(category_id: int):
    try:
        all_products = await db.get_products_by_category(category_id)
        products_list = [prod for prod in all_products]
        
        keyboard = InlineKeyboardBuilder()
        
        if not products_list:
            keyboard.add(InlineKeyboardButton(
                text="◀️ Назад к категориям",
                callback_data="back_to_categories"
            ))
        else:
            for product in products_list:
                keyboard.add(InlineKeyboardButton(
                    text=f"{product.name} - {product.price}₽",
                    callback_data=f'product_{product.product_id}'
                ))
            keyboard.add(InlineKeyboardButton(
                text="◀️ Назад к категориям",
                callback_data="back_to_categories"
            ))
        
        return keyboard.adjust(2).as_markup()
    except Exception as e:
        logging.error(f"Ошибка при создании клавиатуры продуктов: {e}")
        return None
