from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message, CallbackQuery

from config import ADMIN_IDS


class AuthMiddleware(BaseMiddleware):
    """Пропускает только пользователей из списка ADMIN_IDS."""

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        user = data.get("event_from_user")

        if user is None or user.id not in ADMIN_IDS:
            if isinstance(event, Message):
                await event.answer("⛔ Доступ запрещён.")
            elif isinstance(event, CallbackQuery):
                await event.answer("⛔ Доступ запрещён.", show_alert=True)
            return  # не передаём дальше

        return await handler(event, data)
