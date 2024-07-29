from aiogram import types, Router, F
from aiogram.fsm.context import FSMContext

from tgbot.keyboards.inline import accept_create_app_kb
from tgbot.models.db_commands import select_client

echo_router = Router()
echo_router.message.filter(F.chat.type == 'private')


@echo_router.message(F.text)
async def bot_echo(message: types.Message, state: FSMContext):
    user = await select_client(message.chat.id)
    await state.update_data(text=message.text)
    await message.answer(text='\n'.join([
        f'Подтвердите: \n'
        f'Компания: {user.company}',
        f'ФИО: {user.fcs}',
        f'Текст заявки: {message.text}'
    ]), reply_markup=await accept_create_app_kb())
