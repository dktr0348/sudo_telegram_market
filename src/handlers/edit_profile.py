from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
import re
import logging
from ..database.database import Database
from ..keyboards import (profile_keyboard, send_contact, 
                        send_location, main, confirm_keyboard,
                        cancel_keyboard)
from ..state import EditProfile
from .user import cmd_profile

router = Router()

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
        'name': EditProfile.edit_name,
        'email': EditProfile.edit_email,
        'phone': EditProfile.edit_contact,
        'age': EditProfile.edit_age,
        'photo': EditProfile.edit_photo,
        'location': EditProfile.edit_location
    }
    
    await state.set_state(states[edit_type])
    await state.update_data(edit_mode=True, edit_type=edit_type)
    
    if edit_type == 'phone':
        kb = send_contact
    elif edit_type == 'location':
        kb = send_location
    else:
        kb = cancel_keyboard
    
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

# Обработчик подтверждения изменений
@router.message(F.text == "Подтвердить")
async def confirm_edit(message: Message, state: FSMContext, db: Database):
    data = await state.get_data()
    if not data.get('edit_mode'):
        return
    
    edit_type = data.get('edit_type')
    new_value = data.get('new_value')
    
    field_mapping = {
        'name': 'name',
        'email': 'email',
        'phone': 'phone_number',
        'age': 'age',
        'photo': 'photo_id'
    }
    
    try:
        if edit_type == 'location':
            lat = data.get('new_value_lat')
            lon = data.get('new_value_lon')
            success = await db.update_user_field(message.from_user.id, 'location_lat', lat)
            success = success and await db.update_user_field(message.from_user.id, 'location_lon', lon)
        elif edit_type in field_mapping:
            success = await db.update_user_field(message.from_user.id, field_mapping[edit_type], new_value)
        
        if success:
            await message.answer(f'{edit_type.capitalize()} успешно обновлен!', reply_markup=main)
            await cmd_profile(message, db)
        else:
            await message.answer('Произошла ошибка при обновлении.', reply_markup=main)
    except Exception as e:
        logging.error(f"Ошибка при обновлении: {e}")
        await message.answer('Произошла ошибка при обновлении.', reply_markup=main)
    finally:
        await state.clear()

@router.message(EditProfile.edit_photo, F.photo)
async def process_photo(message: Message, state: FSMContext):
    """Обработка нового фото профиля"""
    try:
        photo_id = message.photo[-1].file_id
        await state.update_data(new_value=photo_id, edit_mode=True, edit_type='photo')
        
        # Сначала отправляем сообщение с подтверждением
        await message.answer(
            'Установить это фото в качестве фото профиля?',
            reply_markup=confirm_keyboard
        )
        # Затем отправляем фото
        await message.answer_photo(photo=photo_id)
    except Exception as e:
        logging.error(f"Ошибка при обработке фото: {e}")
        await message.answer(
            "Произошла ошибка при обработке фото. Попробуйте еще раз или отмените редактирование.",
            reply_markup=cancel_keyboard
        )

@router.message(EditProfile.edit_photo)
async def wrong_photo(message: Message):
    await message.answer("Пожалуйста, отправьте фото", reply_markup=cancel_keyboard)

@router.message(EditProfile.edit_contact, F.contact)
async def process_contact(message: Message, state: FSMContext):
    """Обработка нового номера телефона"""
    try:
        await state.update_data(new_value=message.contact.phone_number, edit_mode=True, edit_type='phone')
        await message.answer(
            f'Вы хотите изменить номер телефона на {message.contact.phone_number}?',
            reply_markup=confirm_keyboard
        )
    except Exception as e:
        logging.error(f"Ошибка при обработке контакта: {e}")
        await message.answer(
            "Произошла ошибка. Попробуйте еще раз или отмените редактирование.",
            reply_markup=cancel_keyboard
        )

@router.message(EditProfile.edit_contact)
async def wrong_contact(message: Message):
    await message.answer("Пожалуйста, используйте кнопку для отправки контакта", reply_markup=send_contact)

@router.message(EditProfile.edit_location)
async def wrong_location(message: Message):
    if not message.location:
        await message.answer("Пожалуйста, используйте кнопку для отправки локации", reply_markup=send_location)

@router.message(EditProfile.edit_name)
async def process_name(message: Message, state: FSMContext):
    if message.text == "Отменить редактирование":
        await cancel_edit(message, state)
        return
    
    await state.update_data(new_value=message.text)
    await message.answer(f'Вы хотите изменить имя на "{message.text}"?', reply_markup=confirm_keyboard)

@router.message(EditProfile.edit_email)
async def process_email(message: Message, state: FSMContext):
    if message.text == "Отменить редактирование":
        await cancel_edit(message, state)
        return

    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if re.match(email_pattern, message.text):
        await state.update_data(new_value=message.text)
        await message.answer(f'Вы хотите изменить email на "{message.text}"?', reply_markup=confirm_keyboard)
    else:
        await message.answer('Пожалуйста, введите корректный email адрес.', reply_markup=cancel_keyboard)

@router.message(EditProfile.edit_age)
async def process_age(message: Message, state: FSMContext):
    if message.text == "Отменить редактирование":
        await cancel_edit(message, state)
        return

    if message.text.isdigit():
        await state.update_data(new_value=int(message.text))
        await message.answer(f'Вы хотите изменить возраст на {message.text}?', reply_markup=confirm_keyboard)
    else:
        await message.answer('Пожалуйста, введите корректный возраст (целое число).', reply_markup=cancel_keyboard)

@router.callback_query(F.data == "back")
async def back_to_profile(callback: CallbackQuery, db: Database):
    await callback.message.delete()
    await cmd_profile(callback.message, db)

@router.message(EditProfile.edit_location, F.location)
async def process_location(message: Message, state: FSMContext):
    """Обработка новой локации"""
    try:
        await state.update_data(
            new_value_lat=message.location.latitude,
            new_value_lon=message.location.longitude,
            edit_mode=True,
            edit_type='location'
        )
        await message.answer(
            'Вы хотите установить эту локацию?',
            reply_markup=confirm_keyboard
        )
    except Exception as e:
        logging.error(f"Ошибка при обработке локации: {e}")
        await message.answer(
            "Произошла ошибка. Попробуйте еще раз или отмените редактирование.",
            reply_markup=cancel_keyboard
        )
 