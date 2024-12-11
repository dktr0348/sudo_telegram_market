from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove, ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
import re
import logging
from ..database.database import Database
from ..keyboards.keyboards import (profile_keyboard, send_contact, 
                                 send_location, main)
from ..states.user import Register
from .user import cmd_profile

router = Router()

# Клавиатура для отмены редактирования
cancel_kb = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="Отменить редактирование")]],
    resize_keyboard=True
)

@router.callback_query(F.data.startswith('edit_'))
async def process_edit_profile(callback: CallbackQuery, state: FSMContext):
    edit_type = callback.data.split('_')[1]
    
    edit_messages = {
        'name': 'Введите новое имя:',
        'email': 'Введите новый email:',
        'phone': 'Отправьте новый номер телефона:',
        'age': 'Введите новый возраст:',
        'photo': 'Отправьте новое фото:',
        'location': 'Отправьте новую локацию:'
    }
    
    states = {
        'name': Register.name,
        'email': Register.email,
        'phone': Register.contact,
        'age': Register.age,
        'photo': Register.photo,
        'location': Register.location
    }
    
    await state.set_state(states[edit_type])
    await state.update_data(edit_mode=True, edit_type=edit_type)
    
    if edit_type == 'phone':
        kb = send_contact
    elif edit_type == 'location':
        kb = send_location
    else:
        kb = cancel_kb
    
    await callback.message.answer(
        edit_messages[edit_type],
        reply_markup=kb
    )
    await callback.answer()

# Обработчик отмены редактирования
@router.message(F.text == "Отменить редактирование")
async def cancel_edit(message: Message, state: FSMContext, db: Database):
    await state.clear()
    await message.answer("Редактирование отменено", reply_markup=main)
    await cmd_profile(message, db)

# Обработчики неправильных типов сообщений
@router.message(Register.photo)
async def wrong_photo(message: Message):
    await message.answer("Пожалуйста, отправьте фото", reply_markup=cancel_kb)

@router.message(Register.contact)
async def wrong_contact(message: Message):
    await message.answer("Пожалуйста, используйте кнопку для отправки контакта", reply_markup=send_contact)

@router.message(Register.location)
async def wrong_location(message: Message):
    await message.answer("Пожалуйста, используйте кнопку для отправки локации", reply_markup=send_location)

@router.message(Register.name)
async def process_name(message: Message, state: FSMContext, db: Database):
    data = await state.get_data()
    if not data.get('edit_mode'):
        return
        
    if message.text == "Отменить редактирование":
        await cancel_edit(message, state, db)
        return
        
    if await db.update_user_field(message.from_user.id, 'name', message.text):
        await message.answer('Имя успешно обновлено!', reply_markup=main)
        await cmd_profile(message, db)
    else:
        await message.answer('Произошла ошибка при обновлении.', reply_markup=main)
    await state.clear()

@router.message(Register.email)
async def process_email(message: Message, state: FSMContext, db: Database):
    data = await state.get_data()
    if not data.get('edit_mode'):
        return
        
    if message.text == "Отменить редактирование":
        await cancel_edit(message, state, db)
        return

    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if re.match(email_pattern, message.text):
        if await db.update_user_field(message.from_user.id, 'email', message.text):
            await message.answer('Email успешно обновлен!', reply_markup=main)
            await cmd_profile(message, db)
        else:
            await message.answer('Произошла ошибка при обновлении.', reply_markup=main)
    else:
        await message.answer('Пожалуйста, введите корректный email адрес.', reply_markup=cancel_kb)
        return
    await state.clear()

@router.message(Register.age)
async def process_age(message: Message, state: FSMContext, db: Database):
    data = await state.get_data()
    if not data.get('edit_mode'):
        return
        
    if message.text == "Отменить редактирование":
        await cancel_edit(message, state, db)
        return

    if message.text.isdigit():
        if await db.update_user_field(message.from_user.id, 'age', int(message.text)):
            await message.answer('Возраст успешно обновлен!', reply_markup=main)
            await cmd_profile(message, db)
        else:
            await message.answer('Произошла ошибка при обновлении.', reply_markup=main)
    else:
        await message.answer('Пожалуйста, введите корректный возраст (целое число).', reply_markup=cancel_kb)
        return
    await state.clear()

@router.message(Register.photo, F.photo)
async def process_photo(message: Message, state: FSMContext, db: Database):
    data = await state.get_data()
    if not data.get('edit_mode'):
        return
        
    if await db.update_user_field(message.from_user.id, 'photo_id', message.photo[-1].file_id):
        await message.answer('Фото успешно обновлено!', reply_markup=main)
        await cmd_profile(message, db)
    else:
        await message.answer('Произошла ошибка при обновлении.', reply_markup=main)
    await state.clear()

@router.message(Register.contact, F.contact)
async def process_contact(message: Message, state: FSMContext, db: Database):
    data = await state.get_data()
    if not data.get('edit_mode'):
        return
        
    if await db.update_user_field(message.from_user.id, 'phone_number', message.contact.phone_number):
        await message.answer('Номер телефона успешно обновлен!', reply_markup=main)
        await cmd_profile(message, db)
    else:
        await message.answer('Произошла ошибка при обновлении.', reply_markup=main)
    await state.clear()

@router.message(Register.location, F.location)
async def process_location(message: Message, state: FSMContext, db: Database):
    data = await state.get_data()
    if not data.get('edit_mode'):
        return
        
    try:
        if (await db.update_user_field(message.from_user.id, 'location_lat', message.location.latitude) and
            await db.update_user_field(message.from_user.id, 'location_lon', message.location.longitude)):
            await message.answer('Локация успешно обновлена!', reply_markup=main)
            await cmd_profile(message, db)
        else:
            await message.answer('Произошла ошибка при обновлении.', reply_markup=main)
    except Exception as e:
        logging.error(f"Ошибка при обновлении локации: {e}")
        await message.answer('Произошла ошибка при обновлении.', reply_markup=main)
    await state.clear()

@router.callback_query(F.data == "back")
async def back_to_profile(callback: CallbackQuery, db: Database):
    await callback.message.delete()
    await cmd_profile(callback.message, db) 