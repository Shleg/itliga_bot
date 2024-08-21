import os

import aiosmtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from aiogram import Router, Bot, F
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery
from aiogram.utils.markdown import hlink

from admin_panel.telebot.models import Application
from tgbot.config import Config
from tgbot.keyboards.callback_data import UserAppCallback, ShowAppInfo, CompletedCommunication, BackInWork, \
    GradeCallback
from tgbot.keyboards.inline import user_application_kb, app_info_kb_kb, back_to_manu_2_kb, menu_kb
from tgbot.keyboards.reply import close_support_chat_kb
from tgbot.misc.states import States
from tgbot.misc.tools import pagination
from tgbot.models.db_commands import select_client, get_app, create_messages

app_info_router = Router()
app_info_router.message.filter(F.chat.type == 'private')


@app_info_router.callback_query(UserAppCallback.filter())
async def user_application(call: CallbackQuery, callback_data: UserAppCallback, state: FSMContext):
    await call.answer()
    user = await select_client(call.message.chat.id)
    await state.update_data(method=callback_data.method)
    current_idx = callback_data.current_idx
    if callback_data.method == 'work':
        objects = user.applications.filter(status__in=['open', 'in_work'])
    else:
        objects = user.applications.filter(status__in=['done', 'closed'])

    categories, current_idx, current_page = await pagination(objects, current_idx, 5)
    try:
        await call.message.edit_text('Выберите интересующую вас категорию 👇',
                                     reply_markup=await user_application_kb(categories, current_idx, current_page,
                                                                            callback_data.method))
    except TelegramBadRequest:
        pass


@app_info_router.callback_query(ShowAppInfo.filter())
async def shows_app_info(call: CallbackQuery, callback_data: ShowAppInfo, state: FSMContext):
    data = await state.get_data()
    app: Application = await get_app(callback_data.id)
    await call.message.edit_text(text='\n'.join([
        f'Данные заявки №{app.pk} {app.created.strftime("%d.%m.%Y %H:%M")}\n',
        f'Компания: {app.user.company}',
        f'Текст обращения: {app.text}\n',
        f'Статус: {app.get_status_display()}'
    ]), reply_markup=await app_info_kb_kb(app.status, data.get('method'), app.pk))


@app_info_router.callback_query(CompletedCommunication.filter())
async def shows_app_info(call: CallbackQuery, callback_data: CompletedCommunication, state: FSMContext):
    await state.update_data(app_id=callback_data.id)
    await call.message.delete()
    await state.set_state(States.dialog)
    await call.message.answer(text='\n'.join([
        f'Можете продолжить общение по заявке 👇'
    ]), reply_markup=await close_support_chat_kb())


@app_info_router.callback_query(BackInWork.filter())
async def shows_app_info(call: CallbackQuery, callback_data: BackInWork, state: FSMContext, bot: Bot, config: Config):
    app: Application = await get_app(callback_data.id)
    user = await select_client(call.message.chat.id)
    if not app.message_thread_id:
        topic = await bot.create_forum_topic(config.misc.chat_support, name=f'Заявка №{app.pk}')
        if call.from_user.username:
            username = f"(@{call.from_user.username})"
        else:
            username = f''
        await bot.send_message(
            chat_id=config.misc.chat_support,
            text='\n'.join([
                f'📧 {hlink(f"{call.from_user.full_name} {username}", call.from_user.url)}',
                f'Компания: {user.company}',
                f'ФИО: {user.fcs}',
                f'Текст заявки: {app.text}\n',
                f'Пользователь вернул заявку в работу'
            ]), message_thread_id=topic.message_thread_id)
        app.message_thread_id = topic.message_thread_id
    await create_messages('user', f'Пользователь ({call.from_user.full_name})', app, 'text',
                          'Пользователь вернул заявку в работу')
    app.status = 'in_work'
    app.save()
    await state.update_data(app_id=app.pk)
    await call.message.delete()
    await state.set_state(States.dialog)
    await call.message.answer(text='\n'.join([
        f'Заявка №{app.pk} возвращена в работу, можете вести диалог 👇'
    ]), reply_markup=await close_support_chat_kb())


@app_info_router.callback_query(GradeCallback.filter())
async def grade_app(call: CallbackQuery, callback_data: GradeCallback, state: FSMContext, bot: Bot, config: Config):
    await state.set_state(None)
    app: Application = await get_app(callback_data.id)
    try:
        await bot.delete_forum_topic(chat_id=config.misc.chat_support, message_thread_id=app.message_thread_id)
    except TelegramBadRequest:
        pass
    app.grade = callback_data.grade
    app.status = 'closed'
    app.message_thread_id = None
    app.save()

    await call.message.edit_text(text='Благодарим за обратную связь. Заявка успешно закрыта',
                                 reply_markup=await menu_kb(app.user.export))
    await create_messages('user', f'Пользователь ({call.from_user.full_name})', app, 'text',
                          f'Пользователь поставил оценку заявке: {callback_data.grade} ⭐️')

    # Отправка письма
    await send_email(app.pk, app.text, callback_data.grade)


async def send_email(app_id, app_text, grade):
    sender_email = os.getenv('SENDER_EMAIL')
    auth_email = os.getenv('AUTH_EMAIL')
    receiver_email = os.getenv('RECEIVER_EMAIL')
    password = os.getenv('EMAIL_PASSWORD')
    smtp_server = os.getenv('SMTP_SERVER')
    smtp_port = os.getenv('SMTP_PORT')

    message = MIMEMultipart("alternative")
    message["Subject"] = f"Заявка {app_id} {app_text[:20]}"
    message["From"] = sender_email
    message["To"] = receiver_email

    text = f"Заявка №{app_id}\nТекст заявки:\n{app_text}\nОценка: {grade} ⭐️"

    part = MIMEText(text, "plain")
    message.attach(part)

    try:
        await aiosmtplib.send(
            message,
            hostname=smtp_server,
            port=smtp_port,
            username=auth_email,  # Аутентификация под telegram-bot@itliga.lan
            password=password,
            start_tls=True,
        )
    except Exception as e:
        print(f"Error sending email: {e}")
