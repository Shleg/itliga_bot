from typing import Callable, Dict, Any, Awaitable

from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery

from tgbot.models.db_commands import select_client


class BlockUser(BaseMiddleware):
    async def __call__(
            self,
            handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
            event: Message,
            data: Dict[str, Any]
    ) -> Any:
        if isinstance(event, CallbackQuery):
            user = await select_client(event.message.chat.id)
        else:
            user = await select_client(event.chat.id)
        if not user or not user.is_blocked:
            return await handler(event, data)


