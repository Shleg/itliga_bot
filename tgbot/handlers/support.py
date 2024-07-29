from datetime import datetime

import pytz
from aiogram import Router, Bot
from aiogram.exceptions import TelegramForbiddenError
from aiogram.filters import Command
from aiogram.types import Message

from admin_panel.telebot.models import Application
from tgbot.config import Config
from tgbot.filters.admin import AnswerSupportFilter
from tgbot.keyboards.inline import feed_back_kb
from tgbot.misc.tools import support_chat, create_message_history
from tgbot.models.db_commands import get_app_by_thread_id, create_messages, get_operator

support_router = Router()
support_router.message.filter(AnswerSupportFilter())


@support_router.message(Command(commands=["finish"]))
async def answer_support(message: Message, bot: Bot, config: Config):
    if not message.message_thread_id:
        return
    app: Application = await get_app_by_thread_id(message.message_thread_id)
    if not app:
        return
    await create_messages('admin', f'Админ ({message.from_user.full_name})', app, 'text',
                          "✅ Оператор отметил заявку выполненной")
    await bot.send_message(text='\n'.join([
        f'Заявка №{app.pk} отмечена выполненной, пожалуйста оцените работу оператора 👇'
    ]), chat_id=app.user.telegram_id, reply_markup=await feed_back_kb(app.pk))
    await bot.send_message(chat_id=config.misc.chat_support, message_thread_id=message.message_thread_id,
                           text='✅ Заявка перешла в статус выполнена')
    operator = await get_operator(message.from_user.id, message.from_user.username, message.from_user.full_name,
                                  message.from_user)
    app.status = 'done'
    app.completed_time = datetime.now(pytz.timezone('Europe/Moscow'))
    app.operator = operator
    app.save()


@support_router.message()
async def answer_support(message: Message, bot: Bot, config: Config):
    if not message.message_thread_id:
        return
    app: Application = await get_app_by_thread_id(message.message_thread_id)
    if not app:
        return
    if app.status == 'open':
        app.status = 'in_work'
        app.save()
    try:
        await create_message_history(message, sender='admin', app=app, bot=bot,
                                     author=f'Админ ({message.from_user.full_name})')
        await support_chat(bot, message, app.user.telegram_id, app_id=app.pk, app_text=app.text)
    except TelegramForbiddenError:
        await bot.send_message(chat_id=config.misc.chat_support, message_thread_id=message.message_thread_id,
                               text='❌ Не удалось отправить сообщение пользователю')
