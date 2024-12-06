import asyncio
from aiogram import Dispatcher, Bot
from handlers import router
from bot_commands import set_commands
from database import Database
from middleware import DatabaseMiddleware

async def main():
    bot = Bot(token='7188432169:AAHKMW8XYbf9PSFQ_PmzmXcbwfSM0uPtTgc')
    dp = Dispatcher()
    
    # Инициализация базы данных
    db = Database('bot_database.db')
    
    # Регистрация middleware
    dp.message.middleware(DatabaseMiddleware(db))
    
    # Регистрация роутера
    dp.include_router(router)
    
    # Установка команд бота
    await set_commands(bot)
    
    # Запуск бота
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()
        db.close()

if __name__ == '__main__':
    asyncio.run(main())