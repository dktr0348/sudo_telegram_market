from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import Message
from ..database.database import Database

class DatabaseMiddleware(BaseMiddleware):
    def __init__(self, db_session: Database):
        self.db_session = db_session
        super().__init__()

    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any]
    ) -> Any:
        data['db'] = self.db_session
        return await handler(event, data) 