from aiogram import Router, F, Bot
from aiogram.types import (CallbackQuery, Message, ReplyKeyboardMarkup, 
                           ReplyKeyboardRemove, BotCommand, KeyboardButton)
from aiogram.filters import CommandStart, Command

from aiogram.fsm.context import FSMContext

import keybords as kb
import state as st
from database import Database

router = Router()

@router.callback_query(F.data == 'back')
@router.message(CommandStart())
async def cmd_start(message: Message, db: Database):
    if isinstance(message, Message):
        user = message.from_user
        db.add_user(
            user_id=user.id,
            username=user.username,
            first_name=user.first_name
        )
        await message.answer('Добро пожаловать',
                         reply_markup=kb.main)
    else:
        await message.message.delete()
        await message.message.answer('Добро пожаловать',
                               reply_markup=kb.main)

@router.message(F.text == "Поделиться контактом")
async def request_contact(message: Message):
    keyboard = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="Отправить контакт", request_contact=True)]],
        resize_keyboard=True
    )
    await message.answer("Пожалуйста, поделитесь вашим контактом", reply_markup=keyboard)

@router.message(F.contact)
async def handle_contact(message: Message):
    db = message.bot.get('db')
    contact = message.contact
    db.save_contact(
        user_id=contact.user_id,
        phone_number=contact.phone_number
    )
    await message.answer("Спасибо! Ваш контакт сохранен.", reply_markup=kb.main)

@router.message(F.text == "Поделиться локацией")
async def request_location(message: Message):
    keyboard = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="Отправить локацию", request_location=True)]],
        resize_keyboard=True
    )
    await message.answer("Пожалуйста, поделитесь вашей локацией", reply_markup=keyboard)

@router.message(F.location)
async def handle_location(message: Message):
    db = message.bot.get('db')
    location = message.location
    db.save_location(
        user_id=message.from_user.id,
        latitude=location.latitude,
        longitude=location.longitude
    )
    await message.answer("Спасибо! Ваша локация схранена.", reply_markup=kb.main)

@router.message(F.text == "Корзина")
async def show_cart(message: Message):
    db = message.bot.get('db')
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
    
    await message.answer(cart_text, reply_markup=kb.cart_keyboard)

@router.message(Command('menu'))
async def cmd_menu(message: Message):
    await message.answer(text='основные команды бота',
                         reply_markup=kb.main_command)
@router.message(F.text == "В главное меню")
async def back_to_main_menu(message: Message):
    await message.answer('Вы вернулись в главное меню', reply_markup=kb.main) 
    
@router.message(F.text == 'Каталог')
async def catalog(message: Message):
    await message.answer('Выбрать товар',
                         reply_markup=await kb.catalog_builder())
@router.callback_query(F.data.startswith('catalog_'))
async def show_catalog(callback: CallbackQuery):
    await callback.answer('вы выбрали товар')
    await callback.message.answer(f'вы выбрали {callback.data}',
                                  reply_markup=ReplyKeyboardRemove())
    
@router.message(Command('register'))
async def reg_name(message: Message, state: FSMContext):
    await state.set_state(st.Register.name)
    await message.answer('Введите ваше имя')

@router.message(st.Register.name)
async def reg_contact(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await state.set_state(st.Register.contact)
    await message.answer('Отправьте контакт',
                         reply_markup=kb.send_contact)
@router.message(st.Register.contact, F.contact)
async def reg_location(message: Message, state: FSMContext):
    await state.update_data(contact=message.contact.phone_number)
    await state.set_state(st.Register.location)
    await message.answer('отправьте локацию',
                         reply_markup=kb.send_location)

@router.message(st.Register.contact)
async def reg_no_contact(message: Message):
    await message.answer('отправьте контакт через кнопку ниже')

@router.message(st.Register.location, F.location)
async def reg_age(message: Message, state: FSMContext):
    await state.update_data(location=[message.location.latitude,
                            message.location.longitude])
    await state.set_state(st.Register.age)
    await message.answer('введите возраст')

@router.message(st.Register.location)
async def reg_no_location(message: Message):
    await message.answer('отправьте локацию через кнопку ниже')

@router.message(st.Register.age)
async def reg_photo(message: Message, state: FSMContext):
    if message.text.isdigit():
        await state.update_data(age=message.text)
        await state.set_state(st.Register.photo)
        await message.answer('Отправьте ваше фото')
    else:
         await message.answer('введите возраст целым числом')

@router.message(st.Register.photo, F.photo)
async def reg_done(message: Message, state: FSMContext):
    try:
        await state.update_data(photo=message.photo[-1].file_id)                           
        data = await state.get_data()
        
        db = message.bot.get('db')
        if db.register_user(
            user_id=message.from_user.id,
            name=data['name'],
            phone=data['contact'],
            location_lat=data['location'][0],
            location_lon=data['location'][1],
            age=int(data['age']),
            photo_id=data['photo']
        ):
            await message.answer('Регистрация успешно завершена!', reply_markup=kb.main)
        else:
            await message.answer('Произошла ошибка при регистрации. Попробуйте позже.')
    except Exception as e:
        await message.answer('Произошла ошибка при регистрации. Попробуйте позже.')
    finally:
        await state.clear()

@router.message(st.Register.photo)
async def reg_no_photo(message: Message):
    await message.answer('отправьте фото')
    
@router.message(F.text == "Регистрация")
async def start_registration(message: Message, state: FSMContext):
    db = message.bot.get('db')
    if db.is_user_registered(message.from_user.id):
        await message.answer("Вы уже зарегистрированы!")
        return
    
    await state.set_state(st.Register.name)
    await message.answer('Введите ваше имя')

@router.message(F.text == "Авторизация")
async def authorization(message: Message):
    db = message.bot.get('db')
    if db.is_user_registered(message.from_user.id):
        await message.answer("Вы успешно авторизованы!")
    else:
        await message.answer("Вы не зарегистрированы. Пожалуйста, сначала пройдите регистрацию.", 
                           reply_markup=kb.main)

    

