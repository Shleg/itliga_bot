from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest

from tgbot.config import load_config


async def close_thread(message_thread_id):
    config = load_config(".env")
    bot = Bot(token=config.tg_bot.token, parse_mode='HTML')
    try:
        await bot.delete_forum_topic(chat_id=config.misc.chat_support, message_thread_id=message_thread_id)
    except TelegramBadRequest:
        pass
