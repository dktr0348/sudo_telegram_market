from aiogram.types import (ReplyKeyboardMarkup, KeyboardButton, 
                          InlineKeyboardMarkup, InlineKeyboardButton)
from aiogram.utils.keyboard import InlineKeyboardBuilder
import src.database.requests as db
import logging
# Главное меню
main = ReplyKeyboardMarkup(keyboard=[
    [
        KeyboardButton(text='👤 Регистрация'),
        KeyboardButton(text='🔑 Авторизация')
    ],
    [
        KeyboardButton(text='🛍️ Каталог'),
        KeyboardButton(text='🛒 Корзина')
    ],
    [KeyboardButton(text='🏠 В главное меню')]
], resize_keyboard=True)

# Клавиатура для корзины
cart_keyboard = ReplyKeyboardMarkup(keyboard=[
    [
        KeyboardButton(text='💳 Оформить заказ'),
        KeyboardButton(text='🗑️ Очистить корзину')
    ],
    [KeyboardButton(text='🏠 В главное меню')]
], resize_keyboard=True)

# Клавиатура для основных команд
main_command = InlineKeyboardMarkup(inline_keyboard=[
    [
        InlineKeyboardButton(text='🛍️ Катал����г', callback_data='catalog'),
        InlineKeyboardButton(text='🛒 Корзина', callback_data='cart')
    ],
    [
        InlineKeyboardButton(text='📞 Контакты', callback_data='contacts'),
        InlineKeyboardButton(text='📍 Локация', callback_data='location')
    ],
    [InlineKeyboardButton(text='◀️ Назад', callback_data='back')]
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
    [KeyboardButton(text='📱 Отправить номер телефона', request_contact=True)],
    [KeyboardButton(text='❌ Отмена регистрации')]
], resize_keyboard=True)

send_location = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text='📍 Отправить местоположение', request_location=True)],
    [KeyboardButton(text='❌ Отмена регистрации')]
], resize_keyboard=True)

# Клавиатура для меню команд
menu_commands = ReplyKeyboardMarkup(keyboard=[
    [
        KeyboardButton(text='🚀 /start'),
        KeyboardButton(text='📋 /menu'),
        KeyboardButton(text='❓ /help')
    ],
    [
        KeyboardButton(text='👤 /profile'),
        KeyboardButton(text='⚙️ /settings'),
        KeyboardButton(text='📝 /register')
    ],
    [KeyboardButton(text='🏠 В главное меню')]
], resize_keyboard=True)

# Клавиатура для отмены действия
cancel_kb = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text="❌ Отменить редактирование")]
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

confirm = InlineKeyboardMarkup (inline_keyboard=[
    [InlineKeyboardButton(text='✅ Да', callback_data='ok-sure')], 
    [InlineKeyboardButton(text='❌ Нет', callback_data='cancel-sure')]],
    resize_keyboard=True)

admin_main = ReplyKeyboardMarkup(keyboard=[
    [
        KeyboardButton(text='➕ Добавить категорию'),
        KeyboardButton(text='➖ Удалить категорию')
    ],
    [
        KeyboardButton(text='➕ Добавить товар'),
        KeyboardButton(text='➖ Удалить товар')
    ],
    [KeyboardButton(text='✏️ Редактировать товар')],
    [
        KeyboardButton(text='👥 Добавить админа'),
        KeyboardButton(text='🚫 Удалить админа')
    ],
    [KeyboardButton(text='🚪 Выйти')]
], resize_keyboard=True)

async def delete_categories():
    all_categories = await db.get_categories()
    keyboard = InlineKeyboardBuilder()
    for category in all_categories:
        keyboard.add(InlineKeyboardButton(text=category.name, callback_data=f'delete_{category.id}'))
    return keyboard.adjust(2).as_markup()

async def admin_categories():
    all_categories = await db.get_categories()
    keyboard = InlineKeyboardBuilder()
    for category in all_categories:
        keyboard.add(InlineKeyboardButton(text=category.name, callback_data=f'addcategory_{category.id}'))
    return keyboard.adjust(2).as_markup()

async def delete_product():
    try:
        all_products = await db.get_all_products()
        keyboard = InlineKeyboardBuilder()
        
        if not all_products:
            keyboard.add(InlineKeyboardButton(
                text="Нет доступных товаров",
                callback_data="no_products"
            ))
        else:
            for product in all_products:
                keyboard.add(InlineKeyboardButton(
                    text=f"{product.name} - {product.price}₽",
                    callback_data=f"proddelete_{product.product_id}"
                ))
                
        keyboard.add(InlineKeyboardButton(
            text="◀️ Отмена",
            callback_data="cancel_delete"
        ))
        
        return keyboard.adjust(1).as_markup()
    except Exception as e:
        logging.error(f"Ошибка при создании клавиатуры: {e}")
        return None

async def add_admins():
    all_admins = await db.get_admins()
    keyboard = InlineKeyboardBuilder()
    for admin in all_admins:
        keyboard.add(InlineKeyboardButton(
            text=f"{admin.first_name or f'ID: {admin.user_id}'}", 
            callback_data=f'addadmin_{admin.user_id}'
        ))
    return keyboard.adjust(2).as_markup()
    
async def delete_admins():
    try:
        all_admins = await db.get_admins()
        keyboard = InlineKeyboardBuilder()
        
        if not all_admins:
            keyboard.add(InlineKeyboardButton(
                text="Нет администраторов для удаления",
                callback_data="no_admins"
            ))
        else:
            for admin in all_admins:
                keyboard.add(InlineKeyboardButton(
                    text=f"{admin.first_name or f'ID: {admin.user_id}'}", 
                    callback_data=f'deleteadmin_{admin.user_id}'
                ))
            
        keyboard.add(InlineKeyboardButton(
            text="◀️ Отмена",
            callback_data="cancel_delete"
        ))
        
        return keyboard.adjust(1).as_markup()
    except Exception as e:
        logging.error(f"Ошибка при создании клавиатуры администраторов: {e}")
        return None

async def edit_product_kb():
    """Клавиатура для выбора товара для редактирования"""
    try:
        all_products = await db.get_all_products()
        keyboard = InlineKeyboardBuilder()
        
        if not all_products:
            keyboard.add(InlineKeyboardButton(
                text="Нет доступных товаров",
                callback_data="no_products"
            ))
        else:
            for product in all_products:
                keyboard.add(InlineKeyboardButton(
                    text=f"{product.name} - {product.price}₽",
                    callback_data=f"edit_product_{product.product_id}"
                ))
                
        keyboard.add(InlineKeyboardButton(
            text="◀️ Отмена",
            callback_data="cancel_edit"
        ))
        
        return keyboard.adjust(1).as_markup()
    except Exception as e:
        logging.error(f"Ошибка при создании клавиатуры: {e}")
        return None

edit_product_fields = InlineKeyboardMarkup(inline_keyboard=[
    [
        InlineKeyboardButton(text="📝 Название", callback_data="edit_field_name"),
        InlineKeyboardButton(text="📋 Описание", callback_data="edit_field_description")
    ],
    [
        InlineKeyboardButton(text="💰 Цена", callback_data="edit_field_price"),
        InlineKeyboardButton(text="🔢 Количество", callback_data="edit_field_quantity")
    ],
    [
        InlineKeyboardButton(text="📷 Фото", callback_data="edit_field_photo"),
        InlineKeyboardButton(text="📁 Категория", callback_data="edit_field_category")
    ],
    [InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_admin_menu")]
])

def product_actions(product_id: int, current_quantity: int = 1) -> InlineKeyboardMarkup:
    """Клавиатура действий с товаром"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="➖", callback_data=f"decrease_{product_id}"),
            InlineKeyboardButton(text=f"{current_quantity} шт.", callback_data=f"quantity_{product_id}"),
            InlineKeyboardButton(text="➕", callback_data=f"increase_{product_id}")
        ],
        [
            InlineKeyboardButton(text="🛒 Добавить в корзину", callback_data=f"add_to_cart_{product_id}")
        ],
        [
            InlineKeyboardButton(text="◀️ Назад к категориям", callback_data="back_to_categories")
        ]
    ])

async def edit_product_by_category_kb(category_id: int):
    """Клавиатура для выбора товара для редактирования из конкретной категории"""
    try:
        products = await db.get_products_by_category(category_id)
        keyboard = InlineKeyboardBuilder()
        
        if not products:
            keyboard.add(InlineKeyboardButton(
                text="Нет доступных товаров",
                callback_data="no_products"
            ))
        else:
            for product in products:
                keyboard.add(InlineKeyboardButton(
                    text=f"{product.name} - {product.price}₽",
                    callback_data=f"edit_product_{product.product_id}"
                ))
                
        keyboard.add(InlineKeyboardButton(
            text="◀️ Назад к категориям",
            callback_data="back_to_categories"
        ))
        
        return keyboard.adjust(1).as_markup()
    except Exception as e:
        logging.error(f"Ошибка при создании клавиатуры: {e}")
        return None

async def delete_products():
    """Клавиатура для удаления товаров"""
    try:
        all_products = await db.get_all_products()
        keyboard = InlineKeyboardBuilder()
        
        if not all_products:
            keyboard.add(InlineKeyboardButton(
                text="Нет доступных товаров",
                callback_data="no_products"
            ))
        else:
            for product in all_products:
                keyboard.add(InlineKeyboardButton(
                    text=f"{product.name} - {product.price}₽",
                    callback_data=f"deleteproduct_{product.product_id}"
                ))
                
        keyboard.add(InlineKeyboardButton(
            text="◀️ Отмена",
            callback_data="cancel_delete"
        ))
        
        return keyboard.adjust(1).as_markup()
    except Exception as e:
        logging.error(f"Ошибка при создании клавиатуры: {e}")
        return None

async def products_by_category(category_id: int):
    """Клавиатура для выбора товара из категории"""
    try:
        products = await db.get_products_by_category(category_id)
        keyboard = InlineKeyboardBuilder()
        
        if not products:
            keyboard.add(InlineKeyboardButton(
                text="В этой категории нет товаров",
                callback_data="no_products"
            ))
        else:
            for product in products:
                keyboard.add(InlineKeyboardButton(
                    text=f"{product.name} - {product.price}₽",
                    callback_data=f"product_{product.product_id}"
                ))
                
        keyboard.add(InlineKeyboardButton(
            text="◀️ Назад к категориям",
            callback_data="back_to_categories"
        ))
        
        return keyboard.adjust(1).as_markup()
    except Exception as e:
        logging.error(f"Ошибка при создании клавиатуры: {e}")
        return None

edit_product = InlineKeyboardMarkup(inline_keyboard=[
    [
        InlineKeyboardButton(text="📝 Название", callback_data="edit_field_name"),
        InlineKeyboardButton(text="📋 Описание", callback_data="edit_field_description")
    ],
    [
        InlineKeyboardButton(text="💰 Цена", callback_data="edit_field_price"),
        InlineKeyboardButton(text="🔢 Количество", callback_data="edit_field_quantity")
    ],
    [
        InlineKeyboardButton(text="📷 Фото", callback_data="edit_field_photo"),
        InlineKeyboardButton(text="📁 Категория", callback_data="edit_field_category")
    ],
    [
        InlineKeyboardButton(text="◀️ К категориям", callback_data="back_to_admin_categories"),
        InlineKeyboardButton(text="🏠 В меню", callback_data="back_to_admin_menu")
    ]
])

async def admin_products_by_category(category_id: int):
    """Клавиатура для выбора товара для редактирования (для админа)"""
    try:
        products = await db.get_products_by_category(category_id)
        keyboard = InlineKeyboardBuilder()
        
        if not products:
            keyboard.add(InlineKeyboardButton(
                text="В этой категории нет товаров",
                callback_data="no_products"
            ))
        else:
            for product in products:
                keyboard.add(InlineKeyboardButton(
                    text=f"✏️ {product.name}",
                    callback_data=f"edit_product_{product.product_id}"
                ))
                
        keyboard.add(InlineKeyboardButton(
            text="◀️ Назад к категориям",
            callback_data="back_to_categories"
        ))
        
        return keyboard.adjust(1).as_markup()
    except Exception as e:
        logging.error(f"Ошибка при создании клавиатуры: {e}")
        return None

# Клавиатура для пропуска геолокации
skip_location = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text='📍 Отправить местоположение', request_location=True)],
    [KeyboardButton(text='⏩ Пропустить')],
    [KeyboardButton(text='❌ Отмена регистрации')]
], resize_keyboard=True)

async def admin_categories_kb():
    """Клавиатура для выбора категории (админская версия)"""
    try:
        all_categories = await db.get_categories()
        categories_list = [cat for cat in all_categories]
        
        keyboard = InlineKeyboardBuilder()
        
        if not categories_list:
            keyboard.add(InlineKeyboardButton(
                text="Нет доступных категорий",
                callback_data="no_categories"
            ))
        else:
            for category in categories_list:
                keyboard.add(InlineKeyboardButton(
                    text=category.name,
                    callback_data=f'admin_category_{category.id}'
                ))
                
        keyboard.add(InlineKeyboardButton(
            text="◀️ Назад",
            callback_data="back_to_admin_menu"
        ))
        
        return keyboard.adjust(2).as_markup()
    except Exception as e:
        logging.error(f"Ошибка при создании админской клавиатуры категорий: {e}")
        return None

async def admin_products_by_category_kb(category_id: int):
    """Клавиатура для выбора товара из категории (админская версия)"""
    try:
        products = await db.get_products_by_category(category_id)
        keyboard = InlineKeyboardBuilder()
        
        if not products:
            keyboard.add(InlineKeyboardButton(
                text="В этой категории нет товаров",
                callback_data="no_products"
            ))
        else:
            for product in products:
                keyboard.add(InlineKeyboardButton(
                    text=f"{product.name} - {product.price}₽",
                    callback_data=f'admin_product_{product.product_id}'
                ))
                
        keyboard.add(InlineKeyboardButton(
            text="◀️ Назад к категориям",
            callback_data="back_to_admin_categories"
        ))
        
        return keyboard.adjust(1).as_markup()
    except Exception as e:
        logging.error(f"Ошибка при создании админской клавиатуры товаров: {e}")
        return None

cancel_button = KeyboardButton(text="❌ Отменить")
cancel_keyboard = ReplyKeyboardMarkup(
    keyboard=[[cancel_button]], 
    resize_keyboard=True
)

skip_photo_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="⏩ Пропустить фото")],
        [KeyboardButton(text="❌ Отменить")]
    ],
    resize_keyboard=True
)

def cart_item_keyboard(product_id: int, current_quantity: int = 1) -> InlineKeyboardMarkup:
    """Клавиатура для товара в корзине"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="➖", callback_data=f"cart_decrease_{product_id}"),
            InlineKeyboardButton(text=f"{current_quantity} шт.", callback_data=f"cart_quantity_{product_id}"),
            InlineKeyboardButton(text="➕", callback_data=f"cart_increase_{product_id}")
        ],
        [
            InlineKeyboardButton(text="🗑 Удалить", callback_data=f"remove_from_cart_{product_id}")
        ]
    ])

def cart_summary_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура для корзины"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="💳 Оформить заказ", callback_data="checkout"),
            InlineKeyboardButton(text="🗑 Очистить корзину", callback_data="clear_cart")
        ],
        [
            InlineKeyboardButton(text="🛍️ Продолжить покупки", callback_data="continue_shopping")
        ]
    ])
