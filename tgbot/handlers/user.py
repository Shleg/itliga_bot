from aiogram import Router, F, Bot
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, BufferedInputFile
from aiogram.utils.markdown import hbold

from tgbot.config import Config
from tgbot.keyboards.inline import menu_kb, first_kb, back_to_manu_kb
from tgbot.misc.generate_sheet import generate_statistic
from tgbot.misc.states import States
from tgbot.misc.tools import support_chat, create_message_history, check_time_status
from tgbot.models.db_commands import select_client, create_client, get_app, create_messages, get_not_online_message, \
    get_application_by_company

user_router = Router()
user_router.message.filter(F.chat.type == 'private')


@user_router.message(Command(commands=["start"]))
async def user_start(message: Message, state: FSMContext):
    user = await select_client(message.chat.id)
    if not user:
        await create_client(message.from_user.username, message.chat.id, message.from_user.url,
                            message.from_user.full_name)
        return await message.answer(text='\n'.join([
            f'Привет! Это чат с инженерами службы технической поддержки ITLiga. Мы будем рады Вам помочь.'
        ]), reply_markup=await first_kb())
    if not user.fcs or not user.company:
        await state.set_state(States.fcs)
        return await message.answer(text='Введите ваше ФИО ниже 👇')
    await message.answer('Выберите: ', reply_markup=await menu_kb(user.export))


@user_router.message(States.dialog, F.text == 'Завершить диалог')
async def close_dialog(message: Message, config: Config, bot: Bot, state: FSMContext):
    await state.set_state(None)
    data = await state.get_data()
    await user_start(message, state)
    app = await get_app(data.get('app_id'))
    await create_messages('user', f'Пользователь ({message.from_user.full_name})', app, 'text',
                          "✅ Пользователь завершил диалог")
    await bot.send_message(chat_id=config.misc.chat_support, text=hbold("✅ Пользователь завершил диалог"),
                           message_thread_id=app.message_thread_id)


@user_router.callback_query(F.data == "support")
async def support(call: CallbackQuery):
    await call.message.edit_text(text='Телефон: 84953692434', reply_markup=await back_to_manu_kb())


@user_router.callback_query(F.data == "back_to_menu")
async def back_to_manu(call: CallbackQuery, state: FSMContext):
    await call.message.delete()
    await user_start(call.message, state)


@user_router.callback_query(F.data == "export_exel_user")
async def export_exel_user(call: CallbackQuery):
    await call.message.delete()
    user = await select_client(call.message.chat.id)
    applications = await get_application_by_company(user.company)
    document_buffer = await generate_statistic(applications)
    document = BufferedInputFile(document_buffer.getvalue(), filename='Статистика.xlsx')
    await call.message.answer_document(document=document, caption='Ваша статистика 👆',
                                       reply_markup=await back_to_manu_kb())


@user_router.message(States.fcs)
async def set_fcs(message: Message, state: FSMContext):
    await state.set_state(States.company)
    await state.update_data(fcs=message.text)
    await message.answer(text='Введите название вашей компании ниже 👇')


@user_router.message(States.company)
async def set_company(message: Message, state: FSMContext):
    data = await state.get_data()
    user = await select_client(message.chat.id)
    user.fcs = data.get('fcs')
    user.company = message.text
    user.save()
    await user_start(message, state)


@user_router.message(States.dialog)
async def support_dialog(message: Message, config: Config, bot: Bot, state: FSMContext):
    data = await state.get_data()
    app = await get_app(data.get('app_id'))
    if app.status in ['closed', 'done']:
        return await message.answer(
            text=f'Заявка №{app.pk} была закрыта, для возобновления общения перейдите к заявке и верните ее в работу')
    status = await check_time_status()
    if not status:
        not_online_message = await get_not_online_message()
        await message.answer(text=not_online_message)
        await create_messages('admin', f'Админ (БОТ)', app, 'text', not_online_message)

    await create_message_history(message, sender='user', app=app, bot=bot,
                                 author=f'Пользователь ({message.from_user.full_name})')
    print(app.message_thread_id)
    await support_chat(bot, message, config.misc.chat_support, app.message_thread_id)
