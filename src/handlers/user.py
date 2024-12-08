from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from ..database.database import Database
from ..keyboards.keyboards import (main, cart_keyboard, main_command, menu_commands,
                                 send_contact, send_location, catalog_builder)
from ..states.user import Register
import logging

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
        db.add_user(
            user_id=user.id,
            username=user.username,
            first_name=user.first_name
        )
        await message.answer('Добро пожаловать', reply_markup=main)
    else:
        await message.message.delete()
        await message.message.answer('Добро пожаловать', reply_markup=main)

@router.message(F.text == "Корзина")
async def show_cart(message: Message, db: Database):
    cart_items = db.get_cart(message.from_user.id)
    if not cart_items:
        await message.answer("Ваша корзина пуста")
        return
    
    cart_text = "Ваша корзина:\n\n"
    total = 0
    for name, price, quantity in cart_items:
        subtotal = price * quantity
        total += subtotal
        cart_text += f"{name} x{quantity} = {subtotal}₽\n"
    cart_text += f"\nИтого: {total}₽"
    
    await message.answer(cart_text, reply_markup=cart_keyboard)

@router.message(Command('menu'))
async def cmd_menu(message: Message):
    await message.answer(
        text='Доступные команды:', 
        reply_markup=menu_commands
    )

@router.message(F.text == "В главное меню")
async def back_to_main_menu(message: Message):
    await message.answer('Вы вернулись в главное меню', reply_markup=main)

@router.message(F.text == 'Каталог')
async def catalog(message: Message):
    await send_with_inline_kb(message, 'Выбрать товар', await catalog_builder())

@router.callback_query(F.data.startswith('catalog_'))
async def show_catalog(callback: CallbackQuery):
    await callback.answer('вы выбрали товар')
    await callback.message.answer(f'вы выбрали {callback.data}',
                                reply_markup=ReplyKeyboardRemove())

# Регистрация
@router.message(F.text == "Регистрация")
async def start_registration(message: Message, state: FSMContext, db: Database):
    if db.is_user_registered(message.from_user.id):
        await message.answer("Вы уже зарегистриованы!")
        return
    
    await state.set_state(Register.name)
    await message.answer('Введите ваше имя')

@router.message(Register.name)
async def reg_contact(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await state.set_state(Register.contact)
    await message.answer('О��правьте контакт', reply_markup=send_contact)

@router.message(Register.contact, F.contact)
async def reg_location(message: Message, state: FSMContext):
    await state.update_data(contact=message.contact.phone_number)
    await state.set_state(Register.location)
    await message.answer('Отправьте локацию',
                        reply_markup=send_location,
                        protect_content=True)

@router.message(Register.contact)
async def reg_no_contact(message: Message):
    await message.answer('отправьте контакт через кнопку ниже')

@router.message(Register.location, F.location)
async def reg_age(message: Message, state: FSMContext):
    await state.update_data(location=[message.location.latitude,
                            message.location.longitude])
    await state.set_state(Register.age)
    await message.answer('Введите возраст', reply_markup=ReplyKeyboardRemove())

@router.message(Register.location)
async def reg_no_location(message: Message):
    await message.answer('отправьте локацию через кнопку ниже')

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

@router.message(F.text == "Авторизация")
async def authorization(message: Message, db: Database):
    if db.is_user_registered(message.from_user.id):
        await message.answer("Вы успешно авторизованы!")
    else:
        await message.answer("Вы не зарегистрированы. Пожалуйста, сначала пройдите регистрацию.", 
                           reply_markup=main)

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
            if db.register_user(
                user_id=message.from_user.id,
                name=data['name'],
                phone=data['contact'],
                location_lat=data['location'][0],
                location_lon=data['location'][1],
                age=int(data['age']),
                photo_id=data['photo']
            ):
                await message.answer('Регистрация успешно завершена!', reply_markup=main)
            else:
                await message.answer('Произошла ошибка при регистрации. Попробуйте позже.')
        except Exception as e:
            logging.error(f"Ошибк при регистрации: {e}")
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
    # Проверяем, не зарегистрирован ли уже пользователь
    if db.is_user_registered(message.from_user.id):
        await message.answer("Вы уже зарегис��рированы!")
        return
    
    # Начинаем процесс регистрации
    await state.set_state(Register.name)
    await message.answer('Введите ваше имя')

# Остальные ваши обработчики... 

@router.callback_query(F.data == 'back')
async def back_to_menu(callback: CallbackQuery):
    await callback.message.delete()
    await callback.message.answer(
        'Вы вернулись в главное меню',
        reply_markup=main
    )