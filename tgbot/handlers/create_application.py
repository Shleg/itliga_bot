from aiogram import Router, F, Bot
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from aiogram.utils.markdown import hlink

from tgbot.config import Config
from tgbot.keyboards.inline import back_to_manu_kb, accept_create_app_kb
from tgbot.keyboards.reply import close_support_chat_kb
from tgbot.misc.states import States
from tgbot.misc.tools import check_time_status
from tgbot.models.db_commands import select_client, create_app, create_messages, get_not_online_message

application_router = Router()
application_router.message.filter(F.chat.type == 'private')


@application_router.callback_query(F.data == "create_application")
async def back_to_manu(call: CallbackQuery, state: FSMContext):
    await state.set_state(States.text)
    await call.message.edit_text(text='\n'.join([
        f'Опишите проблему текстом ниже. 👇\n',
        f'Обратите внимание! Фото, аудио и видео файлы по желанию Вы сможете приложить в следующих сообщениях.'
    ]), reply_markup=await back_to_manu_kb())


@application_router.message(States.text)
async def set_fcs(message: Message, state: FSMContext):
    user = await select_client(message.chat.id)
    await state.set_state(None)
    await state.update_data(text=message.text)
    await message.answer(text='\n'.join([
        f'Подтвердите: \n'
        f'Компания: {user.company}',
        f'ФИО: {user.fcs}',
        f'Текст заявки: {message.text}'
    ]), reply_markup=await accept_create_app_kb())


@application_router.callback_query(F.data == "accept_create_app")
async def accept_create_app(call: CallbackQuery, state: FSMContext, bot: Bot, config: Config):
    data = await state.get_data()
    user = await select_client(call.message.chat.id)
    if call.from_user.username:
        username = f"(@{call.from_user.username})"
    else:
        username = f''
    app = await create_app(user, data.get("text"))
    topic = await bot.create_forum_topic(config.misc.chat_support, name=f'Заявка №{app.pk}')
    await create_messages('user', f'Пользователь ({call.from_user.full_name})', app, 'text', data.get("text"))
    await bot.send_message(
        chat_id=config.misc.chat_support,
        text='\n'.join([
            f'📧 {hlink(f"{call.from_user.full_name} {username}", call.from_user.url)}',
            f'Компания: {user.company}',
            f'ФИО: {user.fcs}',
            f'Текст заявки: {data.get("text")}'
        ]), message_thread_id=topic.message_thread_id)
    app.message_thread_id = topic.message_thread_id
    app.save()
    await state.update_data(app_id=app.pk)
    await call.message.delete()
    await state.set_state(States.dialog)
    await call.message.answer(text='\n'.join([
        f'Заявка №{app.pk} успешно создана, ожидайте пока с вами свяжется оператор '
    ]), reply_markup=await close_support_chat_kb())

    status = await check_time_status()
    if not status:
        not_online_message = await get_not_online_message()
        await call.message.answer(text=not_online_message)
        await create_messages('admin', f'Админ (БОТ)', app, 'text', not_online_message)
