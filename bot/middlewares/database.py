"""Database middleware for providing session to handlers"""
from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery
from database.engine import db


class DatabaseMiddleware(BaseMiddleware):
    
    async def __call__(
        self,
        handler: Callable[[Message | CallbackQuery, Dict[str, Any]], Awaitable[Any]],
        event: Message | CallbackQuery,
        data: Dict[str, Any]
    ) -> Any:
        """Provide database session"""
        async for session in db.get_session():
            data["session"] = session
            return await handler(event, data)