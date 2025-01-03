from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
import src.keyboards as kb
from ..database import requests as db
import logging
from ..utils.i18n import get_text

router = Router()

@router.message(Command("settings"))
async def show_settings(message: Message):
    """Показ настроек пользователя"""
    settings_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text=await get_text('btn_notifications', message.from_user.id),
                callback_data="settings_notifications"
            ),
            InlineKeyboardButton(
                text=await get_text('btn_language', message.from_user.id),
                callback_data="settings_language"
            )
        ],
        [InlineKeyboardButton(
            text=await get_text('btn_back', message.from_user.id),
            callback_data="back_to_main"
        )]
    ])
    
    await message.answer(
        await get_text('settings_title', message.from_user.id),
        reply_markup=settings_keyboard
    )

@router.callback_query(F.data == "settings_notifications")
async def show_notifications_settings(callback: CallbackQuery):
    """Настройки уведомлений"""
    try:
        await callback.message.edit_text(
            await get_text('notifications_settings', callback.from_user.id),
            reply_markup=kb.notifications_keyboard
        )
    except Exception as e:
        logging.error(f"Ошибка при показе настроек уведомлений: {e}")
        await callback.answer(await get_text('error', callback.from_user.id))

@router.callback_query(F.data == "settings_language")
async def show_language_settings(callback: CallbackQuery):
    """Настройки языка"""
    try:
        await callback.message.edit_text(
            await get_text('language_settings', callback.from_user.id),
            reply_markup=kb.language_keyboard
        )
    except Exception as e:
        logging.error(f"Ошибка при показе настроек языка: {e}")
        await callback.answer(await get_text('error', callback.from_user.id))

@router.callback_query(F.data.startswith("notif_"))
async def process_notification_setting(callback: CallbackQuery):
    """Обработка настройки уведомлений"""
    try:
        setting = callback.data.split("_")[1]  # on/off
        user_id = callback.from_user.id
        enabled = setting == "on"
        
        if await db.update_user_notifications(user_id, enabled):
            await callback.message.edit_text(
                await get_text('notifications_on' if enabled else 'notifications_off', user_id),
                reply_markup=kb.settings_keyboard
            )
        else:
            await callback.answer(await get_text('error', user_id))
        
    except Exception as e:
        logging.error(f"Ошибка при настройке уведомлений: {e}")
        await callback.answer(await get_text('error', user_id))

@router.callback_query(F.data.startswith("lang_"))
async def process_language_setting(callback: CallbackQuery):
    """Обработка выбора языка"""
    try:
        lang = callback.data.split("_")[1]
        user_id = callback.from_user.id
        
        if await db.update_user_language(user_id, lang):
            # Используем текст в зависимости от выбранного языка
            text = "🌍 Language changed to English" if lang == "en" else "🌍 Язык изменен на русский"
            await callback.message.edit_text(text, reply_markup=kb.settings_keyboard)
        else:
            await callback.answer("Error" if lang == "en" else "Ошибка")
        
    except Exception as e:
        logging.error(f"Ошибка при смене языка: {e}")
        await callback.answer("Error occurred" if lang == "en" else "Произошла ошибка")

@router.callback_query(F.data == "back_to_settings")
async def back_to_settings(callback: CallbackQuery):
    """Возврат к основным настройкам"""
    await show_settings(callback.message) 