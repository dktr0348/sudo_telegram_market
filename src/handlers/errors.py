from aiogram import Router
from aiogram.types import ErrorEvent

router = Router()

@router.errors()
async def error_handler(event: ErrorEvent):
    # Обработка ошибок
    print(f"Произошла ошибка: {event.exception}") 