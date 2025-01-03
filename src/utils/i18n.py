from typing import Dict
from ..database import requests as db

texts = {
    'ru': {
        # Настройки
        'settings_title': '⚙️ Настройки\n\nВыберите раздел настроек:',
        'notifications_settings': '🔔 Настройки уведомлений\n\nВключить или выключить уведомления:',
        'language_settings': '🌍 Выберите язык интерфейса:',
        'notifications_on': '🔔 Уведомления включены',
        'notifications_off': '🔕 Уведомления выключены',
        'language_changed': '🌍 Язык изменен на русский',
        'error': 'Произошла ошибка',
        
        # Кнопки настроек
        'btn_notifications': '🔔 Уведомления',
        'btn_language': '🌍 Язык',
        'btn_back': '◀️ Назад',
        'btn_notif_on': '🔔 Вкл',
        'btn_notif_off': '🔕 Выкл',
        'btn_lang_ru': '🇷🇺 Русский',
        'btn_lang_en': '🇬🇧 English'
    },
    'en': {
        # Settings
        'settings_title': '⚙️ Settings\n\nSelect settings section:',
        'notifications_settings': '🔔 Notification Settings\n\nEnable or disable notifications:',
        'language_settings': '🌍 Choose interface language:',
        'notifications_on': '🔔 Notifications enabled',
        'notifications_off': '🔕 Notifications disabled',
        'language_changed': '🌍 Language changed to English',
        'error': 'An error occurred',
        
        # Settings buttons
        'btn_notifications': '🔔 Notifications',
        'btn_language': '🌍 Language',
        'btn_back': '◀️ Back',
        'btn_notif_on': '🔔 On',
        'btn_notif_off': '🔕 Off',
        'btn_lang_ru': '🇷🇺 Russian',
        'btn_lang_en': '🇬🇧 English'
    }
}

async def get_text(key: str, user_id: int) -> str:
    """Получение текста на языке пользователя"""
    user_lang = await db.get_user_language(user_id)
    return texts.get(user_lang, texts['ru']).get(key, texts['ru'][key]) 