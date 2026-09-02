from aiogram import BaseMiddleware
from aiogram.types import TelegramObject

from bot.database.dao import get_user_language


class LanguageMiddleware(BaseMiddleware):
    async def __call__(self, handler, event: TelegramObject, data: dict):
        user_id = None
        if hasattr(event, "from_user") and event.from_user:
            user_id = event.from_user.id

        if user_id:
            lang = await get_user_language(user_id)
            data["lang"] = lang if lang else "ru"
        else:
            data["lang"] = "ru"

        return await handler(event, data)
