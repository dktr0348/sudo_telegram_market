from aiogram import Router, F, Bot
from aiogram.types import (CallbackQuery, Message, ReplyKeyboardMarkup, 
                           ReplyKeyboardRemove, BotCommand)
from aiogram.filters import CommandStart, Command


async def set_commands(bot: Bot):
    commands = [
        BotCommand(
            command='start',
            description='Запустить бота'
        ),
        BotCommand(
            command='menu',
            description='Показать меню команд'
        ),
        BotCommand(
            command='help',
            description='Получить помощь' 
        ),
        BotCommand(
            command='profile',
            description='Мой профиль'
        ),
        BotCommand(
            command='settings',
            description='Настройки'
        ),
        BotCommand(
            command='register',
            description='Регистрация в боте'
        )
    ]
    await bot.set_my_commands(commands)
    print("Команды установлены:", commands)