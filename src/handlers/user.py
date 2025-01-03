from aiogram import Router, F, Bot
from aiogram.types import (Message, CallbackQuery, ReplyKeyboardRemove,
                            ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup,
                            InlineKeyboardButton)
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from ..database.database import Database
from ..database.models import OrderStatus
import src.keyboards as kb
from ..state import Register
from ..database import requests as db
import logging
import re
from typing import Union
from aiogram.fsm.state import State, StatesGroup
from src.config import Config

router = Router()

# Добавим состояния для поиска и отзывов
class ProductStates(StatesGroup):
    waiting_for_search = State()
    waiting_for_review = State()
    waiting_for_rating = State()

async def send_with_inline_kb(message: Message, text: str, inline_kb: InlineKeyboardMarkup):
    """Отправка сообщения с inline клавиатурой и скрытием reply клавиатуры"""
    await message.answer(
        text=text,
        reply_markup=inline_kb,
        reply_markup_remove=True
    )

@router.message(CommandStart())
async def cmd_start(message: Message, db: Database):
    if isinstance(message, Message):
        user = message.from_user
        await db.add_user(
            user_id=user.id,
            username=user.username,
            first_name=user.first_name
        )
        await message.answer('Добро пожаловать', reply_markup=kb.main)
    else:
        await message.message.delete()
        await message.message.answer('Добро пожаловать', reply_markup=main)

@router.message(F.text.in_({'🛒 Корзина', 'Корзина'}))
@router.callback_query(F.data == "show_cart")
async def show_cart(event: Union[Message, CallbackQuery], db: Database):
    """Показ корзины"""
    try:
        user_id = event.from_user.id
        cart_items = await db.get_cart(user_id)
        
        if not cart_items:
            text = "🛒 Ваша корзина пуста"
            if isinstance(event, CallbackQuery):
                await event.message.edit_text(text, reply_markup=kb.main)
            else:
                await event.answer(text, reply_markup=kb.main)
            return
        
        total = 0
        # Показываем каждый товар отдельным сообщением с кнопками управления
        for product, quantity in cart_items:
            item_total = product.price * quantity
            total += item_total
            
            text = (
                f"📦 {product.name}\n"
                f"💰 {product.price}₽ x {quantity} шт. = {item_total}₽"
            )
            
            if isinstance(event, CallbackQuery):
                message = event.message
            else:
                message = event
                
            if product.photo_id:
                await message.answer_photo(
                    photo=product.photo_id,
                    caption=text,
                    reply_markup=kb.cart_item_keyboard(product.product_id, quantity)
                )
            else:
                await message.answer(
                    text,
                    reply_markup=kb.cart_item_keyboard(product.product_id, quantity)
                )
        
        # В конце показываем итоговую сумму и общие кнопки корзины
        await message.answer(
            f"💰 Итого: {total}₽",
            reply_markup=kb.cart_summary_keyboard()
        )
            
    except Exception as e:
        logging.error(f"Ошибка при отображении корзины: {e}")
        error_text = "Произошла ошибка при загрузке корзины"
        if isinstance(event, CallbackQuery):
            await event.message.edit_text(error_text, reply_markup=kb.main)
        else:
            await event.answer(error_text, reply_markup=kb.main)

@router.message(Command('menu'))
async def cmd_menu(message: Message):
    """Показ главного меню вместо списка команд"""
    await message.answer(
        text='🏠 Главное меню',
        reply_markup=kb.main  # Используем основную reply-клавиатуру вместо menu_commands
    )

@router.message(Command('catalog'))
async def cmd_catalog(message: Message):
    keyboard = await kb.categories()
    if keyboard:
        await message.answer(
            text='Выберите категорию:',
            reply_markup=keyboard
        )
    else:
        await message.answer("К сожалению, категории сейчас недоступны")

@router.message(F.text.in_({'🏠 В главное меню', 'В главное меню'}))
async def back_to_main_menu(message: Message):
    """Возврат в главное меню"""
    await message.answer('🏠 Вы вернулись в главное меню', reply_markup=kb.main)

@router.message(F.text.in_({'🛍️ Каталог', 'Каталог'}))
async def catalog(message: Message):
    """Показывает каталог товаров"""
    keyboard = await kb.categories()
    if keyboard:
        await message.answer(
            text='📋 Выберите категорию:',
            reply_markup=keyboard
        )
    else:
        await message.answer("❌ К сожалению, категории сейчас недоступны")

@router.callback_query(F.data.startswith('category_'))
async def show_category_products(callback: CallbackQuery):
    category_id = int(callback.data.split('_')[1])
    keyboard = await kb.category_products(category_id)
    if keyboard:
        await callback.message.edit_text(
            text='Выберите товар:',
            reply_markup=keyboard
        )
    else:
        await callback.answer("В этой категории пока нет товаров")

@router.callback_query(F.data.startswith('product_'))
async def show_product_details(callback: CallbackQuery, db: Database):
    """Показ деталей товара"""
    try:
        product_id = int(callback.data.split("_")[1])
        product = await db.get_product_by_id(product_id)
        
        if product:
            is_favorite = await db.is_favorite(callback.from_user.id, product_id)
            cart_quantity = await db.get_cart_item_quantity(callback.from_user.id, product_id)
            
            rating = product.average_rating if product.reviews else 0
            rating_stars = "⭐" * round(rating)
            
            text = (
                f"📦 {product.name}\n"
                f"💰 Цена: {product.price}₽\n"
                f"📝 Описание: {product.description}\n"
                f"{rating_stars} Рейтинг: {rating:.1f}\n"
                f"{'❤️ В избранном' if is_favorite else '🤍 Не в избранном'}\n"
                f"📦 В наличии: {product.quantity} шт.\n"
                f"🛒 Выбрано: {cart_quantity} шт.\n\n"
                f"💰 Итого: {product.price * cart_quantity}₽"
            )
            
            keyboard = kb.product_keyboard(product_id, is_favorite)
            
            try:
                # Пробуем отредактировать текущее сообщение
                if product.photo_id:
                    try:
                        await callback.message.edit_caption(
                            caption=text,
                            reply_markup=keyboard
                        )
                    except Exception:
                        # Если не получилось отредактировать caption, отправляем новое сообщение
                        await callback.message.delete()
                        await callback.message.answer_photo(
                            photo=product.photo_id,
                            caption=text,
                            reply_markup=keyboard
                        )
                else:
                    try:
                        await callback.message.edit_text(
                            text,
                            reply_markup=keyboard
                        )
                    except Exception:
                        # Если не получилось отредактировать текст, отправляем новое сообщение
                        await callback.message.delete()
                        await callback.message.answer(
                            text,
                            reply_markup=keyboard
                        )
            except Exception as e:
                logging.error(f"Ошибка при обновлении сообщения: {e}")
                # Если все попытки редактирования не удались, отправляем новое сообщение
                await callback.message.delete()
                if product.photo_id:
                    await callback.message.answer_photo(
                        photo=product.photo_id,
                        caption=text,
                        reply_markup=keyboard
                    )
                else:
                    await callback.message.answer(
                        text,
                        reply_markup=keyboard
                    )
        else:
            await callback.answer("Товар не найден")
    except Exception as e:
        logging.error(f"Ошибка при показе товара: {e}")
        await callback.answer("Произошла ошибка при загрузке товара")

@router.callback_query(F.data == "back_to_categories")
async def back_to_categories(callback: CallbackQuery):
    """Возврат к категориям"""
    try:
        keyboard = await kb.categories()
        if keyboard:
            try:
                # Пробуем удалить текущее сообщение
                await callback.message.delete()
            except Exception as e:
                logging.error(f"Ошибка при удалении сообщения: {e}")
            
            # Отправляем новое сообщение с категориями
            await callback.message.answer(
                text='📋 Выберите категорию:',
                reply_markup=keyboard
            )
        else:
            await callback.answer("❌ К сожалению, категории сейчас недоступны")
    except Exception as e:
        logging.error(f"Ошибка при возврате к категориям: {e}")
        await callback.answer("Произошла ошибка")

# Регистрация
@router.message(F.text.in_({'👤 Регистрация', 'Регистрация'}))
async def start_registration(message: Message, state: FSMContext, db: Database):
    """Начало процесса регистрации"""
    if await db.is_user_registered(message.from_user.id):
        await message.answer("✅ Вы уже зарегистрированы!")
        return
    
    await state.set_state(Register.name)
    await message.answer('👤 Введите ваше имя')

@router.message(Register.name)
async def reg_contact(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await state.set_state(Register.contact)
    await message.answer('Отправьте контакт', reply_markup=kb.send_contact)

@router.message(Register.contact, F.contact)
async def reg_location(message: Message, state: FSMContext):
    await state.update_data(contact=message.contact.phone_number)
    await state.set_state(Register.location)
    await message.answer('Отправьте локацию или пропустите этот шаг',
                        reply_markup=kb.skip_location)

@router.message(Register.location, F.text == "⏩ Пропустить")
async def skip_location(message: Message, state: FSMContext):
    """Пропуск отправки геолокации"""
    await state.update_data(location=[None, None])
    await state.set_state(Register.email)
    await message.answer('Введите e-mail', reply_markup=ReplyKeyboardRemove())

@router.message(Register.location, F.location)
async def reg_email(message: Message, state: FSMContext):
    await state.update_data(location=[message.location.latitude,
                            message.location.longitude])
    await state.set_state(Register.email)
    await message.answer('Введите e-mail', reply_markup=ReplyKeyboardRemove())

@router.message(Register.email)
async def reg_age(message: Message, state: FSMContext):
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if re.match(email_pattern, message.text):
        await state.update_data(email=message.text)
        await state.set_state(Register.age)
        await message.answer('Введите возраст', reply_markup=ReplyKeyboardRemove())
    else:
        await message.answer('Пожалуйста, введите корректный e-mail адрес.')

@router.message(Register.age)
async def reg_photo(message: Message, state: FSMContext):
    if message.text.isdigit():
        await state.update_data(age=message.text)
        await state.set_state(Register.photo)
        await message.answer('Отправьте ваше фото', reply_markup=ReplyKeyboardRemove())
    else:
        await message.answer('Введите возраст целым числом')

@router.message(Register.photo, F.photo)
async def confirm_registration(message: Message, state: FSMContext):
    await state.update_data(photo=message.photo[-1].file_id)
    data = await state.get_data()
    
    confirm_text = (
        "Пожалуйста, проверьте введенные данные:\n"
        f"Имя: {data['name']}\n"
        f"Телефон: {data['contact']}\n"
        f"Email: {data['email']}\n"
        f"Возраст: {data['age']}\n"
        "Локация и фото получены\n\n"
        "Все верно?"
    )
    
    confirm_kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Подтвердить")],
            [KeyboardButton(text="Отменить")]
        ],
        resize_keyboard=True
    )
    
    await state.set_state(Register.confirm)
    await message.answer(confirm_text, reply_markup=confirm_kb)

@router.message(Register.photo)
async def reg_no_photo(message: Message):
    await message.answer('отправьте фото')

@router.message(F.text.in_({'🔑 Авторизация', 'Авторизация'}))
async def authorization(message: Message, db: Database):
    """Авторизация пользователя"""
    if await db.is_user_registered(message.from_user.id):
        await message.answer("✅ Вы успешно авторизованы!")
    else:
        await message.answer(
            "❌ Вы не зарегистрированы. Пожалуйста, сначала пройдите регистрацию.", 
            reply_markup=kb.main
        )

@router.message(Command("cancel"))
@router.message(F.text.lower() == "отмена")
async def cancel_registration(message: Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state is None:
        return
    
    await state.clear()
    await message.answer(
        "Регистрация отменена. Вы можете начать заново.",
        reply_markup=kb.main
    )

@router.message(Register.confirm)
async def process_confirm(message: Message, state: FSMContext, db: Database):
    if message.text == "Подтвердить":
        data = await state.get_data()
        try:
            if await db.register_user(
                user_id=message.from_user.id,
                name=data['name'],
                phone=data['contact'],
                email=data['email'],
                location_lat=data['location'][0],
                location_lon=data['location'][1],
                age=int(data['age']),
                photo_id=data['photo']
            ):
                await message.answer('Регистрация успешно завершена!', reply_markup=kb.main)
            else:
                await message.answer('Произошла ошибка при регистрации. Попробуйте позже.')
        except Exception as e:
            logging.error(f"Ошибка при регистрации: {e}")
            await message.answer('Произошла ошибка при регистрации. Попробуйте позже.')
        finally:
            await state.clear()
    elif message.text == "Отменить":
        await state.clear()
        await message.answer(
            "Регистрация отменена. Вы можете начать заново.",
            reply_markup=kb.main
        )
    else:
        await message.answer("Пожалуйста, используйте кнопки для подтверждения или отмены")

@router.message(Command("register"))
async def cmd_register(message: Message, state: FSMContext, db: Database):
    """Обработчик команды /register"""
    if await db.is_user_registered(message.from_user.id):
        await message.answer("Вы уже зарегистрированы!")
        return
    
    # Начинаем процесс регистрации
    await state.set_state(Register.name)
    await message.answer('Введите ваше имя')

@router.callback_query(F.data == 'back')
async def back_to_menu(callback: CallbackQuery):
    await callback.message.delete()
    await callback.message.answer(
        'Вы вернулись в главное меню',
        reply_markup=kb.main
    )

@router.message(Command("profile"))
async def cmd_profile(message: Message, db: Database):
    """Показ профиля пользователя"""
    logging.info(f"Получен запрос на профиль от пользователя {message.from_user.id}")
    try:
        user_data = await db.get_user_profile(message.from_user.id)
        logging.info(f"Получены данные профиля: {user_data}")
        
        if not user_data:
            await message.answer(
                "Вы не зарегистрированы. Используйте /register для регистрации.",
                reply_markup=kb.main
            )
            return

        # Распаковываем данные из БД
        (user_id, name, phone, email, lat, lon, 
         age, photo_id, reg_date, username) = user_data
        
        # Форматируем дату регистрации
        reg_date_formatted = reg_date.split('.')[0] if reg_date else 'Не указана'
        
        # Формируем текст профиля
        profile_text = (
            f"👤 <b>Ваш профиль</b>\n\n"
            f"Имя: {name or 'Не указано'}\n"
            f"📱 Телефон: {phone or 'Не указан'}\n"
            f"📧 Email: {email or 'Не указан'}\n"
            f"🎂 Возраст: {age or 'Не указан'}\n"
            f"📍 Локация: {'Указана' if lat and lon else 'Не указана'}\n"
            f"📅 Дата регистрации: {reg_date_formatted}\n"
            f"🆔 Username: @{username or 'Не указан'}"
        )
        
        # Отправляем фото профиля с информацией, если оно есть
        if photo_id:
            try:
                await message.answer_photo(
                    photo=photo_id,
                    caption=profile_text,
                    parse_mode="HTML",
                    reply_markup=kb.profile_keyboard
                )
            except Exception as e:
                logging.error(f"Ошибка при отправке фото профиля: {e}")
                await message.answer(
                    profile_text,
                    parse_mode="HTML",
                    reply_markup=kb.profile_keyboard
                )
        else:
            await message.answer(
                profile_text,
                parse_mode="HTML",
                reply_markup=kb.profile_keyboard
            )
            
    except Exception as e:
        logging.error(f"Ошибка при отбражении профиля: {e}")
        await message.answer(
            "Произошла ошибка при загрузке профиля. Попробуйте позже.",
            reply_markup=kb.main
        )

@router.callback_query(F.data.startswith('cart_add_'))
async def add_to_cart(callback: CallbackQuery, db: Database):
    """Добавление товара в корзину"""
    try:
        product_id = int(callback.data.split('_')[2])
        product = await db.get_product_by_id(product_id)
        
        if not product:
            await callback.answer("❌ Товар не найден")
            return
            
        if product.quantity <= 0:
            await callback.answer("❌ Товар закончился")
            return
        
        current_qty = int(callback.message.reply_markup.inline_keyboard[0][1].text)
            
        if current_qty > product.quantity:
            await callback.answer("❌ Недостаточно товара на складе")
            return
        
        if await db.add_to_cart(callback.from_user.id, product_id, current_qty):
            await callback.answer("✅ Товар добавлен в корзину")
            # Обновляем отображение товара с актуальным количеством
            is_favorite = await db.is_favorite(callback.from_user.id, product_id)
            cart_quantity = await db.get_cart_item_quantity(callback.from_user.id, product_id)
            
            text = (
                f"📦 {product.name}\n"
                f"💰 Цена: {product.price}₽\n"
                f"📝 Описание: {product.description}\n"
                f"⭐ Рейтинг: {product.average_rating:.1f}\n"
                f"{'❤️ В избранном' if is_favorite else '🤍 Не в избранном'}\n"
                f"📦 В наличии: {product.quantity} шт.\n"
                f"🛒 В корзине: {cart_quantity} шт."
            )
            
            keyboard = kb.product_keyboard(product_id, is_favorite)
            
            if product.photo_id:
                await callback.message.edit_caption(caption=text, reply_markup=keyboard)
            else:
                await callback.message.edit_text(text, reply_markup=keyboard)
        else:
            await callback.answer("❌ Ошибка при добавлении в корзину")
    except Exception as e:
        logging.error(f"Ошибка при добавлении в корзину: {e}")
        await callback.answer("Произошла ошибка")

@router.callback_query(F.data.startswith('qty_minus_'))
async def decrease_quantity(callback: CallbackQuery, db: Database):
    """Уменьшение количества товара"""
    try:
        product_id = int(callback.data.split('_')[2])
        current_qty = int(callback.message.reply_markup.inline_keyboard[0][1].text)
        
        if current_qty > 1:
            new_qty = current_qty - 1
            if await db.add_to_cart(callback.from_user.id, product_id, new_qty):
                await update_product_view(callback, db, product_id, new_qty)
            else:
                await callback.answer("❌ Ошибка при обновлении количества")
        else:
            await callback.answer("❌ Минимальное количество: 1")
    except Exception as e:
        logging.error(f"Ошибка при уменьшении количества: {e}")
        await callback.answer("Произошла ошибка")

@router.callback_query(F.data.startswith('qty_plus_'))
async def increase_quantity(callback: CallbackQuery, db: Database):
    """Увеличение количества товара"""
    try:
        product_id = int(callback.data.split('_')[2])
        current_qty = int(callback.message.reply_markup.inline_keyboard[0][1].text)
        new_qty = current_qty + 1
        
        if await db.add_to_cart(callback.from_user.id, product_id, new_qty):
            await update_product_view(callback, db, product_id, new_qty)
        else:
            await callback.answer("❌ Ошибка при обновлении количества")
    except Exception as e:
        logging.error(f"Ошибка при увеличении количества: {e}")
        await callback.answer("Произошла ошибка")

async def update_product_view(callback: CallbackQuery, db: Database, product_id: int, quantity: int):
    """Обновление отображения товара с новым количеством"""
    product = await db.get_product_by_id(product_id)
    is_favorite = await db.is_favorite(callback.from_user.id, product_id)
    
    text = (
        f"📦 {product.name}\n"
        f"💰 Цена: {product.price}₽\n"
        f"📝 Описание: {product.description}\n"
        f"⭐ Рейтинг: {product.average_rating:.1f}\n"
        f"{'❤️ В избранном' if is_favorite else '🤍 Не в избранном'}\n"
        f"🛒 В корзине: {quantity} шт.\n\n"
        f"💰 Итого: {product.price * quantity}₽"
    )
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="➖", callback_data=f"qty_minus_{product_id}"),
            InlineKeyboardButton(text=str(quantity), callback_data="current_qty"),
            InlineKeyboardButton(text="➕", callback_data=f"qty_plus_{product_id}")
        ],
        [
            InlineKeyboardButton(
                text="❤️" if is_favorite else "🤍",
                callback_data=f"toggle_favorite_{product_id}"
            ),
            InlineKeyboardButton(
                text="🛒 В корзину",
                callback_data=f"cart_add_{product_id}"
            )
        ],
        [
            InlineKeyboardButton(
                text="📝 Отзывы",
                callback_data=f"show_reviews_{product_id}"
            ),
            InlineKeyboardButton(
                text="✍️ Написать отзыв",
                callback_data=f"review_{product_id}"
            )
        ],
        [
            InlineKeyboardButton(
                text="◀️ Назад к категориям",
                callback_data="back_to_categories"
            )
        ]
    ])
    
    if product.photo_id:
        await callback.message.edit_caption(
            caption=text,
            reply_markup=keyboard
        )
    else:
        await callback.message.edit_text(
            text,
            reply_markup=keyboard
        )

@router.callback_query(F.data.startswith('confirm_cart_'))
async def confirm_add_to_cart(callback: CallbackQuery, db: Database):
    """Подтверждение добавления в корзину"""
    product_id = int(callback.data.split('_')[2])
    quantity = int(callback.message.reply_markup.inline_keyboard[0][1].text)
    user_id = callback.from_user.id
    
    if await db.add_to_cart(user_id, product_id, quantity):
        await callback.message.edit_text(
            f"✅ Товар добавлен в корзину (количество: {quantity})"
        )
    else:
        await callback.message.edit_text("❌ Ошибка при добавлении товара в корзину")

@router.message(F.text == '🗑️ Очистить корзину')
async def clear_cart(message: Message, db: Database):
    """Очистка корзины"""
    if await db.clear_cart(message.from_user.id):
        await message.answer("🗑️ Корзина очищена", reply_markup=kb.main)
    else:
        await message.answer("❌ Ошибка при очистке корзины")

@router.message(F.text == '💳 Оформить заказ')
async def checkout(message: Message, db: Database):
    """Оформление заказа"""
    cart_items = await db.get_cart(message.from_user.id)
    if not cart_items:
        await message.answer("❌ Ваша корзина пуста")
        return
    
    total = sum(price * quantity for _, price, quantity in cart_items)
    order_text = "📋 Ваш заказ:\n\n"
    for name, price, quantity in cart_items:
        order_text += f"📦 {name} x{quantity} = {price * quantity}₽\n"
    order_text += f"\n💰 Итого к оплате: {total}₽"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💳 Оплатить", callback_data="pay_order")],
        [InlineKeyboardButton(text="❌ Отменить", callback_data="cancel_order")]
    ])
    
    await message.answer(order_text, reply_markup=keyboard)

@router.callback_query(F.data.startswith("increase_"))
async def increase_product_quantity(callback: CallbackQuery, db: Database):
    """Увеличение количества товара перед добавлением в корзину"""
    product_id = int(callback.data.split("_")[1])
    product = await db.get_product_by_id(product_id)
    current_quantity = int(callback.message.reply_markup.inline_keyboard[0][1].text.split()[0])
    
    if product and current_quantity < product.quantity:
        new_quantity = current_quantity + 1
        await callback.message.edit_reply_markup(
            reply_markup=kb.product_actions(product_id, new_quantity)
        )
    await callback.answer()

@router.callback_query(F.data.startswith("decrease_"))
async def decrease_product_quantity(callback: CallbackQuery):
    """Уменьшение количества товара перед добавлением в корзину"""
    product_id = int(callback.data.split("_")[1])
    current_quantity = int(callback.message.reply_markup.inline_keyboard[0][1].text.split()[0])
    
    if current_quantity > 1:
        new_quantity = current_quantity - 1
        await callback.message.edit_reply_markup(
            reply_markup=kb.product_actions(product_id, new_quantity)
        )
    await callback.answer()

@router.callback_query(F.data.startswith("remove_from_cart_"))
async def remove_from_cart(callback: CallbackQuery, db: Database):
    """Удаление товара из корзины"""
    try:
        product_id = int(callback.data.split("_")[-1])
        
        if await db.remove_from_cart(callback.from_user.id, product_id):
            # Удаляем сообщение с товаром
            await callback.message.delete()
            
            # Проверяем остались ли товары в корзине
            cart_items = await db.get_cart(callback.from_user.id)
            if cart_items:
                # Показываем обновленную сумму
                total = sum(product.price * quantity for product, quantity in cart_items)
                await callback.message.answer(
                    f"💰 Итого: {total}₽",
                    reply_markup=kb.cart_summary_keyboard()
                )
            else:
                await callback.message.answer(
                    "🛒 Ваша корзина пуста",
                    reply_markup=kb.main
                )
            await callback.answer("✅ Товар удален из корзины")
        else:
            await callback.answer("❌ Ошибка при удалении товара")
    except Exception as e:
        logging.error(f"Ошибка при удалении товара из корзины: {e}")
        await callback.answer("❌ Произошла ошибка")

@router.callback_query(F.data == "clear_cart")
async def clear_cart(callback: CallbackQuery, db: Database):
    """Очистка корзины"""
    try:
        if await db.clear_cart(callback.from_user.id):
            await callback.message.edit_text(
                "🛒 Корзина очищена",
                reply_markup=kb.main_inline
            )
            await callback.answer("✅ Корзина очищена")
        else:
            await callback.answer("❌ Ошибка при очистке корзины")
    except Exception as e:
        logging.error(f"Ошибка при очистке корзины: {e}")
        await callback.answer("Произошла ошибка")

@router.callback_query(F.data.startswith("cart_increase_"))
async def cart_increase_quantity(callback: CallbackQuery, db: Database):
    """Увеличение количества товара в корзине"""
    try:
        product_id = int(callback.data.split("_")[2])
        current_quantity = await db.get_cart_item_quantity(callback.from_user.id, product_id)
        product = await db.get_product_by_id(product_id)
        
        if product and current_quantity < product.quantity:
            new_quantity = current_quantity + 1
            if await db.add_to_cart(callback.from_user.id, product_id, new_quantity):
                # Обновляем текст сообщения с новой суммой
                item_total = product.price * new_quantity
                text = (
                    f"📦 {product.name}\n"
                    f"💰 {product.price}₽ x {new_quantity} шт. = {item_total}₽"
                )
                
                if product.photo_id:
                    await callback.message.edit_caption(
                        caption=text,
                        reply_markup=kb.cart_item_keyboard(product_id, new_quantity)
                    )
                else:
                    await callback.message.edit_text(
                        text=text,
                        reply_markup=kb.cart_item_keyboard(product_id, new_quantity)
                    )
                
                # Обновляем итоговую сумму корзины
                cart_items = await db.get_cart(callback.from_user.id)
                total = sum(p.price * q for p, q in cart_items)
                await callback.message.answer(f"💰 Итого: {total}₽", reply_markup=kb.cart_summary_keyboard())
                
                await callback.answer("✅ Количество обновлено")
            else:
                await callback.answer("❌ Ошибка при обновлении количества")
        else:
            await callback.answer("❌ Достигнуто максимальное количество")
    except Exception as e:
        logging.error(f"Ошибка при увеличении количества: {e}")
        await callback.answer("❌ Произошла ошибка")

@router.callback_query(F.data.startswith("cart_decrease_"))
async def cart_decrease_quantity(callback: CallbackQuery, db: Database):
    """Уменьшение количества товара в корзине"""
    try:
        product_id = int(callback.data.split("_")[2])
        current_quantity = await db.get_cart_item_quantity(callback.from_user.id, product_id)
        product = await db.get_product_by_id(product_id)
        
        if current_quantity > 1:
            new_quantity = current_quantity - 1
            if await db.add_to_cart(callback.from_user.id, product_id, new_quantity):
                # Обновляем текст сообщения с новой суммой
                item_total = product.price * new_quantity
                text = (
                    f"📦 {product.name}\n"
                    f"💰 {product.price}₽ x {new_quantity} шт. = {item_total}₽"
                )
                
                if product.photo_id:
                    await callback.message.edit_caption(
                        caption=text,
                        reply_markup=kb.cart_item_keyboard(product_id, new_quantity)
                    )
                else:
                    await callback.message.edit_text(
                        text=text,
                        reply_markup=kb.cart_item_keyboard(product_id, new_quantity)
                    )
                
                # Обновляем итоговую сумму корзины
                cart_items = await db.get_cart(callback.from_user.id)
                total = sum(p.price * q for p, q in cart_items)
                await callback.message.answer(f"💰 Итого: {total}₽", reply_markup=kb.cart_summary_keyboard())
                
                await callback.answer("✅ Количество обновлено")
            else:
                await callback.answer("❌ Ошибка при обновлении количества")
        else:
            await callback.answer("❌ Минимальное количество: 1")
    except Exception as e:
        logging.error(f"Ошибка при уменьшении количества: {e}")
        await callback.answer("❌ Произошла ошибка")

@router.message(F.text == "🛒 Корзина")
async def show_cart(message: Message, db: Database):
    """Показ корзины"""
    try:
        cart_items = await db.get_cart(message.from_user.id)
        if not cart_items:
            await message.answer(
                "🛒 Ваша корзина пуста",
                reply_markup=kb.main
            )
            return

        total = 0
        # Показываем каждый товар отдельным сообщением с кнопками управления
        for product, quantity in cart_items:
            item_total = product.price * quantity
            total += item_total
            
            text = (
                f"📦 {product.name}\n"
                f"💰 {product.price}₽ x {quantity} шт. = {item_total}₽"
            )
            
            if product.photo_id:
                await message.answer_photo(
                    photo=product.photo_id,
                    caption=text,
                    reply_markup=kb.cart_item_keyboard(product.product_id, quantity)
                )
            else:
                await message.answer(
                    text,
                    reply_markup=kb.cart_item_keyboard(product.product_id, quantity)
                )
        
        # В конце показываем итоговую сумму и общие кнопки корзины
        await message.answer(
            f"💰 Итого: {total}₽",
            reply_markup=kb.cart_summary_keyboard()
        )
    except Exception as e:
        logging.error(f"Ошибка при отображении корзины: {e}")
        await message.answer(
            "Произошла ошибка при загрузке корзины",
            reply_markup=kb.main
        )

async def update_cart_total(message: Message, user_id: int, db: Database):
    """Обновление общей суммы корзины"""
    try:
        cart_items = await db.get_cart(user_id)
        if cart_items:
            total = sum(product.price * quantity for product, quantity in cart_items)
            # Отправляем новое сообщение с обновленной суммой
            await message.answer(
                f"💰 Итого: {total}₽",
                reply_markup=kb.cart_summary_keyboard()
            )
        else:
            # Если корзина пуста
            await message.answer(
                "🛒 Ваша корзина пуста",
                reply_markup=kb.main
            )
    except Exception as e:
        logging.error(f"Ошибка при обновлении суммы корзины: {e}")

@router.callback_query(F.data == "show_orders")
async def show_orders_callback(callback: CallbackQuery):
    """Показ истории заказов"""
    try:
        orders = await db.get_user_orders(callback.from_user.id)
        if not orders:
            await callback.message.answer(
                "У вас пока нет заказов",
                reply_markup=kb.main
            )
            await callback.message.delete()
            return

        text = "📋 Ваши заказы:\n\n"
        keyboard = InlineKeyboardMarkup(inline_keyboard=[])
        
        for order in orders:
            status_emoji = kb.get_order_status_emoji(order.status)
            text += (
                f"🆔 Заказ #{order.order_id}\n"
                f"Статус: {status_emoji} {order.status}\n"
                f"💰 Сумма: {order.total_amount}₽\n"
                f"📅 Дата: {order.created_at.strftime('%d.%m.%Y %H:%M')}\n"
                "-------------------\n"
            )
            # Добавляем кнопку для каждого заказа
            keyboard.inline_keyboard.append([
                InlineKeyboardButton(
                    text=f"📦 Заказ №{order.order_id}",
                    callback_data=f"order_details_{order.order_id}"
                )
            ])
        
        # Добавляем кнопку возврата
        keyboard.inline_keyboard.append([
            InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_profile")
        ])

        await callback.message.answer(text, reply_markup=keyboard)
        await callback.message.delete()
    except Exception as e:
        logging.error(f"Ошибка при показе заказов: {e}")
        await callback.answer("Произошла ошибка при загрузке заказов")

@router.message(F.text == "📋 Мои заказы")
async def show_orders_command(message: Message):
    """Показать заказы пользователя через команду"""
    try:
        orders = await db.get_user_orders(message.from_user.id)
        if not orders:
            await message.answer(
                "У вас пока нет заказов",
                reply_markup=kb.main
            )
            return

        # Форматируем каждый заказ
        orders_text = []
        for order in orders:
            status_emoji = kb.get_order_status_emoji(order.status)
            order_text = (
                f"🆔 Заказ #{order.order_id}\n"
                f"💰 Сумма: {order.total_amount}₽\n"
                f"📅 Дата: {order.created_at.strftime('%d.%m.%Y %H:%M')}\n"
                f"Статус: {status_emoji} {order.status}"
            )
            orders_text.append(order_text)

        await message.answer(
            f"📋 Ваши заказы:\n\n" + "\n\n".join(orders_text),
            reply_markup=kb.main
        )
    except Exception as e:
        logging.error(f"Ошибка при показе заказов: {e}")
        await message.answer(
            "Произошла ошибка при получении заказов",
            reply_markup=kb.main
        )

@router.message(F.text == "🔍 Поиск")
async def start_search(message: Message, state: FSMContext):
    """Начало поиска товаров"""
    await state.set_state(ProductStates.waiting_for_search)
    await message.answer(
        "Введите название или описание товара для поиска:",
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="❌ Отменить поиск")]],
            resize_keyboard=True
        )
    )

@router.message(ProductStates.waiting_for_search)
async def process_search(message: Message, state: FSMContext, db: Database):
    """Обработка поискового запроса"""
    if message.text == "❌ Отменить поиск":
        await state.clear()
        await message.answer("Поиск отменен", reply_markup=kb.main)
        return

    products = await db.search_products(message.text)
    if not products:
        await message.answer(
            "По вашему запросу ничего не найдено",
            reply_markup=kb.main
        )
        await state.clear()
        return

    text = "🔍 Результаты поиска:\n\n"
    keyboard = InlineKeyboardMarkup(inline_keyboard=[])
    
    for product in products:
        keyboard.inline_keyboard.append([
            InlineKeyboardButton(
                text=f"{product.name} - {product.price}₽",
                callback_data=f"product_{product.product_id}"
            )
        ])
    
    keyboard.inline_keyboard.append([
        InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_catalog")
    ])
    
    await message.answer(text, reply_markup=keyboard)
    await state.clear()

@router.callback_query(F.data == "filter_products")
async def show_filters(callback: CallbackQuery):
    """Показ фильтров для товаров"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="💰 По цене ⬆️", callback_data="sort_price_asc"),
            InlineKeyboardButton(text="💰 По цене ⬇️", callback_data="sort_price_desc")
        ],
        [
            InlineKeyboardButton(text="⭐ По рейтингу", callback_data="sort_rating"),
            InlineKeyboardButton(text="🔤 По названию", callback_data="sort_name")
        ],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_catalog")]
    ])
    
    await callback.message.edit_text(
        "Выберите способ сортировки:",
        reply_markup=keyboard
    )

@router.callback_query(F.data == "show_favorites")
async def show_favorites(callback: CallbackQuery, db: Database):
    """Показ избранных товаров"""
    try:
        favorites = await db.get_user_favorites(callback.from_user.id)
        
        # Сначала отправляем новое сообщение
        text = "❤️ Избранные товары:\n\n" if favorites else "У вас пока нет избранных товаров"
        keyboard = InlineKeyboardMarkup(inline_keyboard=[])
        
        if favorites:
            for favorite in favorites:
                product = favorite.product
                rating = product.average_rating if product.reviews else 0
                rating_stars = "⭐" * round(rating)
                text += f"📦 {product.name} - {product.price}₽ {rating_stars}\n"
                keyboard.inline_keyboard.append([
                    InlineKeyboardButton(
                        text=f"Просмотреть {product.name}",
                        callback_data=f"product_{product.product_id}"
                    )
                ])
        
        keyboard.inline_keyboard.append([
            InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_profile")
        ])
        
        # Отправляем новое сообщение вместо редактирования
        await callback.message.answer(text, reply_markup=keyboard)
        # Удаляем предыдущее сообщение
        await callback.message.delete()
        
    except Exception as e:
        logging.error(f"Ошибка при показе избранного: {e}")
        await callback.answer("Произошла ошибка при загрузке избранного")

@router.callback_query(F.data.startswith("toggle_favorite_"))
async def toggle_favorite(callback: CallbackQuery, db: Database):
    """Добавление/удаление из избранного"""
    try:
        product_id = int(callback.data.split("_")[2])  # Получаем product_id
        result = await db.toggle_favorite(callback.from_user.id, product_id)
        
        if result:
            # Проверяем новый статус избранного
            is_favorite = await db.is_favorite(callback.from_user.id, product_id)
            await callback.answer(
                "✅ Добавлено в избранное" if is_favorite else "❌ Удалено из избранного"
            )
            
            # Получаем актуальные данные о товаре
            product = await db.get_product_by_id(product_id)
            cart_quantity = await db.get_cart_item_quantity(callback.from_user.id, product_id)
            
            # Обновляем отображение товара
            rating = product.average_rating if product.reviews else 0
            rating_stars = "⭐" * round(rating)
            
            text = (
                f"📦 {product.name}\n"
                f"💰 Цена: {product.price}₽\n"
                f"📝 Описание: {product.description}\n"
                f"{rating_stars} Рейтинг: {rating:.1f}\n"
                f"{'❤️ В избранном' if is_favorite else '🤍 Не в избранном'}\n"
                f"📦 В наличии: {product.quantity} шт.\n"
                f"🛒 Выбрано: {cart_quantity} шт.\n\n"
                f"💰 Итого: {product.price * cart_quantity}₽"
            )
            
            keyboard = kb.product_keyboard(product_id, is_favorite)
            
            if product.photo_id:
                await callback.message.edit_caption(
                    caption=text,
                    reply_markup=keyboard
                )
            else:
                await callback.message.edit_text(
                    text,
                    reply_markup=keyboard
                )
        else:
            await callback.answer("❌ Произошла ошибка")
    except Exception as e:
        logging.error(f"Ошибка при работе с избранным: {e}")
        await callback.answer("Произошла ошибка")

@router.message(F.text == "👤 Профиль")
async def show_profile_command(message: Message, db: Database):
    """Показ профиля через команду в главном меню"""
    await cmd_profile(message, db)

@router.callback_query(F.data.startswith("order_details_"))
async def show_order_details(callback: CallbackQuery, db: Database):
    """Показ деталей заказа"""
    try:
        order_id = int(callback.data.split("_")[2])
        order = await db.get_order_by_id(order_id)
        
        if order:
            # Получаем товары заказа
            items = await db.get_order_items(order_id)
            
            text = (
                f"📦 Заказ №{order.order_id}\n"
                f"📅 Дата: {order.created_at.strftime('%d.%m.%Y %H:%M')}\n"
                f"📊 Статус: {order.status.value}\n"
                f"💰 Сумма: {order.total_amount}₽\n"
                f"🚚 Способ доставки: {order.delivery_method.value}\n"
                f"📍 Адрес: {order.delivery_address}\n"
                f"💳 Способ оплаты: {order.payment_method.value}\n\n"
                "📋 Состав заказа:\n"
            )
            
            for item in items:
                text += f"• {item.product.name} x {item.quantity} шт. = {item.price * item.quantity}₽\n"
            
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="◀️ Назад к заказам", callback_data="show_orders")]
            ])
            
            await callback.message.edit_text(text, reply_markup=keyboard)
        else:
            await callback.answer("Заказ не найден")
    except Exception as e:
        logging.error(f"Ошибка при показе деталей заказа: {e}")
        await callback.answer("Произошла ошибка при загрузке деталей заказа")

@router.callback_query(F.data == "back_to_profile")
async def back_to_profile(callback: CallbackQuery, db: Database):
    """Возврат к профилю"""
    try:
        profile = await db.get_user_profile(callback.from_user.id)
        if profile:
            user_id, name, phone, email, lat, lon, age, photo_id, reg_date, username = profile
            
            text = (
                f"👤 Профиль\n\n"
                f"Имя: {name}\n"
                f"Телефон: {phone}\n"
                f"Email: {email}\n"
                f"Возраст: {age}\n"
                f"Дата регистрации: {reg_date}\n"
                f"Username: @{username}"
            )
            
            await callback.message.edit_text(text, reply_markup=kb.profile_keyboard)
        else:
            await callback.message.edit_text(
                "Профиль не найден. Пожалуйста, зарегистрируйтесь.",
                reply_markup=kb.main_inline
            )
    except Exception as e:
        logging.error(f"Ошибка при возврате к профилю: {e}")
        await callback.answer("Произошла ошибка")

@router.callback_query(F.data.startswith("review_"))
async def start_review(callback: CallbackQuery, state: FSMContext):
    """Начало создания отзыва"""
    try:
        product_id = int(callback.data.split("_")[1])
        product = await db.get_product_by_id(product_id)
        if not product:
            await callback.answer("Товар не найден")
            return

        await state.set_state(ProductStates.waiting_for_rating)
        await state.update_data(product_id=product_id)
        
        # Отправляем новое сообщение вместо редактирования
        await callback.message.answer(
            f"Оцените товар {product.name}:",
            reply_markup=kb.review_keyboard
        )
        # Удаляем предыдущее сообщение если оно с фото
        if callback.message.photo:
            await callback.message.delete()
            
    except Exception as e:
        logging.error(f"Ошибка при начале создания отзыва: {e}")
        await callback.answer("❌ Произошла ошибка")

@router.callback_query(ProductStates.waiting_for_rating, F.data.startswith("rate_"))
async def process_rating(callback: CallbackQuery, state: FSMContext):
    """Обработка выбранного рейтинга"""
    try:
        rating = int(callback.data.split("_")[1])
        await state.update_data(rating=rating)
        await state.set_state(ProductStates.waiting_for_review)
        
        await callback.message.edit_text(
            f"Вы поставили {rating} ⭐\nТеперь напишите текст отзыва:",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_review")]
            ])
        )
    except Exception as e:
        logging.error(f"Ошибка при обработке рейтинга: {e}")
        await callback.answer("❌ Произошла ошибка")

@router.message(ProductStates.waiting_for_review)
async def process_review_text(message: Message, state: FSMContext, db: Database):
    """Сохранение отзыва"""
    try:
        data = await state.get_data()
        product_id = data['product_id']
        rating = data['rating']
        
        if await db.add_review(
            user_id=message.from_user.id,
            product_id=product_id,
            rating=rating,
            text=message.text
        ):
            # Получаем товар для возврата к его просмотру
            product = await db.get_product_by_id(product_id)
            is_favorite = await db.is_favorite(message.from_user.id, product_id)
            
            text = (
                "✅ Спасибо за ваш отзыв!\n\n"
                f"📦 {product.name}\n"
                f"💰 Цена: {product.price}₽\n"
                f"📝 Описание: {product.description}\n"
                f"⭐ Рейтинг: {product.average_rating:.1f}"
            )
            
            await message.answer(
                text,
                reply_markup=kb.product_keyboard(product_id, is_favorite)
            )
        else:
            await message.answer(
                "❌ Произошла ошибка при сохранении отзыва",
                reply_markup=kb.main
            )
    except Exception as e:
        logging.error(f"Ошибка при сохранении отзыва: {e}")
        await message.answer("Произошла ошибка", reply_markup=kb.main)
    finally:
        await state.clear()

@router.callback_query(F.data == "cancel_review")
async def cancel_review(callback: CallbackQuery, state: FSMContext):
    """Отмена создания отзыва"""
    await state.clear()
    await callback.message.edit_text(
        "❌ Создание отзыва отменено",
        reply_markup=kb.main_inline
    )

@router.callback_query(F.data.startswith("show_reviews_"))
async def show_product_reviews(callback: CallbackQuery):
    """Показ всех отзывов о товаре"""
    try:
        product_id = int(callback.data.split("_")[2])
        product = await db.get_product_by_id(product_id)
        if not product:
            await callback.answer("Товар не найден")
            return

        reviews = await db.get_product_reviews(product_id)
        
        text = f"📝 Отзывы о товаре {product.name}:\n\n"
        
        if not reviews:
            text += "Пока нет отзывов о товаре"
        else:
            for review in reviews:
                rating_stars = "⭐" * review.rating
                text += (
                    f"{rating_stars}\n"
                    f"👤 {review.text}\n"
                    f"📅 {review.created_at.strftime('%d.%m.%Y %H:%M')}\n"
                    "-------------------\n"
                )

        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✍️ Написать отзыв",
                    callback_data=f"review_{product_id}"
                )
            ],
            [
                InlineKeyboardButton(
                    text="◀️ Назад к товару",
                    callback_data=f"product_{product_id}"
                )
            ]
        ])

        # Проверяем, есть ли текст в сообщении перед редактированием
        if callback.message.text:
            await callback.message.edit_text(text, reply_markup=keyboard)
        else:
            # Если текста нет, отправляем новое сообщение
            await callback.message.answer(text, reply_markup=keyboard)
            await callback.message.delete()

    except Exception as e:
        logging.error(f"Ошибка при показе отзывов: {e}")
        await callback.answer("Произошла ошибка при загрузке отзывов")

@router.callback_query(F.data.startswith("back_to_product_"))
async def back_to_product(callback: CallbackQuery):
    """Возврат к просмотру товара"""
    try:
        product_id = int(callback.data.split('_')[-1])
        product = await db.get_product_by_id(product_id)
        if not product:
            await callback.answer("Товар не найден")
            return

        # Проверяем, является ли товар избранным
        is_favorite = await db.is_favorite(callback.from_user.id, product_id)
        
        text = (
            f"📦 {product.name}\n"
            f"💰 Цена: {product.price}₽\n"
            f"📝 {product.description}\n"
            f"📦 В наличии: {product.quantity} шт."
        )

        await callback.message.answer(
            text,
            reply_markup=kb.product_keyboard(product_id, is_favorite)
        )
        await callback.message.delete()

    except Exception as e:
        logging.error(f"Ошибка при возврате к товару: {e}")
        await callback.answer("Произошла ошибка")

@router.callback_query(F.data == "back_to_catalog")
async def back_to_catalog(callback: CallbackQuery):
    """Возврат к каталогу"""
    try:
        keyboard = await kb.categories()
        if keyboard:
            await callback.message.edit_text(
                text='📋 Выберите категорию:',
                reply_markup=keyboard
            )
        else:
            await callback.answer("❌ К сожалению, категории сейчас недоступны")
    except Exception as e:
        logging.error(f"Ошибка при возврате к каталогу: {e}")
        await callback.answer("Произошла ошибка")

@router.callback_query(F.data == "back_to_categories")
async def back_to_categories(callback: CallbackQuery):
    """Возврат к категориям"""
    try:
        keyboard = await kb.categories()
        if keyboard:
            try:
                # Пробуем удалить текущее сообщение
                await callback.message.delete()
            except Exception as e:
                logging.error(f"Ошибка при удалении сообщения: {e}")
            
            # Отправляем новое сообщение с категориями
            await callback.message.answer(
                text='📋 Выберите категорию:',
                reply_markup=keyboard
            )
        else:
            await callback.answer("❌ К сожалению, категории сейчас недоступны")
    except Exception as e:
        logging.error(f"Ошибка при возврате к категориям: {e}")
        await callback.answer("Произошла ошибка")

@router.callback_query(F.data.startswith('qty_'))
async def change_quantity(callback: CallbackQuery, state: FSMContext, db: Database):
    """Изменение количества товара перед добавлением в корзину"""
    try:
        action, product_id = callback.data.split('_')[1:]
        product_id = int(product_id)
        product = await db.get_product_by_id(product_id)
        
        if not product:
            await callback.answer("❌ Товар не найден")
            return
            
        # Получаем текущее количество из кнопки
        current_qty = int(callback.message.reply_markup.inline_keyboard[0][1].text)
        
        # Изменяем количество в зависимости от действия
        if action == 'minus' and current_qty > 0:
            new_qty = current_qty - 1
        elif action == 'plus' and current_qty < product.quantity:
            new_qty = current_qty + 1
        else:
            await callback.answer("❌ Невозможно изменить количество")
            return
            
        # Обновляем отображение товара
        is_favorite = await db.is_favorite(callback.from_user.id, product_id)
        text = (
            f"📦 {product.name}\n"
            f"💰 Цена: {product.price}₽\n"
            f"📝 Описание: {product.description}\n"
            f"⭐ Рейтинг: {product.average_rating:.1f}\n"
            f"{'❤️ В избранном' if is_favorite else '🤍 Не в избранном'}\n"
            f"📦 В наличии: {product.quantity} шт.\n"
            f"🛒 Выбрано: {new_qty} шт.\n\n"
            f"💰 Итого: {product.price * new_qty}₽"
        )
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="➖", callback_data=f"qty_minus_{product_id}"),
                InlineKeyboardButton(text=str(new_qty), callback_data="current_qty"),
                InlineKeyboardButton(text="➕", callback_data=f"qty_plus_{product_id}")
            ],
            [
                InlineKeyboardButton(
                    text="❤️" if is_favorite else "🤍",
                    callback_data=f"toggle_favorite_{product_id}"
                ),
                InlineKeyboardButton(
                    text="🛒 В корзину",
                    callback_data=f"cart_add_{product_id}"
                )
            ],
            [
                InlineKeyboardButton(
                    text="📝 Отзывы",
                    callback_data=f"show_reviews_{product_id}"
                ),
                InlineKeyboardButton(
                    text="✍️ Написать отзыв",
                    callback_data=f"review_{product_id}"
                )
            ],
            [
                InlineKeyboardButton(
                    text="◀️ Назад к категориям",
                    callback_data="back_to_categories"
                )
            ]
        ])
        
        if product.photo_id:
            await callback.message.edit_caption(
                caption=text,
                reply_markup=keyboard
            )
        else:
            await callback.message.edit_text(
                text,
                reply_markup=keyboard
            )
        
        await callback.answer()
        
    except Exception as e:
        logging.error(f"Ошибка при изменении количества: {e}")
        await callback.answer("Произошла ошибка")

async def show_cart_summary(callback: CallbackQuery, db: Database):
    """Показ итоговой информации о корзине"""
    try:
        cart_items = await db.get_cart(callback.from_user.id)
        if not cart_items:
            await callback.message.answer(
                "🛒 Ваша корзина пуста",
                reply_markup=kb.main_inline
            )
            return

        total = 0
        cart_text = "🛒 Ваша корзина:\n\n"
        
        for product, quantity in cart_items:
            item_total = product.price * quantity
            total += item_total
            cart_text += (
                f"📦 {product.name}\n"
                f"   {product.price}₽ x {quantity} шт. = {item_total}₽\n\n"
            )
       
        cart_text += f"\n💰 Итого: {total}₽"
        
        # Отправляем сообщение с итогами и клавиатурой
        await callback.message.answer(
            cart_text,
            reply_markup=kb.cart_summary_keyboard()
        )
    except Exception as e:
        logging.error(f"Ошибка при показе итогов корзины: {e}")

@router.callback_query(F.data == "continue_shopping")
async def continue_shopping(callback: CallbackQuery, db: Database):
    """Возврат к категориям из корзины"""
    try:
        keyboard = await kb.categories()
        if keyboard:
            # Удаляем сообщение с корзиной
            try:
                await callback.message.delete()
            except Exception as e:
                logging.error(f"Ошибка при удалении сообщения корзины: {e}")
            
            # Отправляем новое сообщение с категориями
            await callback.message.answer(
                text='📋 Выберите категорию:',
                reply_markup=keyboard
            )
        else:
            await callback.answer("❌ К сожалению, категории сейчас недоступны")
    except Exception as e:
        logging.error(f"Ошибка при возврате к категориям: {e}")
        await callback.answer("Произошла ошибка")

@router.callback_query(F.data == "clear_cart")
async def clear_cart(callback: CallbackQuery, db: Database):
    """Очистка корзины"""
    try:
        if await db.clear_cart(callback.from_user.id):
            await callback.message.edit_text(
                "🛒 Корзина очищена",
                reply_markup=kb.main_inline
            )
            await callback.answer("✅ Корзина очищена")
        else:
            await callback.answer("❌ Ошибка при очистке корзины")
    except Exception as e:
        logging.error(f"Ошибка при очистке корзины: {e}")
        await callback.answer("Произошла ошибка")

@router.message(Command("stars"))
async def check_stars_balance(message: Message, db: Database):
    """Проверка баланса Stars"""
    try:
        total_stars, total_rub = await db.get_user_stars_total(message.from_user.id)
        
        await message.answer(
            f"💫 Ваш баланс Stars:\n\n"
            f"⭐ Всего потрачено Stars: {total_stars}\n"
            f"💰 На сумму: {total_rub}₽\n\n"
            f"📊 Текущий курс: 1 Star = {Config.STARS_RATE}₽"
        )
    except Exception as e:
        logging.error(f"Ошибка при проверке баланса Stars: {e}")
        await message.answer("❌ Не удалось получить информацию о балансе Stars")

@router.message(F.text == '💳 Оплатить')
async def process_payment_cmd(message: Message):
    """Обработка нажатия кнопки Оплатить"""
    try:
        # Проверяем есть ли товары в корзине
        cart_items = await db.get_cart(message.from_user.id)
        if not cart_items:
            await message.answer(
                "🛒 Ваша корзина пуста!\n"
                "Добавьте товары в корзину перед оплатой.",
                reply_markup=kb.main
            )
            return

        # Считаем общую сумму
        total = sum(product.price * quantity for product, quantity in cart_items)
        
        # Формируем текст с содержимым корзины
        cart_text = "🛒 Ваша корзина:\n\n"
        for product, quantity in cart_items:
            cart_text += f"📦 {product.name} x {quantity} шт. = {product.price * quantity}₽\n"
        cart_text += f"\n💰 Итого к оплате: {total}₽"

        # Показываем способы оплаты
        payment_kb = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="💳 Картой", callback_data="payment_card"),
                InlineKeyboardButton(text="⭐ Stars", callback_data="payment_stars")
            ],
            [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_payment")]
        ])

        await message.answer(
            cart_text,
            reply_markup=payment_kb
        )

    except Exception as e:
        logging.error(f"Ошибка при обработке оплаты: {e}")
        await message.answer(
            "❌ Произошла ошибка при обработке оплаты",
            reply_markup=kb.main
        )

@router.callback_query(F.data == "show_catalog")
async def show_catalog_inline(callback: CallbackQuery):
    """Показ каталога через inline кнопку"""
    try:
        keyboard = await kb.categories()
        if keyboard:
            await callback.message.edit_text(
                text='📋 Выберите категорию:',
                reply_markup=keyboard
            )
        else:
            await callback.answer("❌ К сожалению, категории сейчас недоступны")
    except Exception as e:
        logging.error(f"Ошибка при показе каталога: {e}")
        await callback.answer("Произошла ошибка")

@router.callback_query(F.data == "show_profile")
async def show_profile_inline(callback: CallbackQuery):
    """Показ профиля через inline кнопку"""
    try:
        user = await db.get_user(callback.from_user.id)
        if not user:
            await callback.answer("Профиль не найден")
            return
            
        profile_text = (
            f"👤 Профиль\n\n"
            f"ID: {user.user_id}\n"
            f"Имя: {user.first_name}\n"
            f"Username: @{user.username}\n"
        )
        
        await callback.message.edit_text(
            profile_text,
            reply_markup=kb.profile_keyboard
        )
    except Exception as e:
        logging.error(f"Ошибка при показе профиля: {e}")
        await callback.answer("Произошла ошибка")

@router.callback_query(F.data == "back_to_main")
async def back_to_main_menu_inline(callback: CallbackQuery):
    """Возврат в главное меню через inline кнопку"""
    try:
        await callback.message.edit_text(
            "🏠 Главное меню",
            reply_markup=kb.main_inline
        )
    except Exception as e:
        logging.error(f"Ошибка при возврате в меню: {e}")
        await callback.answer("Произошла ошибка")

@router.message(Command("help"))
async def show_help(message: Message):
    """Показ справки по боту"""
    help_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🛍️ Как сделать заказ", callback_data="help_order"),
            InlineKeyboardButton(text="💳 Оплата", callback_data="help_payment")
        ],
        [
            InlineKeyboardButton(text="📝 Отзывы", callback_data="help_reviews"),
            InlineKeyboardButton(text="⚙️ Настройки", callback_data="help_settings")
        ],
        [
            InlineKeyboardButton(text="👤 Профиль", callback_data="help_profile")
        ],
        [
            InlineKeyboardButton(text="💬 Чат поддержки", url="https://t.me/chanvasya")
        ]
    ])
    
    await message.answer(
        "🤖 Добро пожаловать в справочный раздел!\n"
        "Выберите интересующую вас тему или обратитесь в поддержку:",
        reply_markup=help_keyboard
    )

@router.callback_query(F.data == "help_back")
async def help_back_to_main(callback: CallbackQuery):
    """Возврат к главному меню помощи"""
    help_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🛍️ Как сделать заказ", callback_data="help_order"),
            InlineKeyboardButton(text="💳 Оплата", callback_data="help_payment")
        ],
        [
            InlineKeyboardButton(text="📝 Отзывы", callback_data="help_reviews"),
            InlineKeyboardButton(text="⚙️ Настройки", callback_data="help_settings")
        ],
        [
            InlineKeyboardButton(text="👤 Профиль", callback_data="help_profile")
        ],
        [
            InlineKeyboardButton(text="💬 Чат поддержки", url="https://t.me/chanvasya")
        ]
    ])
    
    await callback.message.edit_text(
        "🤖 Добро пожаловать в справочный раздел!\n"
        "Выберите интересующую вас тему или обратитесь в поддержку:",
        reply_markup=help_keyboard
    )

@router.callback_query(F.data.startswith("help_"))
async def process_help_section(callback: CallbackQuery):
    """Обработка выбора раздела помощи"""
    if callback.data == "help_back":
        await help_back_to_main(callback)
        return
        
    section = callback.data.split("_")[1]
    
    help_texts = {
        "order": (
            "🛍️ Как сделать заказ:\n\n"
            "1. Выберите товары в каталоге\n"
            "2. Добавьте их в корзину\n"
            "3. Перейдите в корзину\n"
            "4. Нажмите «Оформить заказ»\n"
            "5. Укажите адрес доставки\n"
            "6. Выберите способ оплаты\n\n"
            "После оформления заказа вы получите уведомление о его статусе"
        ),
        "payment": (
            "💳 Способы оплаты:\n\n"
            "• Банковской картой\n"
            "• Stars (бонусная система)\n\n"
            "При оплате Stars используется курс: 1 Star = 1,35₽"
        ),
        "reviews": (
            "📝 Система отзывов:\n\n"
            "• Оставить отзыв можно на странице товара\n"
            "• Укажите рейтинг от 1 до 5 звезд\n"
            "• Напишите текстовый отзыв\n"
            "• Ваш отзыв поможет другим покупателям"
        ),
        "settings": (
            "⚙️ Настройки:\n\n"
            "• Язык интерфейса\n"
            "• Уведомления\n"
            "Изменить настройки: /settings"
        ),
        "profile": (
            "👤 Профиль:\n\n"
            "• Просмотр и редактирование данных\n"
            "• История заказов\n"
            "• Баланс Stars\n"
            "• Управление уведомлениями"
        )
    }
    
    back_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Назад к разделам", callback_data="help_back")]
    ])
    
    try:
        if section in help_texts:
            await callback.message.edit_text(
                help_texts[section],
                reply_markup=back_kb
            )
        else:
            await callback.answer("❌ Раздел не найден")
    except Exception as e:
        logging.error(f"Ошибка при показе справки: {e}")
        await callback.answer("❌ Произошла ошибка")
