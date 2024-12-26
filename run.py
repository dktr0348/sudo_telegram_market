import asyncio
import logging
import os
from pathlib import Path
from aiogram import Bot, Dispatcher
from src.config import load_config
from src.database.database import Database
from src.middlewares.database import DatabaseMiddleware
from src.handlers import user, admin, errors, edit_profile, order

# Получаем путь к корневой директории проекта
BASE_DIR = Path(__file__).parent

async def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    )

    config = load_config()
    
    # Создаем путь к файлу БД относительно корневой директории
    db_path = BASE_DIR / config.database_path
    
    bot = Bot(token=config.token)
    dp = Dispatcher()
    
    db = Database(str(db_path))
    await db.init_db()  # Инициализируем базу данных
    
    dp.update.middleware(DatabaseMiddleware(db))
    
    dp.include_router(user.router)
    dp.include_router(admin.router)
    dp.include_router(errors.router)
    dp.include_router(edit_profile.router)
    dp.include_router(order.router)
    
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()
        await db.close()

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Бот остановлен")