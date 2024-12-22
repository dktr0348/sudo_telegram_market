from aiogram import Router, F, Bot
from aiogram.types import (Message, CallbackQuery, ReplyKeyboardRemove,
                            ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup,
                            InlineKeyboardButton)
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from ..database.database import Database
from ..keyboards import (main, cart_keyboard, main_command, menu_commands,
                                 send_contact, send_location, categories,
                                 category_products, profile_keyboard)
from ..state import Register
from ..database import requests as db
import logging
import re

router = Router()

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
        await message.answer('Добро пожаловать', reply_markup=main)
    else:
        await message.message.delete()
        await message.message.answer('Добро пожаловать', reply_markup=main)

@router.message(F.text.in_({'🛒 Корзина', 'Корзина'}))
async def show_cart(message: Message, db: Database):
    """Показывает содержимое корзины пользователя"""
    cart_items = await db.get_cart(message.from_user.id)
    if not cart_items:
        await message.answer("🛒 Ваша корзина пуста")
        return
    
    cart_text = "🛒 Ваша корзина:\n\n"
    total = 0
    for name, price, quantity in cart_items:
        subtotal = price * quantity
        total += subtotal
        cart_text += f"📦 {name} x{quantity} = {subtotal}₽\n"
    cart_text += f"\n💰 Итого: {total}₽"
    
    await message.answer(cart_text, reply_markup=cart_keyboard)

@router.message(Command('menu'))
async def cmd_menu(message: Message):
    await message.answer(
        text='Доступные команды:', 
        reply_markup=menu_commands
    )

@router.message(Command('catalog'))
async def cmd_catalog(message: Message):
    keyboard = await categories()
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
    await message.answer('🏠 Вы вернулись в главное меню', reply_markup=main)

@router.message(F.text.in_({'🛍️ Каталог', 'Каталог'}))
async def catalog(message: Message):
    """Показывает каталог товаров"""
    keyboard = await categories()
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
    keyboard = await category_products(category_id)
    if keyboard:
        await callback.message.edit_text(
            text='Выберите товар:',
            reply_markup=keyboard
        )
    else:
        await callback.answer("В этой категории пока нет товаров")

@router.callback_query(F.data.startswith('product_'))
async def show_product_details(callback: CallbackQuery):
    product_id = int(callback.data.split('_')[1])
    product = await db.get_product_by_id(product_id)
    
    if product:
        text = (
            f"📦 <b>{product.name}</b>\n\n"
            f"📝 {product.description}\n\n"
            f"💰 Цена: {product.price}₽"
        )
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(
                    text="🛒 Добавить в корзину", 
                    callback_data=f"add_to_cart_{product_id}")],
                [InlineKeyboardButton(
                    text="◀️ Назад к категориям", 
                    callback_data="back_to_categories")]
            ]
        )
        
        if product.photo_id:
            await callback.message.answer_photo(
                photo=product.photo_id,
                caption=text,
                reply_markup=keyboard,
                parse_mode="HTML"
            )
        else:
            await callback.message.edit_text(
                text=text,
                reply_markup=keyboard,
                parse_mode="HTML"
            )
    else:
        await callback.answer("Товар не найден")

@router.callback_query(F.data == "back_to_categories")
async def back_to_categories(callback: CallbackQuery):
    keyboard = await categories()
    if keyboard:
        await callback.message.edit_text(
            text='Выберите категорию:',
            reply_markup=keyboard
        )
    else:
        await callback.answer("Категории недоступны")

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
    await message.answer('Отправьте контакт', reply_markup=send_contact)

@router.message(Register.contact, F.contact)
async def reg_location(message: Message, state: FSMContext):
    await state.update_data(contact=message.contact.phone_number)
    await state.set_state(Register.location)
    await message.answer('Отправьте локацию',
                        reply_markup=send_location,
                        protect_content=True)

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
            reply_markup=main
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
        reply_markup=main
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
                await message.answer('Регистрация успешно завершена!', reply_markup=main)
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
            reply_markup=main
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
        reply_markup=main
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
                reply_markup=main
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
            f"📝 Имя: {name or 'Не указано'}\n"
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
                    reply_markup=profile_keyboard
                )
            except Exception as e:
                logging.error(f"Ошибка при отправке фото профиля: {e}")
                await message.answer(
                    profile_text,
                    parse_mode="HTML",
                    reply_markup=profile_keyboard
                )
        else:
            await message.answer(
                profile_text,
                parse_mode="HTML",
                reply_markup=profile_keyboard
            )
            
    except Exception as e:
        logging.error(f"Ошибка при отображении профиля: {e}")
        await message.answer(
            "Произошла ошибка при загрузке профиля. Попробуйте позже.",
            reply_markup=main
        )
