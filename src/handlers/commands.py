from aiogram import Bot
from aiogram.types import BotCommand

async def set_commands(bot: Bot):
    """
    Установка команд бота в меню.
    
    Команды:
    - /start - Начало работы с ботом
    - /menu - Показ доступных команд
    - /help - Получение справки
    - /profile - Просмотр профиля пользователя
    - /settings - Настройки пользователя
    - /register - Регистрация нового пользователя
    - /catalog - Просмотр каталога товаров
    """
    commands = [
        BotCommand(command='start', description='Запустить бота'),
        BotCommand(command='menu', description='Показать меню команд'),
        BotCommand(command='help', description='Получить помощь'),
        BotCommand(command='profile', description='Мой профиль'),
        BotCommand(command='settings', description='Настройки'),
        BotCommand(command='register', description='Регистрация в боте'),
        BotCommand(command='catalog', description='Просмотр каталога товаров')
    ]
    await bot.set_my_commands(commands)