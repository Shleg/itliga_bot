from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest

from tgbot.config import Config
from tgbot.models.db_commands import get_closed_app, create_messages


async def close_app(bot: Bot, config: Config):
    applications = await get_closed_app()
    for app in applications:
        if app.message_thread_id:
            try:
                await bot.delete_forum_topic(chat_id=config.misc.chat_support, message_thread_id=app.message_thread_id)
            except TelegramBadRequest:
                pass
        app.status = 'closed'
        app.message_thread_id = None
        app.save()
        await create_messages('admin', f'Админ (БОТ)', app, 'text', f'Заявка автоматически закрыта')
